"""Read-only verification of downloaded or installed MIDWAY client PAK files."""
from pathlib import Path
from collections import Counter
import sys, json, hashlib, re

def verify(root, manifest, installed=False):
    expected = {}
    issues = []
    for row in manifest['files']:
        rel = row['relative_path'] if installed else row['relative_path'].removeprefix('~mods/')
        if '..' in Path(rel).parts or Path(rel).is_absolute():
            raise ValueError('Invalid manifest path')
        key = rel.replace('\\', '/').casefold()
        if key in expected: raise ValueError('Duplicate manifest path')
        expected[key] = row
    actual = {}
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in ('.pak', '.sig'): continue
        if '.git' in p.relative_to(root).parts: continue
        if installed and p.parent == root and re.fullmatch(r'pakchunk\d+(?:_s\d+)?(?:optional)?-WindowsNoEditor\.(pak|sig)', p.name, re.I): continue
        key = p.relative_to(root).as_posix().casefold()
        if key in actual: issues.append('DUPLICATE_PATH: ' + key)
        actual[key] = p
    names = Counter(p.name.casefold() for p in actual.values() if p.suffix.lower() == '.pak')
    issues.extend('DUPLICATE_PAK: ' + n for n, count in names.items() if count > 1)
    issues.extend('MISSING: ' + k for k in sorted(expected.keys() - actual.keys()))
    issues.extend('UNEXPECTED: ' + k for k in sorted(actual.keys() - expected.keys()))
    for key in sorted(expected.keys() & actual.keys()):
        p, row = actual[key], expected[key]
        h = hashlib.sha256()
        with p.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1048576), b''): h.update(chunk)
        digest = h.hexdigest()
        if p.stat().st_size != row['bytes'] or digest != row['sha256']: issues.append('CHANGED: ' + key)
    return issues

if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else base
    if not root.is_dir(): raise SystemExit('Folder not found: ' + str(root))
    manifest = json.loads((base / 'INSTALL_MANIFEST.json').read_text(encoding='utf-8-sig'))
    issues = verify(root, manifest, installed=len(sys.argv) > 1)
    print('\n'.join(issues) if issues else 'OK: all 31 MIDWAY PAK files match; no unexpected PAK files.')
    raise SystemExit(bool(issues))
