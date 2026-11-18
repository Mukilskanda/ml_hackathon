"""Execute the backend deployment ZIP in isolation using the clean environment."""
import sys,os,json,time,subprocess,zipfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx,pandas as pd
from pathsnap.core import ROOT

def main():
    archive=ROOT/'packages'/'PathSnap_Laptop1_Backend.zip';target=ROOT/'tmp'/'deployment_package_test'
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            path=(target/name).resolve();assert path.is_relative_to(target.resolve())
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    clean=ROOT/'tmp'/'clean_env'/'Scripts'/'python.exe'
    assert clean.exists(),'Create and install the isolated clean environment first'
    env=os.environ.copy();env['OMP_NUM_THREADS']='4';env['OPENBLAS_NUM_THREADS']='4'
    env.pop('PATHSNAP_DATA_ROOT',None)
    log=(ROOT/'tmp'/'deployment_package_server.log').open('wb')
    server=subprocess.Popen([str(clean),'-I','-c',
      'import sys;sys.path.insert(0,sys.argv[1]);import uvicorn;uvicorn.run("backend.app:app",host="127.0.0.1",port=8001,access_log=True)',str(target)],cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT)
    rows=[];browser_checks=[]
    try:
        with httpx.Client(base_url='http://127.0.0.1:8001',timeout=90) as client:
            for attempt in range(100):
                try:
                    if client.get('/api/health').status_code==200:break
                except httpx.TransportError:pass
                time.sleep(.2)
            else:raise RuntimeError('Isolated packaged server did not start')
            listing=client.get('/api/trips').json();assert len(listing['trips'])==10
            expected=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str});expected=expected[expected.method=='audited_hmm'].set_index('trip_id')
            if listing['mode']=='evaluator':
                expected=pd.DataFrame(json.loads((ROOT/'results/evaluator_verification.json').read_text())['records']).set_index('trip_id')
            for trip in listing['trips']:
                response=client.post('/api/predict',json={'trip_id':trip['id']});assert response.status_code==200,response.text
                p=response.json();assert abs(p['metrics']['point_accuracy']-expected.loc[trip['id'],'point_accuracy'])<1e-12
                assert p['observations']==len(p['arc_ids'])
                assert 0<=p['direct_arc_continuity']<=1
                if listing['mode']=='evaluator':
                    import numpy as np
                    assert hashlib.sha256(np.asarray(p['arc_ids'],dtype='<i4').tobytes()).hexdigest()==expected.loc[trip['id'],'prediction_sha256'],'Predicted sequence changed'
                assert not {'labels','reference_route','ground_truth'}&p.keys()
                ref=client.get('/api/reference/'+trip['id']).json()
                if listing['mode']=='evaluator':
                    assert not ref['available'] and 'geometry' not in ref
                else:assert ref['available'] and len(ref['geometry'])==ref['route_arc_count']
                rows.append({'trip_id':trip['id'],'http_status':response.status_code,'observations':p['observations'],'matches_recorded_accuracy':True})
            assert client.get('/api/experiments').status_code==200
        # Optional global browser QA tool tests the isolated packaged app at a
        # nondefault port. The runtime server still uses the clean environment.
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True);page=browser.new_page()
                page.goto('http://127.0.0.1:8001',wait_until='domcontentloaded')
                page.wait_for_function("document.querySelector('#connection').textContent==='Model server online'")
                page.locator('#trip').select_option(listing['trips'][0]['id']);page.locator('#run').click()
                page.wait_for_function("document.querySelector('#observations').textContent!=='—' && !document.querySelector('#run').disabled",timeout=90000)
                if listing['mode']=='evaluator':assert page.locator('[data-layer="reference"]').is_disabled()
                else:assert page.locator('[data-layer="reference"]').is_enabled()
                assert page.locator('#routeContinuity').inner_text()!='—'
                browser_checks.append('Packaged UI auto-connects, infers and displays continuity; reserved reference geometry is withheld from the UI')
                browser.close()
        except ImportError:browser_checks.append('Optional Playwright unavailable; browser portion not executed')
    finally:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(server.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:server.terminate()
        server.wait(timeout=20);log.close()
    ui=ROOT/'packages'/'PathSnap_Laptop2_UI.zip'
    with zipfile.ZipFile(ui) as z:
        assert z.testzip() is None
        forbidden=[n for n in z.namelist() if n.endswith(('.joblib','.track','.route','.nodes','.arcs'))]
        assert not forbidden
        ui_files=z.namelist()
    result={'isolated_archive_execution':True,'isolated_python_environment':True,
      'all_ten_packaged_trip_requests':rows,'browser_checks':browser_checks,
      'ui_archive_contains_no_model_or_dataset_or_reference':True,'ui_archive_members':ui_files,
      'physical_second_laptop_tested':False,
      'model_sha256':hashlib.sha256((target/'artifacts'/'model.joblib').read_bytes()).hexdigest()}
    output=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results'/'critical_audit'/'package_execution.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
