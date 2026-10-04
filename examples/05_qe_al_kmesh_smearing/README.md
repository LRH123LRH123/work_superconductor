# 第五案例：Al 的 k 网格与展宽交叉测试

[返回首页](../../README.md) · [详细中文教程](Al金属k网格与展宽收敛教程.md) · [实测记录](集群测试记录.md) · [交互 Notebook](Al金属收敛交互教程.ipynb)

接续波函数截断能案例，以同一 Al fcc 结构、同一赝势做 12 组 SCF：
4 种 k 网格 × 3 种 cold-smearing 展宽。
目标是学习怎样读真实结果、识别假收敛，而不是保证这组网格必然足够。
**未计算声子、EPC 或 Tc，也未外推到零展宽。**
实际 JobID 313714 已完成全部 12 组；三个展宽平面均无通过预设联合阈值的非参考网格。
因此本课的状态是“实验完成，电子积分尚未证明收敛”，详见实测记录。

## 本地运行

无需连接集群，本目录保存完整小型输入和输出。
可以沿用前两课的 Python 环境，或新建环境：

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest test_scan.py -v
.\.venv\Scripts\python.exe collect_results.py
.\.venv\Scripts\python.exe -m jupyterlab
~~~

最后打开本目录 Notebook；新环境需选择对应内核。
build_notebook.py 使用默认 python3 内核自动重建并执行，会覆盖教学 Notebook。
个人练习请保存至另一个文件。完整交叉数据缺一组，分析器拒绝给出完整扫描结论。

## 文件作用

| 文件 | 用途 |
|---|---|
| scan_plan.json | 事先写定的 12 组参数和误差阈值 |
| k08_s020 等目录 | 各组 scf.in 与原始 output；s020 代表 0.020 Ry |
| submit.sh | 单次 Slurm 提交，顺序运行 12 组 |
| collect_results.py | 输出解析、输入契约、同展宽比较、绘图 |
| test_scan.py | 8 项自动测试，包括不完整/不一致/非单调与本征求解警告 |
| results/cluster_record.json | 实际作业状态与来源 SHA256 |
| results/validation.json | 参数、逐组观测量、有限参考判据 |
| results/kmesh_smearing_scan.csv | 可自行重新作图的数据 |

配套 [PPTX](../../slides/Al金属k网格与展宽收敛入门.pptx) 与 [PDF](../../slides/Al金属k网格与展宽收敛入门.pdf)。
重新提交时请检查当前分区、模块、账户和赝势，使用新工作目录。
本次使用的 iq-maiagv 不是永久默认分区，赝势没有随仓库再分发。

## 练习验收

手算一组能差，解释一个失败阈值，区分 F、internal E 和 -TS，
说明为什么减小 degauss 必须同时检查 k 网格。能说明“这批数据还不能证明什么”才算完成学习。
