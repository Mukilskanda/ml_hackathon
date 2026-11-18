"""A reference-free API metric must match the report's direct-arc definition."""
import numpy as np
import pytest
from test_pipeline import synthetic
from pathsnap.service import serialize_prediction
from pathsnap.metrics import route_metrics

@pytest.mark.parametrize('arcs,expected',[([0,0,1],1.),([0,1,2],.5),([2,2,2],1.)])
def test_serialized_continuity_matches_report_without_reference(tmp_path,arcs,expected):
    trip=synthetic(tmp_path);selected=np.array(arcs)
    c={'ids':selected[:,None],'foot':trip.start[selected,None,:],'distance':np.zeros((3,1))}
    d={'chosen':np.zeros(3,dtype=int),'arc_ids':selected,'confidence':np.ones(3),'entropy':np.zeros(3),
       'resets':[],'uncertain_fraction':0.,'network_feasible_fraction':1.}
    response=serialize_prediction(trip,c,np.ones((3,1)),d,{},'test')
    assert response['direct_arc_continuity']==pytest.approx(expected)
    assert response['direct_arc_continuity']==route_metrics(selected,selected,selected,trip)['direct_arc_continuity']
