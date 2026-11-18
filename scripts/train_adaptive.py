import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from sklearn.base import clone
from pathsnap.core import ROOT,DATA,load_trip,candidates
from pathsnap.metrics import classification_metrics
from scripts.train import cv_run,predict

def main():
    baseline=ROOT/'artifacts'/'baseline_manifest.json'
    manifest=json.loads((baseline if baseline.exists() else ROOT/'artifacts'/'manifest.json').read_text());original=manifest['model']
    model=joblib.load(ROOT/'artifacts'/f'{original}.joblib');X=[];ids=[];labels=[];groups=[]
    for group,path in enumerate(sorted((DATA/'train').iterdir())):
        trip=load_trip(path);c=candidates(trip,strategy='adaptive',profile='historical_v1')
        with np.load(ROOT/'cache'/f'train_{trip.id}.npz') as reference:
            c.update(labels=reference['labels'],quality=reference['quality'],route=reference['route'])
        np.savez_compressed(ROOT/'cache'/f'adaptive_train_{trip.id}.npz',**c)
        rng=np.random.default_rng(42+group);ix=np.sort(rng.choice(len(c['ids']),min(450,len(c['ids'])),replace=False))
        X.append(c['X'][ix]);ids.append(c['ids'][ix]);labels.append(c['labels'][ix]);groups.extend([group]*len(ix))
        print('Prepared adaptive training '+trip.id,flush=True)
    X=np.concatenate(X);ids=np.concatenate(ids);labels=np.concatenate(labels);groups=np.array(groups)
    t=time.perf_counter();cv,folds=cv_run(model,X,ids,labels,groups)
    model.fit(X.reshape(-1,X.shape[-1]),(ids==labels[:,None]).ravel().astype(int));elapsed=time.perf_counter()-t
    newname=original+'_adaptive_candidates';probs=[];allids=[];alllabels=[];pertrip=[];inference=0
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path);c=candidates(trip,strategy='adaptive',profile='historical_v1')
        with np.load(ROOT/'cache'/f'student_test_{trip.id}.npz') as ref:c.update(labels=ref['labels'],quality=ref['quality'],route=ref['route'])
        np.savez_compressed(ROOT/'cache'/f'adaptive_student_test_{trip.id}.npz',**c)
        t=time.perf_counter();p=predict(model,c['X']);inference+=time.perf_counter()-t
        np.save(ROOT/'results'/'probabilities'/f'{newname}_{trip.id}.npy',p)
        probs.append(p);allids.append(c['ids']);alllabels.append(c['labels'])
        pertrip.append({'trip_id':trip.id,**classification_metrics(p,c['ids'],c['labels'])})
    test=classification_metrics(np.concatenate(probs),np.concatenate(allids),np.concatenate(alllabels));test['inference_s']=inference
    old=manifest['final_metrics'];improved=(cv['macro_f1']+cv['top1_accuracy'])>(old['cv_macro_f1']+old['cv_top1_accuracy'])
    record={'base_model':original,'model':newname,'cv_metrics':cv,'test_metrics':test,'folds':folds,
       'fit_and_cv_s':elapsed,'adopted':bool(improved),'protocol':'Same seed, same sampled observation IDs, same 3 trip-grouped folds, same tuned HGB hyperparameters; only candidate selection changes.'}
    (ROOT/'results'/'adaptive_training.json').write_text(json.dumps(record,indent=2))
    (ROOT/'results'/'adaptive_model_per_trip.json').write_text(json.dumps(pertrip,indent=2))
    joblib.dump(model,ROOT/'artifacts'/f'{newname}.joblib',compress=3)
    if improved:
        (ROOT/'artifacts'/'baseline_manifest.json').write_text(json.dumps(manifest,indent=2))
        joblib.dump(model,ROOT/'artifacts'/'model.joblib',compress=3)
        row={'model':newname,**{f'cv_{k}':v for k,v in cv.items() if k!='confusion_matrix'},
             **{f'test_{k}':v for k,v in test.items() if k!='confusion_matrix'},'fit_and_cv_s':elapsed}
        manifest.update(model=newname,candidate_strategy='adaptive',final_metrics=row)
        (ROOT/'artifacts'/'manifest.json').write_text(json.dumps(manifest,indent=2))
        table=pd.read_csv(ROOT/'results'/'model_comparison.csv');table=table[table.model!=newname];pd.concat([table,pd.DataFrame([row])],ignore_index=True).to_csv(ROOT/'results'/'model_comparison.csv',index=False)
    print(json.dumps(record),flush=True)

if __name__=='__main__':main()
