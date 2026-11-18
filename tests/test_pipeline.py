from pathlib import Path
import tempfile
import numpy as np
from scipy.sparse import csr_matrix
from pathsnap.core import load_trip,project,candidates,ROOT,DATA,FEATURES
from pathsnap.decoder import bounded_distances,decode,transitions

def synthetic(tmp_path):
    path=tmp_path/'00000001';path.mkdir()
    # A directed eastbound road and a separate eastbound distractor.
    np.savetxt(path/'00000001.nodes',[[8,50],[8.001,50],[8.002,50],[8,50.001],[8.001,50.001]])
    np.savetxt(path/'00000001.arcs',[[0,1],[1,2],[3,4],[0,1]],fmt='%d')
    np.savetxt(path/'00000001.track',[[8.0002,50,1],[8.0008,50,2],[8.0015,50,3]])
    return load_trip(path)

def test_projection_clamps_to_segment():
    frac,dist,foot=project(np.array([[2.,1.],[-1.,0.]]),np.zeros((2,2)),np.array([[1.,0.],[1.,0.]]))
    np.testing.assert_allclose(frac,[1,0]);np.testing.assert_allclose(dist,[2**.5,1])

def test_directed_paths_and_duplicate_edges(tmp_path):
    trip=synthetic(tmp_path)
    assert abs(trip.graph[0,1]-trip.length[0])<1e-6
    assert 2 in bounded_distances(trip.graph,0,{2})
    assert 0 not in bounded_distances(trip.graph,2,{0})

def test_candidate_identity_and_geometry(tmp_path):
    trip=synthetic(tmp_path); c=candidates(trip,k=3)
    assert c['X'].shape==(3,3,len(FEATURES))
    assert np.isfinite(c['X']).all()
    assert all(len(set(row))==3 for row in c['ids'])
    np.testing.assert_allclose(c['distance'][:,0],0,atol=1e-3)

def test_single_observation_and_small_candidate_set(tmp_path):
    trip=synthetic(tmp_path)
    from dataclasses import replace
    trip=replace(trip,gps=trip.gps[:1],track=trip.track[:1])
    c=candidates(trip,k=8)
    assert c['ids'].shape==(1,4)
    d=decode(trip,c,np.ones((1,4))*.5,mode='adaptive')
    assert len(d['arc_ids'])==1

def test_invalid_timestamp_rejected(tmp_path):
    import pytest
    trip=synthetic(tmp_path)
    path=tmp_path/'00000001'/'00000001.track'
    track=trip.track.copy();track[1,2]=track[0,2];np.savetxt(path,track)
    with pytest.raises(ValueError,match='strictly increasing'):load_trip(path.parent)

def test_invalid_coordinate_rejected(tmp_path):
    import pytest
    trip=synthetic(tmp_path)
    path=tmp_path/'00000001'/'00000001.track'
    track=trip.track.copy();track[0,1]=120;np.savetxt(path,track)
    with pytest.raises(ValueError,match='geographic ranges'):load_trip(path.parent)

def test_viterbi_uses_future_and_directed_connectivity(tmp_path):
    trip=synthetic(tmp_path)
    c={'ids':np.array([[0,2],[0,2],[1,2]]),'fraction':np.array([[.2,.2],[.8,.8],[.5,.9]]),
       'dt':np.ones(3),'distance':np.zeros((3,2)),'X':np.zeros((3,2,len(FEATURES))),'reliability':np.ones(3)}
    net=transitions(trip,c)
    assert np.isinf(net[0,0,1])
    prob=np.array([[.4,.6],[.45,.55],[.99,.01]])
    d=decode(trip,c,prob,net,mode='fixed',beta=40)
    assert d['arc_ids'].tolist()==[0,0,1]

def test_gap_reset_is_explicit(tmp_path):
    trip=synthetic(tmp_path)
    c={'ids':np.array([[0,2],[0,2],[1,2]]),'fraction':np.zeros((3,2)),
       'dt':np.array([1,90,1]),'distance':np.zeros((3,2)),'X':np.zeros((3,2,len(FEATURES))),'reliability':np.ones(3)}
    d=decode(trip,c,np.full((3,2),.5),transitions(trip,c),mode='fixed')
    assert 1 in d['resets']

def test_inference_never_reads_reference(monkeypatch):
    import joblib,json
    from pathsnap.service import predict_trip
    real=np.loadtxt
    def guarded(path,*args,**kwargs):
        assert not str(path).endswith('.route'),'Reference leaked into prediction'
        return real(path,*args,**kwargs)
    monkeypatch.setattr(np,'loadtxt',guarded)
    model=joblib.load(ROOT/'artifacts'/'model.joblib')
    config=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    trip,c,p,d,timing=predict_trip(DATA/'student_test'/'00000052',model,config)
    assert len(d['arc_ids'])==len(trip.track)
    assert np.isfinite(p).all()

def test_api_validation_and_no_reference_exposure(monkeypatch):
    from backend import app as api
    monkeypatch.setattr(api,'trip_root',lambda:DATA/'student_test')
    from fastapi.testclient import TestClient
    from backend.app import app
    with TestClient(app) as client:
        assert client.get('/api/health').status_code==200
        experiments=client.get('/api/experiments')
        assert experiments.status_code==200
        assert len(experiments.json()['models'])>=7
        assert client.post('/api/predict',json={'trip_id':'../../etc'}).status_code==422
        assert client.post('/api/predict',json={'trip_id':'99999999'}).status_code==404
        response=client.post('/api/predict',json={'trip_id':'00000052'})
        assert response.status_code==200,response.text
        payload=response.json()
        assert not {'labels','reference_route','ground_truth','reference_arc_ids'}&payload.keys()
        assert len(payload['arc_ids'])==payload['observations']
