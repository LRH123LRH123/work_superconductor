"""Prove the standalone package validator catches concrete corrupted artifacts."""
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
try:
    from validate_mgb2_data_package import validate_package
except ModuleNotFoundError as exc:
    if exc.name != 'validate_mgb2_data_package':
        raise
    validate_package = None


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(validate_package, 'package validator not implemented')
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)/'package'
        shutil.copytree(Path(__file__).resolve().parent, self.root,
                        ignore=shutil.ignore_patterns('__pycache__'))

    def alter_json(self, relative, change):
        p = self.root/relative
        obj = json.loads(p.read_text(encoding='utf-8'))
        change(obj)
        p.write_text(json.dumps(obj), encoding='utf-8', newline='\n')

    def test_valid_package(self):
        self.assertEqual(validate_package(self.root), [])

    def test_modified_source_input_rejected(self):
        p = self.root/'reference/materialscloud-2020.58/inputs/epw.in'
        p.write_bytes(p.read_bytes()+b'changed')
        self.assertTrue(validate_package(self.root))

    def test_wrong_license_rejected(self):
        self.alter_json('reference/materialscloud-2020.58/record_metadata_excerpt.json',
                        lambda obj: obj.update(rights=[]))
        self.assertTrue(validate_package(self.root))

    def test_unsupported_reproduction_claim_rejected(self):
        self.alter_json('source_manifest.json', lambda obj: obj.update(paper_reproduction_completed=True))
        self.assertTrue(validate_package(self.root))

    def test_corrupted_synthetic_report_rejected(self):
        self.alter_json('results/validation.json', lambda obj: obj.update(is_author_data=True))
        self.assertTrue(validate_package(self.root))

    def test_unexecuted_notebook_rejected(self):
        def clear_execution(nb):
            next(c for c in nb['cells'] if c['cell_type'] == 'code')['execution_count'] = None
        self.alter_json('MgB₂数据核查交互教程.ipynb', clear_execution)
        self.assertTrue(validate_package(self.root))

    def test_manifest_creator_change_rejected(self):
        self.alter_json('source_manifest.json', lambda obj: obj.update(authors=['UNRELATED CREATOR']))
        self.assertTrue(validate_package(self.root))

    def test_undeclared_upstream_file_rejected(self):
        (self.root/'reference/materialscloud-2020.58/inputs/extra.m').write_bytes(b'not permitted')
        self.assertTrue(validate_package(self.root))

    def test_notebook_modified_code_with_old_execution_rejected(self):
        def change_source(nb):
            next(c for c in nb['cells'] if c['cell_type'] == 'code')['source'] = ['raise RuntimeError()']
        self.alter_json('MgB₂数据核查交互教程.ipynb', change_source)
        self.assertTrue(validate_package(self.root))

    def test_notebook_empty_outputs_rejected(self):
        def clear_outputs(nb):
            for c in nb['cells']:
                if c['cell_type'] == 'code':
                    c['outputs'] = []
        self.alter_json('MgB₂数据核查交互教程.ipynb', clear_outputs)
        self.assertTrue(validate_package(self.root))


if __name__ == '__main__':
    unittest.main()
