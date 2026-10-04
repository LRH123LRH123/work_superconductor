// Original teaching deck. All figures are rebuilt from pinned data or the stated model.
const fs=require("fs"), path=require("path");
const PptxGenJS=require("pptxgenjs"), JSZip=require("jszip");
const pptx=new PptxGenJS();
pptx.layout="LAYOUT_WIDE";pptx.author="work_superconductor";
pptx.title="电子声子耦合与Eliashberg计算入门";pptx.lang="zh-CN";
pptx.theme={headFontFace:"Microsoft YaHei",bodyFontFace:"Microsoft YaHei",lang:"zh-CN"};
const S=pptx.ShapeType, C={ink:"183B3C",teal:"117E83",coral:"C55B43",gold:"857140",
 paper:"F7F4ED",pale:"EDF5F2",white:"FFFFFF",muted:"546968"};
const root=path.resolve(__dirname,".."), example=path.join(root,"examples/06_epc_eliashberg");
const r=JSON.parse(fs.readFileSync(path.join(example,"results/validation.json"),"utf8"));
let n=0;
function tx(s,t,x,y,w,h,o={}){s.addText(t,{x,y,w,h,fontFace:"Microsoft YaHei",fontSize:21,
 color:C.ink,margin:0,valign:"top",...o});}
function box(s,x,y,w,h,fill){s.addShape(S.rect,{x,y,w,h,fill:{color:fill},line:{color:fill}});}
function page(title,en,notes,dark=false){const s=pptx.addSlide();n++;
 s.background={color:dark?C.ink:C.paper};
 tx(s,String(n).padStart(2,"0"),.6,.4,.55,.35,{fontSize:17,color:dark?"B1CECA":C.teal});
 tx(s,title,1.15,.34,11.5,.7,{fontSize:32,bold:true,color:dark?C.white:C.ink});
 tx(s,en,1.15,1.09,11.4,.35,{fontSize:13,color:dark?"B1CECA":C.muted});
 tx(s,"work_superconductor / EPC 与 Eliashberg / 2026-10-04",.6,7.05,12,.25,
 {fontSize:10,color:dark?"B1CECA":C.muted});s.addNotes(notes);return s;}
function card(s,title,body,x,y,w=3.8,h=3.45,color=C.teal){box(s,x,y,w,h,C.white);
 box(s,x,y,.08,h,color);tx(s,title,x+.24,y+.26,w-.48,.65,{fontSize:24,bold:true,color});
 tx(s,body,x+.24,y+1.2,w-.48,h-1.42,{fontSize:20,paraSpaceAfter:10});}
function banner(s,t){box(s,.6,6.35,12.1,.5,C.pale);tx(s,t,.8,6.44,11.7,.32,
 {fontSize:15,bold:true,color:C.teal});}
function formula(s,t,y=2,h=1.15,fontSize=30){box(s,.8,y,11.7,h,C.pale);
 tx(s,t,1.05,y+.22,11.2,h-.34,{fontFace:"Cambria Math",fontSize,align:"center"});}
function picture(s,name,x=.7,y=1.7,w=11.9,h=4.5){const file=path.join(example,"results",name),b=fs.readFileSync(file);
 const iw=b.readUInt32BE(16),ih=b.readUInt32BE(20),scale=Math.min(w/iw,h/ih);
 s.addImage({path:file,x:x+(w-iw*scale)/2,y:y+(h-ih*scale)/2,w:iw*scale,h:ih*scale});}
function table(s,rows,widths,y=1.9,h=3.8){s.addTable(rows,{x:.7,y,w:11.9,h,colW:widths,
 fontFace:"Microsoft YaHei",fontSize:19,color:C.ink,fill:C.white,margin:.13,rowH:.6,
 valign:"middle",autoPage:false,border:{type:"solid",color:"D8E2DC",pt:.8}});}

