"""Evaluate the frozen pipeline on supplied evaluator trips; never tune or fit."""
import sys,json,time,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx,numpy as np
from pathsnap.core import ROOT,load_trip,load_indices

def main():
    model=ROOT/'artifacts/model.joblib'
    frozen=subprocess.check_output(['git','show','16bd43d:artifacts/model.joblib'],cwd=ROOT)
    assert model.read_bytes()==frozen,'Selected model changed'
    for name in ['decoder.json','manifest.json']:
        baseline=subprocess.check_output(['git','show',f'16bd43d:artifacts/{name}'],cwd=ROOT)
        assert json.loads((ROOT/'artifacts'/name).read_text())==json.loads(baseline),'Selected configuration changed'
    records=[]
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=180) as client:
        listing=client.get('/api/trips').json()
        assert listing['mode']=='evaluator' and len(listing['trips'])==10
        for entry in listing['trips']:
            tid=entry['id'];started=time.perf_counter()
            response=client.post('/api/predict',json={'trip_id':tid})
            assert response.status_code==200,response.text
            result=response.json()
            assert result['observations']==len(result['arc_ids'])==len(result['gps'])
            assert not {'labels','ground_truth','reference_route','reference'}&result.keys()
            reference=client.get('/api/reference/'+tid).json()
            assert not reference['available'] and 'geometry' not in reference
            path=ROOT/'data/evaluator_test'/tid
            trip=load_trip(path);route=load_indices(path/f'{tid}.route',1).ravel()
            assert route.max()<len(trip.arcs)
            records.append({'trip_id':tid,'observations':result['observations'],
                'point_accuracy':result['metrics']['point_accuracy'],'classifier_top1':result['metrics']['classifier_top1'],
                'network_feasible_fraction':result['network_feasible_fraction'],
                'inference_s':result['timings']['total_s'],'request_id':result['request_id'],
                'reference_arcs':len(route),'reference_remains_server_side':True,
                'prediction_sha256':hashlib.sha256(np.asarray(result['arc_ids'],dtype='<i4').tobytes()).hexdigest(),
                'wall_s':time.perf_counter()-started})
            print(json.dumps(records[-1]),flush=True)
    evaluator_ids={r['trip_id'] for r in records}
    permitted={p.name for part in ['train','student_test'] for p in (ROOT/'data/Student folder'/part).glob('*') if p.is_dir()}
    assert not evaluator_ids&permitted,'Trip partition overlap'
    permitted_tracks={hashlib.sha256(p.read_bytes()).hexdigest() for part in ['train','student_test'] for p in (ROOT/'data/Student folder'/part).glob('*/*.track')}
    assert len(permitted)==90 and len(permitted_tracks)==90,'Expected 90 permitted trips'
    assert not any(hashlib.sha256((ROOT/f'data/evaluator_test/{tid}/{tid}.track').read_bytes()).hexdigest() in permitted_tracks for tid in evaluator_ids),'Identical GPS track across partitions'
    inventory=json.loads((ROOT/'results/evaluator_inventory.json').read_text())
    result={'records':records,'trips':len(records),'observations':sum(r['observations'] for r in records),
        'equal_trip_point_accuracy':float(np.mean([r['point_accuracy'] for r in records])),
        'pooled_point_accuracy':float(np.average([r['point_accuracy'] for r in records],weights=[r['observations'] for r in records])),
        'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'model_matches_audited_artifact':True,
        'source_zip_sha256':inventory['source_zip_sha256'],'trip_ids_overlap_permitted_partitions':False,
        'permitted_trips_checked':len(permitted),'duplicate_track_files_across_partitions':False,
        'evaluation_basis':'Derived monotone point alignment to supplied evaluator .route; not official evaluator scoring.',
        'model_retrained':False,'hyperparameters_changed':False,'used_for_selection':False,
        'physical_two_laptops_verified':False}
    (ROOT/'results/evaluator_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)

if __name__=='__main__':main()
