"""Directed shortest-path HMM with entropy-adaptive emissions and gap resets."""
from heapq import heappop, heappush
import numpy as np

def bounded_distances(graph, source, targets, limit=2000.):
    targets=set(map(int,targets)); found={}; distance={int(source):0.}; queue=[(0.,int(source))]
    while queue and targets:
        cost,node=heappop(queue)
        if cost!=distance.get(node): continue
        if cost>limit: break
        if node in targets:
            found[node]=cost; targets.remove(node)
        a,b=graph.indptr[node:node+2]
        for neighbor,weight in zip(graph.indices[a:b],graph.data[a:b]):
            candidate=cost+float(weight); neighbor=int(neighbor)
            if candidate<=limit and candidate<distance.get(neighbor,float('inf')):
                distance[neighbor]=candidate; heappush(queue,(candidate,neighbor))
    return found

def transitions(trip,c,limit=2000.):
    ids=c['ids']; n,k=ids.shape
    sources=trip.arcs[ids[:-1],1]; targets=trip.arcs[ids[1:],0]
    needed={}
    for sr,tr in zip(sources,targets):
        unique=set(map(int,tr))
        for source in set(map(int,sr)): needed.setdefault(source,set()).update(unique)
    lookup={s:bounded_distances(trip.graph,s,tar,limit) for s,tar in needed.items()}
    matrix=np.full((n-1,k,k),np.inf,dtype=np.float32)
    for t in range(n-1):
        current,following=ids[t],ids[t+1]
        for a in range(k):
            mid=lookup[int(sources[t,a])]
            for b in range(k):
                if current[a]==following[b]:
                    progress=(c['fraction'][t+1,b]-c['fraction'][t,a])*trip.length[current[a]]
                    # Keep signed progress so decoding can explicitly distinguish
                    # tolerated GPS jitter from actual graph traversal.
                    matrix[t,a,b]=progress
                else:
                    d=mid.get(int(targets[t,b]),np.inf)
                    matrix[t,a,b]=(1-c['fraction'][t,a])*trip.length[current[a]]+d+c['fraction'][t+1,b]*trip.length[following[b]]
    return matrix

def decode(trip,c,prob,network=None,mode='adaptive',beta=18.,geometry_weight=.3,jitter_m=8.,emission_strength=1.):
    ids=c['ids']; n,k=ids.shape
    if network is None: network=transitions(trip,c)
    p=np.clip(prob,1e-7,1-1e-7)
    p=p/p.sum(axis=1,keepdims=True)
    entropy=-np.sum(p*np.log(p),axis=1)/np.log(k)
    if mode=='adaptive':
        weight=np.clip(geometry_weight+.35*entropy,.05,.8)
        sigma=np.clip(np.median(c['distance'][:,:2],axis=1)+8,8,35)
        geo=-c['distance']/sigma[:,None]+1.3*c['X'][:,:,1]*c['reliability'][:,None]
        # Confidence changes emission sharpness; network feasibility remains explicit.
        emission=(1-weight[:,None])*np.log(p)+weight[:,None]*geo
    else: emission=np.log(p)
    emission*=emission_strength
    emission-=emission.max(axis=1,keepdims=True)
    score=emission[0].copy(); back=np.zeros((n,k),dtype=np.int16); resets=[];chunks=[]
    observed=np.linalg.norm(np.diff(trip.gps,axis=0),axis=1)
    for t in range(1,n):
        dt=c['dt'][t]
        distance=network[t-1]
        feasible=np.isfinite(distance)&(distance<=65*dt+70)&(distance>=-jitter_m)
        penalty=np.abs(np.maximum(distance,0)-observed[t-1])/(beta+2*np.sqrt(max(dt,1)))
        transition=np.where(feasible,-penalty,-np.inf)
        values=score[:,None]+transition
        if dt>60 or not np.isfinite(values).any():
            chunks.append((t,int(np.argmax(score))))
            back[t]=-1;score=emission[t].copy();resets.append(t)
        else:
            back[t]=np.argmax(values,axis=0)
            score=values.max(axis=0)+emission[t]
        score-=np.max(score)
    chosen=np.zeros(n,dtype=np.int32)
    chunks.append((n,int(np.argmax(score))))
    lo=0
    for hi,state in chunks:
        for t in range(hi-1,lo-1,-1):
            chosen[t]=state
            if t>lo:state=int(back[t,state])
        lo=hi
    selected=ids[np.arange(n),chosen]
    selected_distance=network[np.arange(n-1),chosen[:-1],chosen[1:]]
    feasible=np.isfinite(selected_distance)&(selected_distance<=65*c['dt'][1:]+70)&(selected_distance>=-jitter_m)
    return {'arc_ids':selected,'chosen':chosen,'entropy':entropy,
            'confidence':p[np.arange(n),chosen], 'resets':resets,
            'network_feasible_fraction':float(np.mean(feasible)) if len(feasible) else 1.,
            'uncertain_fraction':float(np.mean(entropy>.7))}
