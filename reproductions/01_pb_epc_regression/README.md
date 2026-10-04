# Pb 官方 EPC 标量基准复现

状态：**固定软件回归的 λ 对照通过；材料精度与原论文图表复现未完成。**
日期：2026-10-04。

本目录建立第一个明确范围的复现记录，运行文件放在配套案例，不重复储存大型数据。
目标不是复现 Pb 实验 Tc，而是同一 QE 官方回归条件下重新得到直接模式/q 求和的 λ。

## 原目标和条件

- 原源：QEF/q-e `test-suite/epw_metal`，qe-7.5 固定提交 `770a0b2d12928a67048e2f3da8d10d057e52179e`。
- 原基准：[benchmark 输出](../../examples/06_epc_eliashberg/reference/qe-7.5/test-suite/epw_metal/benchmark.out.git.inp=epw1.in.args=3)，λ=0.1608789。
- 条件：粗 k/q=3³，细 k/q=6³，60 Ry、标量相对论、无 SOC；复用原 DFPT 保存文件。
- 自有运行：SCF、NSCF、Wannier/EPC；原输入仅改路径并注明上游许可。
- 比较对象：直接 λ 标量，不选择单个 q 的值，也不与生产教程的 λ 混用。
- 容差：后处理阶段固定为 2×10^-6 绝对值，打印精度级对照，不冒称提交前盲设标准，不作物理误差上限。

## 实际结果

本集群 λ=0.1608797，绝对差 8×10^-7，通过。
谱积分约 0.16088553，匹配谱文件尾部，但与直接求和属于不同离散对象。
最终 Job 313836 为 COMPLETED，前两次完成检查错误导致 FAILED，均保留。

[完整输入、作业身份与来源清单](../../examples/06_epc_eliashberg/cluster/pb_regression/results/cluster_record.json)
记录原路径、哈希、字节数及重试状态。
[结果解释](../../examples/06_epc_eliashberg/学习结果与基准对照.md) 与
[集群实测记录](../../examples/06_epc_eliashberg/集群测试记录.md) 说明失败原因和数值警告。

## 限制与后续

没有全面对照所有自能、输运项、能带或 Wannier spread；stderr 的浮点警告仍存在。
没有自有完整 DFPT、生产级 EPC/SOC 误差证据或材料 Eliashberg 解，不能称为完整材料复现。
本项目是官方软件基准，不是 PRB 原论文图号项目。
下一步按 [Eliashberg 文献任务单](../../literature/Eliashberg方法文献阅读与复现目标.md)
选择明确方程/图表和来源，再建立单独项目；当前不扩展 DFT 收敛扫描。
