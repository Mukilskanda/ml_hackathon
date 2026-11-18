"""Independent raw-file replay and alternative implementation of reference DP."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json,time,hashlib,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from pathsnap.core import ROOT,DATA,load_trip,candidates,reference_labels

def independent_labels(trip,route,heading_weight=8.,progress_weight=.015):
    # Independent geometry + convolution + DP history/argmin traceback; no cache,
    # production reference_labels, prefix-winner array or candidate predictions.
    gps=trip.gps
    smooth=np.column_stack([np.convolve(np.pad(gps[:,a],2,mode='edge'),np.ones(5)/5,mode='valid') for a in range(2)])
    velocity=np.gradient(smooth,axis=0) if len(gps)>1 else np.zeros_like(gps)
    magnitude=np.linalg.norm(velocity,axis=1);heading=velocity/np.maximum(magnitude[:,None],1e-6)
    reliable=np.clip(magnitude/4,0,1)
    a=trip.xy[trip.arcs[route,0]];v=trip.xy[trip.arcs[route,1]]-a
    length=np.maximum(np.linalg.norm(v,axis=1),.01)
    progress=np.r_[0,np.cumsum(length)[:-1]]
    history=np.empty((len(gps)+1,len(route)))
    history[0]=.002*progress
    for t,point in enumerate(gps):
        f=np.clip(np.einsum('ij,ij->i',point-a,v)/np.maximum(np.einsum('ij,ij->i',v,v),1e-8),0,1)
        distance=np.sqrt(((point-a-f[:,None]*v)**2).sum(axis=1))
        local=np.minimum(distance,300)+heading_weight*reliable[t]*(1-(v/length[:,None])@heading[t])
        history[t+1]=local+np.minimum.accumulate(history[t]-progress_weight*progress)+progress_weight*progress
    j=int(history[-1].argmin());positions=np.empty(len(gps),int)
    for t in range(len(gps)-1,-1,-1):
        positions[t]=j
        candidates=history[t,:j+1]-progress_weight*progress[:j+1]
        j=int(np.flatnonzero(candidates==candidates.min())[-1])
    return route[positions]

def moving_window_overlap():
    windows={};duplicates=[];identical={};raw_duplicates=[]
    for partition in ['train','student_test']:
        for path in sorted((DATA/partition).iterdir()):
            content=(path/f'{path.name}.track').read_bytes();digest=hashlib.sha256(content).hexdigest()
            if digest in identical:raw_duplicates.append([identical[digest],f'{partition}/{path.name}'])
            identical[digest]=f'{partition}/{path.name}'
            gps=np.loadtxt(path/f'{path.name}.track',ndmin=2)[:,:2]
            coords=np.rint(gps*1e6).astype(np.int64)
            for i in range(max(0,len(coords)-9)):
                segment=coords[i:i+10]
                if np.linalg.norm(segment[-1]-segment[0])<50:continue
                key=hashlib.sha256(segment.tobytes()).digest()
                if partition=='train':windows.setdefault(key,(path.name,i))
                elif key in windows:duplicates.append({'train':windows[key],'student_test':[path.name,i]})
    return {'identical_track_files':raw_duplicates,'cross_partition_moving_10_point_windows':duplicates,
      'window_coordinates':'Rounded to 1e-6 degrees; excludes nearly stationary windows; not a proof against all semantic overlap.'}

def main():
    out=ROOT/'results'/'critical_audit';out.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('frozen_decoder',out/'frozen_decoder.py')
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
    model=joblib.load(ROOT/'artifacts'/'model.joblib')
    config_path=ROOT/'artifacts'/'decoder_baseline.json'
    config=json.loads((config_path if config_path.exists() else ROOT/'artifacts'/'decoder.json').read_text())
    saved=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str});records=[]
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path);c=candidates(trip,strategy=config['candidate_strategy'])
        labels,quality,route=reference_labels(trip,path);independent=independent_labels(trip,route)
        with np.load(ROOT/'cache'/f'adaptive_student_test_{trip.id}.npz') as z:
            assert np.array_equal(c['ids'],z['ids']);np.testing.assert_allclose(c['X'],z['X'],atol=1e-6)
            assert np.array_equal(labels,z['labels'])
        prob=model.predict_proba(c['X'].reshape(-1,c['X'].shape[-1]))[:,1].reshape(c['ids'].shape)
        np.testing.assert_allclose(prob,np.load(ROOT/'results'/'probabilities'/f'{json.loads((ROOT/"artifacts"/"manifest.json").read_text())["model"]}_{trip.id}.npy'),atol=1e-7)
        network=baseline.transitions(trip,c);d=baseline.decode(trip,c,prob,network,**{k:config[k] for k in ['mode','beta','geometry_weight','jitter_m','emission_strength']})
        prediction=d['arc_ids'];correct=int(np.sum(prediction==labels));wrong=prediction!=labels
        candidate_miss=~np.any(c['ids']==labels[:,None],axis=1)
        reversed_pair=np.all(trip.arcs[prediction]==trip.arcs[labels][:,::-1],axis=1)
        same_pair=np.all(trip.arcs[prediction]==trip.arcs[labels],axis=1)
        rate=correct/len(labels)
        assert abs(rate-float(saved[(saved.method=='adaptive_hmm')&(saved.trip_id==trip.id)].point_accuracy.iloc[0]))<1e-12
        # Sensitivity uses two plausible reference alignment changes, never to
        # choose a new model or repair predictions from test labels.
        no_heading=independent_labels(trip,route,heading_weight=0)
        progress2=independent_labels(trip,route,progress_weight=.03)
        record={'trip_id':trip.id,'observations':len(labels),'correct':correct,'accuracy':rate,
          'independent_alignment_disagreements':int(np.sum(labels!=independent)),
          'errors':int(wrong.sum()),'errors_reference_not_candidate':int(np.sum(wrong&candidate_miss)),
          'errors_reverse_directed_segment':int(np.sum(wrong&reversed_pair)),
          'errors_equivalent_directed_node_pair':int(np.sum(wrong&same_pair)),
          'errors_reference_distance_over_30m':int(np.sum(wrong&(quality>30))),
          'label_change_no_heading':float(np.mean(no_heading!=labels)),
          'prediction_agreement_no_heading_reference':float(np.mean(prediction==no_heading)),
          'label_change_double_progress_cost':float(np.mean(progress2!=labels)),
          'prediction_agreement_double_progress_reference':float(np.mean(prediction==progress2))}
        records.append(record)
        np.savez_compressed(out/f'baseline_{trip.id}.npz',predicted=prediction,labels=labels,independent_labels=independent,probability=prob)
        print(json.dumps(record),flush=True)
    overlap=moving_window_overlap();(out/'partition_overlap.json').write_text(json.dumps(overlap,indent=2))
    split=json.loads((ROOT/'results'/'training_split_manifest.json').read_text())
    train_ids={p.name for p in (DATA/'train').iterdir()};test_ids={p.name for p in (DATA/'student_test').iterdir()}
    assert not train_ids&test_ids
    for f in split['folds']:
        a,b=set(f['fit_trip_ids']),set(f['validation_trip_ids']);assert not a&b and a|b==train_ids
    summary={'macro_trip_accuracy':float(np.mean([r['accuracy'] for r in records])),
      'observation_weighted_accuracy':sum(r['correct'] for r in records)/sum(r['observations'] for r in records),
      'total_observations':sum(r['observations'] for r in records),'total_correct':sum(r['correct'] for r in records),
      'all_cached_candidates_features_probabilities_labels_reproduced':True,
      'independent_alignment_disagreements':sum(r['independent_alignment_disagreements'] for r in records),
      'trip_id_partitions_disjoint':True,'all_three_group_folds_disjoint_and_cover_80_trips':True,
      'interpretation':'Agreement with derived labels on repeatedly used development trips; neither independent truth nor an unbiased final generalisation estimate.',
      'records':records}
    (out/'accuracy_audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)

if __name__=='__main__':main()
