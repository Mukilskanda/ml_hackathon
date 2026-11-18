from itertools import product
from types import SimpleNamespace
from pathlib import Path
import json,shutil
import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.special import logsumexp
from pathsnap.core import ROOT,DATA,load_trip,candidates,load_indices
from pathsnap.decoder import bounded_distances,decode,transitions

def test_directed_dijkstra_matches_scipy_on_random_graph():
    rng=np.random.default_rng(44)
    matrix=rng.uniform(1,50,(14,14));matrix[rng.random((14,14))<.7]=0;np.fill_diagonal(matrix,0)
    graph=csr_matrix(matrix)
    for source in range(14):
        expected=dijkstra(graph,indices=source,directed=True,limit=65)
        actual=bounded_distances(graph,source,range(14),65)
        for target in range(14):
            assert actual.get(target,np.inf)==pytest.approx(expected[target])

@pytest.mark.parametrize('normalized',[False,True])
def test_viterbi_matches_exhaustive_path_enumeration(normalized):
    rng=np.random.default_rng(87);n=5;k=2
    trip=SimpleNamespace(gps=np.column_stack([np.arange(n)*4,np.zeros(n)]),arcs=np.array([[0,1],[1,0]]))
    c={'ids':np.tile([0,1],(n,1)),'dt':np.ones(n),'distance':np.zeros((n,k)),
       'X':np.zeros((n,k,15)),'reliability':np.zeros(n)}
    for repeat in range(10):
        p=rng.uniform(.01,.99,(n,k));net=rng.uniform(-2,25,(n-1,k,k))
        loge=np.log(p/p.sum(axis=1,keepdims=True))*.4
        logt=-np.abs(np.maximum(net,0)-4)/(8+2)
        reverse=np.array([[False,True],[True,False]])
        logt-=np.log(2)*reverse
        if normalized:logt-=logsumexp(logt,axis=2,keepdims=True)
        scores={path:sum(loge[t,path[t]] for t in range(n))+sum(logt[t-1,path[t-1],path[t]] for t in range(1,n)) for path in product(range(k),repeat=n)}
        expected=max(scores,key=scores.get)
        result=decode(trip,c,p,net,mode='fixed',beta=8,jitter_m=30,emission_strength=.4,
                      uturn_penalty=np.log(2),normalize_transitions=normalized)
        assert tuple(result['chosen'])==expected

def test_single_arc_entropy_and_serializable_output(tmp_path):
    path=tmp_path/'00000001';path.mkdir()
    np.savetxt(path/'00000001.nodes',[[8,50],[8.001,50]])
    np.savetxt(path/'00000001.arcs',[[0,1]],fmt='%d')
    np.savetxt(path/'00000001.track',[[8.0002,50,1],[8.0003,50,2]])
    trip=load_trip(path);c=candidates(trip)
    result=decode(trip,c,np.array([[.1],[.2]]))
    assert result['entropy'].tolist()==[0.,0.]
    assert np.isfinite(result['confidence']).all()
    assert result['arc_ids'].tolist()==[0,0]

@pytest.mark.parametrize('contents',['0.5 1\n','0 nan\n','-1 1\n','0 9999999999999\n'])
def test_index_files_reject_nonintegers_and_invalid_values(tmp_path,contents):
    file=tmp_path/'arcs';file.write_text(contents)
    with pytest.raises(ValueError):load_indices(file,2)

def test_pruning_preserves_feasible_arcs():
    trip=load_trip(DATA/'student_test'/'00000052')
    c=dict(np.load(ROOT/'cache'/'adaptive_student_test_00000052.npz'))
    a=transitions(trip,c,prune=False);b=transitions(trip,c)
    feasible=np.isfinite(a)&(a<=65*c['dt'][1:,None,None]+70)&(a>=-30)
    assert np.array_equal(feasible,np.isfinite(b)&(b<=65*c['dt'][1:,None,None]+70)&(b>=-30))
    np.testing.assert_array_equal(a[feasible],b[feasible])

@pytest.mark.parametrize('value',[np.nan,np.inf,-.01,1.01])
def test_invalid_probabilities_rejected(value):
    with pytest.raises(ValueError,match='probabilities'):
        decode(None,{'ids':np.zeros((1,1),int)},np.array([[value]]),network=np.empty((0,1,1)))

def test_reference_failure_does_not_destroy_prediction(tmp_path,monkeypatch):
    from backend import app as api
    from fastapi.testclient import TestClient
    root=tmp_path/'student_test';target=root/'00000052';target.mkdir(parents=True)
    for ext in ('nodes','arcs','track'):
        shutil.copyfile(DATA/'student_test'/'00000052'/f'00000052.{ext}',target/f'00000052.{ext}')
    monkeypatch.setattr(api,'trip_root',lambda:root)
    with TestClient(api.app) as client:
        without=client.post('/api/predict',json={'trip_id':'00000052'}).json()
        assert without['metrics'] is None
        (target/'00000052.route').write_text('0.5\n')
        response=client.post('/api/predict',json={'trip_id':'00000052'})
        assert response.status_code==200,response.text
        broken=response.json()
        assert broken['metrics'] is None
        assert broken['arc_ids']==without['arc_ids']
        assert any('scoring failed' in w for w in broken['warnings'])
        json.dumps(broken,allow_nan=False)

def test_evaluator_partition_inventory_isolation(tmp_path,monkeypatch):
    from backend import app as api
    monkeypatch.setenv('PATHSNAP_DATA_ROOT',str(tmp_path))
    evaluator=tmp_path/'evaluator_test';evaluator.mkdir()
    (evaluator/'README.txt').write_text('metadata is not a trip')
    assert api.trip_root().name=='student_test'
    trip=evaluator/'12345678';trip.mkdir();(trip/'12345678.track').write_text('8 50 1\n')
    root,complete,warnings=api.partition_inventory()
    assert root==evaluator and complete==[] and any('nodes' in w for w in warnings)
    for ext in ('nodes','arcs'):(trip/f'12345678.{ext}').write_text('0 1\n')
    root,complete,warnings=api.partition_inventory()
    assert complete==[trip] and any('expects ten' in w for w in warnings)

def test_ascii_and_exact_length_trip_ids():
    from backend.app import PredictionRequest
    for value in ['٠٠٠٠٠٠٥٢','00000052\n','000000520','../00052']:
        with pytest.raises(ValueError):PredictionRequest(trip_id=value)

def test_route_geometry_does_not_bridge_a_reset():
    from pathsnap.service import route_geometry
    trip=SimpleNamespace(nodes=np.array([[0,0],[1,0],[2,0],[3,0]],float),
                         arcs=np.array([[0,1],[1,2],[2,3]]),
                         graph=csr_matrix(([1.,1.,1.],([0,1,2],[1,2,3])),shape=(4,4)))
    unbroken,gaps=route_geometry(trip,np.array([0,2]))
    broken,breaks=route_geometry(trip,np.array([0,2]),[1])
    assert len(unbroken)==3 and gaps==0
    assert len(broken)==2 and breaks==1

def test_historical_candidate_profile_reproduces_training_cache():
    trip=load_trip(DATA/'train'/'00000096')
    historical=candidates(trip,strategy='adaptive',profile='historical_v1')
    with np.load(ROOT/'cache'/'adaptive_train_00000096.npz') as saved:
        np.testing.assert_array_equal(historical['ids'],saved['ids'])
        np.testing.assert_allclose(historical['X'],saved['X'],atol=1e-6)
