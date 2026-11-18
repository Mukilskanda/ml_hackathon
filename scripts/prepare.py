import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json, time
import numpy as np
import pandas as pd
from pathsnap.core import DATA, ROOT, FEATURES, load_trip, candidates, reference_labels, inventory

def main():
    (ROOT/'cache').mkdir(exist_ok=True)
    (ROOT/'results').mkdir(exist_ok=True)
    records=[]
    for path in sorted(DATA.glob('*/*')):
        if not path.is_dir(): continue
        started=time.perf_counter()
        trip=load_trip(path)
        item=inventory(trip,path)
        target=ROOT/'cache'/f'{trip.partition}_{trip.id}.npz'
        if not target.exists():
            c=candidates(trip)
            labels, quality, route=reference_labels(trip,path)
            np.savez_compressed(target, **c, labels=labels, quality=quality, route=route)
        with np.load(target) as c:
            item.update(candidate_miss_rate=float(np.mean(~np.any(c['ids']==c['labels'][:,None],axis=1))),
                        reference_distance_median=float(np.median(c['quality'])),
                        reference_over_50m=float(np.mean(c['quality']>50)))
        records.append(item)
        pd.DataFrame(records).to_csv(ROOT/'results'/'dataset_inventory.csv',index=False)
        print(f'{trip.partition} {trip.id}: {item["observations"]} GPS, miss={item["candidate_miss_rate"]:.3f}, {time.perf_counter()-started:.1f}s',flush=True)
    (ROOT/'results'/'feature_schema.json').write_text(json.dumps(FEATURES,indent=2))

if __name__=='__main__': main()
