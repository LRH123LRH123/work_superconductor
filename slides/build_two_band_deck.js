// Original diagrams and model results; no author paper images embedded.
const fs=require('fs'),path=require('path');
const PptxGenJS=require('pptxgenjs'),JSZip=require('jszip');
const pptx=new PptxGenJS();pptx.layout='LAYOUT_WIDE';pptx.author='work_superconductor';
pptx.title='双带与各向异性Eliashberg入门';pptx.lang='zh-CN';
pptx.theme={headFontFace:'Microsoft YaHei',bodyFontFace:'Microsoft YaHei',lang:'zh-CN'};
const S=pptx.ShapeType,C={ink:'183B3C',teal:'117E83',coral:'C55B43',gold:'857140',
 paper:'F7F4ED',pale:'EDF5F2',white:'FFFFFF',muted:'546968'};
const example=path.resolve(__dirname,'../examples/07_two_band_eliashberg');
const r=JSON.parse(fs.readFileSync(path.join(example,'results/validation.json'),'utf8'));let n=0;
function mathRuns(t){const runs=[];let end=0;const re=/([_^])\{([^}]+)\}/g;let m;
 while((m=re.exec(t))){if(m.index>end)runs.push({text:t.slice(end,m.index)});
  runs.push({text:m[2],options:m[1]==='_'?{subscript:true}:{superscript:true}});end=re.lastIndex;}
 if(end<t.length)runs.push({text:t.slice(end)});return runs;}
function tx(s,t,x,y,w,h,o={}){if(o.fontFace==='Cambria Math'&&typeof t==='string')t=mathRuns(t);
 s.addText(t,{x,y,w,h,fontFace:'Microsoft YaHei',fontSize:23,
 color:C.ink,margin:0,valign:'top',...o});}
function box(s,x,y,w,h,fill){s.addShape(S.rect,{x,y,w,h,fill:{color:fill},line:{color:fill}});}
function page(title,en,notes,dark=false){let s=pptx.addSlide();n++;
 s.background={color:dark?C.ink:C.paper};tx(s,String(n).padStart(2,'0'),.6,.4,.55,.35,
 {fontSize:17,color:dark?'B1CECA':C.teal});
 tx(s,title,1.15,.34,11.5,.75,{fontSize:34,bold:true,color:dark?C.white:C.ink});
 tx(s,en,1.15,1.13,11.4,.35,{fontSize:13,color:dark?'B1CECA':C.muted});
 tx(s,'work_superconductor / 双带 Eliashberg / 2026-10-04',.6,7.05,12,.25,
 {fontSize:10,color:dark?'B1CECA':C.muted});s.addNotes(notes);return s;}
function card(s,title,body,x,y,w=3.8,h=3.4,color=C.teal){box(s,x,y,w,h,C.white);
 box(s,x,y,.08,h,color);tx(s,title,x+.23,y+.25,w-.46,.7,{fontSize:24,bold:true,color});
 tx(s,body,x+.23,y+1.15,w-.46,h-1.35,{fontSize:21,paraSpaceAfter:10});}
function banner(s,t){box(s,.6,6.35,12.1,.5,C.pale);tx(s,t,.8,6.44,11.7,.32,
 {fontSize:15,bold:true,color:C.teal});}
function formula(s,t,y=2,h=1.1,fontSize=30){box(s,.8,y,11.7,h,C.pale);
 tx(s,t,1.05,y+.2,11.2,h-.3,{fontFace:'Cambria Math',fontSize,align:'center'});}
function picture(s,name,x=.7,y=1.7,w=11.9,h=4.5){const file=path.join(example,'results',name),b=fs.readFileSync(file);
 const iw=b.readUInt32BE(16),ih=b.readUInt32BE(20),scale=Math.min(w/iw,h/ih);
 s.addImage({path:file,x:x+(w-iw*scale)/2,y:y+(h-ih*scale)/2,w:iw*scale,h:ih*scale});}
function table(s,rows,widths,y=1.9,h=3.8){s.addTable(rows,{x:.7,y,w:11.9,h,colW:widths,
 fontFace:'Microsoft YaHei',fontSize:19,color:C.ink,fill:C.white,margin:.13,rowH:.7,
 valign:'middle',autoPage:false,border:{type:'solid',color:'D8E2DC',pt:.8}});}
function arrow(s,x,y,w=.35,h=.45){s.addShape(S.chevron,{x,y,w,h,fill:{color:C.coral},line:{color:C.coral}});}

