// Original teaching deck; plots come from the archived SCF scan.
const fs=require("fs"), path=require("path");
const PptxGenJS=require("pptxgenjs"), JSZip=require("jszip");
const pptx=new PptxGenJS();
pptx.layout="LAYOUT_WIDE";
pptx.author="work_superconductor";
pptx.title="Al金属k网格与展宽收敛入门";
pptx.lang="zh-CN";
pptx.theme={headFontFace:"Microsoft YaHei",bodyFontFace:"Microsoft YaHei",lang:"zh-CN"};
const S=pptx.ShapeType;
const C={ink:"183B3C",teal:"117E83",coral:"C55B43",gold:"857140",
         pale:"EDF5F2",paper:"F7F4ED",white:"FFFFFF",muted:"546968"};
const root=path.resolve(__dirname,"..");
const example=path.join(root,"examples/05_qe_al_kmesh_smearing");
const report=JSON.parse(fs.readFileSync(path.join(example,"results/validation.json"),"utf8"));
const record=JSON.parse(fs.readFileSync(path.join(example,"results/cluster_record.json"),"utf8"));
let n=0;
function tx(s,t,x,y,w,h,o={}){s.addText(t,{x,y,w,h,fontFace:"Microsoft YaHei",fontSize:20,
 color:C.ink,margin:0,valign:"top",...o});}
function box(s,x,y,w,h,fill){s.addShape(S.rect,{x,y,w,h,fill:{color:fill},line:{color:fill}});}
function page(title,en,notes,dark=false){
 const s=pptx.addSlide();n++;s.background={color:dark?C.ink:C.paper};
 tx(s,String(n).padStart(2,"0"),.6,.38,.55,.35,{fontSize:17,color:dark?"B1CECA":C.teal});
 tx(s,title,1.15,.34,11.5,.67,{fontSize:32,bold:true,color:dark?C.white:C.ink});
 tx(s,en,1.15,1.07,11.2,.37,{fontSize:13,color:dark?"B1CECA":C.muted});
 tx(s,"work_superconductor  /  Al 材料计算收敛  /  2026-10-03",.6,7.05,12,.25,
    {fontSize:10,color:dark?"B1CECA":C.muted});s.addNotes(notes);return s;
}
function card(s,title,body,x,y,w=3.8,h=3.4,color=C.teal){
 box(s,x,y,w,h,C.white);box(s,x,y,.08,h,color);
 tx(s,title,x+.24,y+.28,w-.48,.65,{fontSize:23,bold:true,color});
 tx(s,body,x+.24,y+1.17,w-.48,h-1.4,{fontSize:19});
}
function banner(s,t){box(s,.6,6.35,12.1,.5,C.pale);
 tx(s,t,.8,6.44,11.7,.3,{fontSize:15,bold:true,color:C.teal});}
function formula(s,t,y=2,w=11.6){box(s,.8,y,w,1.15,C.pale);
 tx(s,t,1.05,y+.25,w-.5,.65,{fontFace:"Cambria Math",fontSize:32,align:"center"});}
function picture(s,name,x=.65,y=1.65,w=12,h=4.65){
 const file=path.join(example,"results",name),b=fs.readFileSync(file);
 const iw=b.readUInt32BE(16),ih=b.readUInt32BE(20),scale=Math.min(w/iw,h/ih);
 s.addImage({path:file,x:x+(w-iw*scale)/2,y:y+(h-ih*scale)/2,w:iw*scale,h:ih*scale});
}
function table(s,rows,widths,y=1.85,h=4.1){
 s.addTable(rows,{x:.7,y,w:11.9,h,colW:widths,fontFace:"Microsoft YaHei",fontSize:19,
 color:C.ink,fill:C.white,margin:.13,rowH:.6,valign:"middle",autoPage:false,
 border:{type:"solid",color:"D8E2DC",pt:.8}});
}