let s=page("电子声子耦合与 Eliashberg 计算","Electron-Phonon Coupling and Migdal-Eliashberg Theory",
 "本课连接已有 BCS 与 BdG 学习包，把常数配对相互作用扩展到含频率结构的核。内容分为官方 Al 数据后处理、原创 Einstein 虚轴模型和真实 Pb 小型软件回归。三种结果不混为一个材料预测。本轮不扩展网格、截断能或展宽扫描。讲义给完整公式，课件突出理解路径与验证边界。",true);
tx(s,"从一个常数，走向一个谱。\n从一个数字，走向一条证据链。",.95,2.2,11.5,1.6,
 {fontSize:35,bold:true,color:C.white});
tx(s,"谱函数 → 配对核 → 虚轴方程 → 基准与局限",.95,4.65,11.5,.7,{fontSize:25,color:"B1CECA"});
tx(s,"中文教程 / Python / 8 格 Notebook / 20 页课件 / 真实集群记录",.95,5.9,11.5,.5,
 {fontSize:19,color:"B1CECA"});

s=page("三个练习，三种证据","Reference data, teaching model and software regression",
 "Al 文件来自固定 QE 提交，并非我们此前 SCF 产生的 EPC。Einstein 解包含有限频率截断，是原创模型教学，不拟合 Pb。Pb 在集群重新做 SCF、NSCF 和 EPW，复用官方 DFPT，只有粗网格回归对照。理解来源和范围，比把它们拼成一个看似完整的第一性原理 Tc 链条更重要。");
card(s,"Al 官方参考","离线谱积分\n单位与矩形求和\n不是新 Al EPC",.7,2);
card(s,"Einstein 模型","线性与非线性方程\n固定 96 正虚频\n不是 Pb",4.78,2,3.8,3.45,C.gold);
card(s,"Pb 真实集群","自有 SCF/NSCF/EPW\n上游 DFPT 数据\n不是收敛 Tc",8.86,2,3.8,3.45,C.coral);
banner(s,"计算完成、基准对照、材料可信与原论文图表复现是不同层次。");

s=page("材料计算里，信息怎样流动","DFT → DFPT → Wannier → EPC → Eliashberg",
 "DFT 描述基态电子结构，DFPT 给位移响应和声子，Wannier 表示使矩阵元可插值，细网格求和给谱，谱再决定虚轴配对核。每一箭头需要文件、规范与单位的一致性。当前 Pb 小例跳过自有 DFPT，使用官方保存数据，所以流程跑通不代表每个环节都从零复算，也不是收敛认证。");
const labels=[["DFT","电子态"],["DFPT","位移响应"],["Wannier","局域表示"],["EPC","谱与 λ"],["Eliashberg","Δ 与 Z"]];
labels.forEach((v,i)=>{const x=.8+i*2.48;box(s,x,2.5,2.05,2.1,i===3?C.teal:C.white);
 tx(s,v[0],x+.15,2.85,1.75,.55,{fontSize:23,bold:true,color:i===3?C.white:C.ink,align:"center"});
 tx(s,v[1],x+.15,3.7,1.75,.45,{fontSize:19,color:i===3?C.white:C.muted,align:"center"});
 if(i<4)s.addShape(S.chevron,{x:x+2.12,y:3.22,w:.25,h:.4,
 fill:{color:C.coral},line:{color:C.coral}});});
banner(s,"插值提升求和效率，不保证粗网格中缺失的信息自动恢复。");

s=page("矩阵元 g：不能只看声子频率","Electron-phonon scattering vertex",
 "哈密顿量中的 g 连接电子从 k 到 k+q 和声子的吸收或发射。频率描述声子能量，矩阵元描述散射强度。势的一阶位移响应、声子极化和电子波函数共同决定 g。迟滞意味着有效作用带有频率差结构。严格归一化可对照 EPW Theory，课件用示意表达强调信息来源而非另写未验证矩阵元代码。");
