import sys,json,zipfile,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathsnap.core import ROOT

def add_tree(z,path):
    for p in sorted(path.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,p.relative_to(ROOT).as_posix())

def main():
    out=ROOT/'packages';out.mkdir(exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    provenance={'source_commit':commit,'model_sha256':hashlib.sha256((ROOT/'artifacts'/'model.joblib').read_bytes()).hexdigest(),
                'implementation':'Audited prediction pipeline with refreshed UI and separate reference display; no training during packaging',
                'public_publication_verified':False,'physical_two_laptop_verified':False}
    def stamp(z):
        z.writestr('SOURCE_COMMIT.txt',commit+'\n')
        z.writestr('PROVENANCE.json',json.dumps(provenance,indent=2))
    ui=out/'PathSnap_Laptop2_UI.zip'
    guide='''# Laptop 2 - UI only

1. Extract this ZIP. Install/use Python 3 if not already available.
2. Double-click run_ui.cmd, or run: python -m http.server 8080 --directory ui
3. Open http://localhost:8080.
4. Click the connection settings gear. Enter http://<Laptop1-IPv4>:<backend-port>.
5. Both laptops must be on the same reachable network. Laptop 1 must run the backend bound to 0.0.0.0.
6. Verify all ten active trip options and watch live request IDs on Laptop 1.

There is no model, raw data, reference route or ground-truth label in this archive. Do not transfer those to the UI laptop. The full physical two-laptop rehearsal remains a team verification step. Optional port: run_ui.cmd 8090.
'''
    with zipfile.ZipFile(ui,'w',zipfile.ZIP_DEFLATED) as z:
        add_tree(z,ROOT/'ui');z.write(ROOT/'run_ui.cmd','run_ui.cmd');z.writestr('LAPTOP2_README.md',guide)
        for name in ['DEPLOYMENT.md','LAPTOP2_SETUP.md','DEMO_SCRIPT.md','REMOTE_TWO_LAPTOP.md']:z.write(ROOT/'docs'/name,'docs/'+name)
        z.write(ROOT/'FINAL_HANDOFF.md','FINAL_HANDOFF.md');stamp(z)
    with zipfile.ZipFile(ui) as z:
        assert set(z.namelist())=={'ui/index.html','ui/style.css','ui/app.js','run_ui.cmd','LAPTOP2_README.md','docs/DEPLOYMENT.md','docs/LAPTOP2_SETUP.md','docs/DEMO_SCRIPT.md','docs/REMOTE_TWO_LAPTOP.md','FINAL_HANDOFF.md','SOURCE_COMMIT.txt','PROVENANCE.json'}
    backend=out/'PathSnap_Laptop1_Backend.zip'
    with zipfile.ZipFile(backend,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for folder in ['pathsnap','backend','ui','docs']:add_tree(z,ROOT/folder)
        for name in ['model.joblib','manifest.json','decoder.json','decoder_baseline.json']:
            p=ROOT/'artifacts'/name
            if p.exists():z.write(p,'artifacts/'+name)
        for name in ['model_comparison.csv','route_comparison.csv']:z.write(ROOT/'results'/name,'results/'+name)
        add_tree(z,ROOT/'data'/'Student folder'/'student_test')
        add_tree(z,ROOT/'data'/'evaluator_test')
        z.write(ROOT/'scripts'/'demo_hmm.py','scripts/demo_hmm.py')
        for name in ['README.md','FINAL_HANDOFF.md','FINAL_READINESS_AUDIT.md','THIRD_PARTY_NOTICES.md','requirements.lock.txt','setup_backend.cmd','run_backend.cmd']:
            z.write(ROOT/name,name)
        z.write(ROOT/'docs'/'LAPTOP1_SETUP.md','LAPTOP1_README.md')
        stamp(z)
    full=out/'PathSnap_Complete_Local.zip'
    with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for folder in ['pathsnap','backend','ui','scripts','tests','docs','artifacts','results','output','data']:
            add_tree(z,ROOT/folder)
        for name in ['README.md','FINAL_HANDOFF.md','FINAL_READINESS_AUDIT.md','THIRD_PARTY_NOTICES.md','requirements.txt','requirements.lock.txt','requirements-dev.txt','setup_backend.cmd','run_backend.cmd','run_ui.cmd','team.json','pytest.ini','.gitignore','.gitattributes']:
            z.write(ROOT/name,name)
        stamp(z)
    checksums={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ui,backend,full]}
    (out/'checksums.json').write_text(json.dumps(checksums,indent=2))
    manifest={}
    for p in [ui,backend]:
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            assert len(z.namelist())==len(set(z.namelist())),'Duplicate archive members'
            manifest[p.name]=[{'path':n,'bytes':z.getinfo(n).file_size,'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist()]
    (out/'transfer_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(checksums),flush=True)

if __name__=='__main__':main()