let s=page("Al 金属 k 网格与展宽收敛","Metallic k-point sampling and cold smearing",
 "本课是已有 Al 截断能案例的后续材料计算实验，目标是学习按原始数据判断收敛。使用四种 k 网格和三种冷展宽组成完整交叉设计。所有图由配套分析器从真实集群日志生成。本课不计算声子、电子–声子耦合或临界温度，也不保证所选网格必然足够。",true);
tx(s,"不是找一个漂亮数字，\n而是建立可信的误差证据。",.9,2.15,11.5,1.65,
 {fontSize:36,bold:true,color:C.white});
tx(s,"12 组真实 SCF  /  JobID "+record.job_id+"  /  固定 60/640 Ry",.95,4.6,11.4,.6,
 {fontSize:23,color:"B1CECA"});
box(s,.95,5.8,4,.15,C.teal);box(s,5.1,5.8,4,.15,C.coral);

s=page("三种收敛，不要混成一种","Iteration, basis set and Brillouin-zone sampling",
 "SCF 收敛描述固定参数下迭代方程被求解到阈值，不能消除基组截断或 k 点采样误差。上一案例只扫描波函数截断，本课扫描金属积分。更后面的声子与 EPC 还有各自网格、展宽和插值误差。任何单一成功标志都不能替代这些分层验证。");
card(s,"SCF 迭代","accuracy / residual\n固定问题是否求稳",.7,2);
card(s,"平面波基组","ecutwfc / ecutrho\n截断近似是否够用",4.78,2,3.8,3.4,C.gold);
card(s,"金属积分","k mesh / degauss\n费米面是否采样充分",8.86,2,3.8,3.4,C.coral);
banner(s,"SCF 达标、基组收敛、k 采样收敛与声子 / EPC / Tc 收敛是不同检查。");

s=page("金属费米面让积分更敏感","Fermi-surface sampling",
 "金属有穿越化学势的能带，零温占据在费米面不连续。有限 k 点对费米面的采样位置会影响积分，网格加密误差未必严格单调。程序利用对称性约化点数，因此网格大小和不可约点数都需要记录。不同偏移或对称性设置不是同一个积分实验。");
card(s,"零温占据","费米面附近突变\n粗网格可能漏掉细节",.85,2,5.55,3.5);
card(s,"有限采样","N³ 是原始网格\n不等于不可约点数\n固定 shift=1,1,1",6.7,2,5.55,3.5,C.coral);
banner(s,"不要要求结果严格单调；偶然接近参考也可能是假收敛。");

s=page("Ry 不是 eV；冷展宽不是 Tc","Smearing width and physical temperature",
 "QE degauss 使用 Ry 单位。本课三个宽度分别约零点二七、零点一四和零点零七 eV。冷展宽是积分与占据平滑方法，不能除以 Boltzmann 常数后称为真实电子温度。Fermi–Dirac 占据是另一个选项。这里的展宽也不等于 BdG 的洛伦兹 LDOS 参数。");
table(s,[["degauss / Ry","能量宽度 / eV","本课用途"],
 ["0.020","0.272113862","Cold smearing"],
 ["0.010","0.136056931","金属积分平滑"],
 ["0.005","0.068028466","与 k 网格交叉检验"]],[3.3,4.0,4.6],2.05,3.3);
banner(s,"mv / cold ≠ Fermi–Dirac 温度；degauss ≠ BdG η ≠ Tc");

s=page("4×3 交叉设计，一次只解释一条线","Controlled scan design",
 "四乘三交叉设计使每个展宽平面都有完整网格扫描。横向比较相同 sigma 的 k 点变化，纵向比较固定 k 的展宽敏感性。截断能、赝势、结构、能带数和偏移都固定。显式六条能带等于上一案例默认实际输出，不在这里额外扫描空带需求。");
table(s,[["k mesh","σ=0.020 Ry","σ=0.010 Ry","σ=0.005 Ry"],
 ["8³","SCF","SCF","SCF"],["12³","SCF","SCF","SCF"],
 ["16³","SCF","SCF","SCF"],["20³","同 σ 参考","同 σ 参考","同 σ 参考"]],
 [2.1,3.26,3.26,3.28],1.8,3.75);
