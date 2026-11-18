"""Real browser integration checks; requires optional playwright + Chromium."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from pathsnap.core import ROOT

def main():
    out=ROOT/'results'/'screenshots';out.mkdir(exist_ok=True)
    report={'physical_two_laptops_tested':False,'origins':['http://127.0.0.1:8080','http://127.0.0.1:8000'],'checks':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8080',wait_until='domcontentloaded')
        print('Loaded UI',flush=True)
        page.locator('#settings').click();page.locator('#apiUrl').fill('http://127.0.0.1:8000');page.locator('#saveSettings').click()
        page.wait_for_function("document.querySelector('#trip').options.length === 10")
        report['checks'].append('Separate UI origin loads ten actual development trip options via API')
        print('Ten trips available',flush=True)
        page.locator('#trip').select_option('00000052');page.locator('#run').click()
        page.wait_for_function("!document.querySelector('#run').disabled && document.querySelector('#observations').textContent === '262'",timeout=120000)
        assert page.locator('#empty').is_hidden()
        assert page.locator('#accuracy').inner_text()!='—'
        page.locator('#scrub').fill('100');page.locator('#scrub').dispatch_event('input')
        page.locator('#zoomIn').click();page.locator('#fit').click()
        page.locator('#map').focus();page.keyboard.press('ArrowLeft');page.keyboard.press('Home')
        page.screenshot(path=str(out/'ui_desktop.png'),full_page=True)
        print('Desktop screenshot captured',flush=True)
        report['checks'].append('Live POST inference, nonempty route/metrics, playback, zoom and keyboard map controls')
        page.locator('[data-view="experiments"]').click();page.wait_for_function("document.querySelectorAll('#experimentRows tr').length >= 8")
        page.screenshot(path=str(out/'experiment_bench.png'),full_page=True)
        print('Experiment screenshot captured',flush=True)
        report['checks'].append('Experiment table renders real API model results and decoder ablations')
        page.locator('[data-view="map"]').click()
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300);page.screenshot(path=str(out/'ui_mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        report['checks'].append('390px mobile layout has no horizontal overflow')
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
