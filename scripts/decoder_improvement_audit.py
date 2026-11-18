"""A training-only holdout gate; student-test data never chooses new settings."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,joblib,pandas as pd
from sklearn.base import clone
from scripts.train import sample_train,predict
from pathsnap.core import ROOT,DATA,load_trip
from pathsnap.decoder import transitions,decode

def main():
    out=ROOT/'results'/'critical_audit';out.mkdir(exist_ok=True)
    cfg=json.loads((ROOT/'artifacts'/'decoder.json').read_text());kwargs={k:cfg[k] for k in ['mode','beta','geometry_weight','jitter_m','emission_strength']}
    X,ids,labels,groups=sample_train(strategy='adaptive')
    paths=sorted((ROOT/'cache').glob('adaptive_train_*.npz'))
    held=np.sort(np.random.default_rng(20261118).choice(len(paths),12,replace=False))
    fit=~np.isin(groups,held)
    model=clone(joblib.load(ROOT/'artifacts'/'model.joblib'))
    model.fit(X[fit].reshape(-1,X.shape[-1]),(ids[fit]==labels[fit,None]).ravel().astype(int))
    held_ids=[paths[i].stem[-8:] for i in held]
    variants={'frozen_baseline':{},'soft_uturn_prior':{'uturn_penalty':float(np.log(2))},
              'row_normalized_hmm':{'normalize_transitions':True}}
    prereg={'holdout_trip_ids':held_ids,'fitting_trips':68,'seed':20261118,
        'variants':variants,'gate':'Adopt only if training-holdout macro accuracy improves >=0.001, no more than 2 trips regress >0.01, and median decode cost <=1.1x baseline. No student-test selection.',
        'limitation':'Hyperparameters and original decoder previously developed on these training trips/CV; this is a training-only replay, not an untouched nested generalisation estimate.'}
    (out/'improvement_protocol.json').write_text(json.dumps(prereg,indent=2))
    rows=[]
    for tid in held_ids:
        trip=load_trip(DATA/'train'/tid);c=dict(np.load(ROOT/'cache'/f'adaptive_train_{tid}.npz'))
        network=transitions(trip,c);p=predict(model,c['X'])
        for name,extra in variants.items():
            t=time.perf_counter();d=decode(trip,c,p,network,**kwargs,**extra);elapsed=time.perf_counter()-t
            rows.append({'trip_id':tid,'variant':name,'observations':len(c['labels']),
                'point_accuracy':float(np.mean(d['arc_ids']==c['labels'])),'decode_s':elapsed})
        print(tid,rows[-3:],flush=True)
    data=pd.DataFrame(rows);data.to_csv(out/'training_holdout_decoder.csv',index=False)
    pivot=data.pivot(index='trip_id',columns='variant',values='point_accuracy');baseline=pivot.frozen_baseline
    decisions=[]
    for name,extra in variants.items():
        if name=='frozen_baseline':continue
        delta=pivot[name]-baseline
        ratio=float(data[data.variant==name].decode_s.median()/data[data.variant=='frozen_baseline'].decode_s.median())
        accept=bool(delta.mean()>=.001 and (delta<-.01).sum()<=2 and ratio<=1.1)
        decisions.append({'variant':name,'mean_accuracy_gain':float(delta.mean()),'trips_regress_over_1pp':int((delta<-.01).sum()),'median_decode_time_ratio':ratio,'passes_gate':accept})
    # Do not change production automatically; any passing proposal requires the
    # robustness/time audit as an additional gate before an explicit promotion.
    (out/'improvement_decisions.json').write_text(json.dumps({'decisions':decisions,'production_changed':False},indent=2))
    joblib.dump(model,out/'training_holdout_model.joblib',compress=3)
    print(json.dumps(decisions),flush=True)

if __name__=='__main__':main()
