# BdG 课件检查记录

日期：2026-10-03。文件：[BdG PPTX](BdG超导理论与计算入门.pptx) / [PDF 阅读版](BdG超导理论与计算入门.pdf)。
生成器 PptxGenJS 4.0.1，封装检查 JSZip 3.10.1。16:9；中文为主，保留英文概念名称。

## 实际执行

- PowerPoint 原生后台打开并导出全部 30 页 PNG 与 30 页 PDF。
- PowerPoint 读取确认 30 页均有较完整讲解备注。
- Office Open XML 结构验证通过；ZIP 完整性、页数、表格锚点及元素边界检查通过。
- 第一轮人工浏览全部 30 页缩略图，重点放大公式、代码和数据页。
- 修复第 2 页第三卡片宽度误传导致的纵向排版。
- 修复第 8 页讲解备注与实际单图不一致；修复第 16、17 页公式下标。
- 原生文本边界检查发现第 23 页代码框约 2.4 pt 高度溢出，已扩展框高。
- 重新导出并检查修正页；最终原生检查报告文本边界溢出为 0。
- PDF 共 30 页，每页均可提取文字。

全体模型图与收敛图由配套程序生成，不借用第三方论文图。
文字、公式文字、表格及大部分示意元素可编辑；程序生成图像为 PNG。
完整 LaTeX 推导在 [中文教程](../examples/03_bdg_uniform/BdG理论与计算入门教程.md)，
避免把 PPT 的紧凑行内写法当作唯一符号定义。

## 物理内容检查

明确声明固定 Δ、自旋单态约化块、单自旋 LDOS、全谱求和一次。
约化块 C=τ_yK 与基底一起说明，不写成所有 BdG 的通用表示。
标量杂质不用于演示 YSR 或 Majorana；展宽尾部与 gap 内本征态区分。
Al 数据明确标为 80 Ry 有限参考总能扫描，不标记为声子/EPC/Tc 已收敛。

字体为 Microsoft YaHei、Cambria Math 和 Consolas；其他系统替换字体后应重新检查。
原生文本边界检查不替代人工视觉检查，也不构成数学或材料结论的完整证明。

## 重复检查

先生成两案例的结果，再在 slides 目录运行：

~~~powershell
npm run build:bdg
.\render_slides.ps1 -Deck .\BdG超导理论与计算入门.pptx -OutDir .\preview_bdg
~~~

仓库完整性检查：

~~~powershell
python tools/validate_learning_package.py
~~~

后一条从仓库根目录执行，覆盖两课 Notebook、数值报告、材料日志哈希、63 页课件备注与边界。
