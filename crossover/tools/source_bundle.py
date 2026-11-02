#!/usr/bin/env python3
"""Collect the exact patched source and dependency notices beside the binary."""
import argparse
from pathlib import Path
import subprocess
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '__pycache__', '.vs', 'node_modules', 'CMakeFiles'}


def tracked(root):
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
    return sorted(root / name for name in names if name and (root / name).is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--feed', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    notices = ['Zelda Crossover UWP: source and third-party notices\n',
               'The accompanying source ZIP contains the patched sources used for this build.\n',
               'Build instructions and pins: project/crossover/README.md and sources.lock.json.\n']
    with zipfile.ZipFile(args.out / 'ZeldaCrossover-source.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        def add_tree(root, prefix, files):
            for path in files:
                relative = path.relative_to(root)
                if any(part in SKIP_DIRS for part in relative.parts):
                    continue
                archive.write(path, f'{prefix}/{relative.as_posix()}')
                if 'LICENSE' in path.name.upper() or path.name.upper().startswith(('COPYING', 'NOTICE', 'COPYRIGHT')):
                    try:
                        content = path.read_text(encoding='utf-8')
                    except UnicodeError:
                        continue
                    notices.extend([f'\n--- {prefix}/{relative.as_posix()} ---\n', content, '\n'])

        for name in ('windwaker', 'aurora', 'decomp', 'recompcore'):
            root = args.sources / name
            add_tree(root, f'upstream/{name}', tracked(root))
        for root in sorted((args.feed / '_deps').glob('*-src')):
            add_tree(root, f'dependencies/{root.name}', sorted(p for p in root.rglob('*') if p.is_file()))
        add_tree(PROJECT.parent, 'project', [p for p in tracked(PROJECT.parent)
                 if p.is_relative_to(PROJECT) or p == PROJECT.parent / '.github/workflows/build-crossover-uwp.yml'])
        archive.write(args.sources / 'source-provenance.json', 'source-provenance.json')
        depot = args.sources / 'uwp-dep'
        add_tree(depot, 'uwp-dep-notices', [p for p in tracked(depot)
                 if p.is_relative_to(depot / 'lic') or
                 p.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE', 'COPYRIGHT', 'README'))])
    (args.out / 'THIRD_PARTY_NOTICES.txt').write_text(''.join(notices), encoding='utf-8')
    print('Collected patched build source and license notices.')


if __name__ == '__main__':
    main()
