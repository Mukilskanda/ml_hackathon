import os
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import sys, json, time, platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import joblib, optuna, sklearn
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.base import clone
from pathsnap.core import ROOT, FEATURES
from pathsnap.metrics import classification_metrics

SEED=42
def models():
    return {
      'LogisticRegression':make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=300,random_state=SEED)),
      'GaussianNB':make_pipeline(StandardScaler(),GaussianNB(var_smoothing=1e-7)),
      'DecisionTree':DecisionTreeClassifier(max_depth=12,min_samples_leaf=25,random_state=SEED),
      'RandomForest':RandomForestClassifier(n_estimators=100,max_depth=18,min_samples_leaf=10,n_jobs=4,random_state=SEED),
      'ExtraTrees':ExtraTreesClassifier(n_estimators=100,max_depth=20,min_samples_leaf=8,n_jobs=4,random_state=SEED),
      'HistGradientBoosting':HistGradientBoostingClassifier(max_iter=130,max_leaf_nodes=23,learning_rate=.09,l2_regularization=2,early_stopping=False,random_state=SEED),
      'MLP':make_pipeline(StandardScaler(),MLPClassifier(hidden_layer_sizes=(32,16),max_iter=45,batch_size=1024,early_stopping=False,random_state=SEED))}

def sample_train(limit=450,strategy='nearest'):
    X=[]; ids=[]; labels=[]; groups=[]
    patterns={'nearest':'train_*.npz','adaptive':'adaptive_train_*.npz','corrected':'corrected_train_*.npz'}
    if strategy not in patterns:raise ValueError('Unknown training candidate strategy')
    pattern=patterns[strategy]
    for group,path in enumerate(sorted((ROOT/'cache').glob(pattern))):
        with np.load(path) as c:
            rng=np.random.default_rng(SEED+group)
            ix=np.sort(rng.choice(len(c['ids']),min(limit,len(c['ids'])),replace=False))
            X.append(c['X'][ix]); ids.append(c['ids'][ix]); labels.append(c['labels'][ix]); groups.extend([group]*len(ix))
    return np.concatenate(X), np.concatenate(ids),np.concatenate(labels), np.array(groups)

def predict(model,X):
    return model.predict_proba(X.reshape(-1,X.shape[-1]))[:,1].reshape(X.shape[:2])

def cv_run(model,X,ids,labels,groups):
    probabilities=np.empty(ids.shape,dtype=np.float32)
    folds=[]
    for train,val in GroupKFold(n_splits=3).split(X,groups=groups):
        assert not set(groups[train])&set(groups[val])
        fitted=clone(model)
        fitted.fit(X[train].reshape(-1,X.shape[-1]),(ids[train]==labels[train,None]).ravel().astype(int))
        probabilities[val]=predict(fitted,X[val])
        folds.append(classification_metrics(probabilities[val],ids[val],labels[val]))
    metrics=classification_metrics(probabilities,ids,labels)
    metrics['fold_top1_std']=float(np.std([x['top1_accuracy'] for x in folds]))
    metrics['fold_macro_f1_std']=float(np.std([x['macro_f1'] for x in folds]))
    return metrics,folds

def student_test(model,name):
    probabilities=[]; ids=[]; labels=[]; pertrip=[]; seconds=0
    for path in sorted((ROOT/'cache').glob('student_test_*.npz')):
        with np.load(path) as c:
            start=time.perf_counter(); p=predict(model,c['X']); elapsed=time.perf_counter()-start
            m=classification_metrics(p,c['ids'],c['labels'])
            pertrip.append({'model':name,'trip_id':path.stem.split('_')[-1],**m,'inference_s':elapsed})
            probabilities.append(p);ids.append(c['ids']);labels.append(c['labels']);seconds+=elapsed
            np.save(ROOT/'results'/'probabilities'/f'{name}_{path.stem.split("_")[-1]}.npy',p)
    m=classification_metrics(np.concatenate(probabilities),np.concatenate(ids),np.concatenate(labels))
    m['inference_s']=seconds
    return m,pertrip

def json_safe(value):
    return json.loads(json.dumps(value,default=lambda v:v.item() if isinstance(v,np.generic) else str(v)))

