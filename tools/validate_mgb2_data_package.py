"""Verify byte-exact author inputs and the explicitly synthetic data lesson."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import nbformat

INPUT_HASHES = {
    'scf.in': '9bf505c8abf8cc5aea574c3b519417ef126772d5072e3bcb3979ac08008ee68c',
    'nscf.in': '39f817228761fab8bd29b39da0f9652549bfffc66e20b44b2dd9204882ac6f16',
    'ph.in': '39a7d573c487d592358945e9f72b6ed2b3a9184105af483fdb705c2595afbf9d',
    'epw.in': '2415f41282ecc66cffdbc87530831f088418697a40275af2424eb1c06f61036e'}
AUTHOR_SHA = '1362f87c28360eaaeda8ca11a9934cf89fa141f8da8364e1dc5206f97d091804'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_package(root):
    problems = []
    names = ['gap_io', 'mgb2_data_lesson_rebuild', 'mgb2_archive_guard']
    previous = {name: sys.modules.get(name) for name in names}
    try:
        manifest = json.loads((root/'source_manifest.json').read_text(encoding='utf-8'))
        expected = {'archive_sha256': AUTHOR_SHA, 'archive_bytes': 1863680,
                    'archive_md5': '06b8275acde7a69090fcbf964bc282a0',
                    'regular_file_count': 75, 'MgB2_file_count': 25,
                    'dataset_doi': '10.24435/materialscloud:tf-kf',
                    'related_paper_doi': '10.1016/j.cpc.2016.07.028',
                    'selected_inputs_license': 'CC-BY-4.0', 'new_cluster_jobs': 0}
        for key, value in expected.items():
            if manifest[key] != value:
                problems.append(f'MgB2 source/identity mismatch: {key}')
        for flag in ['input_bytes_modified', 'upstream_scripts_executed',
                     'pseudopotentials_redistributed', 'source_paper_pdf_redistributed',
                     'contains_author_Fig6_imaginary_gap_pointset', 'contains_material_ephmat_kernel',
                     'paper_reproduction_completed']:
            if manifest[flag] is not False:
                problems.append(f'Unsupported MgB2 scope claim: {flag}')
        target = manifest['target']
        if (target['figure'] != '6(a)' or target['page'] != 10 or target['temperature_K'] != 10
                or target['mu_star'] != .16 or target['doi'] != '10.1103/PhysRevB.87.024505'
                or target['read_version'] != 'arXiv:1211.3345v1'
                or target['publisher_pdf_comparison_completed'] is not False):
            problems.append('MgB2 target/version caveat altered')
        ref = root/'reference/materialscloud-2020.58'
        guard = load_module('mgb2_archive_guard', root/'archive_audit.py')
        actual_reference_files = set()
        def visit(directory):
            guard.safe_output_path(root, directory)
            for path in directory.iterdir():
                guard.safe_output_path(root, path)
                if path.is_dir():
                    visit(path)
                else:
                    actual_reference_files.add(path.relative_to(ref).as_posix())
        visit(ref)
        expected_reference_files = {'archive_inventory.json', 'record_metadata_excerpt.json',
                                    '来源与许可.md', *['inputs/'+name for name in INPUT_HASHES]}
        if actual_reference_files != expected_reference_files:
            problems.append('Undeclared or missing upstream reference file')
        for field, filename in [('inventory_json_sha256', 'archive_inventory.json'),
                                ('license_excerpt_json_sha256', 'record_metadata_excerpt.json')]:
            if digest(ref/filename) != manifest[field]:
                problems.append(f'MgB2 reference checksum mismatch: {filename}')
        metadata = json.loads((ref/'record_metadata_excerpt.json').read_text(encoding='utf-8'))
        if not any(r.get('id') == 'cc-by-4.0' for r in metadata['rights']):
            problems.append('Author input license grant missing')
        if metadata['provenance']['api_url'] != 'https://archive.materialscloud.org/api/records/a6p4k-eh221':
            problems.append('Wrong input license metadata source')
        identity = metadata['record_identity']
        guard.check_record_metadata({
            'id': identity['id'], 'pids': {'doi': {'identifier': identity['doi']}},
            'versions': {'index': identity['version_index']},
            'files': {'entries': {identity['archive_name']: {'key': identity['archive_name'],
                'checksum': identity['archive_checksum'], 'size': identity['archive_bytes']}}},
            'metadata': {'title': metadata['title'], 'publication_date': metadata['publication_date'],
                'rights': metadata['rights'], 'creators': [{'person_or_org': {'name': name}}
                                                         for name in metadata['creators']]}})
        if (manifest['authors'] != guard.CREATORS or metadata['creators'] != guard.CREATORS
                or manifest['dataset_version'] != 'v1 (2020-06-21)'
                or metadata['provenance']['unmodified_api_snapshot_sha256'] != guard.API_SNAPSHOT_SHA256):
            problems.append('Source attribution/version/snapshot differs from pinned record')
        inventory = json.loads((ref/'archive_inventory.json').read_text(encoding='utf-8'))
        files = inventory['files']
        mgb2 = [f for f in files if '/MgB2/' in f['path']]
        if (inventory['sha256'] != AUTHOR_SHA or len(files) != 75 or len(mgb2) != 25
                or len({f['path'].casefold() for f in files}) != 75):
            problems.append('Author archive inventory differs')
        if any('imag_aniso_' in f['path'] or '.ephmat' in f['path'] for f in mgb2):
            problems.append('Inventory conflicts with missing-data audit')
        items = manifest['redistributed_inputs']
        expected_paths = ['reference/materialscloud-2020.58/inputs/'+n for n in INPUT_HASHES]
        if [item['path'] for item in items] != expected_paths:
            problems.append('Only the four selected original inputs may be copied')
        for name, sha in INPUT_HASHES.items():
            path = ref/'inputs'/name
            entry = next(f for f in files if f['path'] == 'Ponce-CPC-2016/MgB2/'+name)
            item = next(f for f in items if f['path'] == 'reference/materialscloud-2020.58/inputs/'+name)
            if (digest(path) != sha or entry['sha256'] != sha or item['sha256'] != sha
                    or path.stat().st_size != entry['bytes'] or entry['bytes'] != item['bytes']
                    or item['archive_path'] != entry['path']):
                problems.append(f'Changed author input: {name}')
        fixture = manifest['synthetic_fixture']
        if (fixture['is_author_data'] is not False or fixture['is_material_calculation'] is not False
                or fixture['path'] != 'fixtures/synthetic_legacy_five.dat'):
            problems.append('Synthetic example mislabeled')
        load_module('gap_io', root/'gap_io.py')
        lesson = load_module('mgb2_data_lesson_rebuild', root/'run_learning.py')
        saved = json.loads((root/'results/validation.json').read_text(encoding='utf-8'))
        if lesson.collect(root) != saved:
            problems.append('Synthetic report cannot be rebuilt from fixture')
        nb = nbformat.read(root/'MgB₂数据核查交互教程.ipynb', as_version=4)
        receipt = json.loads((root/'notebook_execution_receipt.json').read_text(encoding='utf-8'))
        if (digest(root/'MgB₂数据核查交互教程.ipynb') != receipt['notebook_sha256']
                or receipt['executed_cells'] != 6 or receipt['core_tests_run'] != 28
                or receipt['receipt_kind'] != 'local_executed_build_fingerprint_not_a_signature'):
            problems.append('Notebook changed since its executed build')
        dependency_names = ['gap_io.py', 'archive_audit.py', 'test_gap_io.py', 'test_archive_audit.py',
                            'run_learning.py', 'build_notebook.py', 'source_manifest.json',
                            'results/validation.json', 'fixtures/synthetic_legacy_five.dat']
        if (set(receipt['dependencies_sha256']) != set(dependency_names) or any(
                digest(root/name) != receipt['dependencies_sha256'][name] for name in dependency_names)):
            problems.append('Notebook dependency changed since executed build')
        nbformat.validate(nb)
        cells = [c for c in nb.cells if c.cell_type == 'code']
        if len(cells) != 6 or any(c.execution_count is None for c in cells):
            problems.append('MgB2 data notebook missing/unexecuted cells')
        if any(o.output_type == 'error' for c in cells for o in c.outputs):
            problems.append('MgB2 data notebook error output')
        if any(not c.outputs for c in cells):
            problems.append('MgB2 data notebook outputs removed')
        if list(root.rglob('*.pdf')) or list(root.rglob('*.UPF')) or list(root.rglob('*.upf')):
            problems.append('Unplanned source PDF/pseudopotential copied')
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        problems.append(f'MgB2 package invalid: {exc}')
    finally:
        for name, original in previous.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return problems


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    failures = validate_package(root/'reproductions/02_mgb2_imaginary_gap')
    if failures:
        raise SystemExit('\n'.join(failures))
    print('PASS: MgB2 author inputs/license/inventory, synthetic report and six executed cells; no figure-reproduction claim')
