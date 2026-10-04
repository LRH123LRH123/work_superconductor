"""Build six executed Chinese data-inspection cells, never running EPW or SSH."""
import json
import hashlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT/'MgB₂数据核查交互教程.ipynb'
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))


md('''
# MgB₂ 数据核查与虚轴结果读取
Data Provenance and Imaginary-Axis Gap Inspection

本课是数据接入训练，不是材料计算或原图复现。
作者归档对应 2016 CPC，不含目标 2013 Fig. 6(a) 数字点集或材料核。
所有数值演示是原创合成格式样例，不可用于原图 RMSE。
无网络、集群、EPW 调用或参数扫描；理论课件沿用第五套学习包。
先修：双带课的 DOS 与 Matsubara 频率。先作预测，再执行各格。
''')
md('''
## 1. 来源与许可：先核对文件身份
预测：记录级开放意味着所有依赖、输出和论文 PDF 都已经取得吗？
这里只保存四个未修改输入，不将脚本引用的文件名当作已取得数据。
''')
code('''
from pathlib import Path
import hashlib, json, io, unittest
import numpy as np
from gap_io import parse_legacy_five, check_matsubara, window_report, KB_MEV_K
root = Path.cwd()
manifest = json.loads((root/'source_manifest.json').read_text(encoding='utf-8'))
assert manifest['regular_file_count'] == 75 and manifest['MgB2_file_count'] == 25
assert manifest['selected_inputs_license'] == 'CC-BY-4.0'
for f in manifest['redistributed_inputs']:
    data = (root/f['path']).read_bytes()
    assert len(data) == f['bytes'] and hashlib.sha256(data).hexdigest() == f['sha256']
print('Dataset:', manifest['dataset_doi'], 'associated paper:', manifest['related_paper_doi'])
print('Four byte-exact input copies; author Fig6 pointset:', manifest['contains_author_Fig6_imaginary_gap_pointset'])
assert not manifest['paper_reproduction_completed']
''')
md('''
## 2. 原样阅读旧输入，不执行
预测：`muc=0.16` 相同就等于原图条件相同吗？
检查温度字段、采样和截止。没有把旧关键词迁移到现代 EPW，也没有调用求解器。
''')
code('''
source = root/'reference/materialscloud-2020.58/inputs'
epw = (source/'epw.in').read_text(encoding='utf-8')
need = ['nstemp', 'tempsmin', 'tempsmax', 'muc', 'wscut', 'nkf', 'nqf', 'degaussq']
for line in epw.splitlines():
    if any(line.strip().startswith(key) for key in need):
        print(line.strip())
assert 'tempsmin = 15.00' in epw and 'nkf1 = 20' in epw
assert epw.startswith('--')
print('Historical archive input, NOT a runnable modern EPW or 10 K figure-matched job.')
''')
md('''
## 3. 五列读取与手算单位
预测：`0.006 eV` 等于多少 meV？Z 是否也要乘 1000？
全部点是原创 SYNTHETIC FORMAT FIXTURE。重复频率与负能隙不被删掉。
''')
code('''
text = (root/'fixtures/synthetic_legacy_five.dat').read_text(encoding='utf-8')
rows = parse_legacy_five(text, energy_unit='eV')
print('Synthetic omega [meV]:', rows.frequency_meV)
print('Synthetic xi [meV]:', rows.xi_meV)
print('Synthetic Delta [meV]:', rows.gap_meV)
print('Unscaled Z:', rows.Z)
assert np.allclose(rows.gap_meV, [6, -2, 4])
assert np.allclose(rows.Z, [1.5, 1.3, 1.4])
''')
md('''
## 4. 只做网格兼容检查
预测：10 K 与 20 K 能同时通过这个样例吗？
通过仅表示奇数 Matsubara 网格兼容；真实温度要由输入和成功运行日志核定。
''')
code('''
expected = (2*np.arange(2)+1)*np.pi*KB_MEV_K*10
print('10 K first two Matsubara energies:', expected, 'meV')
residual = check_matsubara(rows, 10)
print('Synthetic printed-grid residual:', residual, 'meV (not a physical error bar)')
assert residual < .001
try:
    check_matsubara(rows, 20)
except ValueError as error:
    print('Correctly rejected incompatible 20 K:', error)
else:
    raise AssertionError('20 K must not pass this fixture')
''')
md('''
## 5. 范围不是带分辨加权分布
预测：同一频率两行可以去重吗？五列能否识别 σ/π？
样本计数与原始范围不等于 DOS 加权均值、材料分布或原图精度。
''')
code('''
full = window_report(rows)
narrow = window_report(rows, max_frequency_meV=2.707, max_abs_xi_meV=50)
print('Full synthetic window:', full)
print('Narrow synthetic window:', narrow)
assert full['retained_rows'] == 3 and narrow['retained_rows'] == 2
assert narrow['gap_range_meV'] == [-2, 6]
assert not narrow['has_band_labels'] and not narrow['has_DOS_weights']
assert not narrow['is_paper_reproduction']
''')
md('''
## 6. 练习、拒绝模糊格式与自动检验
练习：二列 ω/Δ 表能否猜成五列？答案是拒绝，先核对写出代码。
补充题：作者稿抽样展示的点密度是否等于 DOS 权重？答案是否。
下面运行 28 项原始测试，并重建只含合成样例的报告。
''')
code('''
try:
    parse_legacy_five('0.002707 0.006', energy_unit='eV')
except ValueError as error:
    print('Correctly rejected two-column projection:', error)
else:
    raise AssertionError('Ambiguous schema must not be accepted')
import test_gap_io, test_archive_audit
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)
                           for m in [test_gap_io, test_archive_audit])
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
print(stream.getvalue())
assert result.wasSuccessful() and result.testsRun == 28
from run_learning import collect
saved = json.loads((root/'results/validation.json').read_text(encoding='utf-8'))
assert collect(root) == saved
assert not saved['is_author_data'] and not saved['is_material_calculation']
print('All exercises checked. Original Fig6 quantitative reproduction remains incomplete.')
''')
md('''
## 学习提交
写出需要作者提供的字段清单，解释同 μ* 不等于同参数、网格兼容不等于真实 T、
样本范围不等于 DOS 分布。详解与答案见同目录两份中文教程。
下一步先接入既有真实输出或准备作者数据请求，不自动开集群任务。
''')

