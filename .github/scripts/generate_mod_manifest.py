"""Publish a complete immutable mod snapshot using Git metadata, without hydrating PAKs."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SUFFIXES = ('.pak', '.sig', '.ucas', '.utoc')


def make_manifest(owner, repo, branch, commit, items, read_pointer):
    assert re.fullmatch(r'[0-9a-f]{40}', commit)
    files = []
    for item in sorted(items, key=lambda item: item['path']):
        if not item['path'].lower().endswith(SUFFIXES):
            continue
        entry = {key: item[key] for key in ('path', 'size', 'sha')}
        entry['name'] = entry['path'].split('/')[-1]
        assert entry['size'] > 0 and re.fullmatch(r'[0-9a-f]{40}', entry['sha'])
        if entry['size'] <= 1024:
            pointer = read_pointer(entry)
            if pointer.startswith(b'version https://git-lfs.github.com/spec/v1'):
                oid = re.search(rb'^oid sha256:([0-9a-f]{64})$', pointer, re.M)
                size = re.search(rb'^size ([0-9]+)$', pointer, re.M)
                assert oid and size, 'Incomplete Git LFS pointer'
                entry.update(lfs_oid=oid[1].decode(), lfs_size=int(size[1]))
        files.append(entry)
    serialized = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'schema': 1, 'complete': True, 'owner': owner, 'repo': repo, 'branch': branch,
            'commit': commit, 'file_count': len(files),
            'files_sha256': hashlib.sha256(serialized).hexdigest(), 'items': files}


def generate_from_git():
    def git(*args):
        return subprocess.check_output(['git', *args])
    commit = git('rev-parse', 'HEAD').decode().strip()
    items = []
    for record in git('ls-tree', '-r', '-l', '-z', commit).split(b'\0'):
        if not record:
            continue
        metadata, path = record.split(b'\t', 1)
        mode, kind, sha, size = metadata.split()
        if kind == b'blob' and mode in (b'100644', b'100755'):
            items.append({'path': path.decode('utf-8'), 'sha': sha.decode(), 'size': int(size)})
    owner, repo = os.environ.get('GITHUB_REPOSITORY', 'aleksus95-design/wildmods').split('/')
    manifest = make_manifest(owner, repo, 'main', commit, items, lambda item: git('cat-file', 'blob', item['sha']))
    Path('launcher_mod_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Complete launcher manifest:', manifest['file_count'], 'files at', commit)


if __name__ == '__main__':
    generate_from_git()
