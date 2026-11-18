"""Log a real frozen-model HMM/Viterbi run; never train or select parameters."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import argparse,hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib,numpy as np
from pathsnap.core import ROOT,FEATURES,load_trip,candidates,reference_labels
from pathsnap.decoder import transitions,decode
from pathsnap.metrics import route_metrics

def say(stage,message):
    print(f'[{stage}] {message}',flush=True)

def run_trip(path,model,config,steps):
    say('INPUT',f'trip={path.name} partition={path.parent.name}; reading GPS and directed graph')
    start=time.perf_counter();trip=load_trip(path)
    say('OBSERVATIONS',f'{len(trip.track):,} GPS measurements; {len(trip.nodes):,} nodes; {len(trip.arcs):,} directed roads')
    say('CANDIDATES','Retrieving possible hidden states from geometry and motion; no reference input')
    t=time.perf_counter()
    c=candidates(trip,strategy=config.get('candidate_strategy','nearest'),profile=config.get('candidate_profile','historical_v1'))
    n,k=c['ids'].shape
    say('HIDDEN STATES',f'{k} candidate directed road IDs per observation; {len(FEATURES)} features per candidate; generation_s={time.perf_counter()-t:.3f}')
    say('CLASSIFIER','Scoring candidate roads with the saved model; no fitting')
    t=time.perf_counter();p=model.predict_proba(c['X'].reshape(-1,c['X'].shape[-1]))[:,1].reshape(n,k)
    classifier=c['ids'][np.arange(n),p.argmax(axis=1)]
    norm=np.clip(p,1e-7,1-1e-7);norm/=norm.sum(axis=1,keepdims=True)
    say('CLASSIFIER',f'complete in {time.perf_counter()-t:.3f}s; score matrix={n} x {k}')
    say('EMISSION INPUT',f'observation 1 road IDs: {c["ids"][0].tolist()}')
    say('EMISSION INPUT','normalized classifier scores: '+np.array2string(norm[0],precision=4))
    say('EMISSIONS','Adaptive scoring blends log classifier scores with distance/heading evidence using candidate uncertainty')
    say('TRANSITIONS','Building bounded directed shortest-path distances between consecutive candidate sets')
    t=time.perf_counter();network=transitions(trip,c)
    say('TRANSITIONS',f'shape={network.shape}; finite distances={np.isfinite(network).sum():,}/{network.size:,}; construction_s={time.perf_counter()-t:.3f}')
    say('VITERBI',f'Forward dynamic programming then backtracking; mode={config["mode"]}, beta={config["beta"]}, geometry_weight={config["geometry_weight"]}, jitter_m={config.get("jitter_m",8)}, emission_strength={config.get("emission_strength",1)}, reversal_cost={config.get("uturn_penalty",0):.4f}')
    t=time.perf_counter()
    d=decode(trip,c,p,network=network,mode=config['mode'],beta=config['beta'],geometry_weight=config['geometry_weight'],
             jitter_m=config.get('jitter_m',8.),emission_strength=config.get('emission_strength',1.),uturn_penalty=config.get('uturn_penalty',0.))
    decode_s=time.perf_counter()-t
    selected=d['arc_ids'];collapsed=selected[np.r_[True,np.diff(selected)!=0]]
    continuity=float(np.mean(trip.arcs[collapsed[:-1],1]==trip.arcs[collapsed[1:],0])) if len(collapsed)>1 else 1.
    say('VITERBI',f'complete in {decode_s:.3f}s; {n} selected road states; {np.sum(selected!=classifier):,} selections differ from independent classifier Top-1')
    say('TRACE','Selected path AFTER backtracking (not a per-iteration progress trace)')
    for i in range(min(steps,n)):
        connection='first observation'
        if i:
            distance=network[i-1,d['chosen'][i-1],d['chosen'][i]]
            connection=f'network_distance={float(distance):.2f}m; reset={i in d["resets"]}'
        say('PATH',f'observation={i+1}/{n}; classifier_road={classifier[i]}; decoded_road={selected[i]}; relative_classifier_score={d["confidence"][i]:.4f}; {connection}')
    for i in np.flatnonzero(selected!=classifier)[:steps]:
        say('CHANGED',f'observation={i+1}; independent road={classifier[i]} (relative score={norm[i].max():.4f}); decoded road={selected[i]} (relative score={d["confidence"][i]:.4f}); full-sequence score determined the choice')
    say('CONTINUITY',f'direct connected road changes={100*continuity:.2f}% (reference-free)')
    say('FEASIBILITY',f'network-feasible transitions={100*d["network_feasible_fraction"]:.2f}% (allows intermediate roads and GPS jitter)')
    say('RESETS',f'count={len(d["resets"])}; observation indices, zero-based={d["resets"]}')
    record={'trip_id':trip.id,'observations':n,'direct_arc_continuity':continuity,'network_feasible_fraction':d['network_feasible_fraction'],
            'resets':d['resets'],'decode_s':decode_s,'prediction_sha256':hashlib.sha256(np.asarray(selected,dtype='<i4').tobytes()).hexdigest()}
    if (path/f'{trip.id}.route').exists():
        say('SCORING','Prediction finished. Loading supplied reference ONLY NOW for separate scoring')
        try:
            labels,_,route=reference_labels(trip,path)
            m=route_metrics(selected,labels,route,trip)
            record.update(point_accuracy=m['point_accuracy'],classifier_point_accuracy=float(np.mean(classifier==labels)))
            say('AGREEMENT',f'classifier={100*record["classifier_point_accuracy"]:.2f}%; HMM={100*m["point_accuracy"]:.2f}%; derived reference, NOT official evaluator accuracy')
        except (ValueError,OSError,IndexError) as error:
            say('SCORING',f'Unavailable: {error}; prediction remains valid')
    else:say('SCORING','No supplied reference; continuity and prediction remain available')
    say('COMPLETE',f'trip={trip.id}; total_demo_s={time.perf_counter()-start:.3f}')
    return record

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partition',choices=['student','evaluator'],default='student')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--trip',help='Eight-digit trip ID; defaults to a short demonstration trip')
    group.add_argument('--all-trips',action='store_true')
    parser.add_argument('--steps',type=int,default=5,help='Number of post-backtracking path selections to print')
    args=parser.parse_args()
    if args.steps<0:parser.error('--steps must be nonnegative')
    base=Path(os.environ.get('PATHSNAP_DATA_ROOT',str(ROOT/'data')))
    folder=base/'evaluator_test' if args.partition=='evaluator' else base/'Student folder'/'student_test'
    tid=args.trip or ('00000023' if args.partition=='evaluator' else '00000052')
    if not (len(tid)==8 and tid.isascii() and tid.isdigit()):parser.error('--trip requires eight ASCII digits')
    paths=sorted(p for p in folder.glob('*') if p.is_dir() and len(p.name)==8 and p.name.isascii() and p.name.isdigit()) if args.all_trips else [folder/tid]
    if not paths or any(not p.is_dir() for p in paths):parser.error('Requested trips are not available in the selected partition')
    before={n:hashlib.sha256((ROOT/'artifacts'/n).read_bytes()).hexdigest() for n in ['model.joblib','manifest.json','decoder.json']}
    config=json.loads((ROOT/'artifacts/decoder.json').read_text());manifest=json.loads((ROOT/'artifacts/manifest.json').read_text())
    say('MODEL',f'{manifest["model"]}; SHA256={before["model.joblib"]}')
    say('MODE','Frozen saved artifacts; no training, parameter search or model/configuration writes')
    model=joblib.load(ROOT/'artifacts/model.joblib')
    rows=[run_trip(path,model,config,args.steps) for path in paths]
    say('SUMMARY',f'{len(rows)} trips; equal-trip direct continuity={100*np.mean([r["direct_arc_continuity"] for r in rows]):.2f}%')
    if all('point_accuracy' in r for r in rows):
        say('SUMMARY',f'equal-trip derived point agreement={100*np.mean([r["point_accuracy"] for r in rows]):.4f}%; pooled={100*np.average([r["point_accuracy"] for r in rows],weights=[r["observations"] for r in rows]):.4f}%')
    after={n:hashlib.sha256((ROOT/'artifacts'/n).read_bytes()).hexdigest() for n in before}
    if before!=after:raise RuntimeError('Saved artifacts changed during this run')
    say('INTEGRITY','Saved model, manifest and decoder configuration unchanged')

if __name__=='__main__':main()
