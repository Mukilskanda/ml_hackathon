import asyncio,json,logging,re,time,uuid,os
os.environ.setdefault('OMP_NUM_THREADS',os.environ.get('PATHSNAP_THREADS','4'))
os.environ.setdefault('OPENBLAS_NUM_THREADS',os.environ.get('PATHSNAP_THREADS','4'))
from pathlib import Path
from contextlib import asynccontextmanager
import joblib
from fastapi import FastAPI,HTTPException,Request,Path as APIPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from pathsnap.core import ROOT,DATA,FEATURES,reference_labels,load_trip,load_indices
from pathsnap.service import predict_trip,serialize_prediction
from pathsnap.metrics import route_metrics,classification_metrics

log=logging.getLogger('uvicorn.error')
state={};lock=asyncio.Semaphore(1)

@asynccontextmanager
async def lifespan(app):
    for name in ['model.joblib','manifest.json','decoder.json']:
        if not (ROOT/'artifacts'/name).exists():raise RuntimeError(f'Missing artifacts/{name}; run training and route evaluation first')
    state['model']=joblib.load(ROOT/'artifacts'/'model.joblib')
    state['manifest']=json.loads((ROOT/'artifacts'/'manifest.json').read_text())
    state['decoder']=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    if state['manifest']['features']!=FEATURES or getattr(state['model'],'n_features_in_',len(FEATURES))!=len(FEATURES):
        raise RuntimeError('Model/feature schema mismatch; restore matching artifacts')
    if state['decoder'].get('candidate_strategy','nearest')!=state['manifest'].get('candidate_strategy','nearest'):
        raise RuntimeError('Model/decoder candidate strategy mismatch')
    if state['decoder'].get('candidate_profile','historical_v1')!=state['manifest'].get('candidate_profile','historical_v1'):
        raise RuntimeError('Model/decoder candidate profile mismatch')
    log.info('PathSnap model=%s decoder=%s; inference does not read .route files',state['manifest']['model'],state['decoder']['mode'])
    yield

app=FastAPI(title='PathSnap',version='1.0.0',lifespan=lifespan)
# Local hackathon network: requests have no cookies or credentials.
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

class PredictionRequest(BaseModel):
    trip_id:str=Field(pattern=r'^[0-9]{8}$',min_length=8,max_length=8)

def trip_root():
    base=Path(os.environ.get('PATHSNAP_DATA_ROOT',str(ROOT/'data')))
    evaluator=base/'evaluator_test'
    has_trip=evaluator.is_dir() and any(p.is_dir() and re.fullmatch(r'[0-9]{8}',p.name) for p in evaluator.iterdir())
    return evaluator if has_trip else base/'Student folder'/'student_test'

def partition_inventory():
    root=trip_root();complete=[];warnings=[]
    if root.is_dir():
        for path in sorted(root.iterdir()):
            if not path.is_dir() or not re.fullmatch(r'[0-9]{8}',path.name):continue
            missing=[ext for ext in ('track','nodes','arcs') if not (path/f'{path.name}.{ext}').is_file()]
            if missing:warnings.append(f'Trip {path.name} missing required files: {", ".join(missing)}')
            else:complete.append(path)
    if len(complete)!=10:warnings.append(f'{len(complete)} complete trips found; the required demonstration expects ten.')
    return root,complete,warnings

@app.get('/api/health')
def health():
    root,complete,warnings=partition_inventory()
    return {'status':'ok','model':state['manifest']['model'],'decoder':state['decoder']['mode'],
            'mode':'evaluator' if root.name=='evaluator_test' else 'development',
            'complete_trip_count':len(complete),'data_warnings':warnings,'data_ready':bool(complete),
            'reference_warning':state['manifest']['reference_warning']}

@app.get('/api/trips')
def trips():
    root,complete,warnings=partition_inventory()
    return {'mode':'evaluator' if root.name=='evaluator_test' else 'development',
            'warnings':warnings,
            'trips':[{'id':p.name,'label':f'Trip {i+1:02d} · {p.name}'} for i,p in enumerate(complete)]}

@app.get('/api/experiments')
def experiments():
    import pandas as pd
    table=pd.read_csv(ROOT/'results'/'model_comparison.csv').fillna('')
    route=pd.read_csv(ROOT/'results'/'route_comparison.csv')
    return {'models':table.to_dict(orient='records'),
            'routes':json.loads(route.groupby('method').mean(numeric_only=True).to_json(orient='index')),
            'manifest':state['manifest'],'decoder':state['decoder']}

