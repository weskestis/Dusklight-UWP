#!/usr/bin/env python3
"""Stage pinned UWP dependencies with a source-built Windows Store SDL."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from verify_package import check_pe


def single(root, name):
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {name}, found {len(matches)}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--sdl-build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise RuntimeError("Use a fresh runtime staging directory")
    dll = single(args.sdl_build, 'SDL3.dll')
    implib = single(args.sdl_build, 'SDL3.lib')
    # This replacement must satisfy the same checks as our own application.
    check_pe(dll)
    shutil.copytree(args.sources / 'uwp-dep', args.out,
                    ignore=shutil.ignore_patterns('.git'))
    shutil.copy2(dll, args.out / 'x64/bin/SDL3.dll')
    shutil.copy2(implib, args.out / 'x64/lib/SDL3.lib')
    headers = args.out / 'x64/include/SDL3'
    shutil.rmtree(headers)
    shutil.copytree(args.sources / 'sdl/include/SDL3', headers)
    provenance_path = args.sources / 'source-provenance.json'
    provenance = json.loads(provenance_path.read_text())
    provenance['runtime_overrides'] = {
        'SDL3.dll': {'source': provenance['sources']['sdl'],
                     'sha256': hashlib.sha256(dll.read_bytes()).hexdigest(),
                     'app_container_and_imports_checked': True}
    }
    provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
    print("Staged Windows Store SDL with verified runtime imports.")


if __name__ == '__main__':
    main()
