# MgB₂ 虚轴输出读取入门教程

Imaginary-Axis Gap Data: Units, Schema, Provenance and Safe Inspection

[项目入口](README.md) · [来源核查](MgB₂数据来源与固定输入核查.md) · [交互教程](MgB₂数据核查交互教程.ipynb)。

## 1. 为什么先学读数据

原图复现不是“读两列、画线、看起来相似”。先确认物理量、文件格式、单位、状态标签和来源，
才能决定哪一种比较是有效的。本课不需要集群，也不需要重新计算第一性原理。

先修知识：知道费米能（Fermi energy）、能带（band）、k 点（wavevector），
读过 [双带课程](../../examples/07_two_band_eliashberg/README.md) 的虚轴频率与 DOS 权重部分。
预计用时 60–90 分钟。完成后应能拒绝格式/单位不明确的数据，而不是自动猜测。

本课产物：严格的五列读取器、单位转换、温度网格兼容检查、窗口计数、测试与已执行 Notebook。
所有演示点来自 [原创合成格式样例](fixtures/synthetic_legacy_five.dat)。
**样例不是 MgB₂ 计算结果、作者点集或论文参考答案，不可参与原图 RMSE。**

## 2. 先填写数据身份卡

收到数据后先记录这些字段。缺失就写 unknown，不用文件名猜。

| 字段 | 原因 |
|---|---|
| Source / License / SHA256 | 能追溯来源，知道能否转载；哈希不是物理正确性的证明 |
| Code version / Commit / Writer routine | 同名输出可能随版本改变列定义 |
| T、μ*、窗口、截止与输入 | 明确是不是同一个问题 |
| Axis / Energy unit | 虚轴、实轴、循环频率、能量不是同一概念 |
| Band/k ID、DOS weight、排序关系 | 没有它们不能进行带分辨加权统计 |
| Sampling / Subset rule | 明确这是完整点集还是绘图抽样 |
| Solver convergence evidence | 数据可读并不证明自洽方程或材料精度已达到要求 |

文件叫 `10.00` 不能证明程序确实在 10 K 跑完；文件叫 `gap0` 也不能证明它等于实轴激发能隙。

## 3. 本读取器只支持明确的历史五列模式

