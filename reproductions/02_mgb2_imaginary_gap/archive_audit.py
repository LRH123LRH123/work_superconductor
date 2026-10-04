"""Inspect the pinned author tar and copy ONLY four licensed input files.

No extraction of arbitrary paths, imports of upstream code, network, or job execution.
"""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
from tempfile import NamedTemporaryFile

AUTHOR_SHA256 = '1362f87c28360eaaeda8ca11a9934cf89fa141f8da8364e1dc5206f97d091804'
AUTHOR_MD5 = '06b8275acde7a69090fcbf964bc282a0'
RECORD_URL = 'https://archive.materialscloud.org/records/a6p4k-eh221'
API_URL = 'https://archive.materialscloud.org/api/records/a6p4k-eh221'
SELECTED = ['scf.in', 'nscf.in', 'ph.in', 'epw.in']
CREATORS = ['Poncé, Samuel', 'Margine, Elena Roxana', 'Verdi, Carla', 'Giustino, Feliciano']
SOURCE_TITLE = 'EPW: Electron-phonon coupling, transport and superconducting properties using maximally localized Wannier functions'
API_SNAPSHOT_SHA256 = '39e1ef2923727138e4e9625af511577e89b66c151673a8f668e5355d6fc7937b'


def inspect_archive(path, *, expected_sha256, include_payloads=False):
    data = Path(path).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != expected_sha256:
        raise ValueError('SHA256 mismatch')
    seen, files, payloads, total, count = set(), [], {}, 0, 0
    # All hashes and copies derive from this one immutable byte snapshot.
    with tarfile.open(fileobj=BytesIO(data)) as archive:
        for member in archive:
            count += 1
            if count > 1000:
                raise ValueError('too many members')
            p = PurePosixPath(member.name)
            if (p.is_absolute() or '..' in p.parts or ':' in member.name
                    or '\\' in member.name or not p.parts):
                raise ValueError(f'unsafe path: {member.name}')
            key = str(p).casefold()
            if key in seen:
                raise ValueError(f'duplicate path: {member.name}')
            seen.add(key)
            if not (member.isfile() or member.isdir()):
                raise ValueError(f'unsupported member type: {member.name}')
            if member.isdir():
                continue
            total += member.size
            if member.size > 10*1024**2 or total > 64*1024**2:
                raise ValueError('uncompressed size exceeds audit limits')
            payload = archive.extractfile(member).read()
            if len(payload) != member.size:
                raise ValueError('incomplete tar payload')
            files.append({'path': member.name, 'bytes': member.size,
                          'sha256': hashlib.sha256(payload).hexdigest()})
            payloads[member.name] = payload
    inventory = {'bytes': len(data), 'sha256': sha,
            'md5': hashlib.md5(data).hexdigest(), 'member_count': count,
            'regular_file_count': len(files), 'files': files}
    return (inventory, payloads) if include_payloads else inventory


def safe_output_path(root, path):
    root = Path(root).resolve(strict=True)
    path = Path(path).absolute()
    try:
        relative = path.relative_to(root)
        path.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise ValueError('output path escapes project root') from exc
    current = root
    for part in relative.parts:
        current = current/part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or
                getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError(f'output path uses link/reparse point: {current}')
        if stat.S_ISREG(info.st_mode) and getattr(info, 'st_nlink', 1) > 1:
            raise ValueError(f'output file is a hardlink: {current}')
    return path


