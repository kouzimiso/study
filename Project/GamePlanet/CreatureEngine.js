/**
 * CreatureEngine.js — 遺伝子 → 生物の形態（体軸・肢・指・尾のストロークと器官）を生成する
 * GamePlanet.html と creature-test.html から読み込む（classic script・グローバル定数 CreatureEngine を定義）。
 * 依存: なし（内部に 34遺伝子用の Genome / LifeGfx を private に持つ）。
 * API: CreatureEngine.build(g24|g34) → model / draw / complexity / color / padGenome / PLAN_NAMES / GC
 */
// ================================================================
// CreatureEngine — creature-lab.html (34遺伝子 Morphogenエンジン) をそのまま移植し
// IIFEに封じ込めたもの。内部の GC=34 / Genome / LifeGfx はモジュール privateで、
// ゲーム本体の 24遺伝子 GC/Genome/LifeGfx とは衝突しない。
// ゲームの24遺伝子個体は padGenome() で34遺伝子へ決定論的に拡張して描画する。
// API: CreatureEngine.build(g24|g34)->model, .draw(model,sx,sy,scale,yaw,t,ctx),
//      .complexity(g), .color(g), .PLAN_NAMES, .GC
// ================================================================
const CreatureEngine=(function(){
const V={
  add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]],
  sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]],
  scale:(a,s)=>[a[0]*s,a[1]*s,a[2]*s],
  dot:(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],
  cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],
  len:a=>Math.hypot(a[0],a[1],a[2]),
  norm:a=>{const l=Math.hypot(a[0],a[1],a[2])||1;return[a[0]/l,a[1]/l,a[2]/l];}
};
// ロドリゲス回転：ベクトルvを軸axis周りにang回転
function rot(v,axis,ang){
  const a=V.norm(axis),c=Math.cos(ang),s=Math.sin(ang),d=V.dot(a,v);
  return[
    v[0]*c+(a[1]*v[2]-a[2]*v[1])*s+a[0]*d*(1-c),
    v[1]*c+(a[2]*v[0]-a[0]*v[2])*s+a[1]*d*(1-c),
    v[2]*c+(a[0]*v[1]-a[1]*v[0])*s+a[2]*d*(1-c)
  ];
}

/* ---------- 疑似乱数（決定論：同じゲノム→同じ生物） ---------- */
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);
  t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function hashGenome(g){let h=2166136261;for(let i=0;i<g.length;i++){
  h^=Math.floor((g[i]||0)*255);h=Math.imul(h,16777619);}return h>>>0;}

/* ---------- ゲノム ---------- */
const GC=34;
const GENE_NAMES=['外皮','筋肉','装甲','接着','神経','神経維持','走化性','感覚','消化','幹細胞',
  '触媒','毒','代謝','光合成','化学合成','APレート','体格','運動','耐熱','耐寒','水適応','生殖',
  '攻撃','寿命','肢ペア数','肢分岐複雑度','指爪数','体節数','対称性','放射腕数','角の量','角の本数',
  '体断面形状','肢位置バイアス'];
const Genome={
  clamp:v=>v<0?0:(v>1?1:v),
  random(){const g=new Float32Array(GC);for(let i=0;i<GC;i++)g[i]=Math.random();return g;},
  mutate(g,rate,amt){rate=rate||0.15;amt=amt||0.18;const n=new Float32Array(g);
    for(let i=0;i<GC;i++)if(Math.random()<rate)n[i]=Genome.clamp(n[i]+(Math.random()*2-1)*amt);return n;},
  extremeMutate(g){return Genome.mutate(g,0.55,0.55);},
  cross(a,b){const n=new Float32Array(GC);let seg=Math.random()<0.5;
    for(let i=0;i<GC;i++){if(Math.random()<0.18)seg=!seg;n[i]=seg?a[i]:b[i];}return n;},
  distance(a,b){let s=0;for(let i=0;i<GC;i++)s+=Math.abs(a[i]-b[i]);return s/GC;},
  serialize(g){return Array.from(g).map(v=>v.toFixed(3)).join(',');},
  deserialize(s){const a=s.split(',').map(Number),g=new Float32Array(GC);
    for(let i=0;i<GC;i++)g[i]=isFinite(a[i])?a[i]:Math.random();return g;}
};

/* ---------- 細胞型（12種）→ 器官サイズの控えめな補正に使う ---------- */
const CELL_TYPES={
  photo:{gene:13,name:'光合成'}, chemo:{gene:14,name:'化学合成'}, digest:{gene:8,name:'消化'},
  transport:{gene:12,name:'循環'}, nerve:{gene:4,name:'神経'}, muscle:{gene:1,name:'筋肉'},
  sensor:{gene:7,name:'感覚'}, flagella:{gene:17,name:'運動'}, toxin:{gene:11,name:'毒'},
  armor:{gene:2,name:'装甲'}, stem:{gene:9,name:'幹細胞'}, adhesion:{gene:3,name:'接着'}
};
function cellCountsOf(g){const raw={};let sum=0;
  for(const k in CELL_TYPES){const v=Math.max(0,g[CELL_TYPES[k].gene]||0);raw[k]=v;sum+=v;}
  const out={};if(sum<=0){for(const k in CELL_TYPES)out[k]=1/12;return out;}
  for(const k in raw)out[k]=raw[k]/sum;return out;}
function dominantCellOf(cc){let best=null,bv=-1;for(const k in cc)if(cc[k]>bv){bv=cc[k];best=k;}return best;}

/* ---------- 体色（生理遺伝子由来） ---------- */
function hsl2rgb(h,s,l){h=((h%360)+360)%360;h/=360;const a=s*Math.min(l,1-l);
  const f=n=>{const k=(n+h*12)%12;return l-a*Math.max(-1,Math.min(Math.min(k-3,9-k),1));};
  return[f(0),f(8),f(4)];}
const LifeGfx={
  // 実在動物を意識した自然な体色。陸生動物は茶・褐・灰・橙・黒・生成りの毛色帯へ。
  // 生物学的に鮮やかであるべきもの（有毒＝警告色／水棲＝青銀／植物＝緑）のみ高彩度を許す。
  color(g){
    const photo=g[13],toxin=g[11],aqua=g[20];
    const rnd=mulberry32(hashGenome(g)),a=rnd(),b=rnd(),c=rnd();
    // 植物：緑
    if(photo>0.5) return hsl2rgb(88+a*62, 0.38+photo*0.3, 0.28+a*0.14);
    // 有毒：警告色（黄→橙→赤→紫、高彩度）
    if(toxin>0.55){const wh=[52,30,8,286][Math.floor(b*4)%4]; return hsl2rgb(wh, 0.82, 0.46+a*0.1);}
    // 水棲：青〜青緑〜銀
    if(aqua>0.55) return hsl2rgb(188+a*46, 0.28+b*0.32, 0.4+a*0.16);
    // 陸生動物：自然な毛色帯
    const big=g[16]>0.62, gray=(big&&(g[0]>0.45||g[2]>0.4))||c>0.83;   // 大型＋厚皮/装甲→灰(サイ/ゾウ)
    let hue=25+a*16;                    // 茶〜琥珀
    if(b<0.26) hue=8+a*12;             // 赤褐色(キツネ/レッサーパンダ/トラ)
    else if(b>0.9) hue=40+a*8;         // 砂色寄り
    let sat=gray?0.05+a*0.1:0.28+b*0.3;
    let lig=gray?0.36+a*0.28:0.34+a*0.38;   // 中間茶〜クリーム（縞/斑とのコントラストを確保）
    return hsl2rgb(hue,sat,lig);
  }
};

/* ---------- 統一成長文法（樹木の枝も四肢の指も同じ再帰で伸ばす） ---------- */
function growBranch(S,start,dir,radius,length,depth,out,parentId,role,mg){
  if(out.strokes.length>=S.budget)return;
  const P=S.P,rng=S.rng;
  const segLen=Math.max(radius*1.2,length/Math.max(3,Math.round(length/(radius*1.8))));
  const nseg=Math.max(2,Math.min(14,Math.round(length/segLen)));
  let cur=start.slice(),d=V.norm(dir),r=radius;
  const pts=[{p:cur.slice(),r}];
  let up=Math.abs(d[2])>0.9?[1,0,0]:[0,0,1];
  let side=V.norm(V.cross(d,up)),phase=rng()*6.283;
  for(let i=1;i<=nseg;i++){
    const t=i/nseg,tro=[0,0,(depth===0?P.photo:-P.gravity*0.5)];
    d=V.norm(V.add(V.add(d,V.scale(tro,0.12)),V.scale(side,(rng()-0.5)*P.wiggle)));
    cur=V.add(cur,V.scale(d,segLen));
    r=Math.max(P.minR,radius*(1-t*P.taper));
    pts.push({p:cur.slice(),r});
    if(depth<P.maxDepth){
      const doBranch=P.branchAlong?(rng()<P.branchProb):(i===nseg);
      if(doBranch)for(let b=0;b<P.branchCount;b++){phase+=P.phyllo;
        const ax=rot(side,d,phase),cd=rot(d,ax,P.branchAngle*(0.65+rng()*0.7));
        growBranch(S,cur.slice(),cd,r*P.branchRatio,length*P.lenRatio,depth+1,out,parentId,'limb',mg);}
    }
  }
  out.strokes.push({pts,fiber:Math.max(1,Math.round(P.fiber*(1-depth/(P.maxDepth+1.5)))),depth,kind:P.strokeKind});
  const end=cur.slice(),endDir=d.slice();
  if(P.apical&&depth<P.maxDepth&&r>P.minR*1.6)
    growBranch(S,end,endDir,r*P.apicalR,length*P.apicalLen,depth+1,out,parentId,'axis',mg);
  else P.tips.forEach(tip=>{if(rng()<tip.prob)
    out.organs.push({type:tip.type,p:end.slice(),dir:endDir.slice(),size:r*tip.size,depth,col:tip.col});});
}

/* ---------- 生成結果からの表示専用ラベル ---------- */
function classifyFormLabel(sessility,aquaticOnly,radiality,isMicro,jaw,armor,legCount){
  if(isMicro)return'microbe';
  if(sessility>0.5){
    if(aquaticOnly>0.5)return'seaweed';
    if(legCount===0&&aquaticOnly<0.2)return'grass';
    return'plant';
  }
  if(radiality>0.55)return'radialoid';
  if(legCount>=6&&armor>0.32)return'arthropod';
  if(aquaticOnly>0.55&&jaw<0.4)return'swimmer';
  if(jaw>0.5)return'predator';
  return'worm';
}
const PLAN_NAMES={microbe:'微生物',seaweed:'海藻',grass:'草',plant:'植物',radialoid:'放射体',
  arthropod:'節足動物',swimmer:'遊泳者',predator:'捕食者',worm:'蠕虫'};
// 体制（アーキタイプ）の名前も同じ表で引けるようにする（後で ARCH から追加）

