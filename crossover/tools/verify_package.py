#!/usr/bin/env python3
"""Reject wrong-identity, desktop-only or incomplete UWP packages."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import pefile

FORBIDDEN = {"user32.dll", "gdi32.dll", "comdlg32.dll", "shell32.dll", "dbghelp.dll", "psapi.dll"}
NS = {"p": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
RUNTIMES = {'SDL3.dll', 'webgpu_dawn.dll', 'nod.dll', 'libuwp.dll',
            'libpng16.dll', 'z.dll', 'dxcompiler.dll', 'dxil.dll'}


def check_pe(path, *, strict=True):
    pe = pefile.PE(str(path), fast_load=True)
    if pe.FILE_HEADER.Machine != 0x8664:
        raise ValueError(f"Not x64: {path.name}")
    app_container = bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x1000)
    warnings = []
    if not app_container:
        warnings.append('AppContainer flag is absent')
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
                                          pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
    imports = {entry.dll.decode('ascii').lower() for group in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT')
               for entry in getattr(pe, group, [])}
    if imports & FORBIDDEN:
        warnings.append(f'Desktop DLL imports: {sorted(imports & FORBIDDEN)}')
    desktop_crt = imports & {'msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'vccorlib140.dll'}
    if desktop_crt:
        warnings.append(f'Desktop C++ runtime imports: {sorted(desktop_crt)}')
    if strict and warnings:
        raise ValueError(f"UWP application check failed for {path.name}: {'; '.join(warnings)}")
    pe.close()
    return {'app_container': app_container, 'imports': sorted(imports), 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True,
                        help='Pinned uwp-dep x64/bin directory, verified during source preparation')
    args = parser.parse_args()
    candidates = [p for p in args.build.rglob('*') if p.suffix in ('.msix', '.appx')
                  and 'Dependencies' not in p.parts and p.name.startswith('ZeldaCrossoverUWP')]
    if len(candidates) != 1:
        raise ValueError(f"Expected one game package, found {len(candidates)}")
    package = candidates[0]
    report = {'xbox_runtime_tested': False, 'binaries': {}, 'runtime_warnings': []}
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        with zipfile.ZipFile(package) as archive:
            for member in archive.namelist():
                if not (root / member).resolve().is_relative_to(root.resolve()):
                    raise ValueError('Unsafe package member')
                if Path(member).suffix.lower() in ('.iso', '.gcm', '.rvz', '.dol', '.rel'):
                    raise ValueError(f"Game data packaged: {member}")
            archive.extractall(root)
        manifest = ET.parse(root / 'AppxManifest.xml').getroot()
        identity = manifest.find('p:Identity', NS)
        if identity is None or identity.get('Name') != 'ZeldaCrossoverUWP' or identity.get('Publisher') != 'CN=ZeldaCrossoverUWP':
            raise ValueError('Incorrect isolated package identity')
        app = manifest.find('p:Applications/p:Application', NS)
        if app is None or app.get('EntryPoint') != 'uwp.App':
            raise ValueError('Incorrect UWP entry point')
        for required in {'ZeldaCrossoverUWP.exe'} | RUNTIMES:
            if not (root / required).is_file():
                raise ValueError(f"Missing runtime file: {required}")
        for path in root.rglob('*'):
            if path.suffix.lower() in ('.exe', '.dll'):
                # The inherited depot contains non-Store imports. Preserve its exact
                # bytes and record those limitations; do not certify it as Store-safe.
                inherited = path.name in RUNTIMES and path.parent == root
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if inherited:
                    original = args.runtime / path.name
                    if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != digest:
                        raise ValueError(f'Runtime differs from the pinned depot: {path.name}')
                result = check_pe(path, strict=not inherited)
                result.update(sha256=digest, pinned_runtime=inherited)
                report['binaries'][path.relative_to(root).as_posix()] = result
                report['runtime_warnings'].extend(f'{path.name}: {w}' for w in result['warnings'])
    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(package, args.out / 'ZeldaCrossover_0.1.0.1_x64.msix')
    deps = [p for p in args.build.rglob('*.appx') if 'Dependencies' in p.parts
            and 'x64' in str(p).lower() and 'VCLibs' in p.name]
    if not deps:
        raise ValueError('The x64 VCLibs dependency is missing')
    for path in deps:
        shutil.copy2(path, args.out / path.name)
    (args.out / 'package-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Package identity, architecture, application imports and pinned runtime hashes verified.')
    for warning in report['runtime_warnings']:
        print(f'Runtime limitation requiring Xbox testing: {warning}')


if __name__ == '__main__':
    main()
