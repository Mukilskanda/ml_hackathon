import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss, confusion_matrix

def classification_metrics(prob, ids, labels):
    truth=(ids==labels[:,None]).astype(int)
    chosen=np.argmax(prob,axis=1)
    predicted=ids[np.arange(len(ids)),chosen]
    binary=prob.ravel() >= .5
    return {'candidate_accuracy':float(accuracy_score(truth.ravel(),binary)),
            'precision':float(precision_score(truth.ravel(),binary,zero_division=0)),
            'recall':float(recall_score(truth.ravel(),binary,zero_division=0)),
            'macro_f1':float(f1_score(truth.ravel(),binary,average='macro',zero_division=0)),
            'log_loss':float(log_loss(truth.ravel(),np.clip(prob.ravel(),1e-7,1-1e-7),labels=[0,1])),
            'top1_accuracy':float(np.mean(predicted==labels)),
            'candidate_miss_rate':float(np.mean(~truth.any(axis=1))),
            'confusion_matrix':confusion_matrix(truth.ravel(),binary,labels=[0,1]).tolist()}

def route_metrics(predicted, labels, reference_route, trip):
    collapsed=predicted[np.r_[True,np.diff(predicted)!=0]]
    continuity=(collapsed[:-1]==collapsed[1:]) | (trip.arcs[collapsed[:-1],1]==trip.arcs[collapsed[1:],0])
    # Arc-set precision/recall measures coverage; it does not assess route order.
    p,r=set(map(int,collapsed)),set(map(int,reference_route))
    precision=len(p&r)/max(1,len(p)); recall=len(p&r)/max(1,len(r))
    return {'point_accuracy':float(np.mean(predicted==labels)),
            'direct_arc_continuity':float(np.mean(continuity)) if len(continuity) else 1.,
            'route_arc_precision':precision,'route_arc_recall':recall,
            'route_arc_f1':2*precision*recall/max(1e-9,precision+recall),
            'exact_sequence_match':bool(np.array_equal(collapsed,reference_route)),
            'predicted_arc_changes':len(collapsed)-1}
