"""Build a curated publication snapshot; never publishes to a remote service."""
import sys,json,zipfile,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathsnap.core import ROOT
from scripts.submission_checks import candidates,public_allowed,digest,runtime_members,git

def main():
    source=git('rev-parse','HEAD').decode().strip()
    target=(ROOT/'packages'/'PathSnap_Publication_Source').resolve();target.mkdir(parents=True,exist_ok=True)
    assert target.is_relative_to((ROOT/'packages').resolve())
    selected=[n for n in candidates() if public_allowed(n)]
    manifest=[]
    for name in selected:
        path=(target/name).resolve();assert path.is_relative_to(target)
        path.parent.mkdir(parents=True,exist_ok=True);data=(ROOT/name).read_bytes();path.write_bytes(data)
        manifest.append({'path':name,'sha256':hashlib.sha256(data).hexdigest()})
    # These generated provenance files are external to the private workspace commit.
    (target/'SOURCE_COMMIT.txt').write_text(source+'\n',encoding='utf-8',newline='\n')
    info={'source_workspace_commit':source,'source_file_count':len(selected),'files':manifest,
          'private_history_included':False,'raw_dataset_included':False,'publication_verified':False,
          'generated_deliverables_included':[n for n in selected if n.startswith(('output/','results/figures/','results/maps/','results/screenshots/'))],
          'separate_pdf_submission':'The technical report is included at output/pdf/PathSnap_Technical_Report.pdf and must also be submitted as the separate PDF deliverable.'}
    (target/'PUBLICATION_MANIFEST.json').write_text(json.dumps(info,indent=2),encoding='utf-8',newline='\n')
    archive=ROOT/'packages'/'PathSnap_Publication_Source.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in selected+['SOURCE_COMMIT.txt','PUBLICATION_MANIFEST.json']:z.write(target/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert 'output/pdf/PathSnap_Technical_Report.pdf' in z.namelist()
        assert not any(n.startswith(('data/','cache/','.git/')) or n.endswith(('.route','.track','.nodes','.arcs','.npz','.npy')) for n in z.namelist())
    report={'source_workspace_commit':source,'archive':archive.name,'file_count':len(selected),
      'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,
      'runtime_matches_workspace':all(digest(n,(target/n).read_bytes())==digest(n,(ROOT/n).read_bytes()) for n in runtime_members()),
      'raw_data_and_private_history_excluded':True,'public_publication_verified':False}
    (ROOT/'packages'/'publication_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
