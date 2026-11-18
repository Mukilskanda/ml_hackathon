import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from pathsnap.core import ROOT,DATA,load_trip,candidates
from pathsnap.decoder import decode

def main():
    model=joblib.load(ROOT/'artifacts'/'model.joblib');config=json.loads((ROOT/'artifacts'/'decoder.json').read_text());rows=[]
    baseline=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str})
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path)
        with np.load(ROOT/'cache'/f'student_test_{trip.id}.npz') as z:labels=z['labels']
        started=time.perf_counter();c=candidates(trip,strategy='adaptive')
        p=model.predict_proba(c['X'].reshape(-1,c['X'].shape[-1]))[:,1].reshape(c['ids'].shape)
        d=decode(trip,c,p,mode=config['mode'],beta=config['beta'],geometry_weight=config['geometry_weight'],
                 jitter_m=config['jitter_m'],emission_strength=config['emission_strength'])
        rows.append({'trip_id':trip.id,'candidate_miss_rate':float(np.mean(~np.any(c['ids']==labels[:,None],axis=1))),
          'classifier_accuracy':float(np.mean(c['ids'][np.arange(len(p)),p.argmax(axis=1)]==labels)),
          'decoder_accuracy':float(np.mean(d['arc_ids']==labels)),'elapsed_s':time.perf_counter()-started})
        pd.DataFrame(rows).to_csv(ROOT/'results'/'adaptive_candidates.csv',index=False)
        print(rows[-1],flush=True)
    (ROOT/'results'/'adaptive_candidate_decision.json').write_text(json.dumps({
      'adopted':False,'strategy':'Distance plus 18 m * heading-reliability * (1-heading cosine), retaining 8 candidates, re-sorted by distance.',
      'adaptive_mean_accuracy':float(np.mean([r['decoder_accuracy'] for r in rows])),
      'baseline_mean_accuracy':float(baseline[baseline.method==(config['mode']+'_hmm')].point_accuracy.mean()),
      'decision':'Experimental inference-time candidate reranking only. Preserve the training-matched nearest candidate distribution unless a separate training-matched comparison supports replacement.'},indent=2))

if __name__=='__main__':main()
