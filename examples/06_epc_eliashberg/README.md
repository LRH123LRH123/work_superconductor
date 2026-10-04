# 电子声子耦合与 Eliashberg 学习包

[返回仓库首页](../../README.md) · [详细教程](电子声子耦合与Eliashberg入门教程.md) · [结果对照](学习结果与基准对照.md)

本课把 BCS/BdG 与材料 EPC 连接起来，不继续 k 网格、截断能或展宽收敛扫描。
它包含三种不同证据，不能相互替代：

| 练习 | 数据与方法 | 已完成什么 | 不代表什么 |
|---|---|---|---|
| Al 谱函数 | 许可明确、版本固定的 QE 官方参考数据 | 离线计算 λ、谱矩、近似 Tc；重建参考积分 | 不是之前 Al SCF 作业产生的 EPC |
| Einstein 模型 | 原创 Python 虚轴各向同性求解器 | 线性不稳定性、非线性 Δ/Z、有限频率 Tc 区间 | 不是 Pb，也不是完整 EPW 求解器 |
| Pb 官方回归 | 集群重新运行 SCF/NSCF/EPW，复用上游 DFPT 数据 | 固定 3³→6³ 插值和 λ 基准对照；313836 完成 | 不是从零计算全部 DFPT，不是收敛材料 Tc |

## 配套材料

- [中文详细教程](电子声子耦合与Eliashberg入门教程.md)：物理、公式、单位、算法、代码导读、练习及答案。
- [已执行 Notebook](EPC与Eliashberg交互教程.ipynb)：8 个代码单元，从文件积分到真实日志核验。
- [20 页 PPTX](../../slides/电子声子耦合与Eliashberg计算入门.pptx) / [PDF](../../slides/电子声子耦合与Eliashberg计算入门.pdf)：每页附中文讲解备注，图由本课数据生成。
- [Pb 固定参数流程](Pb固定参数计算流程.md) / [真实集群记录](集群测试记录.md)：输入、日志、重试原因与参数边界。
- [来源与许可](reference/来源与许可.md)：官方原始数据、输入、基准和 GPL 许可；不复制许可不明的第三方 PPT。
- [文献阅读与复现任务](../../literature/Eliashberg方法文献阅读与复现目标.md)：先复现方程极限，再选原论文图表。

## 第一次运行

使用 Python 3.11 或 3.12。在本案例目录打开终端，先建立独立环境，避免改变原有计算环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe run_learning.py
.\.venv\Scripts\python.exe build_notebook.py
.\.venv\Scripts\python.exe -m ipykernel install --user --name sc-epc --display-name "Superconductor EPC"
.\.venv\Scripts\python.exe -m jupyterlab
```

`build_notebook.py` 会用当前 Python 注册临时、唯一内核并从头执行，覆盖本课 Notebook。
运行前若已修改 Notebook，请先用不同名称保存自己的练习版本。
交互打开时在内核菜单选择 **Superconductor EPC**，确保不是其他全局 Python 环境。
测试应为 **20 项通过**；生成 `results/validation.json`、温度结果 CSV 和四幅图。
本地复算不需要登录集群或下载大文件。

分析自己的标准数字表必须明确单位及列号：

```powershell
python analyze_spectrum.py reference/qe-7.5/PHonon/examples/tetra_example/reference/aluminum.a2F.dat --unit Ry --column 1
python analyze_spectrum.py cluster/pb_regression/results/pb.a2f.01.300.000 --unit meV --column 1 --format epw_legacy --moments-only
```

列号从 0 开始，0 为能量，1 为第一列 α²F。
`--format epw_legacy` 显式验证旧版 EPW 文件尾部；不猜单位、不丢弃未知文字、不剪裁负值。
近似 Tc 默认 μ*=0.1，仅作为公式示例；Pb 回归用 `--moments-only`，不输出材料 Tc。

## 建议的学习节奏

1. 第一节：理解 EPC 与 α²F，手算单位换算和 λ，重建 Al 参考输出。
2. 第二节：区分 Allen-Dynes 公式与方程求解，推导正频率折叠。
3. 第三节：读 `linearized` 和 `solve_gap`，解释本征值、残差与正常态。
4. 第四节：逐项对照 Pb 原始输入、Slurm 状态及基准，完成教程练习。
5. 第五节：按文献任务单写自己的方程对照记录，不急着宣称原论文图表已复现。

验收不是记住一个 Tc，而是能够独立说明：数据来自哪里、程序解了什么、哪些证据还没有。

整理日期：2026-10-04。