formula(s,"Hₑₚ ∼ Σ g c† c (b + b†)",2.0,1.15,34);
card(s,"电子态","k → k+q\n费米面附近的散射",.9,3.65,5.5,2.35);
card(s,"声子响应","频率 + 极化 + 势导数\n缺一个都不够",6.7,3.65,5.5,2.35,C.coral);

s=page("声子 DOS ≠ Eliashberg 谱函数","Phonon DOS versus alpha2F",
 "声子 DOS 只数模式，alpha2F 还包含散射矩阵元平方以及费米面电子权重。因此同样声子 DOS 不保证同样 lambda。积分还有一除以能量的权重，低能部分可能对耦合贡献很大。不要根据某个 DOS 高峰直接断言主导配对，也不要把归一化不同的 DOS 数值当作谱函数输入。");
card(s,"F(Ω)","有哪些声子模式？\n纵轴通常 1/能量\n不含完整 EPC",.85,2,5.55,3.65);
card(s,"α²F(Ω)","哪些模式强烈散射？\n含 |g|² 与电子权重\n本约定纵轴无量纲",6.7,2,5.55,3.65,C.coral);
banner(s,"同一个 DOS，可以对应不同 λ；大峰不自动等于最大配对贡献。");

s=page("先做单位检查，再算任何积分","Energy-axis conventions",
 "本课用声子能量 Omega 等于 hbar omega，单位 meV。Ry 到 meV 横轴缩放在 dOmega/Omega 中抵消，所以本数据 convention 的 alpha2F 不额外缩放。DOS 的积分要保持模式数，因此纵轴除以换算系数。其他代码如采用另一谱密度定义，需重新做量纲分析，不能照抄本表。");
table(s,[["对象","本课单位","换算要点"],["Ω、Δ、虚频能量","meV","1 Ry = 13605.693123 meV"],
 ["α²F","无量纲（此约定）","只改横轴，不改 A"],["声子 DOS","1/meV","原 1/Ry 值除以换算系数"],
 ["λ、Z、μ*","无量纲","μ* 不是化学势"]],[3.1,3.3,5.5],1.85,3.8);
banner(s,"所有读入要求显式单位、列号和格式，不猜测文件含义。");

s=page("三个谱矩：权重各不相同","Coupling, logarithmic moment and RMS energy",
 "lambda 是无量纲积分。对数矩计算时要用参考能量使对数自变量无量纲，本课取一 meV，最终值不依赖参考能量。Omega2 是二阶矩平方根，不是二阶矩本身。数据积分只到首尾，不外推低频，零频拒绝直接除法。累计 lambda 让我们看到不同能段的贡献，不从曲线的单个最高峰判断耦合。");
formula(s,"λ = 2 ∫ A(Ω) / Ω dΩ",1.8,.95,29);
formula(s,"Ωlog = E₀ exp[ (2/λ) ∫ (A/Ω) ln(Ω/E₀) dΩ ]",3.0,1.05,27);
formula(s,"Ω₂ = [ (2/λ) ∫ A(Ω) Ω dΩ ]¹ᐟ²",4.3,1.0,29);
banner(s,"积分区间、零频极限与非负谱检查要写清楚，不静默修补。");

s=page("Al：由官方数字表重建谱矩","Pinned QE reference, not our earlier Al SCF",
 "三个图由固定提交的官方 Al 数字表重绘。左图是谱函数，中图是累计耦合，右图是声子 DOS，并已正确把一每 Ry 转为一每 meV。数据来源有许可和 SHA256。此前 Al SCF 和 Gamma 声子并不产生这张完整谱，不能将这张官方数据图说成自己的材料计算结果。");
picture(s,"al_spectral_moments.png");banner(s,"梯形积分：λ = 0.39621339，Ωlog = 26.53072 meV。");

s=page("0.396213 与 0.396392：哪里不同？","Match the quadrature before judging reproduction",
 "这不是通过调参消掉误差。官方参考对均匀格点采用完整格点宽度矩形求和，梯形把端点权重减半。Al 文件末端谱不为零，所以两种离散结果有小差异。按官方规则重建 lambda 约三乘十的负十五次误差，只是同数据代数一致性，不代表材料精度达到机器精度，也不替代低频区间审查。");