banner(s,"固定 60/640 Ry、nbnd=6、fcc 几何与同一 PAW 文件；每组独立 scratch。");

s=page("先对齐能量定义","Total F, internal E and entropy-like contribution",
 "Quantum ESPRESSO 的此类输出给出 total energy F、smearing contribution C=-TS 和内部能 E。用 E 等于 F 减 C 检查打印一致性。冷展宽中的类熵项不能按真实 Fermi–Dirac 热力学熵解释。跨 sigma 的差不能全部称为零温误差，也不任意套用平均 F 与 E 的所谓修正。");
formula(s,"C = −TS     F = E + C     E = F − C",1.95);
card(s,"同一 σ","比较相同积分问题\n用各自最密 k 作参考",.85,3.8,5.55,2.25);
card(s,"不同 σ","保存 F、E、C\n不直接声称零温外推",6.7,3.8,5.55,2.25,C.coral);

s=page("阈值先写，结论后算","Predeclared joint acceptance criteria",
 "本节事先约定零点一 meV 每原子、零点一 kbar 和五 meV 的三个教学标准。它们不是所有材料任务的通用推荐。候选点及所有更高测试点要同时通过，且不能仅剩参考自己。这样既排除非单调偶然接近，也保留总能通过而压力失败的情况。");
card(s,"0.1 meV / atom","同 σ 的 F 差\n每胞一个原子",.7,2);
card(s,"0.1 kbar","同 σ 的压力差\n独立于总能检查",4.78,2,3.8,3.4,C.gold);
card(s,"5 meV","同 σ 的 Fermi 差\n相同实现内比较",8.86,2,3.8,3.4,C.coral);
banner(s,"20³ 是有限参考；参考差为 0，不等于无限网格误差为 0。");

s=page("热图：只在同一 σ 内比较","Energy error grid",
 "这张热图由所有十二个原始输出计算，每行使用自己的二十立方参考。右列为零是定义。横向看 k 点误差变化，纵向只观察网格与展宽联动，不将不同 sigma 共用能量基线。图中的颜色不能替代压力与 Fermi energy 的额外标准。");
picture(s,"energy_grid.png",.7,1.7,11.9,4.55);
banner(s,"每行有独立参考；不要把跨 σ 基线差当成 k 采样误差。");

s=page("三种观测量可能不同步","Energy, pressure and Fermi-level sensitivity",
 "图的三个面板分别比较 F、压力与 Fermi energy 的同展宽差。虚线为预设阈值。即使总能相对稳定，压力或费米能仍可能敏感。本次明确允许得出没有联合候选的结果，不根据计算成本改动阈值。下一步应由失败观测量决定补算方向。");
picture(s,"kmesh_convergence.png");
banner(s,"每种展宽各自对照 20³；不通过就保留失败证据。");

s=page("固定 k 看 σ：不是零宽极限","Smearing sensitivity at the largest tested grid",
 "固定本次最高 k 点网格绘制三种展宽结果，只能描述敏感性。若最高网格对窄展宽尚未被证明足够，则不能将窄展宽的数值当成更真实结果。图中能差以最小已测 sigma 为绘图基线，不称作零温真实误差，也没有进行外推拟合。");
picture(s,"smearing_sensitivity.png");
banner(s,"跨 σ 变化同时含占据处理和采样影响；先问 k 对每个 σ 是否足够。");

s=page("本次联合判据的实际结果","Observed finite-reference outcomes",
 "本页由机器可读分析报告自动填入，每个展宽一行。没有候选时写未证明，而不是机械推荐参考网格。共同候选也只能表示本次有限参考和所选观测量下的证据。即使有候选，后续仍需更密锚点、截断能、密度截断和几何检查。");