nb = nbf.read(OUTPUT, as_version=4) if OUTPUT.exists() else nbf.v4.new_notebook()
nb.cells = cells
nb.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
               'language_info': {'name': 'python', 'version': f'{sys.version_info.major}.{sys.version_info.minor}'}}
with TemporaryDirectory(prefix='mgb2-data-kernel-') as directory:
    spec = Path(directory)/'mgb2-current-python'
    spec.mkdir()
    (spec/'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-Xfrozen_modules=off', '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'Data audit build Python', 'language': 'python',
        'env': {'IPYTHONDIR': str(Path(directory)/'ipython'), 'PYTHONDONTWRITEBYTECODE': '1'}
    }), encoding='utf-8', newline='\n')
    manager = KernelManager(kernel_name=spec.name, kernel_spec_manager=KernelSpecManager(kernel_dirs=[directory]))
    try:
        NotebookClient(nb, km=manager, timeout=120, resources={'metadata': {'path': str(ROOT)}}).execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
nbf.validate(nb)
with OUTPUT.open('w', encoding='utf-8', newline='\n') as stream:
    nbf.write(nb, stream)
dependencies = ['gap_io.py', 'archive_audit.py', 'test_gap_io.py', 'test_archive_audit.py',
                'run_learning.py', 'build_notebook.py', 'source_manifest.json',
                'results/validation.json', 'fixtures/synthetic_legacy_five.dat']
receipt = {'receipt_kind': 'local_executed_build_fingerprint_not_a_signature',
           'notebook_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
           'executed_cells': 6, 'core_tests_run': 28,
           'dependencies_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                   for name in dependencies}}
(ROOT/'notebook_execution_receipt.json').write_text(
    json.dumps(receipt, indent=2)+'\n', encoding='utf-8', newline='\n')
print('PASS: six original Chinese data-inspection cells executed; no jobs or material solver')