card(s,"梯形规则",r.al_reference.lambda.toFixed(8)+"\n首尾权重各半\n覆盖格点首尾区间",.85,2,5.55,3.7);
card(s,"官方格点规则",r.al_reference.qe_rectangle_rule.lambda.toFixed(8)+"\n每点完整格点宽度\n重建原谱积分输出",6.7,2,5.55,3.7,C.coral);
banner(s,"先对齐单位、对象、端点与积分规则，再讨论误差。");

s=page("近似 Tc 公式 ≠ Eliashberg 方程解","Modified McMillan and full Allen-Dynes",
 "使用 Omega log 前因子的 base 是修正 McMillan 表达，不是原始 Debye 前因子。完整 Allen Dynes 还乘 f1 f2，考虑强耦合和谱形。这里用 Al 参考与 mu star 零点一算两种公式示例，结果并非自己的 Al 材料预测。实现检查指数分母非正时失败，而不是返回一个没有适用意义的临界温度。来源是 Allen Dynes PRB 12,905。");
formula(s,"Tcᴬᴰ = f₁ f₂ × [ Ωlog / (1.2 kB) ] × exp(…)",1.9,1.1,29);
card(s,"修正 McMillan",r.al_reference.tc_formula_example.modified_mcmillan_K.toFixed(5)+" K\n不含 f₁ / f₂",.85,3.55,5.55,2.35);
card(s,"完整 Allen-Dynes",r.al_reference.tc_formula_example.allen_dynes_K.toFixed(5)+" K\nμ* = 0.1（假设）",6.7,3.55,5.55,2.35,C.coral);

s=page("一个可解析核：Einstein 单模式","Analytical retarded kernel for an independent model",
 "单模式 alpha2F 取 lambda OmegaE 除以二乘 delta，使耦合积分恰为 lambda。代入虚频核可解析得到 lambda OmegaE 平方除以 OmegaE 平方加 nu 平方。K 是偶函数，零频值为 lambda，大频率差下降。这个模型提供独立核检查，不是把真实 Pb 频谱替换为一个峰再假装预测实验。参数固定 lambda 一，OmegaE 十 meV。");
formula(s,"A(Ω) = λ ΩE δ(Ω − ΩE) / 2",1.85,1.0,30);
formula(s,"K(ν) = λ ΩE² / (ΩE² + ν²)",3.15,1.05,32);
tx(s,"K(0) = λ     K(ν) = K(−ν)     大频率差 → 小作用",1.0,5.0,11.3,.75,
 {fontSize:25,bold:true,color:C.teal});banner(s,"这是独立教学模型，不是 Al 或 Pb 的拟合谱。");

s=page("虚轴未知量：Δ、Z 与 φ","Imaginary-axis functions and Matsubara energies",
 "费米 Matsubara 能量是二n加一乘 pi kBT。Z 是正常自能中的频率重整化函数，phi 是异常自能，Delta 等于 phi 除以 Z。Z 不能与电子谱中的准粒子权重直接当作同名量。本课固定九十六个正虚频和库仑截止一百 meV，不扫描它们。最大虚频随温度改变，未证明无限截止极限。最低虚频 Delta 不是实轴激发能隙。");
formula(s,"wₙ = (2n + 1) π kB T       φₙ = Zₙ Δₙ",1.95,1.1,31);
card(s,"固定离散模型","96 个正虚频\nΩc = 100 meV\nμ* = 0.1",.85,3.35,5.55,2.8);
card(s,"不做的推断","Δ(iw₀) ≠ 实轴能隙\n未做解析延拓\n未证截止收敛",6.7,3.35,5.55,2.8,C.coral);

