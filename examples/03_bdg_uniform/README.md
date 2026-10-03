# 第二课：BdG 均匀 s 波模型

[返回首页](../../README.md) · [详细中文教程](BdG理论与计算入门教程.md) · [交互 Notebook](BdG入门交互教程.ipynb) · [课件](../../slides/BdG超导理论与计算入门.pptx)

这套案例接续 BCS 能隙方程：先输入固定 Δ，再研究准粒子谱、边界和局域态密度。
**不求自洽 Δ，不计算 Tc，不模拟拓扑超导，也不是某篇论文的定量复现。**

## 运行

在本目录打开终端。Windows PowerShell 示例：

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest test_bdg.py -v
.\.venv\Scripts\python.exe run_bdg.py
.\.venv\Scripts\python.exe -m jupyterlab
~~~

已有科学 Python 环境时也可直接使用 python。最后一条启动交互界面后打开本目录 Notebook。
如内核不匹配，可在新环境注册内核：

~~~powershell
.\.venv\Scripts\python.exe -m ipykernel install --user --name superconductor-bdg --display-name "Superconductor BdG"
~~~

选用对应内核。若使用 build_notebook.py 自动重建，默认 python3 内核须指向同一环境；
该脚本会覆盖教学 Notebook，请先保存个人练习到另一个文件。

~~~powershell
python run_bdg.py --help
python build_notebook.py
~~~

## 文件导航

| 文件 | 作用 |
|---|---|
| bdg.py | 2×2 块、实空间链、解析谱、电子 LDOS |
| test_bdg.py | 11 项自动测试 |
| run_bdg.py | 统一生成五张图、CSV 与数值报告 |
| build_notebook.py | 重建并执行 8 个代码单元 |
| results/validation.json | 本次误差、版本、物理限制 |
| 数值验证与学习记录.md | 验收结果及完成标准 |

默认 N=48、J=1、μ=-0.5、Δ=0.25、η=0.04。
N 是格点数，矩阵维数为 2N；输出是约化自旋单态 BdG 的单自旋电子谱。

## 验收

能够自行说明 Nambu 基底、矩阵负号、±E、电子谱权重和有限尺寸效应，并通过解析解与残差检查，
才算完成本课。只成功运行脚本或观察到一个能隙，不等于识别微观配对机制。
