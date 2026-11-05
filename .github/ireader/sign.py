#!/usr/bin/env python3
"""Sign and verify one product's three release APKs, including identity and version."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def certificate(verification):
    values = set(re.findall(r'^(?:Signer #\d+|V[\d.]+ Signer):? certificate SHA-256 digest: ([0-9a-fA-F]{64})$', verification, re.MULTILINE))
    if len(values) != 1:
        raise ValueError('Expected one signing certificate')
    return values.pop().lower()


def validate_badging(badging, plan):
    package = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    if not package or package.groups() != (plan['application_id'], str(plan['version_code']), plan['release_tag']):
        raise ValueError('APK package/version differs from release plan')


def sign(source, output, plan_file, product):
    plan = json.loads(plan_file.read_text())
    sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
    tools = [p for p in (sdk / 'build-tools').iterdir() if (p / 'apksigner').exists() and re.fullmatch(r'\d+(\.\d+)+', p.name)]
    tool = max(tools, key=lambda p: tuple(map(int, p.name.split('.'))))
    variant = 'app' + product.capitalize()
    apks = sorted((source / f'app/build/outputs/apk/{variant}/release').glob('*.apk'))
    expected = {'universal', 'arm64-v8a', 'armeabi-v7a'}
    found = set()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        key = Path(temporary) / 'release.p12'
        key.write_bytes(base64.b64decode(os.environ['IREADER_KEYSTORE_BASE64'], validate=True))
        key.chmod(0o600)
        for apk in apks:
            abi = next((name for name in expected if name in apk.name), None)
            if abi is None or abi in found:
                raise ValueError('Unexpected or duplicate APK: ' + apk.name)
            found.add(abi)
            validate_badging(subprocess.check_output([str(tool / 'aapt'), 'dump', 'badging', str(apk)], text=True), plan)
            aligned = Path(temporary) / apk.name
            destination = output / f"legado-{plan['release_tag']}-{product}-{abi}.apk"
            subprocess.run([str(tool / 'zipalign'), '-P', '16', '-f', '4', str(apk), str(aligned)], check=True)
            subprocess.run([str(tool / 'apksigner'), 'sign', '--ks', str(key), '--ks-key-alias', 'ireader',
                '--ks-pass', 'env:IREADER_KEYSTORE_PASSWORD', '--key-pass', 'env:IREADER_KEYSTORE_PASSWORD',
                '--out', str(destination), str(aligned)], check=True)
            verification = subprocess.check_output([str(tool / 'apksigner'), 'verify', '--verbose', '--print-certs', str(destination)], text=True)
            if certificate(verification) != plan['certificate_sha256']:
                raise ValueError('Signing certificate differs from configured update identity')
            subprocess.run([str(tool / 'zipalign'), '-c', '-P', '16', '4', str(destination)], check=True)
    if found != expected:
        raise ValueError('Expected universal, arm64-v8a and armeabi-v7a APKs')
    mapping = source / f'app/build/outputs/mapping/{variant}Release/mapping.txt'
    if not mapping.is_file():
        raise ValueError('Missing R8 mapping for ' + product)
    shutil.copyfile(mapping, output / f'mapping-{product}.txt')
    (output / f'metadata-{product}.json').write_text(json.dumps({**plan, 'product': product}, indent=2) + '\n')
    print('Signed and verified:', product)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('plan', type=Path)
    parser.add_argument('product', choices=['core', 'comic'])
    args = parser.parse_args()
    sign(args.source.resolve(), args.output.resolve(), args.plan.resolve(), args.product)
