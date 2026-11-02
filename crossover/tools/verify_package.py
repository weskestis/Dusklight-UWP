#!/usr/bin/env python3
"""Reject wrong-identity, desktop-only or incomplete UWP packages."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import pefile

FORBIDDEN = {"user32.dll", "gdi32.dll", "comdlg32.dll", "shell32.dll", "dbghelp.dll", "psapi.dll"}
NS = {"p": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}


def check_pe(path):
    pe = pefile.PE(str(path), fast_load=True)
    if pe.FILE_HEADER.Machine != 0x8664:
        raise ValueError(f"Not x64: {path.name}")
    if not pe.OPTIONAL_HEADER.DllCharacteristics & 0x1000:
        raise ValueError(f"Not AppContainer-compatible: {path.name}")
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
                                          pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
    imports = {entry.dll.decode('ascii').lower() for group in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT')
               for entry in getattr(pe, group, [])}
    if imports & FORBIDDEN:
        raise ValueError(f"Desktop DLL dependency in {path.name}: {sorted(imports & FORBIDDEN)}")
    return sorted(imports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    candidates = [p for p in args.build.rglob('*') if p.suffix in ('.msix', '.appx')
                  and 'Dependencies' not in p.parts and p.name.startswith('ZeldaCrossoverUWP')]
    if len(candidates) != 1:
        raise ValueError(f"Expected one game package, found {len(candidates)}")
    package = candidates[0]
    report = {}
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
        for required in ('ZeldaCrossoverUWP.exe', 'SDL3.dll', 'webgpu_dawn.dll', 'libuwp.dll', 'nod.dll'):
            if not (root / required).is_file():
                raise ValueError(f"Missing runtime file: {required}")
        for path in root.rglob('*'):
            if path.suffix.lower() in ('.exe', '.dll'):
                report[path.name] = check_pe(path)
    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(package, args.out / 'ZeldaCrossover_0.1.0.1_x64.msix')
    deps = [p for p in args.build.rglob('*.appx') if 'Dependencies' in p.parts
            and 'x64' in str(p).lower() and 'VCLibs' in p.name]
    if not deps:
        raise ValueError('The x64 VCLibs dependency is missing')
    for path in deps:
        shutil.copy2(path, args.out / path.name)
    (args.out / 'package-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('UWP identity, architecture, imports and dependency files verified.')


if __name__ == '__main__':
    main()