/* ============================================================
   体制（アーキタイプ）— 遺伝子の組み合わせと進化段階から、実在の動植物群に対応する姿を選ぶ
   ・grade（Evolution.js の進化段階）を渡すと、その段階で現れうる体制だけから選ぶ
     （刺胞動物は段階4、カンブリアの魚・節足動物・軟体動物・棘皮動物は6、陸の両生類・昆虫・クモは7、
       最初の有羊膜類＝トカゲ型は8、ヘビ・カメ・ワニ・鳥・哺乳類は9）
   ・grade を省略すると制限なし（遺伝子だけで選ぶ）
   ============================================================ */
const ARCH={
  microbe:{name:'微生物'},
  sponge:{name:'海綿・平板動物'},
  jellyfish:{name:'クラゲ'},anemone:{name:'イソギンチャク'},coral:{name:'サンゴ'},
  worm:{name:'蠕虫'},
  fish:{name:'魚'},shark:{name:'サメ'},crab:{name:'カニ・エビ'},snail:{name:'巻貝'},octopus:{name:'タコ'},starfish:{name:'ヒトデ'},
  insect:{name:'昆虫'},spider:{name:'クモ'},frog:{name:'カエル'},salamander:{name:'イモリ・サンショウウオ'},
  lizard:{name:'トカゲ'},snake:{name:'ヘビ'},turtle:{name:'カメ'},crocodile:{name:'ワニ'},bird:{name:'鳥'},mammal:{name:'哺乳類'},
  seaweed:{name:'海藻'},grass:{name:'草'},fern:{name:'シダ'},tree:{name:'樹木'},flower:{name:'花'},cactus:{name:'サボテン'},mushroom:{name:'キノコ'},
};
function geneFeatures(g){
  return{photo:g[13],motor:g[17],size:g[16],aqua:g[20],armor:g[0]*0.6+g[2]*0.4,jaw:g[22],
    neural:g[4]*0.5+g[7]*0.5,radial:g[28],limbs:g[24],seg:g[27],tox:g[11],heat:g[18],fec:g[21],stem:g[9],
    wood:g[3]*0.7+g[16]*0.4,
    // 分解者（菌類）: 消化が強く、光合成も捕食もしない
    decomp:g[8]>0.6&&g[13]<0.35&&g[22]<0.45&&g[10]<0.55,
    // 植物かどうかはゲーム本体の栄養段階（LifeGfx.trophic）と同じ基準にそろえる
    plant:(g[13]+g[14])>0.9||((g[13]+g[14])>0.5&&(g[12]+g[22])<0.6)};
}
function chooseArch(g,grade){
  const f=geneFeatures(g),any=grade==null;
  const microScale=Math.max(0,Math.min(1,0.85-g[16]*0.9-Math.max(2,Math.floor(2+g[27]*7+g[1]*3))*0.02));
  // 段階を渡されたときは段階で決める（段階3以上の多細胞生物は、小さくても微生物の姿にしない）
  // 段階なしのときは、小さくて多細胞化の遺伝子（接着・幹細胞）が低いものを微生物とする（rStage と同じ基準）
  if(any?(microScale>0.55&&(g[3]+g[9])*0.5<0.35):grade<=2)return 'microbe';
  // 植物
  if(f.plant){
    if(f.aqua>0.55||(!any&&grade<7))return 'seaweed';
    if(f.heat>0.62&&(any||grade>=9))return 'cactus';
    if(f.fec>0.62&&(any||grade>=9))return 'flower';
    if(f.wood>0.55&&f.size>0.4)return 'tree';
    if(f.stem>0.55)return 'fern';
    return 'grass';
  }
  // 菌類
  if(f.decomp&&f.motor<0.3&&(any||grade>=3))return 'mushroom';
  const G=any?null:grade;
  // 段階ごとの候補
  if(G===3)return 'sponge';
  const cnid=()=>f.motor<0.3?(f.armor>0.45?'coral':'anemone'):'jellyfish';
  if(G===4)return cnid();
  if(G===5)return 'worm';
  const marine=()=>{
    if(f.armor>0.4&&f.motor<0.45)return f.neural<0.4?'starfish':'snail';
    if(f.neural>0.55&&f.armor<0.3&&f.limbs>0.5)return 'octopus';
    if(g[2]>=0.35)return 'crab';
    if(f.jaw>0.45&&f.size>0.5)return 'shark';
    return 'fish';};
  if(G===6)return marine();
  // 節足動物: 外骨格（装甲）があり小型。外骨格と気管呼吸が体の大きさを制限する（Harrison et al. 2010）
  const arthro=()=>g[2]>=0.35&&f.size<0.55?(f.aqua>0.55?'crab':f.jaw>0.5?'spider':'insect'):null;
  if(G===7)return arthro()||(f.seg>0.55||(f.size<0.4&&f.motor<0.5)?'salamander':'frog');
  if(G===8)return arthro()||'lizard';
  // 段階9以上（制限なし）
  const amniote=()=>{
    if(f.motor>0.8&&f.size<0.45&&f.neural>0.45)return 'bird';              // 飛ぶには非常に高い運動能力が要る
    if(f.neural>0.45&&g[5]>0.55)return 'mammal';                    // 内温性（神経維持が高い）は哺乳類
    if(f.armor>0.6&&f.motor<0.5)return 'turtle';
    if(f.jaw>0.5&&f.size>0.55&&f.aqua>0.35)return 'crocodile';
    if(f.limbs<0.22||(f.seg>0.72&&f.size<0.6))return 'snake';
    return 'lizard';};
  if(!any)return arthro()||amniote();
  // 制限なし: 遺伝子だけで、水中・放射・節足・両生・脊椎動物を選び分ける
  if(f.radial>0.45||(f.aqua>0.6&&f.neural<0.3&&f.armor<0.35))return cnid();
  if(f.limbs<0.15&&f.neural<0.35&&f.armor<0.35)return 'worm';
  if(f.aqua>0.7)return marine();
  const ar=arthro();if(ar)return ar;
  if(f.aqua>0.38)return f.seg>0.55?'salamander':'frog';
  return amniote();
}

/* ============================================================
   本体：ゲノム → 3D生物モデル
   ============================================================ */
