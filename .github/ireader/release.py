#!/usr/bin/env python3
"""Resolve a published upstream release to immutable source and version coordinates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
TAG = re.compile(r'v?(\d+)\.(\d+)\.(\d+)\Z')


def api(route):
    request = Request('https://api.github.com/' + route, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
        'X-GitHub-Api-Version': '2026-03-10',
    })
    try:
        with urlopen(request, timeout=45) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def coordinates(tag, revision):
    match = TAG.fullmatch(tag)
    if not match or type(revision) is not int or not 1 <= revision <= 999:
        raise ValueError('Expected a numeric upstream version and patch_revision in 1..999')
    major, minor, patch = map(int, match.groups())
    if not (0 <= major <= 20 and 0 <= minor <= 99 and 0 <= patch <= 999):
        raise ValueError('Upstream version exceeds the Android versionCode allocation')
    version_code = major * 100_000_000 + minor * 1_000_000 + patch * 1_000 + revision
    return f'{major}.{minor}.{patch}-ireader.{revision}', version_code


def plan(config, requested='', get=api):
    coordinates(requested or '0.0.0', config['patch_revision'])
    endpoint = 'tags/' + quote(requested, safe='') if requested else 'latest'
    release = get(f"repos/{config['upstream']}/releases/{endpoint}")
    if not release or release.get('draft') or release.get('prerelease') or not release.get('published_at'):
        raise ValueError('Only published stable upstream Releases are accepted')
    tag = release['tag_name']
    release_tag, version_code = coordinates(tag, config['patch_revision'])
    reference = get(f"repos/{config['upstream']}/git/ref/tags/{quote(tag, safe='')}")
    if not reference:
        raise ValueError('Release tag is missing')
    obj = reference['object']
    for _ in range(8):
        if obj['type'] == 'commit':
            break
        if obj['type'] != 'tag':
            raise ValueError('Release tag does not resolve to a commit')
        obj = get(f"repos/{config['upstream']}/git/tags/{obj['sha']}")['object']
    if obj['type'] != 'commit' or not re.fullmatch(r'[a-f0-9]{40}', obj['sha']):
        raise ValueError('Invalid upstream commit')
    existing = get(f"repos/{config['fork']}/releases/tags/{release_tag}")
    return dict(
        needed='false' if existing and not existing.get('draft') else 'true',
        upstream_tag=tag, upstream_commit=obj['sha'], upstream_url=release['html_url'],
        release_tag=release_tag, version_code=version_code, commit_number=version_code - 10000,
        patch_revision=config['patch_revision'], application_id=config['application_id'],
        certificate_sha256=config['certificate_sha256'],
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', default='')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = plan(json.loads((ROOT / 'config.json').read_text()), args.tag)
    result['patch_sha256'] = hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT / 'patches').glob('*.patch')))).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            for key, value in result.items():
                if '\n' in str(value) or '\r' in str(value):
                    raise ValueError('Unsafe workflow output')
                out.write(f'{key}={value}\n')
    print(json.dumps(result, indent=2))