s=page("正频率折叠：别丢掉库仑因子 2","Pair positive and negative frequencies",
 "负虚频索引是负m减一，wm 为奇函数而 Delta 是偶函数。因此正常方程中两个核相减，配对方程相加，库仑排斥在正负频率中都贡献，得到因子二。这些符号影响 Tc，不只是写法。本课单元测试用同截断的完整正负求和独立检验折叠实现，避免两个代码函数共享同一个符号错误却相互通过。");
formula(s,"K⁻ₙₘ = K(wₙ − wₘ)     K⁺ₙₘ = K(wₙ + wₘ)",1.9,1.05,29);
card(s,"正常项 Z","K⁻ − K⁺\n负频率 w 改变符号",.85,3.55,5.55,2.5);
card(s,"配对项 Δ","K⁻ + K⁺ − 2μ*θ\n偶频配对，库仑计两次",6.7,3.55,5.55,2.5,C.coral);

s=page("临界点：最大实本征值达到 1","Linearized instability, not largest absolute eigenvalue",
 "先在 Delta 为零的正常态求 Z，再构造线性配对矩阵。Delta 等于 B Delta 的非零解要求本征值一。本课跟踪最大实本征值，不用最大绝对值，因大负本征值不是该分支吸引。二分前必须有超导低温界和正常高温界，返回有限 bracket。搜索宽度并不等于模型或材料误差。代码还检查本征对残差。");
formula(s,"Δ = B(T) Δ       ρreal,max[B(Tc)] = 1",1.95,1.1,31);
tx(s,"低温端：ρ > 1           高温端：ρ ≤ 1",1.0,3.65,11.3,.6,{fontSize:27,color:C.teal});
tx(s,"有限模型 Tc 区间\n[9.26050, 9.26611] K",1.0,4.65,11.3,1.1,{fontSize:29,bold:true});
banner(s,"bracket 宽度是二分容差，不是物理误差棒。");

s=page("非线性方程：检查原残差","Fixed point, mixing and the normal branch",
 "先用线性本征值判断选取的分支。低温以非零初值迭代，按原非线性表达更新 Z 与 Delta，用零点三混合稳定迭代。残差定义为未混合更新减当前值，Delta 小于一乘十的负八 meV，Z 小于十的负九。若只看混合后的差，小混合因子会伪装收敛。高温返回正常态，并不靠零初值证明低温没有超导。");
card(s,"建立分支","ρ > 1：非零初值\nρ ≤ 1：正常态\n避免零初值假结论",.7,2);
card(s,"更新与混合","算新 Δ / Z\n混合比例 0.3\n达到上限就报错",4.78,2,3.8,3.45,C.gold);
card(s,"原方程残差","|Δnew − Δ| < 10⁻⁸\n|Znew − Z| < 10⁻⁹\n不是混合后的步长",8.86,2,3.8,3.45,C.coral);
banner(s,"所有数字只针对所声明的单模式有限求和，不提供普适分支稳定性证明。");

s=page("温度曲线：模型的配对不稳定性","Fixed Einstein parameters; temperature is a physical variable",
 "图显示固定模型的最低虚频 Delta 与最大实本征值随物理温度变化。改变温度是为了学习序参量，不是 DFT 采样密度、截断或展宽扫描。临界区间在图上标记。高温正常态返回零 Delta。不能把这个约九点二六 K 的数称为真实 Pb 的 Tc，也不能将最低虚频数值当实轴能隙来计算实验强耦合比例。");
picture(s,"einstein_gap_temperature.png");banner(s,"λ=1，ΩE=10 meV，μ*=0.1；不是 Pb，不是材料预测。");

s=page("4 K：能隙函数不是一个常数","Frequency-dependent Delta and Z on the imaginary axis",
 "左图是虚轴配对函数，右图是 Z。高虚频部分可以出现符号结构，不应自动剪裁负 Delta；非负约束仅针对物理谱 alpha2F，不针对这条配对函数。残差已满足声明阈值，但未做解析延拓，所以图不能直接当隧穿能隙或实轴 DOS。读图时同时说出温度、固定频率截断和库仑截止。");
