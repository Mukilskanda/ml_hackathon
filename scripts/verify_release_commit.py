"""Verify generated archives/publication files against the actual final commit."""
import sys,json,hashlib,zipfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathsnap.core import ROOT
from scripts.submission_checks import git,digest,runtime_members

def main():
    commit=git('rev-parse','HEAD').decode().strip()
    assert not git('status','--porcelain').decode().strip(),'Commit final source before producing release provenance'
    records=[];checksums=json.loads((ROOT/'packages/checksums.json').read_text())
    tracked=set(git('ls-tree','-r','--name-only',commit).decode().splitlines())
    aliases={'LAPTOP1_README.md':'docs/LAPTOP1_SETUP.md'}
    generated={'SOURCE_COMMIT.txt','PROVENANCE.json','LAPTOP2_README.md'}
    for name in ['PathSnap_Laptop1_Backend.zip','PathSnap_Laptop2_UI.zip','PathSnap_Complete_Local.zip']:
        path=ROOT/'packages'/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==checksums[name]['sha256']
        count=0
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert z.read('SOURCE_COMMIT.txt').decode().strip()==commit
            assert json.loads(z.read('PROVENANCE.json'))['source_commit']==commit
            for member in z.namelist():
                if member in generated or member.startswith('data/'):continue
                original=aliases.get(member,member)
                if original in tracked:blob=git('show',f'{commit}:{original}')
                else:
                    # Full private backup may contain ignored local experiment
                    # assets; compare those to current private source directly.
                    assert name=='PathSnap_Complete_Local.zip' and (ROOT/original).is_file()
                    blob=(ROOT/original).read_bytes()
                assert digest(original,z.read(member))==digest(original,blob),(name,member)
                count+=1
        records.append({'archive':name,'source_commit':commit,'source_members_compared':count,'matches_commit':True})
    target=ROOT/'packages'/'PathSnap_Publication_Source'
    source=(target/'SOURCE_COMMIT.txt').read_text().strip();assert source==commit
    manifest=json.loads((target/'PUBLICATION_MANIFEST.json').read_text())
    for item in manifest['files']:
        name=item['path'];data=(target/name).read_bytes()
        assert digest(name,data)==digest(name,git('show',f'{commit}:{name}'))
    result={'source_commit':commit,'working_tree_clean':True,'deployment_and_backup_archives':records,
      'publication_snapshot_source_members_match_commit':True,'publication_member_count':len(manifest['files']),
      'public_publication_verified':False,'physical_two_laptop_execution_verified':False}
    (ROOT/'packages'/'commit_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
