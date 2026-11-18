"""Verify pruning cannot alter feasible transitions or selected road sequences."""
import sys,time,json,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from pathsnap.core import ROOT,DATA,load_trip
from pathsnap.decoder import transitions,decode

def main():
    out=ROOT/'results'/'critical_audit';cfg=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    kwargs={k:cfg[k] for k in ['mode','beta','geometry_weight','jitter_m','emission_strength']};rows=[]
    for path in sorted((DATA/'student_test').iterdir()):
        trip=load_trip(path);c=dict(np.load(ROOT/'cache'/f'adaptive_student_test_{trip.id}.npz'))
        frozen=dict(np.load(out/f'baseline_{trip.id}.npz'))
        t=time.perf_counter();original=transitions(trip,c,prune=False);base_s=time.perf_counter()-t
        t=time.perf_counter();pruned=transitions(trip,c);pruned_s=time.perf_counter()-t
        cap=65*c['dt'][1:,None,None]+70
        feasible=np.isfinite(original)&(original<=cap)&(original>=-cfg['jitter_m'])
        optimized=np.isfinite(pruned)&(pruned<=cap)&(pruned>=-cfg['jitter_m'])
        assert np.array_equal(feasible,optimized)
        np.testing.assert_array_equal(original[feasible],pruned[feasible])
        d=decode(trip,c,frozen['probability'],pruned,**kwargs)
        assert np.array_equal(d['arc_ids'],frozen['predicted'])
        rows.append({'trip_id':trip.id,'unpruned_s':base_s,'pruned_s':pruned_s,
                     'feasible_transitions_identical':True,'predictions_identical':True})
        print(rows[-1],flush=True)
    pd.DataFrame(rows).to_csv(out/'decoder_pruning_benchmark.csv',index=False)

if __name__=='__main__':main()
