"""Inference accepts GPS and graph only; scoring is a separate server-side step."""
import json,time
from pathlib import Path
import joblib
import numpy as np
from scipy.sparse.csgraph import dijkstra
from .core import ROOT,load_trip,candidates
from .decoder import decode

def predict_trip(path,model,config):
    start=time.perf_counter(); trip=load_trip(path);loaded=time.perf_counter()
    c=candidates(trip,strategy=config.get('candidate_strategy','nearest'),profile=config.get('candidate_profile','historical_v1')); prepared=time.perf_counter()
    probability=model.predict_proba(c['X'].reshape(-1,c['X'].shape[-1]))[:,1].reshape(c['ids'].shape)
    classified=time.perf_counter()
    decoded=decode(trip,c,probability,mode=config['mode'],beta=config['beta'],geometry_weight=config['geometry_weight'],
                   jitter_m=config.get('jitter_m',8.),emission_strength=config.get('emission_strength',1.),
                   uturn_penalty=config.get('uturn_penalty',0.))
    finished=time.perf_counter()
    return trip,c,probability,decoded,{'load_s':loaded-start,'candidate_s':prepared-loaded,
           'classifier_s':classified-prepared,'decoder_s':finished-classified,'total_s':finished-start}

def route_geometry(trip,selected,break_indices=None):
    breaks=set(break_indices or [])
    retained=np.flatnonzero(np.r_[True,np.diff(selected)!=0] | np.isin(np.arange(len(selected)),list(breaks)))
    lines=[];gaps=0
    previous=None
    for index in retained:
        arc=selected[index]
        if index in breaks and index>0:
            previous=None;gaps+=1
        source,target=map(int,trip.arcs[arc])
        if previous is not None and previous!=source:
            distance,pred=dijkstra(trip.graph,directed=True,indices=previous,return_predecessors=True,limit=2000)
            if np.isfinite(distance[source]):
                chain=[source];current=source
                while current!=previous:
                    current=int(pred[current])
                    if current<0: break
                    chain.append(current)
                if chain[-1]==previous:lines.append(trip.nodes[chain[::-1]].tolist())
                else:gaps+=1
            else:gaps+=1
        lines.append(trip.nodes[[source,target]].tolist());previous=target
    return lines,gaps

def serialize_prediction(trip,c,p,d,timings,model_name):
    n=len(p);chosen=d['chosen'];selected=d['arc_ids']
    lines,gaps=route_geometry(trip,selected,d['resets'])
    # A local road context layer; no route reference is consulted here.
    lo=trip.gps.min(axis=0)-200;hi=trip.gps.max(axis=0)+200
    mid=trip.start+trip.delta*.5
    ix=np.flatnonzero(np.all((mid>=lo)&(mid<=hi),axis=1))
    if len(ix)>14000:ix=ix[np.linspace(0,len(ix)-1,14000).astype(int)]
    classifier=c['ids'][np.arange(n),p.argmax(axis=1)]
    classifier_lines=trip.nodes[trip.arcs[np.unique(classifier)]].tolist()
    points=trip.unproject(c['foot'][np.arange(n),chosen])
    return {'trip_id':trip.id,'partition':trip.partition,'model':model_name,'observations':n,
       'gps':trip.track[:,:2].tolist(),'timestamps':trip.track[:,2].tolist(),
       'roads':trip.nodes[trip.arcs[ix]].tolist(),'route':lines,'classifier_route':classifier_lines,
       'matched_points':points.tolist(),'arc_ids':selected.tolist(),
       'confidence':d['confidence'].tolist(),'entropy':d['entropy'].tolist(),
       'resets':d['resets'],'geometry_gaps':gaps,'uncertain_fraction':d['uncertain_fraction'],
       'network_feasible_fraction':d['network_feasible_fraction'],'timings':timings,
       'warnings':['Model confidence is uncalibrated; use as a relative score.']+
         ([f'{np.mean(c["distance"][:,0]>100):.1%} of observations are over 100 m from the nearest retained candidate.'] if np.any(c['distance'][:,0]>100) else [])+
         ([f'{gaps} reset or unreachable route joins are shown as separate lines.'] if gaps else [])}
