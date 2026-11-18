"""Submission-only checks. Never fits or changes the selected pipeline."""
import sys,json,re,hashlib,subprocess,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathsnap.core import ROOT

TEXT={'.py','.js','.css','.html','.md','.json','.csv','.txt','.ini','.cmd'}
RUNTIME_PREFIXES=('pathsnap/','backend/','ui/')
RUNTIME_FILES={'artifacts/model.joblib','artifacts/manifest.json','artifacts/decoder.json','requirements.lock.txt','setup_backend.cmd','run_backend.cmd','run_ui.cmd'}
EXCLUDE_PREFIXES=('data/','cache/','materials/','packages/','tmp/','submission_evidence/','output/','results/probabilities/','results/maps/','results/screenshots/')
EXCLUDE_FILES={'results/sample_response.json','results/dataset_inventory.csv','results/training_split_manifest.json',
 'results/figures/geographic_comparison.png','results/test_results.txt','results/critical_audit/clean_environment_tests.txt',
 'results/critical_audit/training_holdout_model.joblib','results/submission/final_tests.txt'}
TOKEN_PATTERNS=[re.compile(p) for p in [r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{30,}',
 r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}',r'AKIA[A-Z0-9]{16}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']]

def git(*args,input=None):
    return subprocess.check_output(['git',*args],cwd=ROOT,input=input)

def candidates():
    names=git('ls-files','--cached','--others','--exclude-standard','-z').decode().split('\0')
    return sorted({n for n in names if n and (ROOT/n).is_file()})

def public_allowed(name):
    return not(name.startswith(EXCLUDE_PREFIXES) or name in EXCLUDE_FILES or Path(name).suffix in {'.npz','.npy','.pdf','.zip','.db','.log'} or '__pycache__' in Path(name).parts)

def canonical(name,data):
    return data.replace(b'\r\n',b'\n') if Path(name).suffix in TEXT or Path(name).name in {'.gitignore','.gitattributes'} else data

def digest(name,data):return hashlib.sha256(canonical(name,data)).hexdigest()

def runtime_members():
    tracked=git('ls-files','-z').decode().split('\0')
    return sorted(n for n in tracked if n and (n.startswith(RUNTIME_PREFIXES) or n in RUNTIME_FILES))

def scan_history():
    entries={}
    for line in git('rev-list','--objects','--all').decode().splitlines():
        parts=line.split(' ',1)
        if len(parts)==2 and Path(parts[1]).suffix in TEXT:entries[parts[0]]=parts[1]
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    findings=[]
    try:
        for oid,name in entries.items():
            proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
            header=proc.stdout.readline().decode().split();size=int(header[2]);data=proc.stdout.read(size);proc.stdout.read(1)
            if any(p.search(data.decode('utf-8',errors='replace')) for p in TOKEN_PATTERNS):findings.append({'path':name,'object':oid})
    finally:proc.stdin.close();proc.wait(timeout=20)
    return {'text_objects_scanned':len(entries),'credential_pattern_findings':findings,
       'scope':'Heuristic recognizable-token/private-key scan; not a guarantee against all secrets.'}

def main():
    out=ROOT/'results'/'submission';out.mkdir(parents=True,exist_ok=True)
    files=candidates();findings=[];sensitive=[]
    for name in files:
        p=ROOT/name
        if p.suffix in TEXT:
            if any(pattern.search(p.read_text(encoding='utf-8',errors='replace')) for pattern in TOKEN_PATTERNS):findings.append(name)
        if p.name in {'.env','.netrc','id_rsa','id_ed25519'} or p.suffix in {'.pem','.pfx','.key'}:sensitive.append(name)
    history=scan_history();assert not findings and not sensitive and not history['credential_pattern_findings'],'Credential review required; see private scan report'
    sizes=sorted([{'path':n,'bytes':(ROOT/n).stat().st_size} for n in files],key=lambda r:r['bytes'],reverse=True)
    assert sizes[0]['bytes']<50*1024*1024,'Unexpected oversized source file'
    freeze=[]
    for name in runtime_members():
        committed=git('show',f'16bd43d:{name}')
        assert digest(name,(ROOT/name).read_bytes())==digest(name,committed),f'Frozen implementation changed: {name}'
        freeze.append(name)
    # Import requirements rather than assuming undeclared global dependencies.
    import importlib.metadata as md
    required={'numpy','scipy','pandas','scikit-learn','joblib','fastapi','uvicorn','folium','optuna','reportlab','matplotlib','pillow','httpx','pytest'}
    locked={line.split('==')[0].lower() for line in (ROOT/'requirements.lock.txt').read_text().splitlines() if '==' in line}
    assert required<=locked
    package_check=[]
    for filename in ['PathSnap_Laptop1_Backend.zip','PathSnap_Laptop2_UI.zip']:
        path=ROOT/'packages'/filename
        if not path.exists():continue
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            compared=[]
            for name in z.namelist():
                if name in freeze:
                    assert digest(name,z.read(name))==digest(name,(ROOT/name).read_bytes()),f'ZIP implementation drift: {filename}: {name}'
                    compared.append(name)
            if filename.endswith('UI.zip'):assert not any(n.endswith(('.track','.arcs','.nodes','.route','.joblib')) for n in z.namelist())
        package_check.append({'archive':filename,'runtime_members_compared':compared,'matches_frozen_implementation':True})
    final=json.loads((ROOT/'results/critical_audit/final_accuracy.json').read_text())
    import pymupdf
    pdf=pymupdf.open(ROOT/'output/pdf/PathSnap_Technical_Report.pdf');text='\n'.join(p.get_text() for p in pdf)
    assert '95.2559%' in text and '94.1284%' in text
    assert 'not official' in text.lower() or 'not independent' in text.lower()
    for name in ['README.md','docs/VIVA_GUIDE.md']:
        s=(ROOT/name).read_text(encoding='utf-8');assert '95.25' in s and ('derived' in s.lower() or 'reference' in s.lower())
    log=(out/'final_tests.txt').read_text(encoding='utf-8')
    summary=re.search(r'(\d+) passed(?:, (\d+) warning)?',log)
    assert summary and int(summary.group(1))>=28 and 'failed' not in log.lower()
    (out/'final_tests_summary.json').write_text(json.dumps({'passed':int(summary.group(1)),'warnings':int(summary.group(2) or 0),
       'command':'tmp/clean_env/Scripts/python.exe -m pytest -q','source_log':'Private working project: results/submission/final_tests.txt',
       'physical_two_laptop_tested':False},indent=2),encoding='utf-8',newline='\n')
    result={'frozen_base_commit':'16bd43d39ee3a8474cd334aee5723f8bb464237f','frozen_runtime_members':freeze,
      'model_and_runtime_unchanged':True,'working_text_secret_findings':findings,'sensitive_filename_findings':sensitive,
      'history_scan':history,'largest_files':sizes[:12],'files_over_50_MiB':[],
      'required_direct_dependencies_locked':True,'deployment_checks':package_check,
      'report_final_numbers_present':True,'report_pages':len(pdf),
      'final_tests_passed':int(summary.group(1)),
      'publication_policy':'Curated snapshot excludes raw inputs, per-point arrays, location-bearing generated outputs and private development history.',
      'public_publication_verified':False,'physical_two_laptop_verified':False}
    result_path=Path(sys.argv[1]) if len(sys.argv)>1 else out/'submission_checks.json'
    result_path.parent.mkdir(parents=True,exist_ok=True)
    result_path.write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'runtime_unchanged':True,'secret_pattern_findings':0,'history_text_objects':history['text_objects_scanned'],
                     'largest_file_MiB':round(sizes[0]['bytes']/1048576,2),'report_pages':len(pdf)}),flush=True)

if __name__=='__main__':main()
