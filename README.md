# 超导理论、计算与文献复现

Superconductivity: Theory, Computation and Literature Reproduction

本仓库用于积累超导体的理论学习笔记、计算方法、文献阅读记录与可复现案例。内容以中文为主，保留英文概念名称，覆盖声子介导与非声子候选机制，并逐步连接模型计算和真实材料计算。

当前已有 **BCS 与 BdG 两套详细中文教程、Python、已执行 Notebook、配套 PPTX/PDF 和数值验证**，
以及参考 HostBridge 在 IQ 集群完成的 **Al SCF + Γ 点 DFPT + ASR 冒烟测试、波函数截断能扫描和 k 网格 × 冷展宽交叉扫描**。
金属积分学习包也配有中文教程、已执行 Notebook、14 页 PPTX/PDF 与原始日志。
已保存输入、小型原始日志、版本和 JobID。**尚未完成全 EPC/Tc 材料预测或原论文定量图表复现。**

## 第一套学习包

| 材料 | 入口 | 用法 |
|---|---|---|
| BCS 详细教程 | [BCS 理论与计算入门](examples/01_bcs_gap/BCS理论与计算入门教程.md) | 符号、假设、推导、算法、练习及答案 |
| 可运行代码 | [BCS 案例入口](examples/01_bcs_gap/README.md) | 环境安装、生成图表、7 项检查 |
| 交互学习 | [BCS Notebook](examples/01_bcs_gap/BCS入门交互教程.ipynb) | 已逐格执行，可修改参数 |
| 配套课件 | [33 页 PPTX](slides/BCS超导理论与计算入门.pptx) | 中文为主，每页有讲解备注 |
| 第一性原理 | [集群入门教程](examples/02_qe_al_smoke/第一性原理与集群入门.md) | 逐项解释 QE 输入、输出和收敛 |
| 真实测试 | [Al 集群记录](examples/02_qe_al_smoke/集群测试记录.md) | JobID 313274 / 313279 均已完成 |
| 开放教材 | [教材副本与复用说明](resources/开放教材与复用说明.md) | 两份 MIT OCW 原始 PDF，含许可与哈希 |

推荐顺序：先看课件结构，读 BCS 推导，运行 Notebook，独立重建并检验结果，
最后阅读 Al 集群日志。第一次的目标是完成一个“理论 → 代码 → 验证 → 解释”的小闭环。

## 第二套学习包

| 材料 | 入口 | 完成状态 |
|---|---|---|
| BdG 详细教程 | [BdG 理论与计算入门](examples/03_bdg_uniform/BdG理论与计算入门教程.md) | 基底、推导、边界、LDOS、练习与答案 |
| 代码与验证 | [BdG 案例](examples/03_bdg_uniform/README.md) | 11 项测试，解析误差约 10^-15 |
| 交互练习 | [BdG Notebook](examples/03_bdg_uniform/BdG入门交互教程.ipynb) | 8 个代码单元已执行 |
| 配套课件 | [30 页 PPTX](slides/BdG超导理论与计算入门.pptx) / [PDF](slides/BdG超导理论与计算入门.pdf) | 每页有中文讲解备注 |
| 材料收敛 | [Al 截断能教程与实测记录](examples/04_qe_al_cutoff/Al截断能收敛教程与记录.md) | JobID 313292，5 组 SCF 均完成 |

BdG 案例输入固定 Δ，不计算 Tc，也不是无自旋 Kitaev 链。
Al 的 30 Ry 相对 80 Ry 总能差为 0.793 meV/原子，仅满足当前固定参数下的有限参考总能判据。
**尚未完成 k 网格、展宽、ecutrho、有限 q 声子或 EPC/Tc 收敛。**

## 第三套学习包

| 材料 | 入口 | 完成状态 |
|---|---|---|
| 金属积分教程 | [Al 金属 k 网格与展宽收敛](examples/05_qe_al_kmesh_smearing/Al金属k网格与展宽收敛教程.md) | 费米面、单位、交叉设计、能量定义与联合判据 |
| 代码与验证 | [Al 金属收敛案例](examples/05_qe_al_kmesh_smearing/README.md) | 8 项测试，原始日志可离线重新分析 |
| 交互练习 | [Al 收敛 Notebook](examples/05_qe_al_kmesh_smearing/Al金属收敛交互教程.ipynb) | 6 个代码单元已执行 |
| 配套课件 | [14 页 PPTX](slides/Al金属k网格与展宽收敛入门.pptx) / [PDF](slides/Al金属k网格与展宽收敛入门.pdf) | 每页有中文讲解备注 |
| 集群实测 | [12 组扫描记录](examples/05_qe_al_kmesh_smearing/集群测试记录.md) | JobID 313714 已完成，27 个来源文件有校验值 |

