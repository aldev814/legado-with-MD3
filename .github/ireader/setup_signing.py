#!/usr/bin/env python3
"""Create/reuse the fork's fixed key; never print private material."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess


def setup(directory, upload=False):
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    key = directory / 'ireader.p12'
    password_file = directory / 'IREADER_KEYSTORE_PASSWORD'
    if key.exists() != password_file.exists():
        raise ValueError('Incomplete signing backup; restore it, never replace the existing key')
    if not key.exists():
        password = secrets.token_urlsafe(48)
        env = {**os.environ, 'IREADER_KEYSTORE_PASSWORD': password}
        subprocess.run([
            'keytool', '-genkeypair', '-keystore', str(key), '-storetype', 'PKCS12',
            '-alias', 'ireader', '-keyalg', 'RSA', '-keysize', '3072', '-validity', '10000',
            '-dname', 'CN=Legado iReader, OU=aldev814',
            '-storepass:env', 'IREADER_KEYSTORE_PASSWORD', '-keypass:env', 'IREADER_KEYSTORE_PASSWORD',
        ], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        key.chmod(0o600)
        password_file.write_text(password)
        password_file.chmod(0o600)
    env = {**os.environ, 'IREADER_KEYSTORE_PASSWORD': password_file.read_text()}
    certificate = subprocess.check_output([
        'keytool', '-exportcert', '-alias', 'ireader', '-keystore', str(key),
        '-storepass:env', 'IREADER_KEYSTORE_PASSWORD',
    ], env=env, stderr=subprocess.PIPE)
    fingerprint = hashlib.sha256(certificate).hexdigest()
    encoded = directory / 'IREADER_KEYSTORE_BASE64'
    encoded.write_text(base64.b64encode(key.read_bytes()).decode())
    encoded.chmod(0o600)
    if upload:
        for name in ['IREADER_KEYSTORE_BASE64', 'IREADER_KEYSTORE_PASSWORD']:
            subprocess.run(['gh', 'secret', 'set', name, '--repo', 'aldev814/legado-with-MD3'],
                           input=(directory / name).read_text(), text=True, check=True)
    print(json.dumps({'directory': str(directory), 'certificate_sha256': fingerprint, 'uploaded': upload}))
    return fingerprint


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path.home() / '.config/legado-ireader-signing')
    parser.add_argument('--upload', action='store_true')
    args = parser.parse_args()
    setup(args.directory, args.upload)
