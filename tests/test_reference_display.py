"""Reference comparison remains separate from the immutable prediction pipeline."""
import numpy as np
from fastapi.testclient import TestClient
from backend import app as api
from test_pipeline import synthetic

def test_supplied_geometry_is_exact_and_never_infers(tmp_path,monkeypatch):
    trip=synthetic(tmp_path)
    monkeypatch.setattr(api,'trip_root',lambda:tmp_path)
    monkeypatch.setattr(api,'predict_trip',lambda *args:(_ for _ in ()).throw(AssertionError('Comparison invoked inference')))
    monkeypatch.setenv('PATHSNAP_REFERENCE_DISPLAY','1')
    path=tmp_path/trip.id/f'{trip.id}.route'
    with TestClient(api.app) as client:
        assert client.get(f'/api/reference/{trip.id}').json()['available'] is False
        # Noncontiguous supplied arcs must remain separate; no invented connector.
        path.write_text('0\n2\n')
        reference=client.get(f'/api/reference/{trip.id}').json()
        assert reference['available'] is True
        assert reference['geometry']==trip.nodes[trip.arcs[[0,2]]].tolist()
        assert reference['disconnected_joins']==1
        assert not {'labels','reference_arc_ids'}&reference.keys()
        for invalid in ['0.5\n','999\n','-1\n']:
            path.write_text(invalid)
            assert client.get(f'/api/reference/{trip.id}').json()['available'] is False
        assert client.get('/api/reference/not-a-trip').status_code==422
        assert client.get('/api/reference/99999999').status_code==404

def test_reference_display_can_be_disabled(monkeypatch):
    monkeypatch.setenv('PATHSNAP_REFERENCE_DISPLAY','0')
    with TestClient(api.app) as client:
        response=client.get('/api/reference/00000052')
        assert response.status_code==200 and response.json()['available'] is False
        assert 'disabled' in response.json()['reason']

def test_reserved_reference_never_reaches_ui_even_when_display_enabled(tmp_path,monkeypatch):
    root=tmp_path/'evaluator_test';root.mkdir()
    trip=synthetic(root)
    (root/trip.id/f'{trip.id}.route').write_text('0\n1\n')
    monkeypatch.setattr(api,'trip_root',lambda:root)
    monkeypatch.setenv('PATHSNAP_REFERENCE_DISPLAY','1')
    monkeypatch.setattr(api,'load_trip',lambda *a:(_ for _ in ()).throw(AssertionError('Reserved comparison loaded raw data')))
    with TestClient(api.app) as client:
        payload=client.get(f'/api/reference/{trip.id}').json()
        assert payload['available'] is False
        assert 'server-side' in payload['reason']
        assert not {'geometry','labels','reference_arc_ids'}&payload.keys()