@app.get('/api/reference/{trip_id}')
def reference(trip_id:str=APIPath(pattern=r'^[0-9]{8}$',min_length=8,max_length=8)):
    """Explicit comparison overlay; never called by model inference.

    Return the supplied arcs exactly, without inventing connecting roads or
    deriving point labels. Disable for a reference-free official demonstration.
    """
    if os.environ.get('PATHSNAP_REFERENCE_DISPLAY','1')=='0':
        return {'available':False,'reason':'Reference display is disabled on this server.'}
    path=trip_root()/trip_id
    if not path.is_dir():raise HTTPException(404,'Trip not found in active evaluation partition')
    if path.parent.name=='evaluator_test':
        return {'available':False,'reason':'Reserved evaluator references remain server-side and are not exposed to the UI.'}
    route_path=path/f'{trip_id}.route'
    if not route_path.is_file():
        return {'available':False,'reason':'No supplied .route reference for this trip.'}
    try:
        trip=load_trip(path)
        indices=load_indices(route_path,1).ravel()
        if indices.max()>=len(trip.arcs):raise ValueError('Invalid reference arc index')
        arcs=trip.arcs[indices]
        return {'available':True,'trip_id':trip_id,'source':'Supplied .route reference',
                'geometry':trip.nodes[arcs].tolist(),'route_arc_count':len(indices),
                'disconnected_joins':int(__import__('numpy').sum(arcs[:-1,1]!=arcs[1:,0])),
                'note':'Actual path means the supplied route reference; it is not an independent per-point GPS label or official evaluator score.'}
    except (ValueError,OSError,IndexError):
        log.exception('Reference comparison unavailable for trip=%s',trip_id)
        return {'available':False,'reason':'Supplied reference is invalid; prediction remains independent.'}

def execute(trip_id,request_id):
    started=time.perf_counter()
    path=trip_root()/trip_id
    if not path.is_dir():raise HTTPException(404,'Trip not found in active evaluation partition')
    log.info('INFERENCE request=%s trip=%s started',request_id,trip_id)
    trip,c,p,d,timings=predict_trip(path,state['model'],state['decoder'])
    geometry_started=time.perf_counter()
    response=serialize_prediction(trip,c,p,d,timings,state['manifest']['model'])
    timings['response_geometry_s']=time.perf_counter()-geometry_started
    scoring_started=time.perf_counter()
    # Reference is loaded ONLY AFTER prediction has finished; never serialized.
    if (path/f'{trip_id}.route').exists():
        try:
            labels,quality,route=reference_labels(trip,path)
            response['metrics']={**route_metrics(d['arc_ids'],labels,route,trip),
                'classifier_top1':classification_metrics(p,c['ids'],labels)['top1_accuracy'],
                'reference_distance_median_m':float(__import__('numpy').median(quality))}
            response['metric_basis']='Derived monotone alignment to supplied .route; not independent point ground truth.'
        except (ValueError,OSError,IndexError):
            log.exception('SCORING request=%s failed after successful inference',request_id)
            response['metrics']=None
            response['metric_basis']='Prediction succeeded; reference scoring unavailable due to invalid reference data.'
            response['warnings'].append('Server-side reference scoring failed; see receiving-server logs.')
    else:
        response['metrics']=None
        response['metric_basis']='No reference available; inference completed without accuracy scoring.'
    response['request_id']=request_id
    timings['reference_scoring_s']=time.perf_counter()-scoring_started
    timings['server_processing_s']=time.perf_counter()-started
    log.info('INFERENCE request=%s trip=%s observations=%d inference_s=%.3f scored=%s completed',
             request_id,trip_id,len(trip.gps),timings['total_s'],response['metrics'] is not None)
    return response

@app.post('/api/predict')
async def predict(payload:PredictionRequest):
    async with lock:
        try:return await asyncio.to_thread(execute,payload.trip_id,uuid.uuid4().hex[:10])
        except HTTPException:raise
        except (ValueError,FileNotFoundError) as exc:raise HTTPException(422,str(exc)) from exc
        except Exception as exc:
            log.exception('Inference failed')
            raise HTTPException(500,'Inference failed; see server logs') from exc

app.mount('/',StaticFiles(directory=ROOT/'ui',html=True),name='ui')