const summaries=report.sigma_summaries.map(r=>[r.degauss_Ry.toFixed(3),"20³",
 r.lowest_joint_acceptable_k===null?"未证明":r.lowest_joint_acceptable_k+"³"]);
table(s,[["σ / Ry","有限参考","最低联合候选"],...summaries],[3.3,3.3,5.3],1.95,3.25);
tx(s,report.common_tested_k===null?"共同候选：无，不能宣称电子积分已收敛。":
 "共同有限参考候选："+report.common_tested_k+"³；仍需更密锚点。",
 .95,5.5,11.5,.55,{fontSize:23,bold:true,color:C.coral});

s=page("保留未通过，比假收敛有价值","Failure modes and transparent interpretation",
 "本页总结数值实验常见失败。参考自身零差不是收敛证明，粗网格下缩小展宽不保证精确，SCF 正常结束也不说明积分够密。这些边界均在测试与教程中表达。保持失败结果可追溯，才能规划下一轮补算，而不是隐藏不方便的数据。");
card(s,"参考自身为 0","定义，不是精确度\n需要更密锚点",.7,2,3.8,3.5,C.coral);
card(s,"σ 越小越好？","粗 k 可能更不稳定\n检查联动",4.78,2,3.8,3.5,C.gold);
card(s,"JOB DONE","技术运行完成\n不等于科学收敛",8.86,2,3.8,3.5);
banner(s,"完整扫描、成功解析、满足阈值、材料可信，是不同层次。");

s=page("本地可重做的完整链条","Code, notebook and provenance",
 "所有小型日志与来源哈希保存在仓库，可在本地重新分析，无需每次登录集群。八项单元测试检验失败关闭、联合判据与最终本征求解警告。六格 Notebook 已执行，适合改变阈值做敏感性练习，但不覆盖归档标准。每次计算使用新的目录和实际作业号，不能沿用旧身份。");
box(s,.8,1.95,11.7,3.85,C.ink);
tx(s,"python -m unittest test_scan.py -v\npython collect_results.py\npython build_notebook.py",
 1.15,2.35,11,2.4,{fontFace:"Consolas",fontSize:25,color:C.white,paraSpaceAfter:16});
banner(s,"原始 output + SHA256 + 输入计划 + CSV + 三图 + 已执行 Notebook");

s=page("下一步由失败证据决定","Next evidence, not premature Tc",
 "如果本次没有联合候选，优先扩展更密 k 点参考，同时对窄展宽进行联动检查。然后重新检验截断能、电荷密度截断和几何，随后再讨论有限 q 声子与电子–声子耦合。独立练习需手算一组能差、解释一次失败和能量定义。官方文档与原始方法来源放在中文教程中，不复制论文图。",true);
tx(s,"更密 k 参考 + 展宽联动\n→ 截断能 / 密度截断 / 几何\n→ 有限 q 声子 → EPC → Eliashberg",
 .95,2.0,11.5,2.2,{fontSize:28,color:C.white,paraSpaceAfter:17});
tx(s,"独立练习：手算一组差值，解释一个失败，写明一个局限。\n"+
 "来源：QE INPUT_PW / Cold smearing PRL 82, 3296 / HostBridge",
 .95,5.05,11.5,1.15,{fontSize:18,color:"B1CECA",paraSpaceAfter:14});

(async()=>{
 if(n!==14)throw Error("Expected 14 slides");
 const file=path.join(__dirname,"Al金属k网格与展宽收敛入门.pptx");
 await pptx.writeFile({fileName:file});
 const zip=await JSZip.loadAsync(fs.readFileSync(file));
 const xml=await zip.file("ppt/presentation.xml").async("string");
 zip.file("ppt/presentation.xml",xml.replace(/<p:notesMasterIdLst>[\s\S]*?<\/p:notesMasterIdLst>/,""));
 fs.writeFileSync(file,await zip.generateAsync({type:"nodebuffer",compression:"DEFLATE"}));
 console.log("Built 14 slides with detailed notes");
})().catch(error=>{console.error(error);process.exit(1);});
