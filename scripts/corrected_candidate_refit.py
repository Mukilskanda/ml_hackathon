"""Train-serving consistency gate: corrected candidates versus historical profile."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from sklearn.base import clone
from pathsnap.core import ROOT,DATA,load_trip,candidates
from pathsnap.metrics import classification_metrics,route_metrics
from pathsnap.decoder import decode
from scripts.train import cv_run,predict

def main():
    out=ROOT/'results'/'critical_audit';manifest=json.loads((ROOT/'artifacts'/'manifest.json').read_text())
    original_name='HistGradientBoosting_tuned_adaptive_candidates'
    original=joblib.load(ROOT/'artifacts'/f'{original_name}.joblib');X=[];ids=[];labels=[];groups=[]
    for group,path in enumerate(sorted((DATA/'train').iterdir())):
        trip=load_trip(path);c=candidates(trip,strategy='adaptive',profile='current_v2')
        with np.load(ROOT/'cache'/f'adaptive_train_{trip.id}.npz') as old:c.update(labels=old['labels'],quality=old['quality'],route=old['route'])
        np.savez_compressed(ROOT/'cache'/f'corrected_train_{trip.id}.npz',**c)
        ix=np.sort(np.random.default_rng(42+group).choice(len(c['ids']),min(450,len(c['ids'])),replace=False))
        X.append(c['X'][ix]);ids.append(c['ids'][ix]);labels.append(c['labels'][ix]);groups.extend([group]*len(ix))
    X=np.concatenate(X);ids=np.concatenate(ids);labels=np.concatenate(labels);groups=np.array(groups)
    cv,folds=cv_run(original,X,ids,labels,groups)
    table=pd.read_csv(ROOT/'results'/'model_comparison.csv');old=table[table.model==original_name].iloc[0]
    before=(old.cv_macro_f1+old.cv_top1_accuracy)/2;after=(cv['macro_f1']+cv['top1_accuracy'])/2
    accepted=bool(after>=before)
    cfg=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    # Profile selection is fixed before any student-test evaluation.
    result={'historical_cv_objective':before,'corrected_cv_objective':after,'cv_metrics':cv,'folds':folds,
            'adopted':accepted,'criterion':'Nondecreasing original grouped-CV objective on identical sampled observations/folds; student-test does not choose profile.'}
    (out/'corrected_candidate_refit.json').write_text(json.dumps(result,indent=2))
    if accepted:
        model=clone(original);t=time.perf_counter();model.fit(X.reshape(-1,X.shape[-1]),(ids==labels[:,None]).ravel().astype(int));fit_s=time.perf_counter()-t
        name='HistGradientBoosting_corrected_candidates';probs=[];testids=[];testlabels=[];time_s=0
    else:model=original;name=original_name
    profile='current_v2' if accepted else 'historical_v1';rows=[]
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path);c=candidates(trip,strategy='adaptive',profile=profile)
        with np.load(ROOT/'cache'/f'adaptive_student_test_{trip.id}.npz') as old:c.update(labels=old['labels'],quality=old['quality'],route=old['route'])
        t=time.perf_counter();p=predict(model,c['X']);elapsed=time.perf_counter()-t
        if accepted:
            probs.append(p);testids.append(c['ids']);testlabels.append(c['labels']);time_s+=elapsed
            np.save(ROOT/'results'/'probabilities'/f'{name}_{trip.id}.npy',p)
            np.savez_compressed(ROOT/'cache'/f'corrected_student_test_{trip.id}.npz',**c)
        d=decode(trip,c,p,mode=cfg['mode'],beta=cfg['beta'],geometry_weight=cfg['geometry_weight'],jitter_m=cfg['jitter_m'],
                 emission_strength=cfg['emission_strength'],uturn_penalty=cfg.get('uturn_penalty',0.))
        rows.append({'method':'audited_hmm','trip_id':trip.id,**route_metrics(d['arc_ids'],c['labels'],c['route'],trip),
                     'network_feasible_fraction':d['network_feasible_fraction'],'uncertain_fraction':d['uncertain_fraction'],'resets':len(d['resets'])})
        np.savez_compressed(out/f'final_{trip.id}.npz',predicted=d['arc_ids'])
    cfg['candidate_profile']=profile;(ROOT/'artifacts'/'decoder.json').write_text(json.dumps(cfg,indent=2))
    if accepted:
        test=classification_metrics(np.concatenate(probs),np.concatenate(testids),np.concatenate(testlabels));test['inference_s']=time_s
        row={'model':name,**{f'cv_{k}':v for k,v in cv.items() if k!='confusion_matrix'},**{f'test_{k}':v for k,v in test.items() if k!='confusion_matrix'}}
        table=table[table.model!=name];pd.concat([table,pd.DataFrame([row])],ignore_index=True).to_csv(ROOT/'results'/'model_comparison.csv',index=False)
        joblib.dump(model,ROOT/'artifacts'/f'{name}.joblib',compress=3);joblib.dump(model,ROOT/'artifacts'/'model.joblib',compress=3)
        manifest.update(model=name,candidate_profile=profile,final_metrics=row);(ROOT/'artifacts'/'manifest.json').write_text(json.dumps(manifest,indent=2))
        diag=json.loads((ROOT/'results'/'training_diagnostics.json').read_text());diag=[r for r in diag if r['model']!=name]
        diag.append({'model':name,'single_refit_training_s':fit_s,**classification_metrics(predict(model,X),ids,labels)})
        (ROOT/'results'/'training_diagnostics.json').write_text(json.dumps(diag,indent=2))
    else:
        manifest['candidate_profile']=profile;(ROOT/'artifacts'/'manifest.json').write_text(json.dumps(manifest,indent=2))
    routes=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str});routes=routes[routes.method!='audited_hmm']
    pd.concat([routes,pd.DataFrame(rows)],ignore_index=True).to_csv(ROOT/'results'/'route_comparison.csv',index=False)
    sizes={p.stem[-8:]:len(np.load(p)['labels']) for p in (ROOT/'cache').glob('student_test_*.npz')}
    final={'mean_trip_accuracy':float(np.mean([r['point_accuracy'] for r in rows])),
       'observation_weighted_accuracy':sum(r['point_accuracy']*sizes[r['trip_id']] for r in rows)/sum(sizes.values()),
       'decision_source':'training-only grouped-CV profile selection and holdout-selected U-turn prior; student-test replay is descriptive','records':rows}
    (out/'final_accuracy.json').write_text(json.dumps(final,indent=2));print(json.dumps(result),flush=True)
    print(json.dumps({k:v for k,v in final.items() if k!='records'}),flush=True)

if __name__=='__main__':main()