def atomic_write_bytes(root, path, data):
    safe_output_path(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_output_path(root, path)
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix='.mgb2-write-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        safe_output_path(root, path)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            safe_output_path(root, temporary)
            temporary.unlink()


def write_json(root, path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    atomic_write_bytes(root, path, data)


def check_record_metadata(record):
    if record.get('id') != 'a6p4k-eh221':
        raise ValueError('Unexpected Materials Cloud record identity')
    if record.get('pids', {}).get('doi', {}).get('identifier') != '10.24435/materialscloud:tf-kf':
        raise ValueError('Unexpected dataset DOI')
    metadata = record['metadata']
    if not any(r.get('id') == 'cc-by-4.0' for r in metadata.get('rights', [])):
        raise ValueError('CC BY 4.0 grant not found in expected record metadata')
    entry = record.get('files', {}).get('entries', {}).get('Ponce-CPC-2016.tar', {})
    if (record.get('versions', {}).get('index') != 1 or entry.get('key') != 'Ponce-CPC-2016.tar'
            or entry.get('size') != 1863680 or entry.get('checksum') != 'md5:'+AUTHOR_MD5):
        raise ValueError('Unexpected archive entry or record version')
    if (metadata.get('publication_date') != '2020-06-21' or metadata.get('title') != SOURCE_TITLE
            or [c['person_or_org']['name'] for c in metadata['creators']] != CREATORS):
        raise ValueError('Unexpected source authors/title/date')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('record_json', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    inventory, payloads = inspect_archive(args.archive, expected_sha256=AUTHOR_SHA256,
                                          include_payloads=True)
    if inventory['md5'] != AUTHOR_MD5:
        raise ValueError('published MD5 mismatch')
    record_bytes = args.record_json.read_bytes()
    if hashlib.sha256(record_bytes).hexdigest() != API_SNAPSHOT_SHA256:
        raise ValueError('API snapshot differs from this pinned audit; review before upgrading')
    record = json.loads(record_bytes.decode('utf-8'))
    metadata = check_record_metadata(record)
    reference = root/'reference/materialscloud-2020.58'
    copied = []
    output_paths = [reference/'inputs'/name for name in SELECTED]
    output_paths += [reference/'archive_inventory.json', reference/'record_metadata_excerpt.json', root/'source_manifest.json']
    for path in output_paths:
        safe_output_path(root, path)
    for name in SELECTED:
        member_path = 'Ponce-CPC-2016/MgB2/'+name
        payload = payloads[member_path]
        destination = safe_output_path(root, reference/'inputs'/name)
        if destination.exists() and destination.read_bytes() != payload:
            raise ValueError(f'refusing to overwrite modified input: {name}')
        atomic_write_bytes(root, destination, payload)
        copied.append({'archive_path': member_path,
                           'path': destination.relative_to(root).as_posix(),
                           'bytes': len(payload),
                           'sha256': hashlib.sha256(payload).hexdigest()})
    write_json(root, reference/'archive_inventory.json', inventory)
    excerpt = {k: metadata[k] for k in ['title', 'publication_date', 'rights']}
    excerpt['creators'] = [c['person_or_org']['name'] for c in metadata['creators']]
    excerpt['record_identity'] = {'id': record['id'], 'doi': record['pids']['doi']['identifier'],
                                 'version_index': record['versions']['index'],
                                 'archive_name': 'Ponce-CPC-2016.tar',
                                 'archive_checksum': 'md5:'+AUTHOR_MD5, 'archive_bytes': 1863680}
    excerpt['provenance'] = {'api_url': API_URL, 'accessed_on': '2026-10-04',
                             'unmodified_api_snapshot_sha256': hashlib.sha256(
                                 record_bytes).hexdigest(),
                             'excerpt_not_full_api_snapshot': True}
    write_json(root, reference/'record_metadata_excerpt.json', excerpt)
    mgb2 = [f for f in inventory['files'] if '/MgB2/' in f['path']]
    manifest = {
        'review_date': '2026-10-04', 'record_url': RECORD_URL, 'record_api_url': API_URL,
        'dataset_doi': '10.24435/materialscloud:tf-kf',
        'related_paper_doi': '10.1016/j.cpc.2016.07.028',
        'authors': excerpt['creators'], 'dataset_version': 'v1 (2020-06-21)',
        'archive_download_url': RECORD_URL+'/files/Ponce-CPC-2016.tar?download=1',
        'archive_sha256': inventory['sha256'], 'archive_md5': inventory['md5'],
        'archive_bytes': inventory['bytes'], 'regular_file_count': len(inventory['files']),
        'inventory_json_sha256': hashlib.sha256((reference/'archive_inventory.json').read_bytes()).hexdigest(),
        'license_excerpt_json_sha256': hashlib.sha256((reference/'record_metadata_excerpt.json').read_bytes()).hexdigest(),
        'MgB2_file_count': len(mgb2), 'redistributed_inputs': copied,
        'selected_inputs_license': 'CC-BY-4.0',
        'license_url': 'https://creativecommons.org/licenses/by/4.0/legalcode.en',
        'input_bytes_modified': False, 'upstream_scripts_executed': False,
        'pseudopotentials_redistributed': False, 'source_paper_pdf_redistributed': False,
        'contains_author_Fig6_imaginary_gap_pointset': False,
        'contains_material_ephmat_kernel': False, 'paper_reproduction_completed': False,
        'new_cluster_jobs': 0,
        'target': {'doi': '10.1103/PhysRevB.87.024505', 'read_version': 'arXiv:1211.3345v1',
                   'page': 10, 'figure': '6(a)', 'temperature_K': 10., 'mu_star': .16,
                   'publisher_pdf_comparison_completed': False},
        'scope': 'Licensed input archive audit and original synthetic parser exercises only',
        'documentation': [
            {'url': 'https://docs.epw-code.org/tutorials/archived/MgB2.html',
             'role': 'Legacy five-column schema only; not a current universal format'},
            {'url': 'https://docs.epw-code.org/tutorials/tutorial_04/index.html',
             'role': '2026 FSR parameter comparison only; mutable page, not copied or run'}],
        'synthetic_fixture': {'path': 'fixtures/synthetic_legacy_five.dat',
                              'is_author_data': False, 'is_material_calculation': False}}
    write_json(root, root/'source_manifest.json', manifest)
    print(f'PASS: {len(inventory["files"])} files inventoried, {len(mgb2)} MgB2 files; '
          'four inputs copied byte-exact; no author Fig6 pointset or ephmat kernel present')


if __name__ == '__main__':
    main()
