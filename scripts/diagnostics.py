import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib,numpy as np,pandas as pd
from sklearn.base import clone
from pathsnap.core import ROOT
from pathsnap.metrics import classification_metrics
from scripts.train import sample_train,predict

def main():
    X,ids,labels,groups=sample_train();rows=[]
    for path in sorted((ROOT/'artifacts').glob('*.joblib')):
        if path.stem in ['model','SigmoidCalibrated']:continue
        if path.stem.endswith('_adaptive_candidates'):
            X,ids,labels,groups=sample_train(strategy='adaptive')
        else:X,ids,labels,groups=sample_train()
        model=joblib.load(path);t=time.perf_counter();refit=clone(model)
        refit.fit(X.reshape(-1,X.shape[-1]),(ids==labels[:,None]).ravel().astype(int));elapsed=time.perf_counter()-t
        metrics=classification_metrics(predict(model,X),ids,labels)
        rows.append({'model':path.stem,'single_refit_training_s':elapsed,**metrics})
        pd.DataFrame(rows).to_json(ROOT/'results'/'training_diagnostics.json',orient='records',indent=2)
        print(path.stem,elapsed,metrics['macro_f1'],flush=True)

if __name__=='__main__':main()
