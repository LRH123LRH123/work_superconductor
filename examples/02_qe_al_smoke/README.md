# 铝的第一性原理与集群入门

这是在 IQ 集群真实执行的小型 Quantum ESPRESSO（QE）测试，不是完整材料超导预测。
先完成 [BCS 教程](../01_bcs_gap/README.md)，再读 [第一性原理与集群入门](第一性原理与集群入门.md)。

## 本例会做什么

- pw.x：fcc Al 单原子原胞的自洽场（SCF）计算。
- ph.x：Γ 点密度泛函微扰理论（DFPT）声子。
- dynmat.x：声学和规则（ASR）后处理，不覆盖原始动力学矩阵。
- 保存输入、提交脚本、小型原始输出、软件版本、JobID 和伪势校验值。

主测试 JobID **313274** 已 COMPLETED，ExitCode=0:0。
SCF 在 5 次迭代后收敛，总能量 −39.50303902 Ry。
原始 Γ 点三个频率都是 −3.374924 cm⁻¹；这是未施加 ASR 的原始结果，需要保留和解释。
ASR 测试的最终结果见 [集群测试记录](集群测试记录.md)。

## 文件

| 文件 | 用途 |
|---|---|
| scf.in | 晶体、赝势、截止能、k 网格与金属占据 |
| ph.in | Γ 点 DFPT 设置 |
| submit.sh | 4 MPI、8 GB、20 分钟的主测试 |
| dynmat.in | crystal ASR 后处理 |
| submit_asr.sh | 单核、1 GB、5 分钟的后处理测试 |
| check_results.py | 从原始日志提取完成标记、SCF、频率和警告 |
| results/ | 已完成测试的原始文本和状态快照 |

输入绑定测试集群路径。换集群时必须调整 pseudo_dir、module、partition、account。
赝势未随仓库再分发，使用集群已有文件并记录 SHA256。不能只替换名字而忽略泛函、价电子和赝势类型。

## 本地查看结果

~~~powershell
python check_results.py
~~~

## 集群运行

进入一个新的独立计算目录，复制输入和脚本，确认伪势存在。不要在已保存的基准目录覆盖输出。

~~~bash
sbatch submit.sh
# 主任务完成且 al.gamma.dyn 存在之后，才运行后处理。
sbatch submit_asr.sh
~~~

提交不是计算完成。记录返回的 JobID，并查看该任务的 output、phonon.output、slurm-JobID.out/err。
本仓库使用 [HostBridge](https://github.com/LRH123LRH123/HostBridge) 的 Direct MCP Task Runner 提交与读取；
服务器操作规范以 HostBridge 的 cluster/CHATGPT_QUICKSTART.md 和 docs/COMPUTE_CONVENTIONS.md 为准。
