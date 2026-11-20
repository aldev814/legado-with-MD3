#!/usr/bin/env python3
"""Remember failed patch or build validation by upstream version."""
import base64
import json
import os

from release import FAILURE_BRANCH, api, failure_route


PATCH_STEPS = {
    'Apply patches (stop on any conflict)',
    'Prepare pinned upstream UI dependencies',
    'Record exact source and pinned submodule revisions',
    'Check reader menu integration first',
    'Run unit tests, lint, architecture check and Release/R8 build',
}


def record(fork, tag, commit, run_id, attempt, request=api):
    jobs = request(f'repos/{fork}/actions/runs/{run_id}/attempts/{attempt}/jobs')['jobs']
    failures = sorted({step['name'] for job in jobs if job['name'].startswith('Build and verify (')
                       for step in job['steps'] if step['conclusion'] == 'failure' and step['name'] in PATCH_STEPS})
    if not failures:
        print('No patch or build validation failure to record.')
        return
    route = failure_route(fork, tag)
    if request(f'{route}?ref={FAILURE_BRANCH}') is not None:
        print(f'Upstream {tag} is already blocked.')
        return
    marker = dict(upstream_tag=tag, upstream_commit=commit, failed_steps=failures,
                  run_url=f'https://github.com/{fork}/actions/runs/{run_id}/attempts/{attempt}')
    content = base64.b64encode((json.dumps(marker, indent=2) + '\n').encode()).decode()
    request(route, data=dict(branch=FAILURE_BRANCH, content=content, message=f'Block failed iReader build for {tag}'))
    print(f'Blocked upstream {tag} after a failed patch or build check.')


if __name__ == '__main__':
    record(os.environ['GITHUB_REPOSITORY'], os.environ['UPSTREAM_TAG'], os.environ['UPSTREAM_COMMIT'],
           os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_RUN_ATTEMPT'])