let s=page('双带与各向异性 Eliashberg 入门','Two-Band and Anisotropic Migdal-Eliashberg Theory',
 '本课延续上一课的虚轴 Eliashberg 模型，从平均成一个数走向保留目标带与起始带的矩阵信息。材料包含详细中文教程、原创 Python、八格已执行 Notebook、十九项测试和本课二十页课件。它是有限频率的带平均模型，不是完整动量分辨 EPW，也不拟合 MgB2。原文图号已核对，但原图定量复现尚未完成。本轮不提交集群或扩展密度、能量、展宽扫描。',true);
tx(s,'从一个平均数\n走向一张配对矩阵',.95,2.2,10,1.75,{fontSize:43,bold:true,color:C.white});
tx(s,'DOS 权重 → 双带核 → 自洽解 → 原文目标',.95,4.75,11.5,.7,{fontSize:25,color:'B1CECA'});
box(s,10.9,2.4,1.25,1.25,C.teal);box(s,10.9,3.8,1.25,1.25,C.coral);
tx(s,'A',11.2,2.7,.7,.6,{fontSize:30,color:C.white});tx(s,'B',11.2,4.1,.7,.6,{fontSize:30,color:C.white});

s=page('四种分辨率，不是四种配对介质','Isotropic, band-averaged, patch and fully anisotropic',
 '各向同性只保留频率函数，带平均保留每个带组，patch 保留费米面区域，而完整各向异性保留带与波矢。多带并不自动意味着非声子机制。本课的 A/B 是有效分组，不是已经构造真实材料能带。各向异性也不要求非常规对称性，声子介导体系仍可有复杂能隙。课堂验收是指出每一级平均丢掉了什么，而非按两个能隙就归类机制。');
[['各向同性','一个 Δ(iw)\n丢失带差别'],['双带平均','两组 Δᵢ(iw)\n丢失带内 k'],['费米面 patch','区域 Δₚ(iw)\n丢失区内细节'],['完整各向异性','Δ(b,k,iw)\n仍有理论近似']].forEach((v,i)=>
 card(s,v[0],v[1],.7+i*3.07,2.1,2.83,3.45,i===1?C.coral:C.teal));
banner(s,'本课属于双带平均：仍是声子 Einstein 核，不是 Hubbard / 自旋涨落求解器。');

s=page('带标签之外，还有积分权重','Fermi-surface measure is not the number of sampled points',
 '示意中的椭圆仅代表两个电子态分组，不是 MgB2 的真实费米面图。费米面权重由部分 DOS 和积分测度决定，不由画出的点数决定。即使每条带使用相同数量的波矢，费米速度和测度不同仍使权重不同。本课人为设 pA 零点四、pB 零点六，并明确没有从第一性原理提取。真实材料须保持同一自旋与体积约定，否则平均与库仑参数都会出错。');
[[1.0,2.1,3.5,2.25,C.teal,'A'],[5.0,2.1,5.3,2.25,C.coral,'B']].forEach(v=>{
 s.addShape(S.ellipse,{x:v[0],y:v[1],w:v[2],h:v[3],fill:{color:C.white},line:{color:v[4],width:4}});
 tx(s,'Band '+v[5],v[0]+.5,v[1]+.8,v[2]-1,.5,{fontSize:28,bold:true,color:v[4],align:'center'});});
tx(s,'pA = 0.4',1.5,4.9,3.2,.6,{fontSize:28,color:C.teal});tx(s,'pB = 0.6',6.1,4.9,4,.6,{fontSize:28,color:C.coral});
banner(s,'原创分组示意，不是真实 MgB₂ 费米面；点数相同不代表 DOS 相同。');

s=page('一条最重要的约定：只乘一次 pⱼ','Destination-band DOS is absorbed into lambda_ij',
 '将目标带内费米面求和压缩为 pj 后，可以把 pj 放在求和外，也可以吸收进 lambdaij。这两种写法都合法，但必须始终一致。我们的代码采用后者，bare lambda 是未加权有效谱幅度，lambda matrix 已乘目标带权重。它不是以电子伏为单位的微观势。若把已加权矩阵传入 bare 参数，会发生第二次加权；此类错误不一定令程序崩溃，所以须手算行和检查。');