// 物理リグ用：直前の growBranch 呼び出しで追加されたストロークに部位グループを付与
function tagStrokes(out,from,group,extra){for(let k=from;k<out.strokes.length;k++){const st=out.strokes[k];if(!st.group)st.group=group;if(extra)Object.assign(st,extra);}}
function buildModelMorpho(g,opt){
  opt=opt||{};
  const clamp=Genome.clamp;
  const cellCounts=cellCountsOf(g),dominantCell=dominantCellOf(cellCounts);
  const cellSizeMul=k=>0.7+Math.min(1,(cellCounts[k]||0)*8)*0.7;
  const rng=mulberry32(hashGenome(g)),size=3+g[16]*9;let col=LifeGfx.color(g);
  // 体制（アーキタイプ）: 遺伝子と進化段階から選ぶ
  const A=opt.arch||chooseArch(g,opt.grade);
  let radiality=g[28];
  const bilateral=radiality<0.5;
  let segN=Math.max(2,Math.floor(2+g[27]*7+g[1]*3));
  const armor=g[0]*0.6+g[2]*0.4,jaw=g[22],photo=g[13],toxin=g[11],
        neural=g[4]*0.5+g[7]*0.5,motor=g[17];

  // 連続派生フラグ（離散plan判定の置き換え）
  let sessility=clamp(photo*0.8-motor*0.55+0.12);
  let aquaticOnly=clamp(g[20]*1.35-0.4);
  let woodiness=clamp(g[3]*0.7+g[16]*0.4-sessility*0.15);
  let elongation=clamp(1-g[16]*0.65);
  const microScale=clamp(0.5-g[16]*0.9-segN*0.02+0.35);
  let limbPairsEst=Math.round(g[24]*5*(1-sessility)*(1-radiality*0.6));
  let uprightness=clamp(motor*0.55+neural*0.45-Math.min(1,limbPairsEst*0.22)-radiality*0.3);
  let parasagittalBias=clamp(neural*0.5+motor*0.35-armor*0.3-radiality*0.4);

  // ---- 体制ごとの骨格の調整（F: 頭部・尾・肢・体表の作り分け） ----
  const F={noTail:0,noEars:0,noTeeth:0,noHead:0,noWhisker:1,integ:null,skipDiv:0,tailLen:1,hindMul:1,legLenMul:1,legRMul:1,
    shape:null,bodyZ:1,armsN:null,armR:1,fins:0,fly:0,skin:null};
  const hrng=mulberry32((hashGenome(g)^0x2c1b3c6d)>>>0),h1=hrng(),h2=hrng();
  const sprawl=()=>{parasagittalBias=0;};
  switch(A){
    case'sponge':sessility=0.8;radiality=0.25;woodiness=0;F.skin=4;col=hsl2rgb(38+h1*20,0.55,0.5+h2*0.12);break;
    case'anemone':sessility=0.85;radiality=0.1;woodiness=0;F.skin=0;col=hsl2rgb([350,20,140,300][Math.floor(h1*4)],0.6,0.5);break;
    case'coral':sessility=0.95;radiality=0.1;woodiness=0.3;F.skin=1;col=hsl2rgb([5,20,330,280,45][Math.floor(h1*5)],0.62,0.55);break;
    case'mushroom':sessility=0.9;radiality=0;woodiness=0;F.skin=0;col=toxin>0.5?[0.82,0.12,0.08]:hsl2rgb(28+h1*14,0.35,0.42+h2*0.25);break;
    case'seaweed':case'grass':case'fern':case'flower':sessility=Math.max(sessility,0.75);if(photo<0.5)col=hsl2rgb(95+h1*40,0.45,0.32+h2*0.1);break;
    case'tree':sessility=Math.max(sessility,0.85);woodiness=Math.max(woodiness,0.7);F.skin=4;if(photo<0.5)col=hsl2rgb(95+h1*40,0.45,0.32+h2*0.1);break;
    case'cactus':sessility=0.9;woodiness=0.15;col=hsl2rgb(105+h1*25,0.4,0.36);F.skin=0;break;
    case'worm':sessility=0;limbPairsEst=0;radiality=0;elongation=Math.max(elongation,0.85);uprightness=0;F.noEars=1;F.noTeeth=1;F.skipDiv=1;F.skin=0;break;
    case'fish':case'shark':sessility=0;aquaticOnly=Math.max(aquaticOnly,0.75);limbPairsEst=0;radiality=0;uprightness=0;F.noEars=1;F.fins=1;F.skipDiv=1;
      F.integ=A==='fish'?'scale':'none';F.skin=A==='fish'?1:0;F.shape=A;if(A==='shark'){elongation=Math.max(elongation,0.65);col=hsl2rgb(205+h1*15,0.12+h2*0.1,0.42+h1*0.1);}break;
    case'crab':sessility=0;radiality=0;limbPairsEst=4;uprightness=0;elongation=0.15;F.noTail=1;F.noEars=1;F.noTeeth=1;F.shape='flat';F.skipDiv=1;F.integ='none';F.skin=3;F.legRMul=0.6;sprawl();
      if(aquaticOnly>0.55)col=hsl2rgb(8+h1*20,0.6,0.42);break;
    case'snail':sessility=0;radiality=0;limbPairsEst=0;uprightness=0;elongation=0.45;F.noTail=1;F.noEars=1;F.noTeeth=1;F.shape='foot';F.bodyZ=0.45;F.skipDiv=1;F.integ='none';F.skin=0;
      col=hsl2rgb(30+h1*15,0.18,0.48);break;
    case'octopus':sessility=0;radiality=0.6;F.armsN=8;F.armR=1.5;limbPairsEst=0;uprightness=0;elongation=0.1;F.noTail=1;F.noEars=1;F.noTeeth=1;F.shape='mantle';F.skipDiv=1;F.integ='none';F.skin=0;
      col=hsl2rgb(h1<0.5?8+h2*20:290+h2*30,0.5,0.45);break;
    case'starfish':sessility=0;radiality=0.7;F.armsN=5;F.armR=1.9;limbPairsEst=0;uprightness=0;elongation=0;F.noTail=1;F.noHead=1;F.shape='disc';F.bodyZ=0.4;F.skipDiv=1;F.integ='none';F.skin=1;
      col=hsl2rgb([18,32,280,350][Math.floor(h1*4)],0.65,0.5);break;
    case'insect':sessility=0;radiality=0;limbPairsEst=3;uprightness=0.05;elongation=0.55;F.noTail=1;F.noEars=1;F.noTeeth=1;F.shape='insect';F.skipDiv=1;F.integ='none';F.skin=3;
      F.legRMul=0.4;F.legLenMul=0.95;sprawl();F.fly=motor>0.5;break;
    case'spider':sessility=0;radiality=0;limbPairsEst=4;uprightness=0;elongation=0.45;F.noTail=1;F.noEars=1;F.noTeeth=1;F.shape='spider';F.skipDiv=1;F.integ='none';F.skin=2;
      F.legRMul=0.35;F.legLenMul=1.45;sprawl();col=hsl2rgb(25+h1*20,0.25,0.22+h2*0.15);break;
    case'frog':sessility=0;radiality=0;limbPairsEst=2;uprightness=0.25;elongation=0.25;aquaticOnly=Math.min(aquaticOnly,0.3);F.noTail=1;F.noEars=1;F.noTeeth=1;F.shape='frog';F.integ='none';F.skin=0;
      F.hindMul=1.8;sprawl();if(toxin<=0.55)col=hsl2rgb(80+h1*45,0.45,0.36+h2*0.12);break;
    case'salamander':F.shape='long';sessility=0;radiality=0;limbPairsEst=2;uprightness=0;elongation=Math.max(elongation,0.85);aquaticOnly=Math.min(aquaticOnly,0.3);F.noEars=1;F.noTeeth=1;F.integ='none';F.skin=0;
      F.legRMul=0.7;F.legLenMul=0.55;F.tailLen=1.4;sprawl();break;
    case'lizard':F.shape='long';sessility=0;radiality=0;limbPairsEst=2;uprightness=0;elongation=Math.max(elongation,0.7);aquaticOnly=Math.min(aquaticOnly,0.3);F.noEars=1;F.integ='scale';F.skin=1;
      F.legLenMul=0.65;F.tailLen=1.6;sprawl();break;
    case'snake':F.shape='thin';sessility=0;radiality=0;limbPairsEst=0;uprightness=0;elongation=1;segN=Math.max(segN,10);aquaticOnly=Math.min(aquaticOnly,0.3);F.noEars=1;F.integ='scale';F.skin=1;F.tailLen=1.3;F.skipDiv=1;break;
    case'turtle':sessility=0;radiality=0;limbPairsEst=2;uprightness=0;elongation=0.15;F.noEars=1;F.noTeeth=1;F.integ='none';F.skin=1;F.legLenMul=0.5;F.legRMul=1.25;F.tailLen=0.35;F.shape='turtle';F.skipDiv=1;sprawl();break;
    case'crocodile':F.shape='long';sessility=0;radiality=0;limbPairsEst=2;uprightness=0;elongation=Math.max(elongation,0.75);F.noEars=1;F.integ='none';F.skin=3;F.legLenMul=0.5;F.tailLen=1.7;F.skipDiv=1;sprawl();
      col=hsl2rgb(75+h1*20,0.25,0.26+h2*0.08);break;
    case'bird':F.shape='bird';sessility=0;radiality=0;limbPairsEst=1;uprightness=0.75;elongation=0.35;aquaticOnly=Math.min(aquaticOnly,0.3);F.noEars=1;F.noTeeth=1;F.integ='feather';F.skin=2;F.legRMul=0.5;F.legLenMul=1.05;F.tailLen=0.45;F.skipDiv=1;
      F.fly=motor>0.55&&g[16]<0.6;break;
    case'mammal':sessility=0;radiality=0;limbPairsEst=2;uprightness=Math.min(uprightness,0.35);parasagittalBias=Math.max(parasagittalBias,0.7);aquaticOnly=Math.min(aquaticOnly,0.3);F.integ='hair';F.noWhisker=0;F.skin=2;break;
    case'jellyfish':col=hsl2rgb([200,320,280,30][Math.floor(h1*4)],0.45,0.72);F.skin=0;break;
  }

  let legCount=0,legPower=0;
  const out={strokes:[],organs:[]},mg={nodes:[]},S={rng,P:null,g,size,budget:260},L=size;
  // 棘の色：真に有毒なら警告色（黄）、そうでなければ角質(ベージュ/骨色)。ネオン色を避ける。
  const spikeCol=toxin>0.6?[0.92,0.8,0.16]:[0.52,0.45,0.36];
  const spikeTip={type:'spike',prob:Math.min(1,toxin*1.2),size:0.7*cellSizeMul('toxin'),col:spikeCol};

  const builtAsMicrobe=A==='microbe'||(microScale>0.55&&!ARCH[A]);
  const axisLen=L*(0.9+elongation*1.6+g[16]*1.4+sessility*0.6)*(A==='anemone'||A==='mushroom'?0.45:A==='cactus'?0.8:A==='sponge'?0.55:A==='snake'?1.7:A==='crocodile'?1.2:A==='bird'?0.65:A==='shark'?1.25:1);
  const axisR=size*(0.32+sessility*0.28)*(A==='cactus'?1.9:A==='anemone'?1.5:A==='sponge'?1.4:A==='mushroom'?0.6:1);
  const bodyPts=[];

  if(A==='jellyfish'){
    // クラゲ: 半透明の傘と、傘の縁から垂れる触手（浮遊。物理は微生物と同じ浮遊モード）
    const bellZ=size*1.6,nT=8+Math.round(g[29]*8);
    out.organs.push({type:'bell',p:[0,0,bellZ],dir:[0,0,1],size:size*1.05,depth:0,free:1});
    out.organs.push({type:'core',p:[0,0,bellZ-size*0.1],dir:[0,0,1],size:size*0.35,depth:0,free:1});
    S.P={maxDepth:0,branchAlong:false,branchProb:0,branchCount:0,branchAngle:0,branchRatio:0.6,lenRatio:0.6,taper:0.75,minR:size*0.02,
      fiber:1,wiggle:0.45,photo:0,gravity:0.9,apical:false,apicalR:0.8,apicalLen:0.7,phyllo:1,strokeKind:'soft',tips:[]};
    for(let k=0;k<nT;k++){const a=k/nT*6.283,b0=out.strokes.length;
      growBranch(S,[Math.cos(a)*size*0.85,Math.sin(a)*size*0.85,bellZ-size*0.3],[Math.cos(a)*0.08,Math.sin(a)*0.08,-1],size*0.05,L*(1.4+motor),0,out,null,'limb',mg);tagStrokes(out,b0,'cilia');}
    for(let k=0;k<4;k++){const a=k/4*6.283+0.4,b0=out.strokes.length;   // 口腕
      growBranch(S,[Math.cos(a)*size*0.2,Math.sin(a)*size*0.2,bellZ-size*0.35],[Math.cos(a)*0.15,Math.sin(a)*0.15,-1],size*0.16,L*0.9,0,out,null,'limb',mg);tagStrokes(out,b0,'cilia');}
  }else if(builtAsMicrobe){
    const cilia=Math.max(3,Math.round(4+motor*10*microScale));
    S.P={maxDepth:0,branchAlong:false,branchProb:0,branchCount:0,branchAngle:0,branchRatio:0.6,
      lenRatio:0.6,taper:0.5,minR:size*0.1,fiber:1,wiggle:0.35,photo:0,gravity:0,apical:false,
      apicalR:0.8,apicalLen:0.7,phyllo:1.8,strokeKind:'soft',tips:[]};
    for(let c=0;c<cilia;c++){const ang=c/cilia*6.283,b0=out.strokes.length;
      growBranch(S,[0,0,size*0.6],[Math.cos(ang),Math.sin(ang),(rng()-0.5)*0.5],
        size*0.14,L*0.45*microScale,0,out,null,'limb',mg);tagStrokes(out,b0,'cilia');}
    out.organs.push({type:'core',p:[0,0,size*0.6],dir:[0,0,1],size:size*0.7,depth:0});
  }else if(sessility<=0.5){
    // 動物寄り体軸：明示的な点列
    const nBody=Math.max(4,segN+2);
    // 姿勢傾斜：直立傾向ほど尾側(股関節)を支点に頭側を持ち上げる
    const standAngle=uprightness*1.0,csA=Math.cos(standAngle),snA=Math.sin(standAngle),
          pivotX=-0.5*axisLen,pivotZ=size*0.9;
    for(let i=0;i<=nBody;i++){
      const t=i/nBody,bulge=Math.pow(Math.sin(t*Math.PI),0.6+microScale*0.3);
      let rw=size*(0.35+bulge*0.85)*(0.55+elongation*0.55),rh=rw;
      if(g[32]<0.5){const f=g[32]*2;rw*=(1+f*0.55);rh*=(1-f*0.4);}
      else{const f=(g[32]-0.5)*2;rw*=(1.55-f*0.55);rh*=(0.6+f*0.55);}
      const neckT=clamp((t-0.78)/0.22),pelvisT=clamp((0.18-t)/0.18);
      const regionMul=(1-neckT*neckT*0.5)*(1-pelvisT*pelvisT*0.35);
      rw*=regionMul;rh*=regionMul;
      // 体制ごとの体の断面
      if(F.shape==='flat'){rw*=1.7;rh*=0.5;}                                   // カニ: 平たく幅広い甲
      else if(F.shape==='foot'){rw*=0.85;rh*=0.4;}                             // 巻貝: 這う足
      else if(F.shape==='disc'){rw*=0.5;rh*=0.3;}                              // ヒトデ: 平たい中心盤
      else if(F.shape==='mantle'){const m=0.55+1.3*Math.pow(t,1.4);rw*=m;rh*=m*1.15;}   // タコ: 頭側の大きな外套膜
      else if(F.shape==='insect'){const pinch=x=>0.35+0.65*clamp(Math.abs(t-x)/0.07);rw*=pinch(0.4)*pinch(0.75)*(t<0.4?1.25:1);rh*=pinch(0.4)*pinch(0.75);}   // 頭・胸・腹
      else if(F.shape==='spider'){const p=0.3+0.7*clamp(Math.abs(t-0.5)/0.08);rw*=p*(t<0.5?1.45:0.85);rh*=p*(t<0.5?1.35:0.8);}   // 頭胸部と大きな腹部
      else if(F.shape==='frog'){rw*=1.35;rh*=0.85;}
      else if(F.shape==='turtle'){rw*=1.2;rh*=0.75;}
      else if(F.shape==='long'){rw*=0.36;rh*=0.36;}                            // トカゲ・イモリ・ワニ: 細長く低い胴
      else if(F.shape==='thin'){rw*=0.3;rh*=0.28;}                             // ヘビ: 細いひも状
      else if(F.shape==='fish'){rw*=0.42;rh*=0.72;}                            // 魚: 左右に平たく背が高い
      else if(F.shape==='shark'){rw*=0.5;rh*=0.55;}                            // サメ: 紡錘形
      else if(F.shape==='bird'){rw*=0.62;rh*=0.7;}                             // 鳥: 小さくまとまった胴
      const bendPrimary=Math.sin(t*3.1+(g[1]-0.5)*4),bendSecondary=Math.sin(t*6.2+(g[1]-0.5)*4+Math.PI);
      const bend=(bendPrimary*(1-uprightness*0.6)+bendSecondary*uprightness*0.6)*size*0.5*g[1]*(1-radiality*0.7);
      const dx=(t-0.5)*axisLen-pivotX;
      bodyPts.push({p:[pivotX+dx*csA,bend,pivotZ*F.bodyZ+dx*snA],r:(rw+rh)*0.5,rw,rh});
    }
    out.strokes.push({pts:bodyPts,fiber:Math.max(1,Math.round((g[1]*0.6+g[0]*0.4)*6+1)),depth:0,kind:'muscle',group:'body'});
    // countershading：腹側(肢側)に淡いストロークを並走
    if(bodyPts.length>=3){
      const bellyPts=bodyPts.map(pt=>({p:[pt.p[0],pt.p[1],pt.p[2]-pt.r*0.62],
        r:pt.r*0.58,rw:pt.rw*0.58,rh:pt.rh*0.42}));
      out.strokes.push({pts:bellyPts,fiber:1,depth:0,kind:'belly',group:'belly'});
    }
  }else{
    // 固着寄り体軸（植物）
    const stemN=Math.max(1,Math.round(1+radiality*(0.6+g[29]*6)*(0.4+sessility*0.6)));
    S.P={maxDepth:Math.round(1+sessility*2.2),branchAlong:sessility>0.7,
      branchProb:0.15+sessility*0.5+g[9]*0.25,
      branchCount:Math.max(1,Math.round(1+sessility*1.4+g[9]*1.6)),
      branchAngle:0.25+g[6]*0.55+sessility*0.25,branchRatio:0.62+g[2]*0.16,
      lenRatio:0.6+sessility*0.16,taper:0.14+(1-sessility)*0.18,minR:size*(0.045+microScale*0.05),
      fiber:Math.max(1,Math.round(1+woodiness*5+g[3]*3)),wiggle:0.12+g[11]*0.25+sessility*0.15,
      photo:photo*0.9,gravity:0.05+(1-sessility)*0.55,apical:sessility>0.35,apicalR:0.8+sessility*0.08,
      apicalLen:0.72+sessility*0.2,phyllo:1.1+sessility*1.3,strokeKind:woodiness>0.55?'wood':'soft',
      tips:[{type:'leaf',prob:Math.min(1,photo*1.3),size:(1.1+g[16]*1.8)*cellSizeMul('photo')},
            {type:'fruit',prob:g[21]*0.45,size:0.85},spikeTip]};
    // 固着生物の体制ごとの作り分け
    let nStem=stemN;
    if(A==='anemone'||A==='mushroom'){Object.assign(S.P,{maxDepth:0,apical:false,taper:A==='mushroom'?0.05:0.1,wiggle:0.04,tips:[],strokeKind:'soft'});nStem=1;}
    else if(A==='sponge'){Object.assign(S.P,{maxDepth:0,apical:false,taper:-0.15,wiggle:0.08,tips:[],strokeKind:'soft'});nStem=1+Math.round(g[9]*2);}
    else if(A==='coral'){Object.assign(S.P,{maxDepth:3,branchAlong:true,branchProb:0.45,branchCount:2,branchAngle:0.6,taper:0.25,wiggle:0.2,
      strokeKind:'soft',apical:false,tips:[{type:'polyp',prob:1,size:1.2,col:[Math.min(1,col[0]+0.25),Math.min(1,col[1]+0.25),Math.min(1,col[2]+0.25)]}]});}
    else if(A==='tree'){Object.assign(S.P,{maxDepth:3,strokeKind:'wood',tips:[{type:'foliage',prob:0.85,size:3.2},{type:'fruit',prob:g[21]*0.3,size:0.85}]});nStem=1;}
    else if(A==='fern'){Object.assign(S.P,{maxDepth:2,branchAlong:true,branchProb:0.85,branchCount:2,branchAngle:1.0,apical:false,lenRatio:0.42,strokeKind:'soft',
      tips:[{type:'leaf',prob:1,size:1.1}]});nStem=3+Math.round(g[9]*3);}
    else if(A==='flower'){S.P.tips=[{type:'flower',prob:0.9,size:1.8,col:hsl2rgb([0,45,280,330,55,210][Math.floor(h1*6)],0.75,0.62)},{type:'leaf',prob:0.5,size:1.3}];}
    else if(A==='cactus'){Object.assign(S.P,{maxDepth:1,branchAlong:true,branchProb:0.25,branchCount:1,branchAngle:1.1,apical:false,taper:0.05,photo:2.5,wiggle:0.02,
      strokeKind:'soft',tips:[{type:'flower',prob:g[21],size:1.0,col:hsl2rgb(330+h2*60,0.7,0.6)}]});nStem=1;}
    for(let st=0;st<nStem;st++){
      const ang=(st/stemN)*6.283+rng()*0.5,b0=out.strokes.length;
      const dir=radiality>0.3?[Math.cos(ang)*(0.3+radiality*0.7),Math.sin(ang)*(0.3+radiality*0.7),1-radiality*0.75]:
        (A==='fern'||A==='sponge')&&nStem>1?[Math.cos(ang)*0.45,Math.sin(ang)*0.45,1]:[0,0,1];
      growBranch(S,[Math.cos(ang)*size*0.12*radiality,Math.sin(ang)*size*0.12*radiality,0],
        dir,axisR*(0.9+g[16]*0.4),axisLen*(0.55+sessility*0.35),0,out,null,'axis',mg);
      tagStrokes(out,b0,'plant',{stem:st});
    }
    if(radiality>0.4)out.organs.push({type:'core',p:[0,0,size*0.3],dir:[0,0,1],size:size*(0.55+radiality*0.4),depth:0});
    const topZ=()=>{let z=0,p=[0,0,0];out.strokes.forEach(st=>st.pts.forEach(q=>{if(q.p[2]>z){z=q.p[2];p=q.p;}}));return p;};
    if(A==='anemone'){   // 口のまわりの触手の冠
      const tp=topZ(),nT=10+Math.round(g[29]*10);
      S.P={maxDepth:0,branchAlong:false,branchProb:0,branchCount:0,branchAngle:0,branchRatio:0.6,lenRatio:0.6,taper:0.6,minR:size*0.03,fiber:1,wiggle:0.25,
        photo:0.4,gravity:0,apical:false,apicalR:0.8,apicalLen:0.7,phyllo:1,strokeKind:'soft',tips:[]};
      for(let k=0;k<nT;k++){const a=k/nT*6.283,b0=out.strokes.length;
        growBranch(S,[tp[0]+Math.cos(a)*axisR*0.7,tp[1]+Math.sin(a)*axisR*0.7,tp[2]],[Math.cos(a)*0.7,Math.sin(a)*0.7,0.8],size*0.07,L*0.75,0,out,null,'limb',mg);tagStrokes(out,b0,'plant');}
    }else if(A==='mushroom'){   // 傘とひだ。有毒なら赤い傘に白い斑点
      const tp=topZ(),cs=size*(0.9+g[16]*0.6);
      out.organs.push({type:'cap',p:[tp[0],tp[1],tp[2]+cs*0.1],dir:[0,0,1],size:cs,depth:0,free:1});
      if(toxin>0.5)for(let k=0;k<9;k++){const a=k*2.4,r=cs*(0.25+0.45*((k*0.37)%1));
        out.organs.push({type:'marking',p:[tp[0]+Math.cos(a)*r,tp[1]+Math.sin(a)*r,tp[2]+cs*0.38],dir:[0,0,1],size:cs*0.16,depth:1,col:[0.96,0.94,0.9],free:1});}
    }else if(A==='cactus'){   // 刺の列
      out.strokes.filter(st=>st.group==='plant').forEach(st=>st.pts.forEach((q,i)=>{for(let k=0;k<5;k++){const a=k/5*6.283+i;
        out.organs.push({type:'spike',p:[q.p[0]+Math.cos(a)*q.r,q.p[1]+Math.sin(a)*q.r,q.p[2]],dir:[Math.cos(a),Math.sin(a),0.2],size:size*0.12,depth:1,col:[0.92,0.88,0.72]});}}));
    }
  }

  /* ---- 肢（脚/腕）：前後/操作役割分化・関節屈曲・直下型/側方投出 ---- */
  const limbPairs=bodyPts.length?limbPairsEst:0;
  if(limbPairs>0){
    legCount=limbPairs*2;legPower=motor/(1+limbPairs*0.3);
    const legRBase=size*0.3/Math.sqrt(1+limbPairs*0.4)*(0.7+Math.min(1,((cellCounts.muscle||0)+(cellCounts.flagella||0))*5)*0.7);
    const jointDepthBase=1+Math.round(g[25]*2);
    const digitNBase=Math.max(1,Math.round(1+g[26]*3));
    const posBias=g[33],nBody=bodyPts.length-1;
    for(let s=0;s<limbPairs;s++){
      const frac=limbPairs>1?s/(limbPairs-1):0.5;
      const biased=frac+(posBias-0.5)*0.5*(1-Math.abs(frac-0.5)*2);
      // bodyPtsは末尾が頭側・先頭が尾側。frac=0(前列)は頭側へ→反転
      const bi=Math.round((1-clamp(biased))*nBody),base=bodyPts[Math.max(0,Math.min(nBody,bi))];
      const frontness=1-frac;
      const manip=clamp(uprightness*frontness*frontness);
      const legRoleTag=manip>0.45?'manipulator':(frac<0.5?'front':'back');
      const legR=legRBase*(1-manip*0.45)*F.legRMul;
      const jointDepth=Math.max(1,Math.round(jointDepthBase+(manip-0.3)*2));
      const digitN=Math.max(1,Math.round(digitNBase+manip*3));
      const legSegCount=Math.max(2,Math.min(4,2+Math.round(g[25]*2)+(manip>0.5?1:0)));
      const hoofBias=clamp(armor*0.6-manip*0.6+g[2]*0.25-toxin*0.3);
      S.P={maxDepth:1,branchAlong:false,branchProb:1,branchCount:digitN,
        branchAngle:0.55+g[26]*0.3+manip*0.2,branchRatio:0.72+g[25]*0.1,
        lenRatio:0.55+g[25]*0.06+jointDepth*0.05,taper:0.4+manip*0.15,minR:size*0.055,
        fiber:Math.max(1,Math.round(1+g[1]*3)),wiggle:0.1,photo:0,gravity:0.55*(1-manip*0.6),
        apical:false,apicalR:0.8,apicalLen:0.7,phyllo:0.9,strokeKind:'limb',
        tips:[{type:'digit',prob:Math.min(1,0.3+g[9]+manip*0.3)*(1-hoofBias*0.6),size:0.75},
              {type:'claw',prob:(g[22]*0.5+Math.min(0.4,legPower*0.5))*(1-manip*0.5)*(1-hoofBias*0.7),size:0.55+legPower*0.5},
              {type:'hoof',prob:Math.min(1,hoofBias*1.3),size:0.6+legR*0.3}]};
      const downDir=-0.5-motor*0.4*(1-manip*0.7);
      const standBias=parasagittalBias*(1-manip),legLat=1-standBias*0.65,legDown=downDir-standBias*0.35;
      [-1,1].forEach(sd=>{
        const before=out.strokes.length;
        growBranch(S,[base.p[0],base.p[1]+sd*base.r*0.7,base.p[2]],
          [0,sd*legLat,legDown],legR,L*(1.0+motor*1.4)*(1-manip*0.25)*F.legLenMul*(frac>=0.5?F.hindMul:1),1,out,null,'limb',mg);
        // 物理リグ用タグ：depth1=脚本体 / depth2=指（指は脚より先にpushされる）
        let legK=-1;for(let k=before;k<out.strokes.length;k++)if(out.strokes[k].depth===1){legK=k;break;}
        for(let k=before;k<out.strokes.length;k++){const st=out.strokes[k];
          if(st.depth===1){st.group='leg';st.side=sd;st.pair=s;st.frac=frac;}
          else{st.group='digit';st.legStroke=legK;}}
        for(let k=before;k<out.strokes.length;k++)if(out.strokes[k].depth===1){
          const st=out.strokes[k];st.segCount=legSegCount;st.legRole=legRoleTag;
          // 休息姿勢の関節屈曲（膝/足首で前後に折れるZ字）
          if(legRoleTag!=='manipulator'){
            const Pl=st.pts,nl=Pl.length;
            if(nl>=3){
              const hip=Pl[0].p,foot=Pl[nl-1].p,
                reach=Math.hypot(foot[0]-hip[0],foot[1]-hip[1],foot[2]-hip[2]);
              const bendSign=(legRoleTag==='front')?-1:1;
              const bendAmt=reach*(0.16+standBias*0.1);
              for(let i=1;i<nl-1;i++){const u=i/(nl-1);Pl[i].p[0]+=bendSign*bendAmt*Math.sin(u*6.283);}
            }
          }
        }
      });
    }
  }

  /* ---- 放射腕（放射相称寄り） ---- */
  if(radiality>0.15&&A!=='jellyfish'){
    const arms=F.armsN!=null?F.armsN:Math.max(0,Math.round(radiality*(3+g[29]*7)));
    if(arms>0){
      S.P={maxDepth:F.armsN!=null?1:Math.max(1,Math.round(1+g[25]*2)),branchAlong:false,branchProb:0.55,
        branchCount:Math.max(1,Math.round(1+g[26]*2)),branchAngle:0.5,branchRatio:0.7,lenRatio:0.62,
        taper:0.3,minR:size*0.05,fiber:2,wiggle:0.2,photo:0,gravity:0.12,apical:false,apicalR:0.8,
        apicalLen:0.7,phyllo:2.0,strokeKind:'soft',
        tips:[{type:'tentacle',prob:0.55,size:0.6},spikeTip]};
      const baseZ=bodyPts.length?bodyPts[Math.floor(bodyPts.length/2)].p[2]:size*0.5;
      for(let a=0;a<arms;a++){const ang=a/arms*6.283,b0=out.strokes.length;
        growBranch(S,[0,0,baseZ],[Math.cos(ang),Math.sin(ang),A==='starfish'?-0.05:0.2],
          size*0.14*F.armR,L*(0.8+radiality*0.6)*(A==='octopus'?1.5:A==='starfish'?1.8:1),1,out,null,'limb',mg);tagStrokes(out,b0,'arm',{armAng:ang});}
      legCount=Math.max(legCount,arms);
    }
  }

  /* ---- 頭部・目・顎・体表・尾（動物寄り体軸がある場合） ---- */
  if(bodyPts.length&&!F.noHead){
    const headP=bodyPts[bodyPts.length-1].p,tailP=bodyPts[0].p;
    out.organs.push({type:'head',p:headP.slice(),dir:[1,0,0],size:size*0.46*(A==='turtle'?0.7:A==='snake'?0.8:A==='frog'?1.25:1),depth:0});
    // 眼: 脊椎動物・頭足類・節足動物は一対、蠕虫などは神経しだい
    const pairEyed=['fish','shark','frog','salamander','lizard','snake','turtle','crocodile','bird','mammal','octopus','insect','crab'].includes(A);
    const eN=pairEyed?2:(neural>0.9?2:(neural>0.4?1:0));
    for(let e=0;e<eN;e++){const yy=eN===1?0:(e?1:-1);
      out.organs.push({type:'eye',p:[headP[0]+size*0.32,headP[1]+yy*size*0.28,headP[2]+size*0.22],
        dir:[1,0,0],size:size*0.145*cellSizeMul('sensor'),depth:0});}
    // 異歯性
    if((jaw>0.35&&!F.noTeeth)||A==='crocodile'||A==='shark'){
      const jn=A==='crocodile'?7:A==='shark'?6:2+Math.floor(jaw*4);
      for(let k=0;k<jn;k++){
        const ay=(k/(jn-1)-0.5),rowPos=jn>1?k/(jn-1):0.5,centerness=1-Math.abs(rowPos-0.5)*2;
        const toothSize=(0.35+centerness*0.35)*(0.6+jaw*0.6);
        S.P={maxDepth:1,branchAlong:false,branchProb:1,branchCount:1,branchAngle:0.5,branchRatio:0.7,
          lenRatio:0.6,taper:0.4,minR:size*0.06,fiber:1,wiggle:0.05,photo:0,gravity:0,apical:false,
          apicalR:0.8,apicalLen:0.7,phyllo:1.2,strokeKind:'limb',tips:[{type:'tooth',prob:Math.min(1,jaw),size:toothSize}]};
        const b0=out.strokes.length;
        growBranch(S,[headP[0]+size*0.5,headP[1]+ay*size*0.5,headP[2]],[1,ay*0.6,-0.1],size*0.14,L*0.6,1,out,null,'limb',mg);
        tagStrokes(out,b0,'tooth');
      }
    }
    const flightBias=clamp((motor-0.5)*2-(g[16]-0.3)*3);
    // 耳（鳥類は外耳なし）
    const earBias=F.noEars?0:clamp(neural*0.6+g[7]*0.4-aquaticOnly*0.5-radiality*0.4-flightBias*1.3);
    if(earBias>0.35)[-1,1].forEach(sd=>out.organs.push({type:'ear',
      p:[headP[0]-size*0.05,headP[1]+sd*size*0.42,headP[2]+size*0.4],
      dir:[-0.3,sd*0.8,0.6],size:size*(0.18+earBias*0.22),depth:0}));
    // 吻部
    const muzzleBias=A==='crocodile'?1:['bird','frog','turtle','snake','insect','spider','crab','snail','octopus','fish','shark'].includes(A)?0:clamp(jaw*0.5+g[9]*0.2-uprightness*0.5);
    if(muzzleBias>0.2)out.organs.push({type:A==='crocodile'?'snout':'muzzle',p:[headP[0]+size*0.35,headP[1],headP[2]+size*0.1],
      dir:[1,0,-0.15],size:size*(0.22+muzzleBias*0.35)*(A==='crocodile'?1.5:1),depth:0});
    // 髭（鳥類には生えない）
    const whiskerBias=clamp(neural*0.5+(cellCounts.sensor||0)*3-uprightness*0.3-flightBias*0.7);
    if(whiskerBias>0.45&&(!F.noWhisker||!ARCH[A])){
      const wN=2+Math.round(whiskerBias*2);
      for(let w=0;w<wN;w++){const rowT=wN>1?w/(wN-1)-0.5:0;
        [-1,1].forEach(sd=>out.organs.push({type:'whisker',
          p:[headP[0]+size*0.3,headP[1]+sd*size*0.22,headP[2]+rowT*size*0.15],
          dir:[1,sd*0.55,rowT*0.3],size:size*(0.11+whiskerBias*0.08),depth:0}));}
    }
    // 体表：毛・羽・鱗（体軸接線に沿って尾側へ寝そべる）
    const scaleW=clamp((g[0]*0.6+toxin*0.25-neural*0.3)*(1-flightBias*0.6));
    const featherW=clamp(flightBias*0.9+neural*0.15-g[0]*0.2-aquaticOnly*0.3);
    const hairW=clamp((neural*0.45+uprightness*0.3+earBias*0.25-aquaticOnly*0.4-g[0]*0.25)*(1-flightBias));
    const integMax=Math.max(scaleW,featherW,hairW);
    let integType=integMax<0.22?null:(integMax===scaleW?'scale':(integMax===featherW?'feather':'hair'));
    if(F.integ)integType=F.integ==='none'?null:F.integ;
    if(integType){
      const integDensity=F.integ?0.75:Math.min(1,integMax),integCount=Math.round(24+integDensity*54);
      const baseSize=size*(integType==='scale'?0.14:integType==='feather'?0.15:0.11);
      const lastB=bodyPts.length-1;
      const spineTan=bi=>{const a=bodyPts[Math.max(0,bi-1)].p,b=bodyPts[Math.min(lastB,bi+1)].p;
        const t=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],l=Math.hypot(t[0],t[1],t[2])||1;return[t[0]/l,t[1]/l,t[2]/l];};
      for(let ii=0;ii<integCount;ii++){
        const bi=Math.max(0,Math.min(lastB,Math.floor(rng()*bodyPts.length))),bp=bodyPts[bi];
        const around=rng()*6.283,nx=Math.cos(around),ny=Math.sin(around)*0.6;
        const tan=spineTan(bi);
        const p=[bp.p[0],bp.p[1]+ny*bp.r*0.88,bp.p[2]+nx*bp.r*0.88];
        let dir;
        if(integType==='scale') dir=[-tan[0]*0.4,ny*0.8-tan[1]*0.4,nx*0.8-tan[2]*0.4];
        else if(integType==='feather') dir=[-tan[0]*0.98,-tan[1]*0.98+ny*0.09,-tan[2]*0.98+nx*0.09];
        else dir=[-tan[0],-tan[1],-tan[2]];
        out.organs.push({type:integType,p,dir,size:baseSize*(0.75+rng()*0.5),depth:1});
      }
    }
    // 斑紋（警告色/迷彩）：背側に配置
    const patternBias=clamp(toxin*0.7+armor*0.35-radiality*0.5);
    if(patternBias>0.28&&bodyPts.length>=3){
      const spotCount=Math.round(3+patternBias*10);
      const warnDominant=toxin>=armor*0.8;
      const spotCol=warnDominant
        ?[Math.min(1,0.7+toxin*0.25),Math.min(1,0.32+toxin*0.28),0.1]
        :[col[0]*0.3,col[1]*0.3,col[2]*0.3];
      const spotSize=size*(0.09+patternBias*0.07);
      for(let ii=0;ii<spotCount;ii++){
        const bi=Math.max(0,Math.min(bodyPts.length-1,Math.floor(rng()*bodyPts.length))),bp=bodyPts[bi];
        const around=(rng()-0.5)*1.7,nx=Math.cos(around),ny=Math.sin(around)*0.6;
        out.organs.push({type:'marking',p:[bp.p[0],bp.p[1]+ny*bp.r*0.9,bp.p[2]+nx*bp.r*0.95],
          dir:[nx*0.3,ny,nx*0.9+0.3],size:spotSize*(0.7+rng()*0.6),depth:1,col:spotCol});
      }
    }
    // 毛皮の模様（実在動物：トラ/シマウマの縞、ヒョウ/キリンの斑点）。陸生の非毒・非水棲・左右相称個体のみ。
    const isLand=!builtAsMicrobe&&sessility<=0.5&&photo<0.4&&aquaticOnly<0.4&&radiality<0.3;
    if(isLand&&bodyPts.length>=4){
      const pr=mulberry32((hashGenome(g)^0x51ed270b)>>>0),pa=pr(),pb=pr();
      const darkCoat=[col[0]*0.24,col[1]*0.22,col[2]*0.2];
      // 縞：走化性/攻撃が高い個体寄り、斑点：中庸、無地：それ以外
      const patType=(pa<0.24||g[6]>0.7)?'stripes':(pa<0.52?'spots':'none');
      if(patType==='stripes'){
        const nb=6+Math.floor(pb*7);
        for(let bb=0;bb<nb;bb++){
          const ft=0.13+0.74*(nb>1?bb/(nb-1):0.5);
          const bp=bodyPts[Math.round(ft*(bodyPts.length-1))];
          for(let a2=-1.25;a2<=1.25;a2+=0.42){
            const yy=Math.sin(a2)*0.92,zz=Math.cos(a2)*0.92;
            out.organs.push({type:'stripe',p:[bp.p[0],bp.p[1]+yy*bp.r,bp.p[2]+zz*bp.r],
              dir:[0,0,1],size:bp.r*0.58,depth:1,col:darkCoat});
          }
        }
      }else if(patType==='spots'){
        const ns=Math.round(12+pb*22);
        for(let si=0;si<ns;si++){
          const bp=bodyPts[Math.floor(pr()*bodyPts.length)];
          const a2=(pr()-0.5)*2.3,yy=Math.sin(a2)*0.92,zz=Math.cos(a2)*0.92;
          out.organs.push({type:'marking',p:[bp.p[0],bp.p[1]+yy*bp.r,bp.p[2]+zz*bp.r],
            dir:[Math.sin(a2)*0.3,yy,zz+0.3],size:bp.r*(0.15+pr()*0.12),depth:1,col:darkCoat});
        }
      }
    }
    // 尾
    S.P={maxDepth:1,branchAlong:false,branchProb:1,branchCount:1,branchAngle:0.15,branchRatio:0.78,
      lenRatio:0.62,taper:0.3,minR:size*0.07,fiber:Math.max(1,Math.round(1+g[1]*3)),wiggle:0.1,photo:0,
      gravity:0.3,apical:false,apicalR:0.8,apicalLen:0.7,phyllo:0.9,strokeKind:'limb',
      tips:[aquaticOnly>0.5?{type:'fin',prob:1,size:1.6+aquaticOnly*0.8}:A==='bird'?{type:'feather',prob:0,size:1}:spikeTip]};
    if(!F.noTail){const b0=out.strokes.length;growBranch(S,tailP.slice(),[-1,0,A==='bird'?0.25:0],size*0.3*(A==='snake'?0.9:1),L*(0.8+g[23]*1.2)*F.tailLen,1,out,null,'tail',mg);tagStrokes(out,b0,'tail');}
    if(aquaticOnly>0.55&&!ARCH[A]){
      const mid=bodyPts[Math.floor(bodyPts.length/2)];
      S.P.tips=[{type:'fin',prob:1,size:2.2+aquaticOnly*0.6}];
      {const b0=out.strokes.length;growBranch(S,[mid.p[0],mid.p[1],mid.p[2]+mid.r],[0,0,1],size*0.16,L*(0.6+aquaticOnly*0.5),1,out,null,'fin',mg);tagStrokes(out,b0,'fin');}
    }
  }

  /* ---- 体制ごとの専用パーツ ---- */
  if(bodyPts.length){
    const nb=bodyPts.length-1,at=t=>bodyPts[Math.max(0,Math.min(nb,Math.round(t*nb)))],hd=bodyPts[nb];
    const push=o=>out.organs.push(Object.assign({depth:0},o));
    switch(A){
      case'snail':{   // 背中の巻貝（対数らせん）と、目のついた触角
        const c=at(0.4),R0=size*0.75,n=11;
        for(let k=0;k<n;k++){const th=k*0.62,r=R0*Math.exp(-0.17*k);
          push({type:'shell',p:[c.p[0]-Math.cos(th)*r*0.9,c.p[1],c.p[2]+c.rh+R0*0.85+Math.sin(th)*r*0.9],dir:[-Math.sin(th),0,Math.cos(th)],size:r*0.72,free:1,col:hsl2rgb(30+h2*25,0.45,0.42+0.2*((k%3)/2))});}
        [-1,1].forEach(sd=>{push({type:'tentacle',p:[hd.p[0]+size*0.25,hd.p[1]+sd*size*0.18,hd.p[2]+size*0.35],dir:[0.6,sd*0.3,1],size:size*0.1});
          push({type:'eye',p:[hd.p[0]+size*0.35,hd.p[1]+sd*size*0.22,hd.p[2]+size*0.62],dir:[1,0,0.3],size:size*0.1});});break;}
      case'crab':{   // はさみと、柄の上の眼
        [-1,1].forEach(sd=>{push({type:'pincer',p:[hd.p[0]+size*0.6,hd.p[1]+sd*hd.rw*0.9,hd.p[2]],dir:[1,sd*0.35,0.15],size:size*(0.45+armor*0.3)});
          push({type:'tentacle',p:[hd.p[0]+size*0.3,hd.p[1]+sd*size*0.25,hd.p[2]+hd.rh],dir:[0.3,0,1],size:size*0.07});});break;}
      case'fish':case'shark':{   // 胸びれ・背びれ
        const m=at(0.55),f=at(0.75);
        [-1,1].forEach(sd=>push({type:'fin',p:[f.p[0],f.p[1]+sd*f.rw,f.p[2]-f.rh*0.3],dir:[-0.4,sd,-0.3],size:size*(A==='shark'?0.7:0.45)}));
        push({type:'fin',p:[m.p[0],m.p[1],m.p[2]+m.rh],dir:[-0.35,0,1],size:size*(A==='shark'?1.0:0.55),dorsal:1});break;}
      case'insect':{   // 触角・翅・大あご
        [-1,1].forEach(sd=>push({type:'antenna',p:[hd.p[0]+size*0.2,hd.p[1]+sd*size*0.12,hd.p[2]+size*0.15],dir:[1,sd*0.45,0.6],size:size*(0.55+neural*0.4)}));
        if(F.fly){const th=at(0.62),n2=g[25]>0.5?2:1;for(let w=0;w<n2;w++)[-1,1].forEach(sd=>push({type:'membrane',p:[th.p[0]-w*size*0.25,th.p[1]+sd*th.rw*0.5,th.p[2]+th.rh*0.9],
          dir:[-0.75,sd*0.45,0.12],size:size*(0.95-w*0.2),free:1,flap:1}));}
        if(jaw>0.4)[-1,1].forEach(sd=>push({type:'claw',p:[hd.p[0]+size*0.3,hd.p[1]+sd*size*0.1,hd.p[2]-size*0.05],dir:[1,-sd*0.4,-0.2],size:size*0.18}));break;}
      case'spider':{   // 多数の単眼と牙
        for(let k=0;k<8;k++){const a=(k%4)/3-0.5,row=k<4?0:1;push({type:'eye',p:[hd.p[0]+size*0.28,hd.p[1]+a*size*0.35,hd.p[2]+size*(0.18+row*0.1)],dir:[1,a*0.3,0.2],size:size*(row?0.05:0.07)});}
        [-1,1].forEach(sd=>push({type:'tooth',p:[hd.p[0]+size*0.35,hd.p[1]+sd*size*0.08,hd.p[2]-size*0.1],dir:[0.4,0,-1],size:size*0.18}));break;}
      case'frog':{   // 頭の上に飛び出した大きな眼
        out.organs=out.organs.filter(o=>o.type!=='eye');
        [-1,1].forEach(sd=>push({type:'eye',p:[hd.p[0]+size*0.1,hd.p[1]+sd*size*0.32,hd.p[2]+size*0.42],dir:[0.5,sd*0.6,0.6],size:size*0.2}));break;}
      case'snake':{   // 二股の舌
        [-1,1].forEach(sd=>push({type:'tongue',p:[hd.p[0]+size*0.55,hd.p[1]+sd*size*0.03,hd.p[2]-size*0.05],dir:[1,sd*0.25,-0.05],size:size*0.35}));break;}
      case'turtle':{   // 甲羅（背甲）と甲板の模様
        const c=at(0.5),R0=Math.max(c.rw,c.rh)*0.92;
        push({type:'carapace',p:[c.p[0],c.p[1],c.p[2]+c.rh*0.35],dir:[0,0,1],size:R0,free:1,col:hsl2rgb(30+h1*30,0.35,0.3+h2*0.1)});
        for(let k=0;k<7;k++){const a=k/7*6.283,r=k?R0*0.55:0,dz=Math.sqrt(Math.max(0,1-(r/R0/1.15)**2))*R0*0.45;
          push({type:'marking',p:[c.p[0]+Math.cos(a)*r,c.p[1]+Math.sin(a)*r,c.p[2]+c.rh*0.35+dz],dir:[Math.cos(a)*r/R0,Math.sin(a)*r/R0,1],size:R0*0.26,depth:1,free:1,col:hsl2rgb(35+h1*30,0.3,0.2)});}break;}
      case'crocodile':{   // 背中の鱗板の列
        for(let k=0;k<14;k++){const p=at(0.08+0.8*k/13);[-1,1].forEach(sd=>push({type:'spike',p:[p.p[0],p.p[1]+sd*p.rw*0.35,p.p[2]+p.rh*0.95],dir:[0,sd*0.2,1],size:p.r*0.28,col:[col[0]*0.7,col[1]*0.7,col[2]*0.7]}));}break;}
      case'bird':{   // くちばし・翼・尾羽
        out.organs=out.organs.filter(o=>o.type!=='muzzle');
        push({type:'beak',p:[hd.p[0]+size*0.35,hd.p[1],hd.p[2]],dir:[1,0,-0.15],size:size*(0.4+jaw*0.35),col:jaw>0.55?[0.25,0.22,0.2]:[0.95,0.72,0.25]});
        const sh=at(0.72);[-1,1].forEach(sd=>push({type:'wing',p:[sh.p[0],sh.p[1]+sd*sh.rw*0.9,sh.p[2]+sh.rh*0.4],dir:[-0.55,sd*0.85,0.1],size:size*(0.55+motor*0.3),free:1,flap:1}));
        const tl=at(0);for(let k=0;k<5;k++){const a=(k/4-0.5)*0.9;push({type:'feather',p:[tl.p[0],tl.p[1],tl.p[2]],dir:[-1,Math.sin(a),0.25],size:size*0.55,free:1});}break;}
    }
  }

  /* ---- 多様性フィーチャー（体制に合うものだけをゲート） ---- */
  if(!F.skipDiv)(function(){
    const ms=out.strokes.reduce((a,b)=>(b.pts&&(!a||b.pts.length>a.pts.length))?b:a,null);
    if(!ms||!ms.pts||!ms.pts.length)return;
    const Ps=ms.pts,N=Ps.length,at=f=>Ps[Math.max(0,Math.min(N-1,Math.round(f*(N-1))))];
    // 背棘
    if(g[2]>0.5){const n=2+Math.floor(g[2]*7);for(let k=0;k<n;k++){const pt=at(n>1?k/(n-1):0.5);
      out.organs.push({type:'spike',p:[pt.p[0],pt.p[1],pt.p[2]+pt.r*0.9],dir:[0,0,1],
        size:pt.r*(0.5+g[2]*0.9)*cellSizeMul('armor'),depth:0});}}
    // 背側甲板（低い瘤列）
    if(g[0]>0.6){const n=Math.max(5,segN*2);for(let k=0;k<n;k++){const pt=at(n>1?k/(n-1):0.5);
      out.organs.push({type:'core',p:[pt.p[0],pt.p[1],pt.p[2]+pt.r*0.62],dir:[0,0,1],
        size:pt.r*(0.1+g[0]*0.06)*cellSizeMul('armor'),depth:0});}}
    // 頭部の角/爪
    if(g[6]>0.55){const h=at(1),hn=1+Math.floor(g[6]*3);for(let k=0;k<hn;k++){const yy=hn>1?(k/(hn-1)-0.5):0;
      out.organs.push({type:'claw',p:[h.p[0]+size*0.2,h.p[1]+yy*size*0.4,h.p[2]+h.r*0.8],
        dir:[0.3,yy,0.9],size:size*(0.25+g[6]*0.4),depth:0});}}
    // 頭部の触手（軟体・放射・水棲のみ）
    if(g[7]>0.5&&(aquaticOnly>0.4||radiality>0.35)){const h=at(1);[-1,1].forEach(sd=>{
      for(let k=1;k<=3;k++)out.organs.push({type:'tentacle',
        p:[h.p[0]+size*0.3+k*size*0.18,h.p[1]+sd*size*0.2,h.p[2]+h.r+k*size*0.12],
        dir:[1,sd*0.2,0.4],size:size*0.12,depth:0});});}
    // 側ひれ（水棲のみ：陸生動物には生やさない）
    if(g[3]>0.55&&aquaticOnly>0.35){const n=2+Math.floor(g[3]*4);for(let k=0;k<n;k++){const pt=at(0.2+0.6*(n>1?k/(n-1):0.5));
      [-1,1].forEach(sd=>out.organs.push({type:'fin',p:[pt.p[0],pt.p[1]+sd*pt.r,pt.p[2]],
        dir:[0,sd,0.2],size:pt.r*(0.8+g[3]),depth:0}));}}
    // 多眼リング（放射相称のみ）
    if(g[4]>0.6&&radiality>0.35){const h=at(1),en=1+Math.floor(g[4]*4);for(let k=0;k<en;k++){const a=k/en*6.283;
      out.organs.push({type:'eye',p:[h.p[0]+size*0.2,h.p[1]+Math.cos(a)*h.r*0.7,h.p[2]+h.r*0.5+Math.sin(a)*h.r*0.5],
        dir:[1,0,0.3],size:size*0.18,depth:0});}}
    // 尾端装飾（体制が決まっている動物には、球状の飾りは付けない）
    if(g[23]>0.5&&(g[22]>0.5||!ARCH[A]||A==='mammal')){const tl=at(0);out.organs.push({type:g[22]>0.5?'spike':'core',
      p:[tl.p[0],tl.p[1],tl.p[2]],dir:[-1,0,0],size:size*(0.3+g[23]*0.5),depth:0});}
    // 実状の瘤（植物寄りのみ）
    if(g[14]>0.55&&(sessility>0.3||photo>0.4)){const n=3+Math.floor(g[14]*5);for(let k=0;k<n;k++){
      const pt=at(n>1?k/(n-1):0.5);out.organs.push({type:'fruit',
        p:[pt.p[0]+Math.sin(k)*pt.r*0.5,pt.p[1]+pt.r*0.6,pt.p[2]],dir:[0,1,0],size:pt.r*0.35,depth:0});}}
  })();

  /* ---- 器官を必ず体表へ吸着（浮いた点を作らない） ---- */
  (function(){
    const pts=[];out.strokes.forEach(s=>s.pts.forEach(p=>pts.push(p)));
    if(!pts.length)return;
    out.organs.forEach(o=>{
      if(o.free)return;                       // 甲羅・翼・傘などは体から離れた位置に置く
      let best=Infinity,bp=null;
      for(let i=0;i<pts.length;i++){const p=pts[i];
        const dd=Math.hypot(o.p[0]-p.p[0],o.p[1]-p.p[1],o.p[2]-p.p[2]);if(dd<best){best=dd;bp=p;}}
      if(!bp)return;
      const allow=bp.r*1.15+(o.size||0)*0.9;
      if(best>allow){const dir=(best>1e-6)?V.norm([o.p[0]-bp.p[0],o.p[1]-bp.p[1],o.p[2]-bp.p[2]]):[0,0,1];
        o.p=[bp.p[0]+dir[0]*allow,bp.p[1]+dir[1]*allow,bp.p[2]+dir[2]*allow];}
    });
  })();

  let viewR=1;
  out.strokes.forEach(s=>s.pts.forEach(pt=>{viewR=Math.max(viewR,Math.hypot(pt.p[0],pt.p[1],pt.p[2]));}));
  out.organs.forEach(o=>viewR=Math.max(viewR,Math.hypot(o.p[0],o.p[1],o.p[2])));
  const eyeCount=out.organs.filter(o=>o.type==='eye').length;
  const formLabel=classifyFormLabel(sessility,aquaticOnly,radiality,builtAsMicrobe,jaw,armor,legCount);
  return {plan:A,arch:A,archName:(ARCH[A]||{}).name,skin:F.skin,formLabel,color:col,size:Math.max(3,viewR/3.0),bilateral,segN,legCount,legPower,
    eyeCount,armor,jaw,photo,toxin,neural,motor,muscle:g[1],g,canFly:!!F.fly,
    strokes:out.strokes,organs:out.organs,cellCounts,dominantCell,
    sessility,aquaticOnly,radiality,elongation,microScale,woodiness,uprightness};
}
function complexityMorpho(g){const m=buildModelMorpho(g),
  maxDepth=m.strokes.reduce((a,s)=>Math.max(a,s.depth),0),
  organKinds=new Set(m.organs.map(o=>o.type)).size;
  return Math.min(10,m.strokes.length*0.15+maxDepth*1.2+organKinds*0.8);}

