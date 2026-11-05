#!/usr/bin/env python3
"""Apply reviewed patches to an exact, clean release checkout; never skip conflicts."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def prepare(source, plan):
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=source, text=True).strip():
        raise ValueError('Source checkout must be clean')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if head != plan['upstream_commit']:
        raise ValueError('Source differs from the detected immutable upstream release')
    patches = sorted((ROOT / 'patches').glob('*.patch'))
    if not patches:
        raise ValueError('No patches found')
    for patch in patches:
        subprocess.run(['git', 'apply', '--3way', '--index', str(patch)], cwd=source, check=True)
    # Keep the release source and its history free of upstream workflow files.
    workflows = source / '.github/workflows'
    if workflows.exists():
        shutil.rmtree(workflows)
    # Match upstream CI: the domestic mirrors are unreliable on GitHub runners.
    settings = source / 'settings.gradle'
    settings.write_text(''.join(line for line in settings.read_text().splitlines(keepends=True) if 'maven.aliyun.com' not in line))
    subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=source, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    prepare(args.source.resolve(), json.loads(args.plan.read_text()))