网格为 8³、12³、16³、20³，冷展宽为 0.020、0.010、0.005 Ry。
**扫描已完成，但三个展宽平面均无通过预设联合阈值的非参考网格；不能宣称电子积分已收敛。**
20³ 只是各展宽的有限参考。下一轮优先测试更密网格，再复核截断能、电荷密度截断和几何。

## 学习导航

| 目标 | 入口 | 当前内容 |
|---|---|---|
| 安排学习顺序 | [超导计算学习路线](docs/超导计算学习路线.md) | 基础理论、数值练习、材料计算与复现阶段 |
| 认识各种配对机制 | [非声子介导超导机制综述](docs/theory/非声子介导超导机制综述.md) | 物理图像、机制证据、近似范围与参考文献 |
| 选择计算方法 | [计算方法与工作流](docs/computation/计算方法与工作流.md) | BCS、BdG、GL、EPC/Eliashberg、Hubbard 与多体方法 |
| 开始读论文 | [文献索引](literature/文献索引.md) | 已有综述与代表性机制论文，按用途导航 |
| 记录论文理解 | [文献阅读模板](templates/文献阅读模板.md) | 研究问题、假设、推导、证据和疑问 |
| 建立复现项目 | [文献复现指南](reproductions/README.md) | 选题、文件组织、误差对比和完成标准 |
| 保存复现过程 | [复现记录模板](templates/复现记录模板.md) | 版本、输入、运行命令、原文目标和验证结果 |

## 仓库组织

```text
docs/
  超导计算学习路线.md
  theory/                    理论与配对机制
  computation/               计算方法与工作流
literature/                  文献索引与后续阅读笔记
reproductions/               每篇论文或基准问题的独立复现目录
templates/                   阅读与复现模板
examples/01_bcs_gap/          BCS 教程、代码、Notebook 与结果
examples/02_qe_al_smoke/      Al SCF/Γ 声子/ASR 输入与实测记录
examples/03_bdg_uniform/      固定均匀 s 波 BdG、LDOS 与解析验证
examples/04_qe_al_cutoff/     Al 截断能扫描输入、原始日志与汇总
examples/05_qe_al_kmesh_smearing/  Al 金属积分交叉扫描、教程与实测证据
slides/                      中文课件、讲解备注与生成源代码
resources/                   许可明确的教材副本及来源清单
```

建议先完成 BCS 能隙方程与简单 BdG 的数值基准，再分流到 `DFT → DFPT → EPC → Eliashberg` 或 `Wannier → 相互作用模型 → 两粒子顶角 → 配对分析`。详细任务和验收点见学习路线。

## 内容维护

- 理论结论注明模型、假设、能标与参考来源；区分实验观测、理论解释和个人推断。
- 新复现项目注明状态：计划中、进行中、部分复现、已复现或暂时阻塞。只在完成对比与误差分析后标记“已复现”。
- 输入、脚本和小型结果表可入库；大型原始输出存外部目录，并记录下载地址、文件校验值与生成方法。
- 文献优先保存 DOI、arXiv 或作者公开链接。引入第三方代码、数据和图像时记录来源与许可。
- 每个可运行案例单独固定软件版本、环境和依赖；目前无全仓库统一运行环境。

## 近期任务

- [x] 完成 BCS 自洽能隙方程的温度扫描与弱耦合极限验证。
- [x] 完成 Al SCF、Γ 点 DFPT 与 ASR 集群冒烟测试。
- [x] 完成 Al ecutwfc 单变量扫描及有限参考总能误差分析。
- [x] 完成 Al k 网格 × 冷展宽交叉实验及联合判据分析，诚实保留未通过结果。
- [ ] 扩展更密 k 参考，完成 smearing、ecutrho 与几何验证，再转向有限 q。
- [x] 完成均匀 s 波 BdG 谱、LDOS 与解析解的比较。
- [ ] 按 EPW 官方教程开展 Pb/MgB2 计算，记录网格和展宽收敛。
- [ ] 建立二维 Hubbard 模型的正常态易感率与配对通道练习。
- [ ] 选定一篇原始论文和一个具体图/表，建立首个文献复现目录。

整理日期：2026-10-03。原机制综述的文献检索范围见其文首说明。