[EPW 历史 MgB₂ 教程](https://docs.epw-code.org/tutorials/archived/MgB2.html)
定义 `MgB2.imag_aniso_XX` 为以下五列。
本程序实现一个**正虚频五列 profile**，不是所有 EPW 版本的通用格式解析器。

| 列 | 英文概念 | 物理量 | 输入单位 |
|---|---|---|---|
| 1 | Matsubara energy | ωₙ，虚轴频率的实数能量坐标 | eV |
| 2 | Kohn–Sham energy relative to EF | ξ_bk = ε_bk − EF | eV |
| 3 | Renormalization function | 超导态 Z_bk(iωₙ) | 无量纲 |
| 4 | Imaginary-axis gap | Δ_bk(iωₙ) | eV |
| 5 | Normal-state renormalization | 正常态 Z_bk | 无量纲 |

不要把第 2 列当能隙，也不要把第 3 或第 5 列乘 1000。
解析后 ω、ξ、Δ 统一成 meV。负 Δ 保留，不能直接取绝对值：频率尾部可能变号，
未经解释的绝对值处理会改变待比较的物理量。

这个文件没有独立的 band/k 标签与 DOS 权重列；重复 ω 是不同态的记录，不是重复错误。
程序保留顺序和所有重复行，不把数据压成单条平均线，不从 Δ 大小推断 σ/π。
`a2f_iso` 的声子模分解也不是带间 α²Fᵢⱼ 矩阵，不能用来补这些标签。

本课不支持二列绘图投影、实轴文件、`gap0` 分布或新版本额外列。
遇到它们会报错。应先查对应的写出程序，再新增有测试的明确模式，不要删除多余列凑格式。

## 4. 环境与第一遍运行

在项目目录使用已有 NumPy / Notebook 环境；不用下载作者归档才能运行。
仓库没有统一全局环境，常规 Python 3.12 + NumPy 1.26 即可运行读取器和单元测试。
Notebook 重建另外使用 `nbformat`、`nbclient`、`ipykernel`。
本次实际验证 Python 3.12.4、NumPy 1.26.4、nbformat 5.9.2、nbclient 0.8.0。

```powershell
Set-Location H:\github\work_superconductor\reproductions\02_mgb2_imaginary_gap
python -B -m unittest -v test_gap_io test_archive_audit
python -B gap_io.py fixtures\synthetic_legacy_five.dat --energy-unit eV --temperature-K 10
```

参数必须显式给能量单位和声明温度。第一遍应报告 3 行、能隙范围 −2 到 6 meV，
并明确 `has_band_labels=false`、`has_DOS_weights=false`、`is_paper_reproduction=false`。
这些输出只表示格式样例处理正确，不表示 MgB₂ 出现负低频能隙。

## 5. 手算一次单位转换

样例第一行是：

```text
0.002707 0.000 1.5 0.006 1.4
```

换成 meV：ω=2.707、ξ=0、Δ=6；Z=1.5、Z_normal=1.4 不变。
代码对应 `a[:, [0,1,3]] *= 1000`。默认不猜单位，即使数据看上去“很像 meV”。

错误单位会造成横轴、电子窗口、能隙同时错 1000 倍。
程序能检查声明是否有效，但不能仅凭数值知道你的单位声明是真是假。
数据身份卡和头部/写出源码仍是必要证据。

## 6. Matsubara 网格检查

费米子虚轴能量满足：

```text
ω_n = (2n + 1) π k_B T,    n = 0, 1, 2, ...
k_B = 0.08617333262145 meV/K
```

这是以能量表示的 angular-frequency 坐标，不是循环频率 f；不要额外乘 2π。
10 K 的前两个正虚频约为 2.7072、8.1216 meV。
读取器为每行找最近的 n，重建 ωₙ，然后比较残差。
默认绝对容差 0.001 meV，只用于兼容文本保留的小数位，**不是原图或求解精度误差棒**。

```python
from pathlib import Path
from gap_io import parse_legacy_five, check_matsubara
rows = parse_legacy_five(Path('fixtures/synthetic_legacy_five.dat').read_text(), energy_unit='eV')
residual = check_matsubara(rows, 10)
print(residual)
```

故意声明 20 K 应报错。通过 10 K 检查只能说明数值与某些奇数频率兼容，
不能证明运行温度、最低频率是否完整、频率截止是否充分或每个态的频率数一致。
程序不推断缺失状态、不补齐频率。零频和负频不属于本课 profile，明确拒绝。

## 7. 限定窗口，但不伪造权重

```python
from gap_io import window_report
report = window_report(rows, max_frequency_meV=2.707, max_abs_xi_meV=50)
print(report)
```

此例应保留 2 行，排除 1 行。边界包含等号，只有一个浮点 ULP 的舍入保护；
不会用宽泛“差不多”容差把明显超窗的点纳入。
`max_abs_xi_meV` 是 |ξ| 阈值，不等于自动解释任意 EPW 版本 `fsthick` 的语义。

这里只输出行数与未加权最小/最大值。它们是样本范围，不是概率分布、误差棒或材料带内宽度验收。
DOS 加权平均需要明确的 p_bk：

```text
<Δ>_band,n = Σ_(bk in band) p_bk Δ_bk,n / Σ_(bk in band) p_bk
```

如果状态权重未知，写 equal-row average 也不能冒充 DOS-weighted average。
本程序宁可不输出均值和分位数；有权重、标签与映射后再扩展。

## 8. 测试和错误处理

18 个读取测试涵盖单位、D 指数、注释、空表、错误列数、非有限值、负能隙、重复行、
窗口与温度兼容检查；10 个归档测试覆盖哈希、路径、链接、重复路径、目录、元数据绑定、
单次不可变快照、输出重解析点与硬链接防护；写入使用同目录临时文件原子替换。
`GapRows` 另外在构造时检查长度与有限值，保存只读数组。

报错显示行号时，先回到原文件与对应源码，保留原始副本和 SHA256。
不要在未理解语义前批量删除报错行、裁掉负能隙或去重。
为了方便验证，本课没有自动下载、SSH、提交任务或调用 EPW 的代码。

## 9. 练习与答案

1. 手算第一行五个值的单位转换，并指出哪两列不变。
2. 把 `--temperature-K` 改为 20，说明为什么应拒绝；也说明通过 10 K 的证明范围。
3. 两行具有同一 ω，能否直接删除一行？
4. 五列能否直接计算 σ 带 DOS 加权均值？需要补什么？
5. 四个作者输入已取得，为何不能标记 Fig. 6(a) 已复现？

答案：1. 2.707、0、1.5、6、1.4，后两种 Z 无量纲不变。
2. 奇数 Matsubara 网格不兼容；通过只证明网格兼容，仍需日志证实 T。
3. 不可以，重复频率可能对应不同 band/k 状态。
4. 不可以，需要同源标签、DOS/积分权重及行映射规则，不能按能隙大小猜带。
5. 尚无目标材料核、作者点集、误差对照，且公开输入和目标存在明确参数/版本差异。

## 10. 本课的完成标准

能独立执行 28 项核心测试、重建样例报告，读懂输入差异和许可，解释哪些统计暂时不能做。
另有 10 项学习包完整性测试，检查篡改输入、署名/许可、报告、执行状态、额外转载文件、
过期 Notebook 输出与虚假复现声明，共 38 项：

```powershell
python -B -m unittest -v test_gap_io test_archive_audit test_package_validation
```

Notebook 重建成功后生成 `notebook_execution_receipt.json`，绑定当前 Notebook 字节和九项代码/数据依赖。
改代码、删除输出或改依赖后，必须重新执行生成器，不能保留旧执行编号假装仍有效。
这是本地构建指纹，不是密码学签名，也不证明材料数据真实或授权；恶意重写全部记录不在其防护范围。

配套理论 PPTX 沿用 [双带与各向异性课程](../../slides/双带与各向异性Eliashberg入门.pptx)，
本次是数据接入补充课，没有新增冒充原图复现结果的材料课件。
取得真实输出后先验证 schema，再谈定量比较；原图任务仍按预先声明的阈值验收。
