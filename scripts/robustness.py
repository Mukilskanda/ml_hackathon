import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import numpy as np,pandas as pd,joblib
from pathsnap.core import ROOT,DATA,load_trip,candidates
from pathsnap.decoder import decode

def main():
    model=joblib.load(ROOT/'artifacts'/'model.joblib');config=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    rows=[]
    for tid in ['00000052','00000007','00000056']:
        original=load_trip(DATA/'student_test'/tid)
        with np.load(ROOT/'cache'/f'student_test_{tid}.npz') as cache:labels=cache['labels']
        for noise,stride in [(0,1),(5,1),(15,1),(30,1),(0,5),(0,10)]:
            rng=np.random.default_rng(42+int(tid));ix=np.arange(0,len(labels),stride)
            gps=original.gps[ix]+rng.normal(0,noise,(len(ix),2))
            track=original.track[ix].copy();track[:,:2]=original.unproject(gps)
            trip=replace(original,gps=gps,track=track)
            started=time.perf_counter();c=candidates(trip,strategy=config.get('candidate_strategy','nearest'),profile=config.get('candidate_profile','historical_v1'))
            p=model.predict_proba(c['X'].reshape(-1,c['X'].shape[-1]))[:,1].reshape(c['ids'].shape)
            d=decode(trip,c,p,mode=config['mode'],beta=config['beta'],geometry_weight=config['geometry_weight'],
                     jitter_m=config.get('jitter_m',8),emission_strength=config.get('emission_strength',1),
                     uturn_penalty=config.get('uturn_penalty',0.))
            rows.append({'trip_id':tid,'noise_sigma_m':noise,'sample_stride':stride,'observations':len(ix),
              'classifier_accuracy':float(np.mean(c['ids'][np.arange(len(ix)),p.argmax(axis=1)]==labels[ix])),
              'decoder_accuracy':float(np.mean(d['arc_ids']==labels[ix])),
              'candidate_miss_rate':float(np.mean(~np.any(c['ids']==labels[ix,None],axis=1))),
              'elapsed_s':time.perf_counter()-started})
            pd.DataFrame(rows).to_csv(ROOT/'results'/'robustness.csv',index=False)
            print(rows[-1],flush=True)

if __name__=='__main__':main()