def main():
    for p in ['artifacts','results/probabilities','results/configurations']: (ROOT/p).mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    X,ids,labels,groups=sample_train()
    print(f'Training sample: {len(X)} observations / {X.size//X.shape[-1]} candidate rows / {len(set(groups))} trips',flush=True)
    rows=[]; triprows=[]; foldlog={}
    for name,model in models().items():
        t=time.perf_counter(); cv,folds=cv_run(model,X,ids,labels,groups)
        model.fit(X.reshape(-1,len(FEATURES)),(ids==labels[:,None]).ravel().astype(int))
        elapsed=time.perf_counter()-t
        test,trips=student_test(model,name)
        row={'model':name,**{f'cv_{k}':v for k,v in cv.items() if k!='confusion_matrix'},
             **{f'test_{k}':v for k,v in test.items() if k!='confusion_matrix'},'fit_and_cv_s':elapsed}
        rows.append(row); triprows+=trips; foldlog[name]=folds
        joblib.dump(model,ROOT/'artifacts'/f'{name}.joblib',compress=3)
        (ROOT/'results'/'configurations'/f'{name}.json').write_text(json.dumps(json_safe(model.get_params()),indent=2))
        pd.DataFrame(rows).to_csv(ROOT/'results'/'model_comparison.csv',index=False)
        pd.DataFrame(triprows).to_json(ROOT/'results'/'model_per_trip.json',orient='records',indent=2)
        (ROOT/'results'/'cv_folds.json').write_text(json.dumps(foldlog,indent=2))
        print(f'{name}: CV F1={cv["macro_f1"]:.4f} top1={cv["top1_accuracy"]:.4f}; test F1={test["macro_f1"]:.4f} top1={test["top1_accuracy"]:.4f} time={elapsed:.1f}s',flush=True)
    table=pd.DataFrame(rows)
    eligible=table[table.model.isin(['RandomForest','ExtraTrees','HistGradientBoosting'])].copy()
    eligible['objective']=(eligible.cv_macro_f1+eligible.cv_top1_accuracy)/2
    chosen=eligible.sort_values('objective',ascending=False).iloc[0]['model']
    baseline=models()[chosen]
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=SEED,n_startup_trials=5),
       storage=f'sqlite:///{(ROOT/"results"/"optuna.db").as_posix()}',study_name='pathsnap-'+chosen,load_if_exists=True)
    def make_tuned(trial):
        if chosen=='HistGradientBoosting':
            return HistGradientBoostingClassifier(max_iter=trial.suggest_int('max_iter',70,210),
              learning_rate=trial.suggest_float('learning_rate',.025,.2,log=True),
              max_leaf_nodes=trial.suggest_int('max_leaf_nodes',10,45),
              min_samples_leaf=trial.suggest_int('min_samples_leaf',15,100),
              l2_regularization=trial.suggest_float('l2_regularization',.1,20,log=True),
              early_stopping=False,random_state=SEED)
        klass=ExtraTreesClassifier if chosen=='ExtraTrees' else RandomForestClassifier
        return klass(n_estimators=trial.suggest_int('n_estimators',70,160,step=30),
           max_depth=trial.suggest_int('max_depth',10,25),min_samples_leaf=trial.suggest_int('min_samples_leaf',3,35),
           max_features=trial.suggest_float('max_features',.4,1.),n_jobs=4,random_state=SEED)
    def objective(trial):
        model=make_tuned(trial); m,folds=cv_run(model,X,ids,labels,groups)
        trial.set_user_attr('metrics',m);trial.set_user_attr('folds',folds)
        study.trials_dataframe().to_csv(ROOT/'results'/'bayesian_trials.csv',index=False)
        print(f'Bayesian trial {trial.number}: F1={m["macro_f1"]:.4f} top1={m["top1_accuracy"]:.4f}',flush=True)
        return (m['macro_f1']+m['top1_accuracy'])/2
    study.optimize(objective,n_trials=max(0,16-len(study.trials)))
    study.trials_dataframe().to_csv(ROOT/'results'/'bayesian_trials.csv',index=False)
    tuned=make_tuned(optuna.trial.FixedTrial(study.best_params))
    tuned.fit(X.reshape(-1,len(FEATURES)),(ids==labels[:,None]).ravel().astype(int))
    cv=study.best_trial.user_attrs['metrics'];test,trips=student_test(tuned,chosen+'_tuned')
    tunedrow={'model':chosen+'_tuned',**{f'cv_{k}':v for k,v in cv.items() if k!='confusion_matrix'},
              **{f'test_{k}':v for k,v in test.items() if k!='confusion_matrix'}}
    rows.append(tunedrow);triprows+=trips
    pd.DataFrame(rows).to_csv(ROOT/'results'/'model_comparison.csv',index=False)
    pd.DataFrame(triprows).to_json(ROOT/'results'/'model_per_trip.json',orient='records',indent=2)
    joblib.dump(tuned,ROOT/'artifacts'/f'{chosen}_tuned.joblib',compress=3)
    # Select by grouped CV, not a favorable student-test outcome.
    best=max(rows,key=lambda r:(r['cv_macro_f1']+r['cv_top1_accuracy'])/2)
    final=joblib.load(ROOT/'artifacts'/f'{best["model"]}.joblib')
    joblib.dump(final,ROOT/'artifacts'/'model.joblib',compress=3)
    manifest={'model':best['model'],'seed':SEED,'features':FEATURES,'k_candidates':8,
      'training_observations':len(X),'training_trips':len(set(groups)),'max_observations_per_training_trip':450,
      'cv':'3-fold GroupKFold by trip; preprocessing fitted separately in each training fold',
      'selection_objective':'mean(candidate binary macro F1, observation Top-1) on grouped CV',
      'tuned_family':chosen,'best_parameters':study.best_params,'trials':len(study.trials),
      'reference_warning':'Point labels are monotone geometric alignments derived from .route, not independent evaluator labels.',
      'python':platform.python_version(),'sklearn':sklearn.__version__,'elapsed_s':time.perf_counter()-start,
      'final_metrics':best}
    (ROOT/'artifacts'/'manifest.json').write_text(json.dumps(json_safe(manifest),indent=2))
    print('SELECTED '+json.dumps(manifest),flush=True)

if __name__=='__main__':main()