/* ============================================================
   Canvas 2.5D レンダラ
   ============================================================ */
function strokeColorM(col,kind){let[r,g,b]=col;
  if(kind==='wood'){r=r*0.4+0.34;g=g*0.35+0.22;b=b*0.3+0.1;}
  else if(kind==='muscle'){r=Math.min(1,r*0.7+0.28);g=g*0.55;b=b*0.5;}
  else if(kind==='belly'){r=Math.min(1,r*0.5+0.42);g=Math.min(1,g*0.5+0.4);b=Math.min(1,b*0.45+0.38);}
  return[r,g,b];}

function drawSegM(cx,p,rc){
  const dx=p.bx-p.ax,dy=p.by-p.ay,Ld=Math.hypot(dx,dy)||1,px=-dy/Ld,py=dx/Ld;
  const wA=Math.max(0.6,p.ar),wB=Math.max(0.6,p.br),F=p.fiber,[r,g,b]=p.col;
  cx.lineCap='round';
  cx.strokeStyle=`rgba(${rc(r*0.5)},${rc(g*0.5)},${rc(b*0.55)},1)`;cx.lineWidth=wA+wB;
  cx.beginPath();cx.moveTo(p.ax,p.ay);cx.lineTo(p.bx,p.by);cx.stroke();
  const fw=Math.max(0.7,(wA+wB)/(F*1.1));
  // 方向性陰影（上方光）：背(上)明るく腹(下)暗く
  for(let f=0;f<F;f++){const tt=F===1?0:(f/(F-1)-0.5),oA=tt*wA,oB=tt*wB;
    const li=Math.max(0.42,Math.min(1.28, 1 - 0.26*Math.abs(tt) - 0.5*(py*tt)));
    cx.strokeStyle=`rgba(${rc(Math.min(1,r*li))},${rc(Math.min(1,g*li))},${rc(Math.min(1,b*li))},1)`;
    cx.lineWidth=fw;
    cx.beginPath();cx.moveTo(p.ax+px*oA,p.ay+py*oA);cx.lineTo(p.bx+px*oB,p.by+py*oB);cx.stroke();}
}

