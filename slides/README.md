# BCS 超导理论与计算入门课件

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
