import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from sklearn.base import clone
from scripts.train import sample_train,cv_run,predict
from pathsnap.core import ROOT,FEATURES
from pathsnap.metrics import classification_metrics

def main():
    X,ids,labels,groups=sample_train()
    final=joblib.load(ROOT/'artifacts'/'HistGradientBoosting_tuned.joblib')
    rows=[]
    sets={'distance_only':[0], 'geometry':[0,2,3,4,9,10,14],
          'geometry_and_motion':[0,1,2,3,4,5,6,7,8,9,10,11,14], 'all_features':list(range(len(FEATURES)))}
    for name,columns in sets.items():
        started=time.perf_counter();m=clone(final)
        cv,_=cv_run(m,X[:,:,columns],ids,labels,groups)
        m.fit(X[:,:,columns].reshape(-1,len(columns)),(ids==labels[:,None]).ravel().astype(int))
        probs=[];test_ids=[];test_labels=[]
        for path in sorted((ROOT/'cache').glob('student_test_*.npz')):
            with np.load(path) as c:
                probs.append(predict(m,c['X'][:,:,columns]));test_ids.append(c['ids']);test_labels.append(c['labels'])
        test=classification_metrics(np.concatenate(probs),np.concatenate(test_ids),np.concatenate(test_labels))
        rows.append({'feature_set':name,'columns':','.join(FEATURES[i] for i in columns),'cv_macro_f1':cv['macro_f1'],
          'cv_top1_accuracy':cv['top1_accuracy'],'test_macro_f1':test['macro_f1'],'test_top1_accuracy':test['top1_accuracy'],
          'elapsed_s':time.perf_counter()-started})
        pd.DataFrame(rows).to_csv(ROOT/'results'/'feature_ablation.csv',index=False)
        print(name,rows[-1],flush=True)
    coverage=[]
    for partition in ['train','student_test']:
        for k in [1,2,4,8]:
            miss=0;n=0
            for path in (ROOT/'cache').glob(partition+'_*.npz'):
                with np.load(path) as c:
                    miss+=np.sum(~np.any(c['ids'][:,:k]==c['labels'][:,None],axis=1));n+=len(c['labels'])
            coverage.append({'partition':partition,'k':k,'candidate_miss_rate':float(miss/n),'observations':n})
    pd.DataFrame(coverage).to_csv(ROOT/'results'/'candidate_coverage.csv',index=False)

if __name__=='__main__':main()
