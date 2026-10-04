# 双带与各向异性 Eliashberg 学习包

Two-Band and Anisotropic Migdal-Eliashberg Learning Package

[返回首页](../../README.md) · [上一课 EPC](../06_epc_eliashberg/README.md) · [详细中文教程](双带与各向异性Eliashberg入门教程.md)

这是一套原创、有限正虚频、带平均的 Einstein 模型。不是 EPW 替代品，不拟合 MgB₂。
学习目标是理解费米面权重、非对称耦合矩阵、多带序参量、线性不稳定性与非线性自洽。
各向异性不是一种新的配对介质；本课仍是声子介导模型。

## 配套材料

| 入口 | 内容 |
|---|---|
| [中文教程](双带与各向异性Eliashberg入门教程.md) | 符号、推导、矩阵约定、逐段代码、练习与答案 |
| [Notebook](双带Eliashberg交互教程.ipynb) | 8 个代码单元已执行，先预测后验证 |
| [20 页 PPTX](../../slides/双带与各向异性Eliashberg入门.pptx) / [PDF](../../slides/双带与各向异性Eliashberg入门.pdf) | 原创图表与中文讲解备注 |
| [原文方程与图号对照](../../literature/各向异性Eliashberg方程与原图对照.md) | 已核对 arXiv v1 页码，非全文翻译 |
| [Fig. 6(a) 复现项目](../../reproductions/02_mgb2_imaginary_gap/README.md) | 已立项，尚未取得材料核或定量复现原图 |
| [数值报告](results/validation.json) | 固定参数、残差、Tc 区间与未完成事项 |
| [来源清单](source_manifest.json) | 原文链接、版本、阅读副本哈希与复用边界 |

## Windows 快速开始

在本目录打开终端。已安装 Python 3.12 时可执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe run_learning.py
.\.venv\Scripts\python.exe build_notebook.py
```

限制线程是小矩阵教学的性能选择，不改变物理模型。没有调用集群，也没有新增 DFT 参数扫描。
测试已在 Python 3.12.4 / NumPy 1.26.4 / SciPy 1.13.1 / Matplotlib 3.8.4 实际运行。
Notebook 构建器临时注册当前 Python 的内核并自动清理，不修改全局内核。

交互修改时，显式注册自己的环境并在 Jupyter 中选择“超导双带学习”：

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --user --name superconductor-two-band --display-name '超导双带学习'
.\.venv\Scripts\python.exe -m jupyter lab 双带Eliashberg交互教程.ipynb
```

不要只根据终端已激活环境判断 Notebook 用的是哪个 Python。
Linux/macOS 使用 `.venv/bin/python`，环境变量设置改为 `export OPENBLAS_NUM_THREADS=1`。

## 已得到的固定模型结果

DOS 权重 `(0.4, 0.6)`；耦合矩阵 `[[1.0, 0.18], [0.12, 0.6]]`；
共同 Einstein 能量 10 meV；μ* 每行和 0.1；96 正虚频；库仑截止 100 meV。

| 对象 | 实际结果 |
|---|---|
| 双带有限模型 Tc 区间 | [10.09155, 10.09717] K |
| 同平均 λ=0.904 的各向同性模型 | [7.87915, 7.88477] K |
| 4 K 时两带 Δ(iw₀) | 1.86538 / 0.87471 meV |
| 单带极限矩阵作用最大误差 | 1.67×10^-16 |
| 温度演示最大原能隙残差 | 小于 10^-8 meV |

这说明在**这个固定模型**中，先平均相互作用再求解不同于保留双带求解。
不是“各向异性必然提高 Tc”的普遍定理，也不是 MgB₂ 的两个实验能隙。
温度是物理变量，演示采用 9 个预设温度加临界区间高温端的正常点，不扫描密度、截断能或展宽。
10 K 接近临界点，实际需要约 4923 次混合迭代；演示上限 10000，残差标准未放宽。

## 验证与范围

19 项测试包括目标带 DOS、加权互易关系、完整正负频率求和、库仑截止跨越、
解析单带矩阵、带标签置换、线性/非线性解耦极限、Tc 两端、独立非线性原方程残差和失败输入。
每个参数和结果都可以离线重建。详细解释见教程，不要求先安装 QE/EPW。
连通分组按当前温度实际有效的核识别；库仑窗口为空时，不把被截止的库仑项当作带间连接。

未完成：无限虚频截止极限、实轴解析延拓、带内 k 分布、材料 α²Fᵢⱼ、
MgB₂ 第一性原理运行和原论文定量图表复现。
绘图的两条曲线不是原论文散点云的复制；仓库未复制论文 PDF 或原图。