formula(s,'λᵢⱼ = Vᵢⱼ pⱼ       μ*ᵢⱼ = Uᵢⱼ pⱼ',1.95,1.1,34);
card(s,'本课求和','Σⱼ λᵢⱼ fⱼ\n目标 DOS 已包括',.85,3.55,5.55,2.3);
card(s,'错误的重复加权','Σⱼ pⱼ λᵢⱼ fⱼ\n悄悄改变模型',6.7,3.55,5.55,2.3,C.coral);

s=page('从对称幅度，到非对称耦合','Symmetric bare amplitude; asymmetric DOS-weighted coupling',
 '手算矩阵是最可靠的入门检查。未加权 V 的非对角元均为零点三，但目标带 B 占零点六，A 占零点四，所以已加权两侧是零点一八和零点一二。对角元也吸收目标 DOS，成为一和零点六。不应为了让矩阵好看而把 lambda 普通对称化。Coulomb 未加权矩阵全为零点一，已加权每行零点零四、零点零六，行和零点一。');
box(s,.85,2.05,5.15,3.3,C.white);box(s,7.3,2.05,5.15,3.3,C.white);
tx(s,'V（未加权）',1.2,2.3,4.5,.5,{fontSize:25,bold:true,color:C.teal});
tx(s,'2.5     0.3\n0.3     1.0',1.7,3.2,3.6,1.4,{fontFace:'Cambria Math',fontSize:36,align:'center'});
arrow(s,6.4,3.25,.5,.7);
tx(s,'λ（已乘 pⱼ）',7.65,2.3,4.5,.5,{fontSize:25,bold:true,color:C.coral});
tx(s,'1.0     0.18\n0.12    0.60',8.0,3.2,3.6,1.4,{fontFace:'Cambria Math',fontSize:36,align:'center'});
banner(s,'0.3 × 0.6 = 0.18；0.3 × 0.4 = 0.12。非对称不等于实现错误。');

s=page('验收的是加权互易，不是普通对称','Weighted reciprocity: p_i lambda_ij = p_j lambda_ji',
 '左图是原创教学矩阵，不是论文中的 MgB2 矩阵。加权互易来自对称有效幅度和一致的 DOS 定义。pA 乘 lambdaAB 与 pB 乘 lambdaBA 都为零点零七二。测试还独立检查 Coulomb 的四个元素，避免正负求和 oracle 与生产代码共用错误矩阵而漏检。谱核还需核对目标带索引，不以图像颜色或平滑度代替验证。');
picture(s,'coupling_matrix.png',.65,1.9,7.0,4.2);
card(s,'手算互易','0.4 × 0.18 = 0.072\n0.6 × 0.12 = 0.072',8.0,2.3,4.5,3.2,C.coral);
banner(s,'普通 λ 矩阵不对称；验收的是加权互易关系 pᵢ λᵢⱼ = pⱼ λⱼᵢ。');

s=page('平均 λ，要平均什么？','Row mass couplings and a weighted Fermi-surface average',
 '行和给每个带与所有目标带的耦合，A 是一点一八，B 是零点七二。整体平均再按起始带 DOS 加权，得到零点九零四。不是对角元平均，更不是四个元素的算术平均。后面的单带对照使用这个平均值及相同能标、截止、库仑行和。该对照是先平均相互作用后求解，不是把已经计算的两条能隙平均。两者操作不交换，是本课要用代码展示的信息损失。');
formula(s,'λ_{A} = 1.18       λ_{B} = 0.72',1.9,1.1,35);
formula(s,'λ_{avg} = 0.4 × 1.18 + 0.6 × 0.72 = 0.904',3.3,1.1,31);
tx(s,'不是四元素算术平均，也不是只看对角元。',1.0,5.2,11.3,.6,{fontSize:25,bold:true,color:C.coral});

s=page('恒定 DOS，不会自动消除各向异性','Constant DOS and isotropic averaging are separate approximations',
 '费米面限制和恒定 DOS 近似简化沿电子能量的积分，在此教学模型中不解 chi 与粒子数。但不同带或不同费米面区域仍可以有不同的核、Z 和 Delta。各向同性是额外平均，不应与恒定 DOS 混用。遇到窄带或费米能附近强 DOS 变化，要重新判断近似，不能把本课两方程直接用于全带宽情形。本页要求同学用一句话分别描述两个近似丢失的变量。');
