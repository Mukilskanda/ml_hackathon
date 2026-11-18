"""Write a factual final audit and reproducibility manifests."""
import sys,json,hashlib,platform,os,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from sklearn.model_selection import GroupKFold
from pathsnap.core import ROOT,DATA

def main():
    manifest=json.loads((ROOT/'artifacts'/'manifest.json').read_text());strategy=manifest.get('candidate_strategy','nearest')
    inventory=pd.read_csv(ROOT/'results'/'dataset_inventory.csv')
    assert inventory.groupby('partition').size().to_dict()=={'student_test':10,'train':80}
    assert len(list(DATA.glob('*/*/*.track')))==90
    integrity=[]
    for path in sorted(DATA.glob('*/*/*')):
        if path.is_file():integrity.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (ROOT/'results'/'dataset_integrity.json').write_text(json.dumps(integrity,indent=2))
    sample=[];group=[]
    prefix='corrected_' if manifest.get('candidate_profile')=='current_v2' else 'adaptive_' if strategy=='adaptive' else ''
    for i,path in enumerate(sorted((ROOT/'cache').glob(prefix+'train_*.npz'))):
        with np.load(path) as c:n=len(c['labels'])
        ix=np.sort(np.random.default_rng(42+i).choice(n,min(450,n),replace=False))
        sample.append({'trip_id':path.stem[-8:],'observation_ids':ix.tolist()});group.extend([i]*len(ix))
    groups=np.array(group);folds=[]
    for train,val in GroupKFold(3).split(groups,groups=groups):
        assert not set(groups[train])&set(groups[val])
        folds.append({'fit_trip_ids':[sample[i]['trip_id'] for i in sorted(set(groups[train]))],
                      'validation_trip_ids':[sample[i]['trip_id'] for i in sorted(set(groups[val]))]})
    (ROOT/'results'/'training_split_manifest.json').write_text(json.dumps({'seed':42,'strategy':strategy,'samples':sample,'folds':folds},indent=2))
    api=json.loads((ROOT/'results'/'api_verification.json').read_text());browser=json.loads((ROOT/'results'/'browser_qa.json').read_text())
    assert len(api)==10 and all(r['status']==200 for r in api)
    assert not browser['javascript_errors'] and browser['physical_two_laptops_tested'] is False
    test=(ROOT/'results'/'test_results.txt').read_text();assert re.search(r'\d+ passed',test) and 'failed' not in test
    sources=list((ROOT/'pathsnap').glob('*.py'))+list((ROOT/'backend').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))
    absolute=[];secrets=[]
    for p in sources:
        text=p.read_text(encoding='utf-8')
        user_prefixes=['/'+x+'/' for x in ('Users','home')]
        if re.search(r'[A-Za-z]:\\\\',text) or any(x in text for x in user_prefixes):absolute.append(p.relative_to(ROOT).as_posix())
        if re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}',text):secrets.append(p.relative_to(ROOT).as_posix())
    assert not absolute,absolute
    assert not secrets,secrets
    artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'artifacts').iterdir()) if p.is_file()}
    (ROOT/'results'/'artifact_checksums.json').write_text(json.dumps(artifacts,indent=2))
    hardware={'python':platform.python_version(),'os':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count()}
    (ROOT/'results'/'runtime_environment.json').write_text(json.dumps(hardware,indent=2))
    routes=pd.read_csv(ROOT/'results'/'route_comparison.csv');means=routes.groupby('method').point_accuracy.mean()
    text=f'''# Final audit - local implementation verified

This is a factual completion boundary, not a claim that the official event submission has occurred.

## Verified

- All five supplied guideline PDFs reviewed; requirement mapping in `REQUIREMENTS_CHECKLIST.md`.
- 80 training trips, 10 student-test trips, {len(integrity)} raw files and {int(inventory.observations.sum()):,} GPS observations audited.
- Seven baseline algorithms, 16 Bayesian TPE trials, tuned/untuned comparison and saved models.
- Trip-grouped cross-validation, training-fold-only scaling and reference-free inference guarded by tests.
- Four feature-set ablations, four candidate-count coverage settings, nested group-aware sigmoid calibration, directional candidate inference and training-matched experiments.
- 36 fixed/adaptive decoder configurations for the final selected candidate/model pipeline. The earlier nearest-candidate pipeline was also searched.
- Eighteen seeded noise/dropout cases on three identified development trips.
- Final selected model: `{manifest['model']}`; candidate strategy: `{strategy}`.
- Candidate classifier student-test Top-1, observation-weighted: {100*manifest['final_metrics']['test_top1_accuracy']:.2f}%.
- Classifier-only equal-trip mean: {100*means['classifier_only']:.2f}%; fixed HMM: {100*means['fixed_hmm']:.2f}%; adaptive HMM: {100*means['adaptive_hmm']:.2f}%.
- Actual API requests succeeded for all 10 supplied student-test trips.
- {re.search(r'(\d+) passed',test).group(1)} automated tests passed, including geometry, exhaustive Viterbi, malformed data, scoring isolation and APIs.
- Separate-origin browser QA passed with no JavaScript errors, including mobile layout, experiment dashboard and recovery from an invalid server URL.
- Actual Folium HTML, graphs, screenshots and local API/server evidence retained.
- Selected artifacts reloaded in fresh Python processes and verified through the live server.
- No project source contains user-specific absolute filesystem paths or recognized credential token patterns (a heuristic scan, not a security certification).
- Reproducibility records include raw-file hashes, exact sampled observation IDs, trip folds, artifact checksums, pinned package versions and runtime environment.

## Limitations and unresolved requirements

1. **Official scoring convention unresolved.** `.route` is a segment sequence, not point labels. Development targets use documented monotone geometric alignment, with label circularity and anomalous references disclosed. Confirm the organizer's scorer before calling the API score official.
2. **No reserved evaluator results.** Those ten trips were not supplied. The loader supports a separate evaluator partition; its real data and complete pipeline have not been tested here.
3. **Physical two-laptop verification remains pending.** UI/API separate origins were tested locally. Network reachability, receiving-console screenshots and final rehearsal on two machines require the team.
4. **Public GitHub publication remains pending.** The local repository is prepared; no authenticated remote repository has been created or verified public.
5. **Team review remains pending.** Names/USNs are placeholders by request; actual ownership, interpretation, AI disclosure and viva readiness require the four members' review.

## Experimental interpretation

The adaptive candidate model slightly improved the predeclared combined CV objective, while lowering some individual classification metrics. The final decoder improved route point agreement on the permitted development set. Adaptive decoding improves only modestly over the strongest fixed HMM, and individual trips can regress. Sigmoid calibration was retained as a diagnostic and not adopted. Severe added GPS noise materially degrades results; these failures are included. No claim of research priority, guaranteed evaluator accuracy, or universal robustness is made.

## Deliverables and handoff

- Source, artifacts and evidence: this local repository.
- Consolidated report: `output/pdf/PathSnap_Technical_Report.pdf`.
- Laptop 2 transfer: `packages/PathSnap_Laptop2_UI.zip` only.
- Full local backup including supplied data: `packages/PathSnap_Complete_Local.zip`; do not publish this ZIP or raw data by default.
- Follow `DEPLOYMENT.md`, `SUBMISSION.md`, and `VIVA_GUIDE.md` before final evaluation.
'''
    (ROOT/'docs'/'FINAL_AUDIT.md').write_text(text,encoding='utf-8')
    print('Final local audit passed; external requirements are explicitly pending.',flush=True)

if __name__=='__main__':main()
