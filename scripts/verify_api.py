import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from pathsnap.core import ROOT

def main():
    records=[]
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=180) as client:
        trips=client.get('/api/trips').json()['trips']
        for trip in trips:
            started=time.perf_counter()
            response=client.post('/api/predict',json={'trip_id':trip['id']})
            assert response.status_code==200,(trip,response.text)
            p=response.json()
            assert p['observations']==len(p['arc_ids'])==len(p['gps'])==len(p['matched_points'])
            assert len(p['route'])>0
            import pandas as pd
            expected=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str})
            method='audited_hmm' if 'audited_hmm' in set(expected.method) else 'adaptive_hmm'
            row=expected[(expected.method==method)&(expected.trip_id==trip['id'])]
            if len(row):assert abs(p['metrics']['point_accuracy']-float(row.point_accuracy.iloc[0]))<1e-12
            assert not {'labels','reference_route','ground_truth'}&p.keys()
            record={'trip_id':trip['id'],'status':response.status_code,'observations':p['observations'],
                'point_accuracy':p['metrics']['point_accuracy'],'wall_s':time.perf_counter()-started,
                'inference_s':p['timings']['total_s'],'request_id':p['request_id']}
            records.append(record)
            print(json.dumps(record),flush=True)
            (ROOT/'results'/'api_verification.json').write_text(json.dumps(records,indent=2))
            if trip['id']=='00000052':
                (ROOT/'results'/'sample_response.json').write_text(json.dumps(p))

if __name__=='__main__':main()
