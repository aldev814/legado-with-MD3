#!/usr/bin/env python3
"""Record the exact patched source as a reproducible root commit (no upstream workflows)."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent


def git(source, *args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=source, text=True, **kwargs).strip()


def package(source, artifacts, plan_file):
    plan = json.loads(plan_file.read_text())
    if git(source, 'rev-parse', 'HEAD') != plan['upstream_commit']:
        raise ValueError('Unexpected upstream source')
    if (source / '.github/workflows').exists():
        raise ValueError('Patched source must not contain workflow files')
    timestamp = git(source, 'log', '-1', '--format=%cI')
    plan['automation_commit'] = git(ROOT.parents[1], 'rev-parse', 'HEAD')
    if os.environ.get('GITHUB_SHA') and os.environ['GITHUB_SHA'] != plan['automation_commit']:
        raise ValueError('Recipe checkout differs from workflow commit')
    git(source, 'add', '--all')
    tree = git(source, 'write-tree')
    identity = dict(GIT_AUTHOR_NAME='github-actions[bot]', GIT_COMMITTER_NAME='github-actions[bot]',
        GIT_AUTHOR_EMAIL='41898282+github-actions[bot]@users.noreply.github.com',
        GIT_COMMITTER_EMAIL='41898282+github-actions[bot]@users.noreply.github.com',
        GIT_AUTHOR_DATE=timestamp, GIT_COMMITTER_DATE=timestamp)
    message = f"Apply iReader {plan['release_tag']}\nUpstream: {plan['upstream_commit']}\nRecipe: {plan['automation_commit']}"
    commit = git(source, 'commit-tree', tree, '-m', message, env={**os.environ, **identity})
    git(source, 'reset', '--soft', commit)
    git(source, 'update-ref', 'refs/heads/ireader-release', commit)
    plan['source_commit'] = commit
    plan_file.write_text(json.dumps(plan, indent=2) + '\n')
    artifacts.mkdir(parents=True, exist_ok=True)
    git(source, '-c', 'pack.threads=1', 'bundle', 'create', str(artifacts / 'patched-source.bundle'), 'refs/heads/ireader-release')
    with zipfile.ZipFile(artifacts / 'ireader-patches.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(ROOT.rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc':
                archive.writestr(zipfile.ZipInfo('.github/ireader/' + file.relative_to(ROOT).as_posix(), (1980, 1, 1, 0, 0, 0)), file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    print('Recorded patched source:', commit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('artifacts', type=Path)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    package(args.source.resolve(), args.artifacts.resolve(), args.plan.resolve())
