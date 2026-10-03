# 第一课：BCS 能隙方程与数值验证

[仓库首页](../../README.md) · [详细教程](BCS理论与计算入门教程.md) · [交互 Notebook](BCS入门交互教程.ipynb) · [验证报告](验证报告.md)

目标是理解配对 Hamiltonian 如何得到能隙方程，并亲手计算能隙、临界温度与态密度。这是常态密度、各向同性、有限截断的 BCS 平均场基准。

## 配套材料

| 文件 | 用途 |
|---|---|
| BCS理论与计算入门教程.md | 中文推导、算法、单位、图像解读、练习与答案 |
| BCS入门交互教程.ipynb | 小段代码逐步执行，包含已执行输出 |
| bcs.py | 模型、数值积分、求根、态密度与单位换算 |
| run_bcs.py | 重建所有 CSV、PNG 和机器可读验证记录 |
| test_bcs.py | 解析极限、单调性、端点、归一化与输入检查 |
| requirements.txt | 经验证的核心依赖及 Notebook 依赖范围 |
| results/ | 已生成的学习结果，CSV 表头明确单位 |
| [配套 PPTX](../../slides/BCS超导理论与计算入门.pptx) | 可编辑文字、图形与逐页讲解备注 |
| [PPTX 生成源码](../../slides/build_bcs_deck.js) | 从本例结果重建课件 |

## 本地运行

推荐 Python 3.12。Windows PowerShell：

~~~powershell
cd H:\github\work_superconductor\examples\01_bcs_gap
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_bcs.py
.\.venv\Scripts\python.exe -m unittest -v test_bcs.py
.\.venv\Scripts\python.exe -m jupyterlab
~~~

Linux/macOS：

~~~bash
cd examples/01_bcs_gap
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_bcs.py
.venv/bin/python -m unittest -v test_bcs.py
.venv/bin/python -m jupyterlab
~~~

现有环境已具备依赖时，可直接运行后三个命令。Jupyter 中选择相同 Python 环境的 kernel；不一致时先用下面命令注册，再选择 bcs-course：

~~~bash
python -m ipykernel install --user --name bcs-course
~~~

更改参数时指定另一输出目录：

~~~bash
python run_bcs.py --coupling 0.18 --cutoff-mev 20 --out results_g018
~~~

coupling 是 g=N_single_spin(0)V；cutoff-mev 只做单位换算。默认 20 meV 和 g=0.30 是演示参数，不能据此认定某个材料的 Tc。

学习顺序：教程第 1–6 节理解方程，第 7–10 节运行并解释图像，第 11–13 节完成验证与练习。最后用 PPTX 复述推导，再独立更改参数。
