"""Apply the pre-gated change, then report student-test results descriptively."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from pathsnap.core import ROOT,DATA,load_trip
from pathsnap.decoder import transitions,decode
from pathsnap.metrics import route_metrics

def main():
    out=ROOT/'results'/'critical_audit'
    decision=json.loads((out/'uturn_validation_decision.json').read_text())
    assert decision['accepted'] and not decision['student_test_used_for_decision']
    current=ROOT/'artifacts'/'decoder.json';baseline=ROOT/'artifacts'/'decoder_baseline.json'
    if not baseline.exists():baseline.write_bytes(current.read_bytes())
    cfg=json.loads(baseline.read_text());cfg['uturn_penalty']=decision['selected_penalty']
    cfg['audit_selection']='Soft U-turn prior validated on fixed training-only holdout and noise/dropout replay; no student-test tuning of this prior.'
    current.write_text(json.dumps(cfg,indent=2))
    rows=[]
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path);c=dict(np.load(ROOT/'cache'/f'adaptive_student_test_{trip.id}.npz'))
        frozen=dict(np.load(out/f'baseline_{trip.id}.npz'));net=transitions(trip,c)
        t=time.perf_counter();d=decode(trip,c,frozen['probability'],net,**{k:cfg[k] for k in ['mode','beta','geometry_weight','jitter_m','emission_strength','uturn_penalty']})
        metrics=route_metrics(d['arc_ids'],c['labels'],c['route'],trip)
        rows.append({'method':'audited_hmm','trip_id':trip.id,**metrics,'network_feasible_fraction':d['network_feasible_fraction'],
                    'uncertain_fraction':d['uncertain_fraction'],'resets':len(d['resets']),'decode_s':time.perf_counter()-t})
        np.savez_compressed(out/f'final_{trip.id}.npz',predicted=d['arc_ids'])
    table=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str});table=table[table.method!='audited_hmm']
    pd.concat([table,pd.DataFrame(rows)],ignore_index=True).to_csv(ROOT/'results'/'route_comparison.csv',index=False)
    count={r['trip_id']:len(np.load(out/f'baseline_{r["trip_id"]}.npz')['labels']) for r in rows}
    result={'mean_trip_accuracy':float(np.mean([r['point_accuracy'] for r in rows])),
            'observation_weighted_accuracy':sum(r['point_accuracy']*count[r['trip_id']] for r in rows)/sum(count.values()),
            'decision_source':'training-only gate; this student-test replay is descriptive', 'records':rows}
    (out/'final_accuracy.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)

if __name__=='__main__':main()
