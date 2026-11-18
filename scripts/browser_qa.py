"""Real browser integration checks; requires optional playwright + Chromium."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from pathsnap.core import ROOT
import httpx

def main():
    out=ROOT/'results'/'screenshots';out.mkdir(exist_ok=True)
    report={'physical_two_laptops_tested':False,'origins':['http://127.0.0.1:8080','http://127.0.0.1:8000'],'checks':[]}
    listing=httpx.get('http://127.0.0.1:8000/api/trips').json()
    ids=[t['id'] for t in listing['trips']]
    trip_id='00000052' if '00000052' in ids else '00000023'
    other_id=next(t for t in ids if t!=trip_id)
    report['partition']=listing['mode']
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8080',wait_until='domcontentloaded')
        print('Loaded UI',flush=True)
        page.locator('#settings').click();page.locator('#apiUrl').fill('http://127.0.0.1:8000');page.locator('#saveSettings').click()
        page.wait_for_function("document.querySelector('#trip').options.length === 10")
        report['checks'].append('Separate UI origin loads ten actual active-partition trip options via API')
        print('Ten trips available',flush=True)
        page.locator('#trip').select_option(trip_id);page.locator('#run').click()
        page.wait_for_function("!document.querySelector('#run').disabled && document.querySelector('#observations').textContent !== '—'",timeout=120000)
        assert page.locator('#empty').is_hidden()
        assert page.locator('#accuracy').inner_text()!='—'
        continuity=page.evaluate('result.direct_arc_continuity')
        assert page.locator('#routeContinuity').inner_text()==f'{100*continuity:.2f}%'
        assert page.locator('[data-layer="reference"]').is_enabled()
        assert 'Blue: actual path' in page.locator('#referenceNote').inner_text()
        page.locator('[data-layer="reference"]').uncheck()
        page.locator('[data-layer="reference"]').check()
        report['checks'].append('Actual supplied reference and predicted route are separately toggleable; reference loaded after POST inference')
        page.locator('#scrub').fill('100');page.locator('#scrub').dispatch_event('input')
        page.locator('#zoomIn').click();page.locator('#fit').click()
        page.locator('#map').focus();page.keyboard.press('ArrowLeft');page.keyboard.press('Home')
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(out/'ui_desktop.png'),full_page=True)
        print('Desktop screenshot captured',flush=True)
        report['checks'].append('Live POST inference, nonempty route/metrics, playback, zoom and keyboard map controls')
        # Delay a real request to make the transient loading state observable.
        def delayed_request(route):
            time.sleep(1)
            route.continue_()
        page.route('**/api/predict', delayed_request)
        page.locator('#run').click()
        assert page.locator('#loading').is_visible()
        assert page.locator('#settings').is_disabled()
        assert page.locator('#export').is_disabled()
        page.wait_for_function("!document.querySelector('#run').disabled",timeout=120000)
        assert page.locator('#loading').is_hidden()
        page.unroute('**/api/predict', delayed_request)
        with page.expect_download() as download_info:
            page.locator('#export').click()
        download=download_info.value
        exported=json.loads(Path(download.path()).read_text())
        assert exported['trip_id']==trip_id and exported['observations']>0
        assert exported['reference']['available'] and len(exported['reference']['geometry'])>0
        # A failed new prediction must identify the old route still displayed.
        page.locator('#trip').select_option(other_id)
        assert f'Showing trip {trip_id}' in page.locator('#message').inner_text()
        page.route('**/api/predict',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"QA simulated unavailable server"}'))
        page.locator('#run').click()
        page.wait_for_function("!document.querySelector('#run').disabled")
        assert f'Displaying the previous result: trip {trip_id}' in page.locator('#message').inner_text()
        assert page.locator('#loading').is_hidden() and page.locator('#export').is_enabled()
        page.unroute('**/api/predict')
        page.locator('#trip').select_option(trip_id)
        report['checks'].append('Loading overlay and disabled controls; actual JSON export; failed request preserves and identifies previous result')
        page.locator('[data-view="experiments"]').click();page.wait_for_function("document.querySelectorAll('#experimentRows tr').length >= 8")
        assert 'Route continuity 90.47%' in page.locator('.final-ablation').inner_text()
        report['checks'].append('Selected-trip direct continuity matches API; final decoder equal-trip benchmark displays 90.47% separately from network feasibility')
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(out/'experiment_bench.png'),full_page=True)
        print('Experiment screenshot captured',flush=True)
        report['checks'].append('Experiment table renders real API model results and decoder ablations')
        page.locator('[data-view="map"]').click()
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300);page.screenshot(path=str(out/'ui_mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.locator('#settings').is_visible() and page.locator('.inspector').is_visible()
        page.locator('#settings').click();assert page.locator('#settingsDialog').is_visible()
        page.keyboard.press('Escape')
        for width in [320,768,1024]:
            page.set_viewport_size({'width':width,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
            page.locator('[data-view="experiments"]').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
            page.locator('[data-view="map"]').click()
        report['checks'].append('320/390/768/1024px responsive layouts have no page overflow; mobile settings and diagnostics remain accessible')
        page.set_viewport_size({'width':1440,'height':1000})
        # Test recovery after a real failed connection, then restore the working setting.
        page.locator('#settings').click();page.locator('#apiUrl').fill('http://127.0.0.1:1');page.locator('#saveSettings').click()
        page.wait_for_function("document.querySelector('#connection').textContent === 'Server unavailable'")
        assert page.locator('#run').is_disabled()
        page.locator('#settings').click();page.locator('#apiUrl').fill('http://127.0.0.1:8000');page.locator('#saveSettings').click()
        page.wait_for_function("document.querySelector('#connection').textContent === 'Model server online'")
        report['checks'].append('Incorrect API URL fails clearly; settings recover connection')
        page.goto('http://127.0.0.1:8000/docs',wait_until='domcontentloaded')
        page.wait_for_timeout(2000)
        page.screenshot(path=str(out/'api_documentation.png'),full_page=True)
        map_path=ROOT/'results'/'maps'/'development_trip_00000007.html'
        if map_path.exists():
            page.goto(map_path.as_uri(),wait_until='domcontentloaded',timeout=60000)
            page.wait_for_timeout(1500)
            assert page.locator('.leaflet-container').count()==1
            page.screenshot(path=str(out/'folium_development_map.png'),full_page=True)
            report['checks'].append('Generated Folium map loads Leaflet canvas and actual trajectory layers')
        assert not errors,errors
        report['javascript_errors']=errors
        browser.close()
    (ROOT/'results'/'browser_qa.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