// 体制ごとの新しい器官は、2D では似た形の既存器官で描く
const ORGAN_2D={snout:'muzzle',wing:'feather',membrane:'fin',petal:'leaf',beak:'claw',pincer:'claw',antenna:'whisker',tongue:'whisker',
  polyp:'fruit',foliage:'leaf',shell:'core',carapace:'core',cap:'core',bell:'core',flower:'fruit'};
function drawOrganM(cx,p,rc){
  const[r,g,b]=p.col,s=Math.max(1,p.size),k=ORGAN_2D[p.kind]||p.kind,R=v=>rc(v);
  if(k==='eye'){
    cx.beginPath();cx.arc(p.x,p.y,s,0,6.283);cx.fillStyle='rgba(235,228,214,.9)';cx.fill();
    const ix=p.x+Math.cos(p.ang)*s*.32,iy=p.y+Math.sin(p.ang)*s*.32;
    cx.beginPath();cx.arc(ix,iy,s*.62,0,6.283);
    cx.fillStyle=`rgba(${R(Math.min(1,r*.5+.12))},${R(Math.min(1,g*.42+.08))},${R(Math.min(1,b*.4+.08))},.95)`;cx.fill();
    cx.beginPath();cx.arc(ix,iy,s*.3,0,6.283);cx.fillStyle='rgba(10,7,10,.95)';cx.fill();
    cx.beginPath();cx.arc(ix-s*.16,iy-s*.18,s*.14,0,6.283);cx.fillStyle='rgba(255,255,255,.8)';cx.fill();
    return;
  }
  if(k==='head'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);
    const gr=cx.createRadialGradient(-s*.15,-s*.35,s*.15,s*.1,0,s*1.15);
    gr.addColorStop(0,`rgba(${R(Math.min(1,r+.16))},${R(Math.min(1,g+.16))},${R(Math.min(1,b+.18))},1)`);
    gr.addColorStop(1,`rgba(${R(r*.55)},${R(g*.55)},${R(b*.6)},1)`);
    cx.beginPath();cx.ellipse(s*.18,0,s*1.02,s*.72,0,0,6.283);cx.fillStyle=gr;cx.fill();cx.restore();return;}
  if(k==='leaf'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.ellipse(s*.6,0,s,s*.5,0,0,6.283);cx.fillStyle=`rgba(${R(r*.4)},${R(Math.min(1,g+.35))},${R(b*.35)},.92)`;
    cx.fill();cx.restore();return;}
  if(k==='fruit'){const gr=cx.createRadialGradient(p.x-s*.3,p.y-s*.3,s*.1,p.x,p.y,s);
    gr.addColorStop(0,`rgba(255,${R(g*.5+.3)},${R(b*.3)},1)`);
    gr.addColorStop(1,`rgba(${R(.6+r*.4)},${R(g*.2)},${R(b*.2)},1)`);
    cx.beginPath();cx.arc(p.x,p.y,s,0,6.283);cx.fillStyle=gr;cx.fill();return;}
  if(k==='tooth'||k==='claw'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.moveTo(0,-s*.5);cx.lineTo(s*1.6,0);cx.lineTo(0,s*.5);cx.closePath();
    cx.fillStyle=k==='tooth'?'rgba(250,248,235,.95)':`rgba(${R(r*.6+.2)},${R(g*.4)},${R(b*.4)},1)`;
    cx.fill();cx.restore();return;}
  if(k==='spike'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.moveTo(0,-s*.4);cx.lineTo(s*1.8,0);cx.lineTo(0,s*.4);cx.closePath();
    const sc=p.col||[0.5,0.44,0.35];cx.fillStyle=`rgba(${R(sc[0])},${R(sc[1])},${R(sc[2])},.92)`;cx.fill();cx.restore();return;}
  if(k==='fin'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.ellipse(s*.5,0,s,s*.5,0,0,6.283);
    cx.fillStyle=`rgba(${R(Math.min(1,r+.15))},${R(Math.min(1,g+.15))},${R(Math.min(1,b+.2))},.55)`;
    cx.fill();cx.restore();return;}
  if(k==='tentacle'){cx.beginPath();cx.arc(p.x,p.y,s*.5,0,6.283);
    cx.fillStyle=`rgba(${R(r)},${R(g)},${R(b)},.85)`;cx.fill();return;}
  if(k==='hoof'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.moveTo(0,-s*.55);cx.lineTo(s*1.1,-s*.2);cx.lineTo(s*1.1,s*.2);cx.lineTo(0,s*.55);cx.closePath();
    cx.fillStyle='rgba(35,28,24,.95)';cx.fill();cx.restore();return;}
  if(k==='ear'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.ellipse(s*.3,0,s*.5,s*.9,0,0,6.283);
    cx.fillStyle=`rgba(${R(r*.75+.1)},${R(g*.6+.08)},${R(b*.55+.08)},.92)`;cx.fill();cx.restore();return;}
  if(k==='muzzle'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.ellipse(s*.7,0,s*1.1,s*.55,0,0,6.283);
    cx.fillStyle=`rgba(${R(Math.min(1,r*.7+.28))},${R(g*.55)},${R(b*.5)},.95)`;cx.fill();cx.restore();return;}
  if(k==='whisker'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);
    cx.strokeStyle='rgba(230,225,215,.75)';cx.lineWidth=Math.max(.4,s*.15);
    cx.beginPath();cx.moveTo(0,0);cx.lineTo(s*2.2,0);cx.stroke();cx.restore();return;}
  if(k==='hair'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);
    cx.strokeStyle=`rgba(${R(r*.55+.08)},${R(g*.5+.06)},${R(b*.45+.06)},.5)`;cx.lineWidth=Math.max(.25,s*.22);
    cx.beginPath();cx.moveTo(0,0);cx.lineTo(s*.5,0);cx.stroke();cx.restore();return;}
  if(k==='feather'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.moveTo(0,0);cx.lineTo(s*1.05,-s*.22);cx.lineTo(s*1.05,s*.22);cx.closePath();
    cx.fillStyle=`rgba(${R(Math.min(1,r*.85+.12))},${R(Math.min(1,g*.85+.12))},${R(Math.min(1,b*.9+.12))},.82)`;
    cx.fill();cx.restore();return;}
  if(k==='scale'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.moveTo(s*.45,0);cx.lineTo(0,-s*.45);cx.lineTo(-s*.45,0);cx.lineTo(0,s*.45);cx.closePath();
    cx.fillStyle=`rgba(${R(r*.6+.15)},${R(g*.65+.15)},${R(b*.5+.1)},.9)`;cx.fill();cx.restore();return;}
  if(k==='marking'){cx.beginPath();cx.ellipse(p.x,p.y,s*.75,s*.6,p.ang,0,6.283);
    cx.fillStyle=`rgba(${R(r)},${R(g)},${R(b)},.88)`;cx.fill();return;}
  if(k==='stripe'){cx.save();cx.translate(p.x,p.y);cx.rotate(p.ang);cx.beginPath();
    cx.ellipse(0,0,s*1.15,s*0.3,0,0,6.283);cx.fillStyle=`rgba(${R(r)},${R(g)},${R(b)},.82)`;cx.fill();cx.restore();return;}
  // 既定：球型器官（核/未分類）
  const kk=k==='core'?[b,g*.6,r*.5]:[r,g,b];
  const gr=cx.createRadialGradient(p.x-s*.35,p.y-s*.4,s*.15,p.x,p.y,s);
  gr.addColorStop(0,`rgba(${R(Math.min(1,kk[0]+.18))},${R(Math.min(1,kk[1]+.18))},${R(Math.min(1,kk[2]+.2))},1)`);
  gr.addColorStop(1,`rgba(${R(kk[0]*.55)},${R(kk[1]*.55)},${R(kk[2]*.6)},1)`);
  cx.beginPath();cx.arc(p.x,p.y,s,0,6.283);cx.fillStyle=gr;cx.fill();
}