picture(s,"einstein_frequency.png");banner(s,"Δ(iw) 与实轴激发能隙不同；本课没有 Padé 延拓或隧穿 DOS。");

s=page("Pb 集群：跑通小回归，不预测材料","Own SCF/NSCF/EPW, reused official DFPT",
 "固定 Pb 小回归粗 k/q 三立方，细 k/q 六立方，六十 Ry，标量相对论无 SOC。SCF NSCF EPW 都实际运行，DFPT 是上游参考。最终 Job 313836 COMPLETED，四十三秒，四 MPI。前两次物理程序已结束但检查器失败，全部留痕。lambda 对照上游差八乘十的负七，说明该标量软件回归通过，而非生产级材料 EPC 或 Tc 收敛。");
table(s,[["对象","本次","证据 / 边界"],["SCF / NSCF / EPW","真实运行","4 MPI，QE 7.5 / EPW 6.0"],
 ["DFPT","官方参考","未从零重算"],["粗 → 细 k/q","3³ → 6³","固定回归，无 SOC"],
 ["最终 Job 313836","COMPLETED","0:0，43 秒"]],[3.6,3.0,5.3],1.8,3.85);
banner(s,"前两次 FAILED 身份和浮点警告保留；没有密度或截断扫描。");

s=page("Pb 谱：先读格式，再对照同一对象","Legacy EPW spectrum, first column selected explicitly",
 "谱有五百数字行及文字尾部，首列 meV，后十列不同谱展宽。本课只分析第一谱列零点零五 meV，不展开列作为收敛扫描。模式 q lambda 为零点一六零八七九七，谱积分略不同但匹配尾部。原始完整数字源用 Job 313824 物理输出，最终成功 Job 313836 谱哈希相同。不把旧日志改名为新作业，不删除 divide by zero 等警告。");
picture(s,"pb_regression_spectrum.png");banner(s,"λq=0.1608797；官方回归 0.1608789；谱积分 0.16088553。");

s=page("下一步：先复现方程，再选择原图","Equation-level learning before a paper figure project",
 "下一阶段按 Allen Dynes 原文、EPW 理论和 Margine Giustino PRB 87,024505 阅读。先写符号约定、各向异性到各向同性平均和失去的信息，然后选择明确图号、数据来源和误差标准。当前已完成方程级模型和软件回归，尚未完成原论文图表。独立练习是手算单位、解释库仑因子二、说明残差并写一条未完成材料证据，不继续 DFT 收敛扫描。",true);
tx(s,"01  手算谱矩与单位\n02  推导折叠中的因子 2\n03  写下证据边界与论文目标",.95,2.0,11.4,2.4,
 {fontSize:29,color:C.white,paraSpaceAfter:18});
tx(s,"阅读：Allen–Dynes (1975) / EPW Theory / Margine–Giustino (2013)\n"+
 "配套：详细中文讲义、已执行 Notebook、测试、源文件与许可。",.95,5.25,11.5,1.1,
 {fontSize:18,color:"B1CECA",paraSpaceAfter:14});

(async()=>{if(n!==20)throw Error("Expected 20 slides");
 const file=path.join(__dirname,"电子声子耦合与Eliashberg计算入门.pptx");
 await pptx.writeFile({fileName:file});
 const zip=await JSZip.loadAsync(fs.readFileSync(file));
 const xml=await zip.file("ppt/presentation.xml").async("string");
 zip.file("ppt/presentation.xml",xml.replace(/<p:notesMasterIdLst>[\s\S]*?<\/p:notesMasterIdLst>/,""));
 fs.writeFileSync(file,await zip.generateAsync({type:"nodebuffer",compression:"DEFLATE"}));
 console.log("Built 20 slides with detailed Chinese notes");
})().catch(e=>{console.error(e);process.exit(1);});
