from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--paks-root',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parent;m=json.loads((root/'INSTALL_MANIFEST.json').read_text(encoding='utf-8-sig'))
expected=set()
for r in m['files']:
    rel=Path(r['relative_path']) if a.paks_root else Path(r['relative_path'].removeprefix('~mods/'))
    base=(a.paks_root or root).resolve();f=(base/rel).resolve();assert f.is_relative_to(base)
    assert f.is_file() and f.stat().st_size==r['bytes'],r['name']
    with f.open('rb')as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==r['sha256'],r['name']
    expected.add(f)
scan=(a.paks_root/'~mods') if a.paks_root else root
assert {f.resolve()for f in scan.rglob('*.pak')}==expected,'Extra PAKs present'
print('OK:',len(expected),'client PAKs; SHA-256 verified')
