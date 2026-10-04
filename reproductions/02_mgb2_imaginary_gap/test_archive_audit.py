"""Exercise archive safety using original in-memory tar fixtures."""
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import stat
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import archive_audit
try:
    from archive_audit import inspect_archive
except ModuleNotFoundError as exc:
    if exc.name != 'archive_audit':
        raise
    inspect_archive = None


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(inspect_archive, 'archive inspection is not implemented')

    def run_tar(self, members, *, wrong_hash=False):
        with TemporaryDirectory() as directory:
            p = Path(directory)/'fixture.tar'
            with tarfile.open(p, 'w') as t:
                for name, kind, payload in members:
                    info = tarfile.TarInfo(name)
                    info.type = kind
                    if kind == tarfile.REGTYPE:
                        info.size = len(payload)
                        t.addfile(info, io.BytesIO(payload))
                    else:
                        info.linkname = 'target'
                        t.addfile(info)
            sha = '0'*64 if wrong_hash else hashlib.sha256(p.read_bytes()).hexdigest()
            return inspect_archive(p, expected_sha256=sha)

    def test_regular_files_hashed_no_execution(self):
        r = self.run_tar([('root/x.in', tarfile.REGTYPE, b'abc')])
        self.assertEqual(r['files'][0]['sha256'], hashlib.sha256(b'abc').hexdigest())
        self.assertEqual(r['files'][0]['bytes'], 3)

    def test_hash_mismatch_rejected_before_read(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            self.run_tar([('root/x', tarfile.REGTYPE, b'a')], wrong_hash=True)

    def test_traversal_absolute_windows_paths_rejected(self):
        for name in ['../x', '/x', 'root/../x', 'C:/x', 'root\\x']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'path'):
                self.run_tar([(name, tarfile.REGTYPE, b'a')])

    def test_links_and_special_members_rejected(self):
        for kind in [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE]:
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'member type'):
                self.run_tar([('root/x', kind, b'')])

    def test_case_insensitive_duplicate_paths_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.run_tar([('root/A.in', tarfile.REGTYPE, b'a'),
                          ('root/a.in', tarfile.REGTYPE, b'b')])

    def test_directory_allowed_and_counted_separately(self):
        r = self.run_tar([('root/', tarfile.DIRTYPE, b''),
                          ('root/x', tarfile.REGTYPE, b'a')])
        self.assertEqual(r['regular_file_count'], 1)
        self.assertEqual(r['member_count'], 2)

    def test_license_must_belong_to_expected_record(self):
        check = getattr(archive_audit, 'check_record_metadata', None)
        self.assertTrue(callable(check), 'record identity/license binding is missing')
        with self.assertRaisesRegex(ValueError, 'identity'):
            check({'id': 'another-record'})
        with self.assertRaisesRegex(ValueError, 'DOI'):
            check({'id': 'a6p4k-eh221', 'pids': {'doi': {'identifier': 'wrong'}}})
        record = {'id': 'a6p4k-eh221',
                  'pids': {'doi': {'identifier': '10.24435/materialscloud:tf-kf'}},
                  'versions': {'index': 1},
                  'files': {'entries': {'Ponce-CPC-2016.tar': {
                      'key': 'Ponce-CPC-2016.tar', 'size': 1863680,
                      'checksum': 'md5:06b8275acde7a69090fcbf964bc282a0'}}},
                  'metadata': {'rights': [], 'publication_date': '2020-06-21',
                               'title': 'EPW: Electron-phonon coupling, transport and superconducting properties using maximally localized Wannier functions',
                               'creators': [{'person_or_org': {'name': n}}
                                            for n in ['Poncé, Samuel', 'Margine, Elena Roxana',
                                                      'Verdi, Carla', 'Giustino, Feliciano']]}}
        with self.assertRaisesRegex(ValueError, 'CC BY'):
            check(record)
        record['metadata']['rights'] = [{'id': 'cc-by-4.0'}]
        self.assertEqual(check(record), record['metadata'])
        for mutate in [lambda r: r['versions'].update(index=999),
                       lambda r: r['files']['entries']['Ponce-CPC-2016.tar'].update(size=123),
                       lambda r: r['files']['entries']['Ponce-CPC-2016.tar'].update(checksum='md5:'+'0'*32)]:
            changed = json.loads(json.dumps(record))
            mutate(changed)
            with self.assertRaises(ValueError):
                check(changed)

    def test_snapshot_not_reopened_when_returning_payloads(self):
        self.assertIn('include_payloads', inspect.signature(inspect_archive).parameters)
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as t:
            member = tarfile.TarInfo('root/x.in')
            member.size = 3
            t.addfile(member, io.BytesIO(b'abc'))
        data = buffer.getvalue()
        with patch.object(Path, 'read_bytes', side_effect=[data, b'corrupted']) as read:
            inventory, payloads = inspect_archive('not-on-disk.tar',
                expected_sha256=hashlib.sha256(data).hexdigest(), include_payloads=True)
        self.assertEqual(read.call_count, 1)
        self.assertEqual(payloads['root/x.in'], b'abc')
        self.assertEqual(inventory['files'][0]['sha256'], hashlib.sha256(b'abc').hexdigest())

    def test_outputs_cannot_escape_root_or_use_reparse_points(self):
        safe = getattr(archive_audit, 'safe_output_path', None)
        self.assertTrue(callable(safe), 'resolved output-path guard is missing')
        with TemporaryDirectory() as directory:
            root = Path(directory)/'project'
            root.mkdir()
            safe(root, root/'normal/file.json')
            with self.assertRaises(ValueError):
                safe(root, root/'../outside.json')
            linked = root/'linked'
            linked.mkdir()
            original_lstat = Path.lstat
            def fake_lstat(path):
                result = original_lstat(path)
                if path == linked:
                    class ReparseStat:
                        st_mode = result.st_mode
                        st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT
                    return ReparseStat()
                return result
            with patch.object(Path, 'lstat', fake_lstat), self.assertRaises(ValueError):
                safe(root, linked/'file.json')

    def test_hardlinked_output_cannot_modify_external_file(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)/'project'
            root.mkdir()
            outside = Path(directory)/'unrelated.json'
            outside.write_bytes(b'KEEP EXTERNAL FILE')
            output = root/'source_manifest.json'
            os.link(outside, output)
            with self.assertRaisesRegex(ValueError, 'hardlink'):
                archive_audit.safe_output_path(root, output)
            with self.assertRaises(ValueError):
                archive_audit.write_json(root, output, {'changed': True})
            self.assertEqual(outside.read_bytes(), b'KEEP EXTERNAL FILE')


if __name__ == '__main__':
    unittest.main()