card(s,'沿电子能量 ξ','忽略能量依赖\n费米面限制\n不解 χ / 粒子数',.85,2.15,5.55,3.4);
card(s,'沿带 / k','本课仍保留 A / B\n完整理论可保留 k\n各向同性是额外平均',6.7,2.15,5.55,3.4,C.coral);
banner(s,'Constant DOS ≠ Isotropic；本课也不是 full-bandwidth 理论。');

s=page('共同 Einstein 能量，四个核幅度','Retarded kernels retain band-pair information',
 '对每个带对设一个 delta 声子谱，幅度 lambdaij OmegaE 除以二，静态核即为 lambdaij。共同 OmegaE 是教学简化，真实四条带对谱不必同形。代码并没有把核改成常数 lambda，而是保留频率差平方的分母。单位全为 meV，核无量纲。图里的 AB 与 BA 振幅不同来自 DOS，频率依赖形状则相同。不能据声子 DOS 单独恢复这些矩阵元权重。');
formula(s,'A_{ij}(Ω) = λ_{ij} Ω_{E} δ(Ω − Ω_{E}) / 2',1.9,1.1,31);
formula(s,'K_{ij}(ν) = λ_{ij} Ω_{E}^{2} / (Ω_{E}^{2} + ν^{2})',3.3,1.15,32);
tx(s,'K_{ij}(0) = λ_{ij}     偶函数     Ω_{E} = 10 meV',1.0,5.2,11.3,.6,
 {fontFace:'Cambria Math',fontSize:25,color:C.teal});

s=page('正负虚频：正常差核，配对和核','Even-frequency folding and the factor of two',
 '费米频率负索引是负m减一。w 是奇函数，而本课 Delta 和 Z 为偶函数。正常方程正负项因此相减，配对方程相加。Coulomb 截止在正负两侧都有一次排斥，折叠后乘二。多一个带指标不会改变奇偶关系。独立测试建立同样截断的完整有符号频率，甚至让截止落在正频率网格内部，检验遗漏库仑因子或截止方向的错误。');
formula(s,'K⁻ = Kᵢⱼ(wₙ − wₘ)     K⁺ = Kᵢⱼ(wₙ + wₘ)',1.9,1.05,29);
card(s,'正常项 Z','K⁻ − K⁺\nwₘ / √(wₘ² + Δⱼₘ²)',.85,3.45,5.55,2.5);
card(s,'配对项 Δ','K⁻ + K⁺ − 2μ*ᵢⱼθ\nΔⱼₘ / √(wₘ² + Δⱼₘ²)',6.7,3.45,5.55,2.5,C.coral);

s=page('矩阵有 192 维，索引必须先交换','Flatten rows (i,n), columns (j,m)',
 '两个带乘九十六正频率，共一百九十二未知量。原核四维形状是 i,j,n,m，而矩阵需要 i,n,j,m，因此先 transpose 零二一三，再 reshape。直接 reshape 仍能生成方阵，甚至画出平滑温度曲线，但索引物理错误。单带向量嵌入、完整正负频率 oracle、带标签置换和线性解耦块测试分别从不同侧面检查。不要只把本征值一这个结果看成算法通过。');
[['B_{AA}',C.teal],['B_{AB}',C.coral],['B_{BA}',C.coral],['B_{BB}',C.teal]].forEach((v,i)=>{
 const x=1.0+(i%2)*2.15,y=2.0+Math.floor(i/2)*1.65;
 box(s,x,y,2,1.5,C.white);tx(s,v[0],x+.2,y+.45,1.6,.6,{fontFace:'Cambria Math',fontSize:27,color:v[1],align:'center'});});
tx(s,'每块 96 × 96\n行：(i,n)  列：(j,m)',6.2,2.2,6,1.35,{fontSize:25,bold:true});
tx(s,'transpose(0, 2, 1, 3)\nreshape(192, 192)',6.2,4.2,6,1.2,{fontFace:'Consolas',fontSize:23,color:C.teal});
banner(s,'独立解析单带嵌入误差约 1.67×10⁻¹⁶；不是只凭曲线形状验收。');

s=page('Tc 判据：最大实本征值达到 1','The largest magnitude is not the pairing criterion',
 '线性方程 Delta等于B Delta，非零解对应本征值一。教学代码跟踪最大实本征值，不取最大绝对值。举例负五、零点九、零点三，最大的绝对值是五，但对应负值不是该配对分支。矩阵含目标频率库仑截止且未做对称变换，所以使用一般 eig 而非 eigh。规范化本征向量并检验本征对残差，仍不等于非线性自由能稳定性证明。');
