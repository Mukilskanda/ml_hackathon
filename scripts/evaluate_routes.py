import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from pathsnap.core import ROOT,DATA,load_trip
from pathsnap.decoder import transitions,decode
from pathsnap.metrics import route_metrics

def main():
    manifest=json.loads((ROOT/'artifacts'/'manifest.json').read_text())
    model=manifest['model'];rows=[]; cache=[]
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path)
        prefix='adaptive_' if manifest.get('candidate_strategy')=='adaptive' else ''
        c=dict(np.load(ROOT/'cache'/f'{prefix}student_test_{trip.id}.npz'))
        p=np.load(ROOT/'results'/'probabilities'/f'{model}_{trip.id}.npy')
        started=time.perf_counter();network=transitions(trip,c);elapsed=time.perf_counter()-started
        np.savez_compressed(ROOT/'cache'/f'network_{trip.id}.npz',network=network)
        cache.append((trip,c,p,network))
        print(f'Graph transitions {trip.id}: {elapsed:.1f}s',flush=True)
    # Decoder search is development-stage tuning on permitted student-test trips.
    searches=[]
    for mode in ['fixed','adaptive']:
     for jitter in [8.,30.]:
      for strength in [.4,1.]:
       for beta in [8.,18.,40.]:
        for weight in ([0.] if mode=='fixed' else [.1,.6]):
         searches.append(evaluate_setting(cache,mode,beta,weight,jitter,strength))
    best=max(searches,key=lambda r:r['mean_trip_accuracy'])
    fixed=max([s for s in searches if s['mode']=='fixed'],key=lambda r:r['mean_trip_accuracy'])
    adaptive=max([s for s in searches if s['mode']=='adaptive'],key=lambda r:r['mean_trip_accuracy'])
    for trip,c,p,network in cache:
        with np.load(ROOT/'cache'/f'student_test_{trip.id}.npz') as raw:nearest=raw['ids'][:,0]
        for name,pred in [('nearest_road',nearest),('classifier_only',c['ids'][np.arange(len(p)),p.argmax(axis=1)])]:
            rows.append({'method':name,'trip_id':trip.id,**route_metrics(pred,c['labels'],c['route'],trip)})
    modelrows=[]
    for probability in sorted((ROOT/'results'/'probabilities').glob('*.npy')):
        name,tid=probability.stem.rsplit('_',1)
        entry=next((v for v in cache if v[0].id==tid),None)
        if entry is None:continue
        trip,c,_,_=entry
        if name!=model:
            c=dict(np.load(ROOT/'cache'/f'student_test_{trip.id}.npz'))
        p=np.load(probability)
        pred=c['ids'][np.arange(len(p)),p.argmax(axis=1)]
        modelrows.append({'model':name,'trip_id':tid,**route_metrics(pred,c['labels'],c['route'],trip)})
    pd.DataFrame(modelrows).to_csv(ROOT/'results'/'model_route_metrics.csv',index=False)
    for name,search in [('fixed_hmm',fixed),('adaptive_hmm',adaptive)]:
        rows.extend([{'method':name,**r} for r in search['records']])
    pd.DataFrame(rows).to_csv(ROOT/'results'/'route_comparison.csv',index=False)
    (ROOT/'results'/'decoder_search.json').write_text(json.dumps(searches,indent=2))
    config={k:best[k] for k in ['mode','beta','geometry_weight','jitter_m','emission_strength']}
    config['candidate_strategy']=manifest.get('candidate_strategy','nearest')
    config['selection']='highest equal-trip mean derived-reference accuracy across 10 permitted student-test trips'
    config['warning']='Development-selected decoder score is optimistic; evaluator generalization remains unmeasured.'
    (ROOT/'artifacts'/'decoder.json').write_text(json.dumps(config,indent=2))
    print('DECODER '+json.dumps(config),flush=True)

def evaluate_setting(cache,mode,beta,weight,jitter,strength):
        records=[]
        for trip,c,p,network in cache:
            t=time.perf_counter();d=decode(trip,c,p,network,mode,beta,weight,jitter,strength)
            m=route_metrics(d['arc_ids'],c['labels'],c['route'],trip)
            records.append({'trip_id':trip.id,**m,'network_feasible_fraction':d['network_feasible_fraction'],
              'uncertain_fraction':d['uncertain_fraction'],'resets':len(d['resets']),'decode_s':time.perf_counter()-t})
        # Equal-trip weighting prevents long tracks dominating decoder selection.
        score=float(np.mean([r['point_accuracy'] for r in records]))
        print(f'{mode} beta={beta} geometry={weight} jitter={jitter} strength={strength}: mean-trip accuracy={score:.4f}',flush=True)
        return {'mode':mode,'beta':beta,'geometry_weight':weight,'jitter_m':jitter,'emission_strength':strength,
                'mean_trip_accuracy':score,'records':records}

if __name__=='__main__':main()
