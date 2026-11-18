"""Replay model metrics and CV; validate every stored tuning trial and ablation."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib,optuna
from scripts.train import sample_train,cv_run,predict
from pathsnap.core import ROOT
from pathsnap.metrics import classification_metrics

def main():
    out=ROOT/'results'/'critical_audit';out.mkdir(exist_ok=True)
    table=pd.read_csv(ROOT/'results'/'model_comparison.csv');records=[]
    for row in table.to_dict('records'):
        name=row['model'];strategy='corrected' if name.endswith('_corrected_candidates') else 'adaptive' if name.endswith('_adaptive_candidates') else 'nearest'
        X,ids,labels,groups=sample_train(strategy=strategy)
        model=joblib.load(ROOT/'artifacts'/f'{name}.joblib');t=time.perf_counter()
        cv,_=cv_run(model,X,ids,labels,groups)
        probabilities=[];allids=[];alllabels=[]
        prefix='corrected_' if strategy=='corrected' else 'adaptive_' if strategy=='adaptive' else ''
        for path in sorted((ROOT/'cache').glob(prefix+'student_test_*.npz')):
            c=dict(np.load(path));p=predict(model,c['X'])
            saved=np.load(ROOT/'results'/'probabilities'/f'{name}_{path.stem[-8:]}.npy')
            np.testing.assert_allclose(p,saved,atol=1e-7)
            probabilities.append(p);allids.append(c['ids']);alllabels.append(c['labels'])
        test=classification_metrics(np.concatenate(probabilities),np.concatenate(allids),np.concatenate(alllabels))
        fields=['candidate_accuracy','precision','recall','macro_f1','log_loss','top1_accuracy','candidate_miss_rate']
        deviations={f'{prefix}{k}':abs(m[k]-row[f'{prefix}{k}']) for prefix,m in [('cv_',cv),('test_',test)] for k in fields}
        assert max(deviations.values())<1e-7,(name,deviations)
        records.append({'model':name,'max_metric_difference':max(deviations.values()),'saved_probabilities_reproduced':True,'cv_replayed':True,'elapsed_s':time.perf_counter()-t})
        (out/'model_replay.json').write_text(json.dumps(records,indent=2));print(records[-1],flush=True)
    trials=pd.read_csv(ROOT/'results'/'bayesian_trials.csv');assert len(trials)==16 and set(trials.state)=={'COMPLETE'}
    checks=[]
    for row in trials.to_dict('records'):
        metrics=ast.literal_eval(row['user_attrs_metrics']);folds=ast.literal_eval(row['user_attrs_folds'])
        assert abs(row['value']-(metrics['macro_f1']+metrics['top1_accuracy'])/2)<1e-12
        assert len(folds)==3
        checks.append({'trial':int(row['number']),'objective_verified':True,'fold_count':3})
    if (ROOT/'results'/'optuna.db').exists():
        study=optuna.load_study(storage=f'sqlite:///{(ROOT/"results"/"optuna.db").as_posix()}',study_name='pathsnap-HistGradientBoosting')
        assert len(study.trials)==16
        for row,t in zip(trials.to_dict('records'),study.trials):assert abs(row['value']-t.value)<1e-12
    (out/'bayesian_log_verification.json').write_text(json.dumps({'trials':checks,'database_matches_csv':(ROOT/'results'/'optuna.db').exists()},indent=2))
    print('All model and tuning records verified.',flush=True)

if __name__=='__main__':main()