formula(s,'Δ = B(T) Δ     →     ρ_{real,max}[B(T_{c})] = 1',1.9,1.1,31);
card(s,'示范谱','−5，0.9，0.3\n最大绝对值：5',.85,3.55,5.55,2.3,C.coral);
card(s,'正确选择','最大实值：0.9\n当前尚未达到 1',6.7,3.55,5.55,2.3);

s=page('相同平均 λ，不是相同 Tc','Fixed two-band model versus a same-average isotropic model',
 '这两组数均由固定九十六正虚频模型求得，声子能量十 meV，库仑截止一百 meV，每行库仑和零点一。双带零点九零四的平均 lambda 对照单带相同平均值，Tc 却不同。原因是带分辨主模和带分辨 Z 与平均后的问题不同。只针对本例，不能宣布各向异性总会提高 Tc。二分宽度零点零一 K 是搜索容差，不是材料或截止误差棒。');
card(s,'双带有限模型',`[${r.two_band_tc.lower_K.toFixed(5)},\n ${r.two_band_tc.upper_K.toFixed(5)}] K`,.85,2.05,5.55,3.45);
card(s,'同平均各向同性',`[${r.isotropic_tc.lower_K.toFixed(5)},\n ${r.isotropic_tc.upper_K.toFixed(5)}] K`,6.7,2.05,5.55,3.45,C.gold);
banner(s,'λavg=0.904；这是固定模型对照，不是 MgB₂，也不是普适增强定理。');

s=page('自洽：先检查未混合残差','Original fixed-point residuals, not the mixed step size',
 '低温主模提供非零初值，正常分支零能隙。每步用旧 Delta 得到 E，更新 Z 和 Delta，并在混合之前检查原方程差。Delta 阈值一乘十的负八 meV，Z 阈值十的负九。只看混合步长会让非常小的混合比例伪装收敛。十 K 近临界点需约四千九百二十三次，演示预算一万，未降低标准。这是简单混合，不是原论文的 Broyden 算法。');
card(s,'先选分支','按连通分组\n主模非零种子\n正常组保持零',.7,2.15,3.8,3.4);
card(s,'未混合残差','rΔ < 10⁻⁸ meV\nrZ < 10⁻⁹\n原更新最大绝对差',4.78,2.15,3.8,3.4,C.gold);
card(s,'混合比例 0.3','x ← 0.7x + 0.3xnew\n超预算就报错\n不把末步当收敛',8.86,2.15,3.8,3.4,C.coral);
banner(s,'临界慢化：10 K 演示约 4923 次迭代；增加预算，不放宽残差。');

s=page('解耦极限：不能只点亮最强的一条带','Seed each unstable disconnected component independently',
 '独立代码复核发现，只用全局最强本征向量做初值，在完全解耦矩阵里会使第二条本来也不稳定的带始终停在零解。它可以有小原残差，但不是应选择的非零分支。现在识别实际有效的 lambda 或 Coulomb 非零项所连分组，截止排除全部频率时不计库仑连接，各组独立初始化。新增测试把解耦非线性解与各自单带对照，还验证稳定组正常与空库仑窗口。给定连通例结果未改变。');
card(s,'独立不稳定组 A','ρA > 1\n单独非零初始化',.85,2.1,5.55,2.9);
card(s,'独立不稳定组 B','ρB > 1\n也需要非零初始化',6.7,2.1,5.55,2.9,C.coral);
tx(s,'19 项测试：独立带非线性退化、稳定组、空库仑窗口。',1.0,5.45,11.3,.55,{fontSize:23,bold:true});
banner(s,'小残差只说明驻点；分支、稳定性与物理解不能省略。');

s=page('4 K：两条虚轴函数，而非两个实验数','Imaginary-axis gap and mass renormalization',
 '图由原创参数实际求解。四 K 的最低虚频 DeltaA约一点八六五三八、DeltaB约零点八七四七一 meV。两个带的频率依赖与 Z 不同，高频能隙函数可有负尾部，不应裁掉。两条线是带平均，不具原论文带内点云宽度。没有解析延拓，不能把数值直接当实轴激发能隙，也不能用它们声称复现 MgB2 隧穿谱。读图时应同时说出温度、虚频数量和截止。');
picture(s,'two_band_frequency.png');banner(s,'ΔA(iw₀)=1.86538、ΔB(iw₀)=0.87471 meV；不是 MgB₂ 实验能隙。');

