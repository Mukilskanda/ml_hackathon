"""Validate the passing training-holdout proposal before any promotion."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import numpy as np,pandas as pd,joblib
from pathsnap.core import ROOT,DATA,load_trip,candidates
from pathsnap.decoder import transitions,decode
from scripts.train import predict

def main():
    out=ROOT/'results'/'critical_audit';protocol=json.loads((out/'improvement_protocol.json').read_text())
    cfg=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    kwargs={k:cfg[k] for k in ['mode','beta','geometry_weight','jitter_m','emission_strength']}
    model=joblib.load(out/'training_holdout_model.joblib');rows=[];timings=[]
    # Three fixed positions in the predeclared training-only holdout, not trips
    # chosen after seeing student-test errors or outcomes.
    selected=[protocol['holdout_trip_ids'][i] for i in [0,5,11]]
    for tid in selected:
        original=load_trip(DATA/'train'/tid)
        with np.load(ROOT/'cache'/f'adaptive_train_{tid}.npz') as z:labels=z['labels']
        for noise,stride in [(0,1),(5,1),(15,1),(30,1),(0,5),(0,10)]:
            ix=np.arange(0,len(labels),stride);rng=np.random.default_rng(20261118+int(tid))
            gps=original.gps[ix]+rng.normal(0,noise,(len(ix),2));track=original.track[ix].copy();track[:,:2]=original.unproject(gps)
            trip=replace(original,gps=gps,track=track);c=candidates(trip,strategy='adaptive',profile='historical_v1');network=transitions(trip,c);p=predict(model,c['X'])
            scores={}
            for name,penalty in [('baseline',0.),('uturn',float(np.log(2)))]:
                d=decode(trip,c,p,network,**kwargs,uturn_penalty=penalty)
                scores[name]=float(np.mean(d['arc_ids']==labels[ix]))
            rows.append({'trip_id':tid,'noise_sigma_m':noise,'sample_stride':stride,**scores,'gain':scores['uturn']-scores['baseline']})
            if noise==0 and stride==1:
                for repeat in range(5):
                    for name,penalty in ([('baseline',0.),('uturn',float(np.log(2)))] if repeat%2==0 else [('uturn',float(np.log(2))),('baseline',0.)]):
                        t=time.perf_counter();decode(trip,c,p,network,**kwargs,uturn_penalty=penalty)
                        timings.append({'trip_id':tid,'repeat':repeat,'variant':name,'decode_s':time.perf_counter()-t})
            print(rows[-1],flush=True)
    pd.DataFrame(rows).to_csv(out/'training_holdout_robustness.csv',index=False)
    t=pd.DataFrame(timings);t.to_csv(out/'uturn_timing_repeats.csv',index=False)
    ratio=float(t[t.variant=='uturn'].decode_s.median()/t[t.variant=='baseline'].decode_s.median())
    decision=json.loads((out/'improvement_decisions.json').read_text());candidate=next(d for d in decision['decisions'] if d['variant']=='soft_uturn_prior')
    delta=np.array([r['gain'] for r in rows]);accepted=bool(candidate['mean_accuracy_gain']>=.001 and candidate['trips_regress_over_1pp']<=2 and ratio<=1.1 and delta.mean()>=-.005 and np.sum(delta<-.02)<=1)
    result={'candidate':'soft_uturn_prior','training_holdout_accuracy_gain':candidate['mean_accuracy_gain'],
      'repeated_median_decode_ratio':ratio,'mean_robustness_gain':float(delta.mean()),
      'robustness_cases_regress_over_2pp':int(np.sum(delta<-.02)),'accepted':accepted,
      'student_test_used_for_decision':False,'selected_penalty':float(np.log(2)),
      'limitations':protocol['limitation']}
    (out/'uturn_validation_decision.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
