import numpy as np

class SigmoidCalibratedModel:
    """Persistable inference-only wrapper; never fits during prediction."""
    def __init__(self,base,calibrator):
        self.base=base;self.calibrator=calibrator;self.classes_=np.array([0,1])
    def predict_proba(self,X):
        p=np.clip(self.base.predict_proba(X)[:,1],1e-7,1-1e-7)
        return self.calibrator.predict_proba(np.log(p/(1-p))[:,None])
