"""Packaging mutations only: no source import, PDQ execution, build or network."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('curated_inspector', PACKAGE / 'inspect_evidence.py')
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


class PublicEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'package'
        shutil.copytree(PACKAGE, self.root)
        self.original_root = inspector.ROOT
        inspector.ROOT = self.root

    def tearDown(self):
        inspector.ROOT = self.original_root
        self.temp.cleanup()

    def mutate_json(self, name, change):
        path = self.root / name
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))
        manifest_path = self.root / 'public-package-sha256.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['files'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))

    def test_valid_scope(self):
        result = inspector.inspect()
        self.assertEqual((result['trees'], result['sourceLeaves'], result['hashesExact'], result['qualityExact']), (6, 17, 32, 6))
        self.assertFalse(result['pdqExecuted'])
        self.assertIn('not recomputed', result['commitToRootBinding'])
        self.assertFalse((self.root / 'upstream-commit.txt').exists())

    def test_raw_file_injection(self):
        (self.root / 'upstream-commit.txt').write_text('synthetic injection, not the upstream object')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            inspector.inspect()

    def test_directory_injection(self):
        (self.root / 'extra').mkdir()
        with self.assertRaisesRegex(ValueError, 'entry type'):
            inspector.inspect()

    def test_file_tamper(self):
        with (self.root / 'bridge.cpp').open('a') as out:
            out.write('tamper')
        with self.assertRaisesRegex(ValueError, 'package hash'):
            inspector.inspect()

    def test_tree_tamper_with_refreshed_manifest(self):
        self.mutate_json('source-tree-proof.json', lambda v: v['trees'][0]['entries'][0].update(oid='0' * 40))
        with self.assertRaisesRegex(ValueError, 'tree object'):
            inspector.inspect()

    def test_leaf_tamper_with_refreshed_manifest(self):
        self.mutate_json('acquisition.json', lambda v: v['files'][0].update(gitBlobSha1='0' * 40))
        with self.assertRaisesRegex(ValueError, 'leaf membership'):
            inspector.inspect()

    def test_reported_identity_tamper_with_refreshed_manifest(self):
        self.mutate_json('original-provenance-verification.json', lambda v: v.update(rawCommitBytes=1134))
        with self.assertRaisesRegex(ValueError, 'reported private object identity'):
            inspector.inspect()

    def test_distance_tamper_with_refreshed_manifest(self):
        self.mutate_json('comparison.json', lambda v: v['cases'][0]['cppHammingByVariant'].update(orig=1))
        with self.assertRaisesRegex(ValueError, 'hash accounting'):
            inspector.inspect()

    def test_quality_tamper_with_refreshed_manifest(self):
        self.mutate_json('comparison.json', lambda v: v['cases'][0]['cpp'].update(quality=1))
        with self.assertRaisesRegex(ValueError, 'quality accounting'):
            inspector.inspect()

    def test_summary_tamper_with_refreshed_manifest(self):
        self.mutate_json('comparison.json', lambda v: v['summary'].update(cppHashesExact=48))
        with self.assertRaisesRegex(ValueError, 'summary accounting'):
            inspector.inspect()


if __name__ == '__main__':
    unittest.main()
