# 超导理论与计算入门课件

## 材料计算专题：Al 金属收敛

[14 页 PPTX](Al金属k网格与展宽收敛入门.pptx) · [PDF](Al金属k网格与展宽收敛入门.pdf) · [详细教程](../examples/05_qe_al_kmesh_smearing/Al金属k网格与展宽收敛教程.md) · [实测记录](../examples/05_qe_al_kmesh_smearing/集群测试记录.md)

12 组真实 SCF 的 k 网格–展宽交叉实验，解释 F/internal E/类熵项、同展宽有限参考和联合阈值。
14 页均有中文讲解备注。失败判据保留为学习结果，不把参考自身零差称为已收敛。
先在案例目录运行 collect_results.py，再在 slides 目录运行 npm run build:al-convergence。
字体与依赖同下方两课，来源图由本仓库分析器生成。
检查记录见 [Al 课件检查记录](Al金属收敛课件检查记录.md)。

## 第二课：BdG

[30 页 PPTX](BdG超导理论与计算入门.pptx) · [PDF](BdG超导理论与计算入门.pdf) · [详细教程](../examples/03_bdg_uniform/BdG理论与计算入门教程.md) · [已执行 Notebook](../examples/03_bdg_uniform/BdG入门交互教程.ipynb)

每页有中文讲解备注。内容为固定均匀 s 波自旋单态约化块、边界、LDOS 和真实 Al 截断能扫描。
不包含自洽 Δ、拓扑计算或材料 Tc 预测。图片由本仓库程序生成，文字与示意元素可编辑；
完整公式推导见 Markdown 教程。Kwant 官方教程仅作为后续链接，不复制其输运结果。

先运行 examples/03_bdg_uniform/run_bdg.py 与 examples/04_qe_al_cutoff/collect_results.py，
然后在本目录执行 npm run build:bdg。
依赖与字体要求同下方 BCS，另使用 Consolas 显示代码。
原生 PowerPoint 的渲染、备注、结构与版面检查见 [BdG 课件检查记录](BdG课件检查记录.md)。

## 第一课：BCS

[打开 PPTX](BCS超导理论与计算入门.pptx) · [PDF 阅读版](BCS超导理论与计算入门.pdf) · [中文教程](../examples/01_bcs_gap/BCS理论与计算入门教程.md) · [交互练习](../examples/01_bcs_gap/BCS入门交互教程.ipynb)

33 页，16:9，中文为主，保留英文概念名称。每页有讲解备注，适合自学或授课。
内容包括 BCS 模型、平均场推导、数值算法、解析/数值检查，以及 Al 的真实集群冒烟测试。
图片来自配套程序，文字和大部分示意元素可编辑；详细 LaTeX 公式在 Markdown 教程中。

## 如何使用

先快速浏览 PPTX，再对照教程读细节，然后运行 Notebook。
PowerPoint 的“备注”区域有完整讲解与注意事项。
不要把课件中的假设 Ec=20 meV 对应的 9.39 K 当作铝或其他材料的预测。
集群页明确区分原始 Γ 频率与 ASR 后处理，以及跑通与材料收敛。

## 重新生成

先在 examples/01_bcs_gap 生成结果，再在本目录运行：

~~~bash
npm install
npm run build
~~~

已验证使用 PptxGenJS 4.0.1。字体为 Microsoft YaHei 和 Cambria Math；
其他系统若缺少这些字体，可能替换字体，需重新检查排版。
MIT OCW 原教材单独保存在 resources，不是本 PPTX 的页面复制。

render_slides.ps1 可在安装 PowerPoint 的 Windows 上后台导出 PNG 和 PDF。
本次使用 PowerShell 7 执行，中文脚本不建议直接用旧版 Windows PowerShell 5 解析。
原生 PowerPoint 已验证打开、33 页导出和 33 页备注；[检查记录](课件检查记录.md)。
