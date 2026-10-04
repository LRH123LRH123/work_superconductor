# Pb 固定参数计算流程

[学习入口](README.md) · [集群实测](集群测试记录.md)

## 一、现在已经跑通的小型回归

这条路线适合学习文件关系、输出检查和标量基准，不适合给真实材料出 Tc。
上游是 QE `test-suite/epw_metal/epw1.in`；不是大型超导教程的替代品。

| 阶段 | 输入 | 本次执行 | 解释 |
|---|---|---|---|
| 上游 DFPT 数据 | 固定提交的 `save/` | 下载且哈希验证 | 动力学矩阵、势导数由上游提供 |
| SCF | `scf.in` | 集群 pw.x | 基态电荷与势，3³ k |
| NSCF | `nscf.in` | 集群 pw.x | 显式完整 27 k 点，供 Wannier 化 |
| Wannier 与 EPC | `epw.in` | 集群 epw.x | Pb:sp3，4 个子空间轨道，粗 3³→细 6³ |
| 结果检查 | `validate_epw.py` | 集群及本地 | 正常结束、有限值、λ、500 行谱及尾部 |
| 基准对照 | `run_learning.py` | 本地 | λ 对照官方参考；没有材料 Tc 求解 |

固定 ecutwfc=60 Ry、celldm(1)=9.27 bohr、一个 fcc Pb 原子。
标量相对论（Scalar Relativistic）赝势，无自旋轨道耦合（Spin-Orbit Coupling, SOC）。
SCF degauss=0.025 Ry、NSCF degauss=0.02 Ry，保留上游不同阶段设置，未拿它们做比较扫描。
EPW fsthick=6 eV、degaussw=0.1 eV、degaussq=0.05 meV、temps=300 K。
300 K 是此回归散射设置，不是求得的超导 Tc。

### 如何重新准备

在集群选择一个**新的独立目录**，放入以下文件：

- `cluster/pb_regression/prepare_cluster.py`
- `cluster/pb_regression/submit.sh`
- `cluster/pb_regression/validate_epw.py`
- `reference/source_manifest.json`，在运行目录中命名为 `source_manifest.json`

进入该目录：

```bash
/home/runhan/anaconda3/bin/python prepare_cluster.py
sbatch submit.sh
```

准备脚本下载固定提交参考，验证字节数/哈希，生成路径调整后的 LF 输入。
首次需要允许访问官方原始下载 URL，已下载文件会重新校验。
脚本只复用同版本官方 DFPT，不调用 ph.x 重算。
不要在已归档目录重新运行来覆盖原作业，也不要借用旧 JobID。

提交脚本按 HostBridge 当前约定使用 job-name=test、iq-main、4 MPI、单线程、8 GB、2 小时上限。
实际队列选择仍需查当时资源；不能因为本次可用就说以后永远优先。
Python 路径和 module 是本集群实例参数，在别的集群要先确认，再运行。
`set -euo pipefail` 捕获程序非零退出；PW 用 JOB DONE 与 SCF 标记；EPW 使用自己的检查器。

运行后至少检查 Slurm 状态、退出码、stderr、SCF/NSCF/EPW 完整输出、谱和源文件哈希。
技术成功与 λ 回归成功是两条检查，不等同于材料精度。

## 二、从零材料计算的完整流程：尚未执行

未来不做密度/截断扫描的情况下，可选择**官方固定设置教学复跑**，明确不作收敛认证。
这与当前小回归是不同任务，不能只把 Nk 改大就声称两者等价。
当前 [官方 Pb/MgB2 教程](https://docs.epw-code.org/tutorials/tutorial_04/index.html) 以 Pb 各向同性和 MgB2 各向异性为路径，
此处只整理执行检查点，未复制其全部文字或未验证的大型输入。

1. 固定结构、赝势、SOC/标量相对论选择和版本。记录官方原始输入与许可，确认不同阶段使用同一套约定。
2. SCF 保存电荷密度、波函数和实际 DOS/费米能信息；之后不擅自换结构或赝势。
3. DFPT 在指定粗 q 上计算完整响应，检查虚频、声学模式和电荷/势的一致性。只算 Γ 不等于完整 q 空间。
4. 按教程整理 dynamical matrices 与 dvscf 文件；完整 k 的 NSCF 与粗 k/q 必须满足工具要求。
5. Wannier 化，比较目标能区的插值能带与原始能带。轨道投影和 spread 是证据，不只看 Wannier 程序结束。
6. EPC 插值生成指定谱，确认文件列、单位、展宽、费米窗、DOS 和所选自能近似。
7. 在固定 μ* 及截止约定下做各向同性虚轴 Eliashberg，保留温度点和方程残差。
8. 与同一官方案例的同一对象比较，标注教学复跑、未验证收敛、不作真实材料预测。

官方当前 Pb 教程使用比本回归大得多的设置；其 SCF 8³、粗电子/声子 6³、细电子 48³、细声子 24³
只是该来源案例的参数，不是本课测出来的推荐，也未在本轮提交。
不要把该教程的 λ≈1.15836 与我们粗回归 λ≈0.16088 直接视为程序错误或精度通过。

## 三、什么时候转向 MgB2

先能解释“各向同性平均会丢掉哪些 k/带信息”，再考虑多带各向异性。
MgB2 的双能隙（Two-Gap Superconductivity）不能由一个标量 λ 或单条 Einstein 曲线直接恢复。
需要保留带/费米面分辨的配对核和 Δ，并审查模型与材料步骤。
本课先推进文献方程对照，不自动提交大型 MgB2 计算。
