# 第四案例：Al 波函数截断能收敛入门

[返回首页](../../README.md) · [逐步教程与实测结果](Al截断能收敛教程与记录.md)

本案例接续 Al SCF/Γ 声子冒烟测试，完成一次真实集群 **ecutwfc 单变量扫描**。
JobID **313292**，2026-10-03，状态 COMPLETED，ExitCode 0:0，耗时 18 秒。
程序 Quantum ESPRESSO 7.5，4 MPI ranks。

ecutwfc=30/40/50/60/80 Ry；固定 ecutrho=640 Ry、8×8×8 k 网格、mv smearing 0.02 Ry，
固定晶格和同一 PAW 赝势。每组使用独立 scratch。
**这是总能有限参考测试，不是完整材料收敛或 Tc 预测。**

## 本地分析

已有原始输出，无需连接集群即可重新收集与画图：

~~~powershell
python -m unittest test_collect.py -v
python collect_results.py
~~~

依赖 NumPy 1.26.4 和 Matplotlib 3.8.4，可使用 BdG/BCS 的科学 Python 环境。
报告默认阈值 1 meV/原子；例如重新分析更严格的 0.1 meV/原子目标：

~~~powershell
python collect_results.py --tolerance-mev 0.1
~~~

此命令会更新本地 results，默认归档值使用 1 meV/原子。恢复时再次运行默认命令。

## 集群重跑

参照 [HostBridge 计算约定](https://github.com/LRH123LRH123/HostBridge/blob/main/docs/COMPUTE_CONVENTIONS.md)
先检查当前可用分区、模块和赝势；不要假设本次 iq-main 永远可用。
按自己的账户与集群修改 submit.sh、每组输入中的 pseudo_dir，使用新的独立工作目录。
若已获取 JobID，不要因尚无输出重复提交。

赝势没有随仓库再分发。文件名、集群路径和 SHA256 见 [cluster_record.json](results/cluster_record.json)；
应按原来源和许可准备完全相同的文件，或明确记录替换来源与差异。

原始 pw.x 输出在各 ecut_*/output，输入在 scf.in。
调度输出、校验记录、汇总表和图在 results。
