#!/usr/bin/env python3
"""Repackage the retained executable only when its code inputs are unchanged."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'crossover/tools'))
from verify_package import RUNTIMES, NS

ORIGIN = 'c7025b94bdd2874bf2b7193b9282a83951185fa2'
RUN_ID = 41412462129
PHONE = 'http://schemas.microsoft.com/appx/2014/phone/manifest'


def version(value):
    return tuple(int(part) for part in value.split('.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    args = parser.parse_args()
    build = args.build.resolve()
    for name in ('main.cpp', 'CMakeLists.txt'):
        relative = f'crossover/platforms/uwp/{name}'
        original = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{ORIGIN}:{relative}']).decode()
        if original.replace('\r\n', '\n') != (ROOT / relative).read_text():
            raise RuntimeError(f'Executable input changed: {relative}; run a full build')
    old = json.loads(next((build / 'recovered').rglob('source-provenance.json')).read_text())
    provenance_path = build / 'sources/source-provenance.json'
    new = json.loads(provenance_path.read_text())
    for key in ('sources', 'windwaker_patch_sha256', 'aurora_patch_sha256'):
        if old[key] != new[key]:
            raise RuntimeError(f'Core input changed: {key}; run a full build')

    executables = list((build / 'recovered').rglob('ZeldaCrossoverUWP.exe'))
    digests = {hashlib.sha256(p.read_bytes()).hexdigest() for p in executables}
    if len(digests) != 1:
        raise RuntimeError('Retained executable is missing or ambiguous')
    executable = executables[0]
    manifest_path = executable.parent / 'AppxManifest.xml'
    manifest_bytes = manifest_path.read_bytes()
    for _, (prefix, uri) in ET.iterparse(io.BytesIO(manifest_bytes), events=['start-ns']):
        ET.register_namespace(prefix, uri)
    ET.register_namespace('mp', PHONE)
    manifest = ET.fromstring(manifest_bytes)
    if manifest.find(f'{{{PHONE}}}PhoneIdentity') is None:
        template = ET.parse(ROOT / 'crossover/platforms/uwp/Package.appxmanifest.in').getroot()
        phone = template.find(f'{{{PHONE}}}PhoneIdentity')
        if phone is None:
            raise RuntimeError('Source manifest has no PhoneIdentity')
        manifest.insert(1, phone)
    ignorable = manifest.get('IgnorableNamespaces', '').split()
    if 'mp' not in ignorable:
        manifest.set('IgnorableNamespaces', ' '.join(ignorable + ['mp']))

    payload = build / 'payload'
    payload.mkdir()
    shutil.copy2(executable, payload / executable.name)
    for name in RUNTIMES:
        shutil.copy2(build / 'runtime/x64/bin' / name, payload / name)
    shutil.copytree(ROOT / 'crossover/platforms/uwp/Assets', payload / 'Assets')
    ET.ElementTree(manifest).write(payload / 'AppxManifest.xml', encoding='utf-8', xml_declaration=True)

    dependencies = manifest.findall('p:Dependencies/p:PackageDependency', NS)
    if len(dependencies) != 1 or dependencies[0].get('Name') != 'Microsoft.VCLibs.140.00':
        raise RuntimeError(f'Unexpected dependency set: {[d.attrib for d in dependencies]}')
    required = dependencies[0]
    sdk = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft SDKs/Windows Kits/10/ExtensionSDKs'
    choices = []
    for path in sdk.rglob('Microsoft.VCLibs.x64.14.00.appx'):
        if 'retail' not in {part.lower() for part in path.parts}:
            continue
        with zipfile.ZipFile(path) as archive:
            doc = ET.fromstring(archive.read('AppxManifest.xml'))
        identity = next(e for e in doc if e.tag.rsplit('}', 1)[-1] == 'Identity')
        if (identity.get('Name') == required.get('Name') and
                identity.get('Publisher') == required.get('Publisher') and
                identity.get('ProcessorArchitecture') == 'x64' and
                version(identity.get('Version')) >= version(required.get('MinVersion'))):
            choices.append((version(identity.get('Version')), path))
    if not choices:
        raise RuntimeError('No installed retail x64 VCLibs package satisfies the manifest')
    destination = build / 'package/Dependencies/x64'
    destination.mkdir(parents=True)
    shutil.copy2(sorted(choices)[0][1], destination)
    new['binary_origin'] = {'workflow_run': RUN_ID, 'control_commit': ORIGIN,
                            'exe_sha256': next(iter(digests)), 'reused_executable': True}
    provenance_path.write_text(json.dumps(new, indent=2) + '\n')
    print('Retained executable and matching code inputs verified; package payload staged.')


if __name__ == '__main__':
    main()
