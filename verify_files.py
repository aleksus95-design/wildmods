"""Read-only SHA-256 verification for the repository folder or extracted FULL ZIP."""
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--paks-root',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parent;m=json.loads((root/'INSTALL_MANIFEST.json').read_text('utf-8-sig'))
if args.paks_root:base=args.paks_root.resolve();prefix=True
elif(root/'SCUM/Content/Paks').is_dir():base=(root/'SCUM/Content/Paks').resolve();prefix=True
else:base=root;prefix=False
expected=set()
for row in m['files']:
 rel=row['relative_path']if prefix else row['relative_path'].removeprefix('~mods/')
 f=(base/rel).resolve();assert f.is_relative_to(base),'Path leaves selected root'
 assert f.is_file()and f.stat().st_size==row['bytes'],row['name']
 with f.open('rb')as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256'],row['name']
 expected.add(f)
scan=base/'~mods'if prefix else base
actual={f.resolve()for f in scan.rglob('*.pak')}
if prefix:
 known={r['name'].casefold()for r in m['files']}|{'midway_client_full_b25804202_r19_225_p.pak'}
 actual|={f.resolve()for f in base.rglob('*.pak')if f.name.casefold()in known}
assert actual==expected,'Missing or additional PAKs: '+str(sorted(str(x)for x in actual^expected))
print('OK:',len(expected),'client PAKs; SHA-256 verified. This verifies files, not server compatibility or publication status.')