s=page('温度变化，是物理演示，不是 DFT 扫描','Two-band order parameters and a shared onset',
 '九个预设温度及临界区间高温端正常点只用于同一固定有限模型的配对学习，并非网格、密度、截断或展宽收敛实验。本例两带通过非零带间核相连，在主配对不稳定性附近共同消失，不能推广到全部解耦情形。金色曲线是同平均相互作用的单带模型。图和 JSON 同时记录未混合残差，二十 K 返回零能隙正常态。模型没有作无限虚频极限，所以温度曲线不是材料预测。');
picture(s,'two_band_temperature.png');banner(s,'固定 96 正虚频与 100 meV 库仑截止；本轮新增集群作业 = 0。');

s=page('主配对模式：振幅规范不等于能隙大小','Normalized linear eigenvector near the instability',
 '这个图是临界区间中点的线性主本征向量，规范化最大绝对分量为一，不是非线性 meV 能隙。两个带的相对幅度显示配对模式如何偏向强耦合带，但整体符号是规范选择。本征对残差很小，说明离散矩阵计算自洽，却不能证明真实材料的对称性或所有竞争分支的自由能排序。此处训练读图的对象意识，避免把任何写着 Delta 的纵轴都当实验能隙。');
picture(s,'leading_mode.png');banner(s,'无量纲线性模式；不可替代非线性 Δ，更不可当实轴激发谱。');

s=page('原文位置已经核对，算法差异也要写','Author preprint arXiv:1211.3345v1, not an unverified figure number',
 '原文来自 Margine Giustino PRB八十七零二四五零五，实际阅读作者公开稿 arXiv一二一一点三三四五第一版。第三页式十八二十给核和 Delta关系，第四页二十一到二十三给费米面限制方程，第六页III B讲自洽与延拓，第十页图六a是 MgB2 十K虚轴能隙，mu star零点一六。本课带平均、Einstein谱、简单混合和线性本征找Tc均是自己的教学取舍。不声称与出版版页码完全一样。');
table(s,[['作者稿位置','核对对象','本课用途'],['p3：式 (18)、(20)','核；Δ = φ/Z','解析核与符号'],
 ['p4：式 (21)–(23)','费米面权重方程','带平均推导'],['p6：III.B','自洽与延拓','记录算法差异'],
 ['p10：Fig. 6(a)','10 K，μ*=0.16，虚轴','固定原图目标']],[3.4,4.5,4.0],1.8,3.85);
banner(s,'原文、动态 EPW 文档和原创教学推导分别标注；不转载原图或论文 PDF。');

s=page('完成了准备课，还没有完成材料原图','A precise target, an honest status and a data checklist',
 '已完成理论到代码的闭环、八格Notebook、十九项测试及原文定位。原图任务固定为作者稿第十页Fig六a，不含实轴六b和网格敏感性图八。缺少作者数字表与材料带动量分辨核，不能伪造参考点。下一步先找许可明确的固定数据，写输入版本与差异，再决定是否进行单组集群流程。当前停止新扫描的安排不变，论文精度缺口也不能因此改写为已收敛。',true);
tx(s,'已完成：方程 → 双带代码 → 独立验证\n已选定：Fig. 6(a) 虚轴能隙\n未完成：材料核、作者点集、原图误差',.95,2.1,11.4,2.55,
 {fontSize:29,color:C.white,paraSpaceAfter:15});
box(s,.95,5.35,11.5,.7,C.teal);tx(s,'下一步先取得固定数据，不自动提交大型作业或新扫描。',1.2,5.5,11,.4,
 {fontSize:20,color:C.white,bold:true});

(async()=>{if(n!==20)throw Error('Expected 20 slides');
 const file=path.join(__dirname,'双带与各向异性Eliashberg入门.pptx');await pptx.writeFile({fileName:file});
 const zip=await JSZip.loadAsync(fs.readFileSync(file));
 const xml=await zip.file('ppt/presentation.xml').async('string');
 zip.file('ppt/presentation.xml',xml.replace(/<p:notesMasterIdLst>[\s\S]*?<\/p:notesMasterIdLst>/,''));
 fs.writeFileSync(file,await zip.generateAsync({type:'nodebuffer'}));
 console.log('Created 20 original slides with Chinese notes:',file);
})().catch(e=>{console.error(e);process.exit(1);});