function drawCreatureMorpho(m,sx,sy,scale,yaw,t,cx){
  if(!m.strokes)return;
  const rc=v=>Math.max(0,Math.min(255,Math.floor(v*255))),cy=Math.cos(yaw),sn=Math.sin(yaw);
  let minZ=Infinity;
  m.strokes.forEach(s=>s.pts.forEach(pt=>{if(pt.p[2]-pt.r<minZ)minZ=pt.p[2]-pt.r;}));
  m.organs.forEach(o=>{if(o.p[2]-o.size<minZ)minZ=o.p[2]-o.size;});
  if(!isFinite(minZ))minZ=0;
  const proj=p=>{const z=p[2]-minZ,sway=Math.sin(t*1.5+z*0.25)*z*0.05,x=p[0]+sway,y=p[1],
    rx=x*cy-y*sn,ry=x*sn+y*cy;return{x:sx+rx*scale,y:sy-z*scale+ry*scale*0.5,d:ry-z*0.35};};
  const prims=[];
  m.strokes.forEach(s=>{const col=strokeColorM(m.color,s.kind),Q=s.pts.map(pt=>({s:proj(pt.p),r:pt.r*scale}));
    for(let i=0;i<Q.length-1;i++){const a=Q[i],b=Q[i+1];
      prims.push({t:'seg',ax:a.s.x,ay:a.s.y,bx:b.s.x,by:b.s.y,ar:a.r,br:b.r,fiber:s.fiber,col,d:(a.s.d+b.s.d)/2});}});
  m.organs.forEach(o=>{const s=proj(o.p),dp=proj([o.p[0]+o.dir[0],o.p[1]+o.dir[1],o.p[2]+o.dir[2]]);
    prims.push({t:'org',kind:o.type,x:s.x,y:s.y,size:o.size*scale,ang:Math.atan2(dp.y-s.y,dp.x-s.x),col:o.col||m.color,d:s.d});});
  prims.sort((a,b)=>a.d-b.d);
  prims.forEach(p=>{if(p.t==='seg')drawSegM(cx,p,rc);else drawOrganM(cx,p,rc);});
}

