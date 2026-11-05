import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load('release')
prepare = load('prepare_source')
packager = load('package_source')
signer = load('sign')
merger = load('merge_artifacts')


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.config = dict(upstream='up/reader', fork='me/reader', patch_revision=1,
                           application_id='app.reader', certificate_sha256='a' * 64)
        self.upstream = dict(tag_name='3.26.23', draft=False, prerelease=False,
                             published_at='2026-11-04T19:49:13Z', html_url='https://example.org/release')

    def result(self, existing=None, upstream=None, requested=''):
        def get(route):
            if '/git/ref/' in route:
                return {'object': {'type': 'commit', 'sha': 'b' * 40}}
            if route.startswith('repos/up/'):
                return upstream or self.upstream
            return existing
        return release.plan(self.config, requested, get)

    def test_new_release_uses_patch_version_and_immutable_commit(self):
        item = self.result()
        self.assertEqual(item['release_tag'], '3.26.23-ireader.1')
        self.assertEqual(item['version_code'], 326023001)
        self.assertEqual(item['commit_number'] + 10000, item['version_code'])
        self.assertEqual(item['upstream_commit'], 'b' * 40)

    def test_published_release_is_skipped_but_draft_can_resume(self):
        self.assertEqual(self.result({'draft': False})['needed'], 'false')
        self.assertEqual(self.result({'draft': True})['needed'], 'true')

    def test_revision_and_next_upstream_are_monotonic(self):
        tag, code = release.coordinates('3.26.23', 999)
        self.assertEqual(tag, '3.26.23-ireader.999')
        self.assertGreater(release.coordinates('3.26.24', 1)[1], code)
        self.assertLessEqual(release.coordinates('20.99.999', 999)[1], 2147483647)
        self.assertEqual(release.coordinates('v3.26.23', 1), release.coordinates('3.26.23', 1))

    def test_drafts_prereleases_and_unpublished_releases_are_rejected(self):
        for overrides in [{'draft': True}, {'prerelease': True}, {'published_at': None}]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.result(upstream={**self.upstream, **overrides})

    def test_unsafe_versions_and_revisions_are_rejected(self):
        for tag in ['../main', '3.26.23\nneeded=true', '3.26.23;true', '--help', '21.0.0', '3.100.0']:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.result(requested=tag)
        for revision in [0, -1, 1000, True, '1']:
            self.config['patch_revision'] = revision
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.result()

    def test_api_failure_does_not_look_like_absent_release(self):
        with self.assertRaises(PermissionError):
            release.plan(self.config, get=lambda _: (_ for _ in ()).throw(PermissionError('403')))

    def test_annotated_tags_resolve_to_commits(self):
        calls = []
        def get(route):
            calls.append(route)
            if '/git/ref/' in route:
                return {'object': {'type': 'tag', 'sha': 'c' * 40}}
            if '/git/tags/' in route:
                return {'object': {'type': 'commit', 'sha': 'b' * 40}}
            if route.startswith('repos/up/'):
                return self.upstream
            return None
        self.assertEqual(release.plan(self.config, '3.26.23', get)['upstream_commit'], 'b' * 40)
        self.assertIn('releases/tags/3.26.23', calls[0])


class SourceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.org')
        self.git('config', 'commit.gpgsign', 'false')
        (self.source / 'file.txt').write_text('before\n')
        wrapper = self.source / 'gradle/wrapper/gradle-wrapper.properties'
        wrapper.parent.mkdir(parents=True)
        wrapper.write_text('distributionUrl=https://services.gradle.org/distributions/gradle-9.8.0-bin.zip\n'
                           'distributionSha256Sum=fixture-hash\nnetworkTimeout=10000\nretries=0\n')
        (self.source / 'settings.gradle').write_text('mavenCentral()\nmaven { url "https://maven.aliyun.com/repository/public" }\n')
        workflows = self.source / '.github/workflows'
        workflows.mkdir(parents=True)
        (workflows / 'upstream.yml').write_text('name: upstream\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'upstream')
        self.plan = dict(upstream_commit=self.git('rev-parse', 'HEAD'), release_tag='3.26.23-ireader.1')
        self.recipe = self.root / 'recipe'
        patches = self.recipe / 'patches'
        patches.mkdir(parents=True)
        (patches / 'change.patch').write_text('diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-before\n+after\n')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.source, text=True, stderr=subprocess.DEVNULL).strip()

    def test_exact_clean_release_is_patched_and_workflows_are_removed(self):
        with patch.object(prepare, 'ROOT', self.recipe):
            prepare.prepare(self.source, self.plan)
        self.assertEqual((self.source / 'file.txt').read_text(), 'after\n')
        self.assertFalse((self.source / '.github/workflows').exists())
        self.assertNotIn('aliyun', (self.source / 'settings.gradle').read_text())
        wrapper = (self.source / 'gradle/wrapper/gradle-wrapper.properties').read_text()
        self.assertIn('distributionSha256Sum=fixture-hash', wrapper)
        self.assertIn('distributionUrl=https://services.gradle.org/distributions/gradle-9.8.0-bin.zip', wrapper)
        self.assertIn('networkTimeout=120000', wrapper)
        self.assertIn('retries=3', wrapper)

    def test_dirty_or_wrong_release_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare.prepare(self.source, {**self.plan, 'upstream_commit': '0' * 40})
        (self.source / 'file.txt').write_text('local changes\n')
        with self.assertRaises(ValueError):
            prepare.prepare(self.source, self.plan)

    def test_patch_conflict_stops_instead_of_skipping(self):
        (self.source / 'file.txt').write_text('upstream drift\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'drift')
        plan = {**self.plan, 'upstream_commit': self.git('rev-parse', 'HEAD')}
        with patch.object(prepare, 'ROOT', self.recipe), self.assertRaises(subprocess.CalledProcessError):
            prepare.prepare(self.source, plan)

    def test_matrix_products_produce_identical_source_bundle_and_recipe(self):
        second = self.root / 'second'
        subprocess.run(['git', 'clone', '--shared', '-q', str(self.source), str(second)], check=True)
        outputs = []
        for index, source in enumerate([self.source, second]):
            with patch.object(prepare, 'ROOT', self.recipe):
                prepare.prepare(source, self.plan)
            plan_file = self.root / f'plan-{index}.json'
            plan_file.write_text(json.dumps(self.plan))
            output = self.root / f'out-{index}'
            packager.package(source, output, plan_file)
            outputs.append(output)
        for name in ['patched-source.bundle', 'ireader-patches.zip']:
            self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes())

    def test_snapshot_has_one_commit_and_exact_tree_without_workflows(self):
        with patch.object(prepare, 'ROOT', self.recipe):
            prepare.prepare(self.source, self.plan)
        plan_file = self.root / 'plan.json'
        plan_file.write_text(json.dumps(self.plan))
        output = self.root / 'artifacts'
        packager.package(self.source, output, plan_file)
        result = json.loads(plan_file.read_text())
        self.assertNotEqual(result['source_commit'], self.plan['upstream_commit'])
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '1')
        self.assertEqual(self.git('ls-tree', '-r', '--name-only', 'HEAD', '--', '.github/workflows'), '')
        self.assertEqual(self.git('show', 'HEAD:file.txt'), 'after')
        self.assertTrue((output / 'patched-source.bundle').is_file())


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plan = dict(release_tag='3.26.23-ireader.1', upstream_tag='3.26.23',
                         upstream_url='https://example.org', application_id='app.reader',
                         version_code=326023001, patch_revision=1, source_commit='a' * 40,
                         certificate_sha256='b' * 64)
        for product in ['core', 'comic']:
            directory = self.root / ('ireader-build-' + product)
            directory.mkdir()
            (directory / f'metadata-{product}.json').write_text(json.dumps({**self.plan, 'product': product}))
            for abi in ['universal', 'arm64-v8a', 'armeabi-v7a']:
                (directory / f"legado-{self.plan['release_tag']}-{product}-{abi}.apk").write_bytes(product.encode())
            for name in ['patched-source.bundle', 'ireader-patches.zip', f'mapping-{product}.txt']:
                (directory / name).write_bytes(b'fixture')

    def test_both_products_are_required_and_have_separate_mappings(self):
        output = self.root / 'release'
        merger.merge(self.root, output)
        self.assertEqual(len(list(output.glob('*.apk'))), 6)
        self.assertTrue((output / 'mapping-core.txt').is_file())
        self.assertTrue((output / 'mapping-comic.txt').is_file())
        self.assertEqual(len((output / 'SHA256SUMS').read_text().splitlines()), 11)

    def test_mismatched_source_or_signing_cannot_publish(self):
        file = self.root / 'ireader-build-comic/metadata-comic.json'
        original = json.loads(file.read_text())
        for key in ['source_commit', 'version_code', 'certificate_sha256']:
            file.write_text(json.dumps({**original, key: 'different'}))
            with self.subTest(key=key), self.assertRaises(ValueError):
                merger.merge(self.root, self.root / 'release')
        file.write_text(json.dumps(original))

    def test_missing_apk_cannot_publish(self):
        next((self.root / 'ireader-build-comic').glob('*.apk')).unlink()
        with self.assertRaises(ValueError):
            merger.merge(self.root, self.root / 'release')

    def test_package_version_and_signature_are_verified(self):
        good = "package: name='app.reader' versionCode='326023001' versionName='3.26.23-ireader.1' platformBuildVersionName='17'"
        signer.validate_badging(good, self.plan)
        for bad in [good.replace('app.reader', 'other.app'), good.replace('326023001', '1'), good.replace('ireader.1', 'ireader.2')]:
            with self.assertRaises(ValueError):
                signer.validate_badging(bad, self.plan)
        self.assertEqual(signer.certificate('Signer #1 certificate SHA-256 digest: ' + 'A' * 64), 'a' * 64)
        with self.assertRaises(ValueError):
            signer.certificate('No certificate')


if __name__ == '__main__':
    unittest.main()
