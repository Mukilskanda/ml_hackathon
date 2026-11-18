"""Validate and import the separately supplied evaluator ZIP, without training."""
import sys,json,re,zipfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathsnap.core import ROOT,load_trip,load_indices

def main():
    archive=Path(sys.argv[1]);base=(ROOT/'data').resolve()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None,'Corrupt ZIP'
        entries=[i for i in z.infolist() if not i.is_dir()]
        assert sum(i.file_size for i in entries)<100_000_000,'Unexpected dataset size'
        pattern=r'evaluator_test/([0-9]{8})/\1\.(track|nodes|arcs|route)'
        assert all(re.fullmatch(pattern,i.filename) for i in entries),'Unexpected archive layout'
        for item in entries:
            target=(base/item.filename).resolve()
            assert target.is_relative_to(base),'Unsafe ZIP path'
            data=z.read(item)
            if target.exists():assert target.read_bytes()==data,f'Existing dataset differs: {target.name}'
            else:
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    records=[]
    for path in sorted((base/'evaluator_test').iterdir()):
        trip=load_trip(path);route=load_indices(path/f'{path.name}.route',1).ravel()
        assert route.max()<len(trip.arcs),'Reference index out of range'
        records.append({'trip_id':path.name,'observations':len(trip.track),'arcs':len(trip.arcs),
                        'reference_arcs':len(route),'reference_available':True})
    assert len(records)==10,'Expected ten evaluator trips'
    report={'source_zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'trips':records,
            'model_retrained':False,'purpose':'Untuned inference and reference comparison only'}
    out=ROOT/'results'/'evaluator_inventory.json'
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