// ---- 24遺伝子 → 34遺伝子 決定論的拡張（同じ個体は常に同じ形態に見える） ----
function padGenome(g){
  if(g&&g.length>=34) return g;
  const src=g||[];
  const n=new Float32Array(34);
  for(let i=0;i<24;i++) n[i]=src[i]!=null?src[i]:0.5;
  // ハッシュ由来の安定ジッタ（インデックスごとに別値）
  const h=hashGenome(n.subarray(0,24));
  const jit=(k)=>{const r=mulberry32((h^(k*0x9e3779b1))>>>0);return r();};
  const c=Genome.clamp;
  const motor=n[17],size=n[16],photo=n[13],stem=n[9],muscle=n[1],attack=n[22],armor=n[2],aqua=n[20];
  n[24]=c(motor*0.85+size*0.25-photo*0.6+ (jit(24)-0.5)*0.2);      // 肢ペア数
  n[25]=c(stem*0.6+ (jit(25)-0.5)*0.3);                            // 肢分岐複雑度
  n[26]=c(attack*0.5+stem*0.3+ (jit(26)-0.5)*0.25);                // 指爪数
  n[27]=c(muscle*0.55+ (jit(27)-0.5)*0.3);                         // 体節数
  n[28]=c(0.12+photo*0.5+ (jit(28)-0.5)*0.22);                     // 対称性(放射度): 動物は低め・植物は高め
  n[29]=c(photo*0.45+ (jit(29)-0.5)*0.3);                          // 放射腕数
  n[30]=c(armor*0.55+ (jit(30)-0.5)*0.2);                          // 角の量
  n[31]=c(armor*0.4+ (jit(31)-0.5)*0.3);                           // 角の本数
  n[32]=c(0.5+ (jit(32)-0.5)*0.35);                                // 体断面形状
  n[33]=c(0.5+ (jit(33)-0.5)*0.4);                                 // 肢位置バイアス
  return n;
}
// opt: {grade: 進化段階（体制の候補を絞る）, arch: 体制を直接指定}
function build(g,opt){ return buildModelMorpho(padGenome(g),opt); }
for(const k in ARCH)PLAN_NAMES[k]=ARCH[k].name;

  return {
    build, draw: drawCreatureMorpho, complexity:(g)=>complexityMorpho(padGenome(g)),
    color:(g)=>LifeGfx.color(padGenome(g)), padGenome,
    PLAN_NAMES, GC, buildRaw: buildModelMorpho, ARCH, chooseArch
  };
})();
