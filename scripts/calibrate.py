import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold,GroupShuffleSplit
from scripts.train import sample_train,predict,student_test
from pathsnap.core import ROOT
from pathsnap.calibration import SigmoidCalibratedModel
from pathsnap.metrics import classification_metrics

def logits(p):
    p=np.clip(p,1e-7,1-1e-7);return np.log(p/(1-p)).reshape(-1,1)

def main():
    X,ids,labels,groups=sample_train();y=(ids==labels[:,None]).astype(int)
    # This experiment explicitly concerns the tuned nearest-candidate model,
    # regardless of which later variant is currently selected for deployment.
    final=joblib.load(ROOT/'artifacts'/'HistGradientBoosting_tuned.joblib')
    cvp=np.zeros(ids.shape);oof=np.zeros(ids.shape)
    for fit,val in GroupKFold(3).split(X,groups=groups):
        inner,cal=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(X[fit],groups=groups[fit]))
        train,cal=fit[inner],fit[cal]
        assert not(set(groups[train])&set(groups[cal]) or set(groups[train])&set(groups[val]) or set(groups[cal])&set(groups[val]))
        model=clone(final);model.fit(X[train].reshape(-1,X.shape[-1]),y[train].ravel())
        calibrator=LogisticRegression(C=100,random_state=42).fit(logits(predict(model,X[cal])),y[cal].ravel())
        cvp[val]=calibrator.predict_proba(logits(predict(model,X[val])))[:,1].reshape(ids[val].shape)
        base=clone(final);base.fit(X[fit].reshape(-1,X.shape[-1]),y[fit].ravel());oof[val]=predict(base,X[val])
    cv=classification_metrics(cvp,ids,labels)
    calibrator=LogisticRegression(C=100,random_state=42).fit(logits(oof),y.ravel())
    wrapped=SigmoidCalibratedModel(final,calibrator)
    test,trips=student_test(wrapped,'SigmoidCalibrated')
    joblib.dump(wrapped,ROOT/'artifacts'/'SigmoidCalibrated.joblib',compress=3)
    comparison=pd.read_csv(ROOT/'results'/'model_comparison.csv')
    baseline=comparison[comparison.model=='HistGradientBoosting_tuned'].iloc[0].to_dict()
    record={'method':'Sigmoid calibration','base_model':'HistGradientBoosting_tuned','candidate_strategy':'nearest','cv_metrics':cv,'test_metrics':test,
      'base_cv_log_loss':baseline['cv_log_loss'],'base_test_log_loss':baseline['test_log_loss'],
      'protocol':'Outer 3-fold GroupKFold; each outer training fold split by trip into 75% fit / 25% calibration. Final calibrator fits group-OOF scores, base refit uses all sampled training trips.',
      'caution':'Calibrated CV base models use fewer fit trips than uncalibrated CV; compare with this limitation.',
      'calibrator_coefficient':calibrator.coef_.tolist(),'calibrator_intercept':calibrator.intercept_.tolist(),
      'adopted':False,'decision':'Retained as a probability-quality experiment; production model selection remains the originally declared grouped-CV candidate objective.'}
    (ROOT/'results'/'calibration.json').write_text(json.dumps(record,indent=2))
    bins=[]
    for name,prob in [('uncalibrated',oof),('calibrated_nested_cv',cvp)]:
        flat=prob.ravel();truth=y.ravel()
        for lo in np.linspace(0,.9,10):
            mask=(flat>=lo)&(flat<lo+.1 if lo<.9 else flat<=1)
            bins.append({'method':name,'bin_lower':lo,'count':int(mask.sum()),'mean_probability':float(flat[mask].mean()) if mask.any() else None,'positive_fraction':float(truth[mask].mean()) if mask.any() else None})
    pd.DataFrame(bins).to_csv(ROOT/'results'/'calibration_bins.csv',index=False)
    print(json.dumps(record),flush=True)

if __name__=='__main__':main()
