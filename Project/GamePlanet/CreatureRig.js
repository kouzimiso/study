/**
 * CreatureRig.js — 生物の物理リグ（Rig）。手足・指・尾で体を支えて歩く XPBD シミュレーション
 * GamePlanet.html と creature-test.html から読み込む（classic script・グローバル定数 Rig を定義）。
 * 依存: なし（純粋な JS）。入力モデルは CreatureEngine.build(g) の出力。
 * API: Rig.create(model,{scale,x,y,heading,env,groundZ,water,teleportDist}) / step / center / setGoal / maxSpeed / pointAt / frameAt / particleFrame / supportInfo
 */
/* ==== gp3d-rig (v17 実3D/物理/多細胞化) ==== */
// ================================================================
// Rig — 生物の物理シミュレーション（手足・指で体を支える）
//
// 方式: XPBD（Macklin, Müller & Chentanez 2016, doi:10.1145/2994258.2994272）
//   胴体 = 剛体（XPBD剛体: Müller et al. 2020 Detailed Rigid Body Simulation with XPBD）
//   脚・指・尾・腕 = 質点チェーン（骨=距離拘束、関節=柔らかい姿勢拘束）
//   接地 = 位置拘束 + 静止/動摩擦（Macklin et al. 2014 Unified Particle Physics, Eq.23-24）
//
// 生体力学の根拠:
//   ・筋の最大張力 σ≈200–300 kPa（Rospars & Meyer-Vernet 2016 doi:10.1098/rsos.160313）
//     脚が出せる地面反力 = σ × 筋断面積 × 有効機械的倍率EMA（Biewener 1989 doi:10.1126/science.2740914）
//     → 断面積∝L²・体重∝L³ の二乗三乗則により、大型個体ほど脚が体重を支えきれず腹這いになる
//   ・歩容: フルード数 Fr=v²/(g h)、歩幅 λ/h≈2.3·Fr^0.3、Fr≈0.5で歩→走（Alexander & Jayes 1983）
//     デューティ比 β: 歩行>0.5 / 走行<0.5
//     位相: 四足=側対歩順(LH0,LF.25,RH.5,RF.75; Hildebrand 1965)、六脚=交互三脚(Wilson 1966)、
//           多脚=後→前のメタクロナル波、二足=0/.5
//   ・遊脚着地点の平衡フィードバック: θd=θd0+cd·d+cv·v（SIMBICON, Yin et al. 2007）
//   ・姿勢保持トルク: 仮想モデル制御（Pratt et al. 2001）— 接地脚が出せる範囲に制限
//   ・脚なし体（蠕虫）: 体の波状屈曲＋異方性摩擦で推進（Hu et al. 2009 PNAS "slithering"）
//   ・水中: 抵抗力理論 Cn≈2Ct（Gray & Hancock 1955）＋浮力
// 単位系: cm, g, s（重力 981 cm/s²、応力 dyn/cm²）。座標: x前 / y左 / z上（CreatureEngineと同じ）
// ================================================================
const Rig = (function(){
'use strict';
const GRAV = 981;          // cm/s²
const SIGMA = 2.5e6;       // dyn/cm² = 250 kPa 筋の最大等尺性張力
const RHO = 1.05;          // g/cm³ 体密度
const RHO_W = 1.0;         // g/cm³ 水
const MU_S = 0.8, MU_K = 0.6;   // 静止/動摩擦係数（土・岩の上の皮膚/爪の目安）
const SUBSTEPS = 8;

// ---------- ベクトル/クォータニオン ----------
const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const mul=(a,s)=>[a[0]*s,a[1]*s,a[2]*s], dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const len=a=>Math.hypot(a[0],a[1],a[2]);
const norm=a=>{const l=len(a)||1;return[a[0]/l,a[1]/l,a[2]/l];};
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
function qmul(a,b){return[a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3],a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],
  a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1],a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]];}
function qrot(q,v){const w=q[0],x=q[1],y=q[2],z=q[3];
  const tx=2*(y*v[2]-z*v[1]),ty=2*(z*v[0]-x*v[2]),tz=2*(x*v[1]-y*v[0]);
  return[v[0]+w*tx+(y*tz-z*ty),v[1]+w*ty+(z*tx-x*tz),v[2]+w*tz+(x*ty-y*tx)];}
const qconj=q=>[q[0],-q[1],-q[2],-q[3]];
const qinvrot=(q,v)=>qrot(qconj(q),v);
function qnormalize(q){const l=Math.hypot(q[0],q[1],q[2],q[3])||1;q[0]/=l;q[1]/=l;q[2]/=l;q[3]/=l;return q;}
function qaxis(ax,ang){const s=Math.sin(ang/2);return[Math.cos(ang/2),ax[0]*s,ax[1]*s,ax[2]*s];}
// 正規直交基底（t=前方/接線, upRef=上方参照）→ [ex(前),ey(左),ez(上)]
function basis(t,upRef){let ex=norm(t);let ey=cross(upRef,ex);if(len(ey)<1e-6)ey=cross([0,1,0],ex);ey=norm(ey);const ez=cross(ex,ey);return[ex,ey,ez];}
const toLocal=(B,v)=>[dot(B[0],v),dot(B[1],v),dot(B[2],v)];
const fromLocal=(B,l)=>[B[0][0]*l[0]+B[1][0]*l[1]+B[2][0]*l[2],B[0][1]*l[0]+B[1][1]*l[1]+B[2][1]*l[2],B[0][2]*l[0]+B[1][2]*l[1]+B[2][2]*l[2]];

// ---------- ストローク再サンプル（関節数に間引き） ----------
function resample(pts,segs){const n=pts.length;if(n<=segs+1)return pts.slice();const out=[];
  for(let j=0;j<=segs;j++)out.push(pts[Math.round(j*(n-1)/segs)]);return out;}

// ================================================================
// build(model, opts) — CreatureEngine モデル → 物理リグ
//   opts: {scale, x, y, heading, env}  env(x,y)->{z, n:[nx,ny,nz], water:zWaterOrNull}
// ================================================================
function build(model,opts){
  const sc=opts.scale||1, env=opts.env;
  const S=pt=>({p:[pt.p[0]*sc,pt.p[1]*sc,pt.p[2]*sc],r:pt.r*sc,rw:(pt.rw||pt.r)*sc,rh:(pt.rh||pt.r)*sc});
  const strokes=model.strokes.map(st=>Object.assign({},st,{P:st.pts.map(S)}));
  const organs=model.organs.map(o=>({type:o.type,p:mul(o.p,sc),dir:o.dir.slice(),size:o.size*sc,col:o.col}));
  const g=model.g;
  const R={model,scale:sc,g,color:model.color,strokes,organs,particles:[],cons:[],legs:[],renderStrokes:[],
    t:0,cycle:0,heading:opts.heading||0,goal:null,vDes:[0,0,0],stats:{},flipT:0};
  const body=strokes.find(s=>s.group==='body');
  const isPlant=model.sessility>0.5||(!body&&strokes.some(s=>s.group==='plant'));
  const isMicrobe=strokes.some(s=>s.group==='cilia');
  const supLegs=strokes.filter(s=>s.group==='leg'&&s.legRole!=='manipulator');
  const arms=strokes.filter(s=>s.group==='arm'&&s.depth===1);
  R.canFly=!!model.canFly&&!isPlant;
  R.mode=isPlant?'plant':isMicrobe?'float':(body&&(supLegs.length>=2||arms.length>=3))?'legged':body?'chain':'float';
  if(R.canFly&&R.mode!=='plant')R.mode='legged';
  if(R.mode==='plant'){buildStatic(R);place(R,opts);return R;}
  if(R.mode==='chain'){buildChain(R,body);place(R,opts);return R;}
  plantLegs(R,supLegs.length?supLegs:(supLegs.length<2?arms:[]));
  buildRigid(R,body,supLegs,arms);place(R,opts);return R;
}

// 立位姿勢の生成: 形態モデルの休息姿勢では足が腹より上にあることがあるため、
// 股関節まわりに肢を下方へ回して「足（指）が胴体の最下点より下＝体を持ち上げる」姿勢にする。
// 胴体と地面のすき間は肢長の約3割（小型ほど屈曲・大型ほど直立: Biewener 1989）
function plantLegs(R,legs){
  if(!legs.length)return;
  let bottom=Infinity;
  R.strokes.forEach(s=>{if(s.group==='body'||s.group==='belly')s.P.forEach(p=>bottom=Math.min(bottom,p.p[2]-p.r));});
  if(!isFinite(bottom))return;
  // 器官の所属（最寄りストローク）を先に記録
  const owner=R.organs.map(o=>{let best=null,bd=Infinity;R.strokes.forEach(s=>s.P.forEach(p=>{const d=len(sub(o.p,p.p));if(d<bd){bd=d;best=s;}}));return best;});
  legs.forEach(ls=>{
    const k=R.strokes.indexOf(ls);
    const members=[ls].concat(R.strokes.filter(d=>d.group==='digit'&&d.legStroke===k));
    if(ls.group==='arm')R.strokes.forEach(d=>{if(d!==ls&&d.group==='arm'&&d.depth>1&&len(sub(d.P[0].p,ls.P[ls.P.length-1].p))<1e-6)members.push(d);});
    const hip=ls.P[0].p;
    const lowZ=()=>Math.min(...members.map(m=>Math.min(...m.P.map(p=>p.p[2]-p.r))));
    const chainLen=ls.P.slice(1).reduce((a,p,i)=>a+len(sub(p.p,ls.P[i].p)),0);
    const target=bottom-chainLen*0.3;
    if(lowZ()<=target)return;
    const foot=ls.P[ls.P.length-1].p,out=[foot[0]-hip[0],foot[1]-hip[1],0];
    if(len(out)<1e-6)out[1]=ls.side||1;
    const axis=norm(cross([0,0,1],norm(out)));
    const rotP=(p,a)=>{const v=sub(p,hip),c=Math.cos(a),sn=Math.sin(a),d=dot(axis,v),ax=cross(axis,v);
      return add(hip,[v[0]*c+ax[0]*sn+axis[0]*d*(1-c),v[1]*c+ax[1]*sn+axis[1]*d*(1-c),v[2]*c+ax[2]*sn+axis[2]*d*(1-c)]);};
    const orig=members.map(m=>m.P.map(p=>p.p.slice()));
    // 足が体の反対側へ潜り込まない範囲（外向き成分を残す）で回す
    const outN=norm(out),minOut=Math.max(ls.P[ls.P.length-1].r*1.5,len(out)*0.35);
    let ang=0;
    for(let a=0.05;a<=1.4;a+=0.05){
      members.forEach((m,mi)=>m.P.forEach((p,pi)=>{p.p=rotP(orig[mi][pi],a);}));
      const f=ls.P[ls.P.length-1].p;
      if(dot(sub(f,hip),outN)<minOut){a-=0.05;members.forEach((m,mi)=>m.P.forEach((p,pi)=>{p.p=rotP(orig[mi][pi],Math.max(0,a));}));ang=Math.max(0,a);break;}
      ang=a;if(lowZ()<=target)break;}
    R.organs.forEach((o,oi)=>{if(members.includes(owner[oi]))o.p=rotP(o.p,ang);});
  });
}

// ---------- 剛体胴体 + 質点肢 ----------
function buildRigid(R,body,supLegs,arms){
  const st=R.strokes;
  // 胴体の構成点（体幹・腹）
  const torsoPts=[];
  if(body)body.P.forEach(p=>torsoPts.push(p));
  st.filter(s=>s.group==='belly').forEach(s=>s.P.forEach(p=>torsoPts.push(p)));
  if(!torsoPts.length)st.forEach(s=>{if(s.depth===0)s.P.forEach(p=>torsoPts.push(p));});
  const head=R.organs.find(o=>o.type==='head'||o.type==='core');
  if(head)torsoPts.push({p:head.p.slice(),r:head.size*0.8});
  // 質量・重心・慣性（各点を球として積算）
  let M=0,c=[0,0,0];
  const mOf=p=>RHO*4/3*Math.PI*p.r*p.r*p.r*0.6;
  torsoPts.forEach(p=>{const m=mOf(p);M+=m;c=add(c,mul(p.p,m));});
  c=mul(c,1/M);
  const I=[0,0,0];
  torsoPts.forEach(p=>{const m=mOf(p),d=sub(p.p,c);I[0]+=m*(d[1]*d[1]+d[2]*d[2]+0.4*p.r*p.r);I[1]+=m*(d[0]*d[0]+d[2]*d[2]+0.4*p.r*p.r);I[2]+=m*(d[0]*d[0]+d[1]*d[1]+0.4*p.r*p.r);});
  R.restCom=c;
  R.tb={x:c.slice(),q:[1,0,0,0],v:[0,0,0],w:[0,0,0],M,Iinv:I.map(v=>1/Math.max(v,1e-6)),I,
    pts:(body?body.P:torsoPts).map(p=>({l:sub(p.p,c),r:p.r})),px:c.slice(),pq:[1,0,0,0]};
  if(head)R.tb.pts.push({l:sub(head.p,c),r:head.size*0.8});
  const T=l=>({t:'T',l});
  const P=i=>({t:'P',i});
  const addParticle=(pt,kind,extra)=>{const m=RHO*Math.PI*pt.r*pt.r*pt.r*2.2;
    R.particles.push(Object.assign({x:pt.p.slice(),px:pt.p.slice(),v:[0,0,0],r:pt.r,m,w:1/m,kind,rest:pt.p.slice(),contact:false},extra||{}));
    return R.particles.length-1;};
  const muscle=0.3+R.g[1]*0.7;
  // 肢チェーン生成: 根元は胴体ローカル点、以降は質点
  const chainFrom=(s,segs,kind)=>{
    const pts=resample(s.P,segs);const ids=[];
    for(let k=1;k<pts.length;k++)ids.push(addParticle(pts[k],kind));
    const nodes=[{a:T(sub(pts[0].p,c)),r:pts[0].r}].concat(ids.map((id,k)=>({a:P(id),r:pts[k+1].r})));
    // 骨（剛）
    for(let k=0;k<nodes.length-1;k++){const A=nodes[k].a,B=nodes[k+1].a;
      R.cons.push({type:'dist',A,B,rest:len(sub(pts[k].p,pts[k+1].p)),alpha:0});}
    // 関節の筋緊張: 各質点を胴体座標の休息位置へ柔らかく保持（姿勢ばね）
    ids.forEach((id,k)=>{const p=R.particles[id];p.poseL=sub(p.rest,c);});
    return {pts,ids,nodes};
  };
  const strokeColor=s=>s.kind;
  // ---- 支持脚 ----
  supLegs.forEach(s=>{
    const segs=Math.max(2,Math.min(4,s.segCount||3));
    const ch=chainFrom(s,segs,'leg');
    const foot=ch.ids[ch.ids.length-1],shin=ch.ids.length>=2?ch.ids[ch.ids.length-2]:null;
    const legR=ch.pts.reduce((a,p)=>a+p.r,0)/ch.pts.length;
    const chainLen=ch.pts.slice(1).reduce((a,p,k)=>a+len(sub(p.p,ch.pts[k].p)),0);
    const reach=len(sub(ch.pts[ch.pts.length-1].p,ch.pts[0].p));
    // EMA（有効機械的倍率）: 肢がまっすぐ(直立姿勢)ほど高い（Biewener 1989: 小型=屈曲0.2〜大型=直立0.9）
    const straight=clamp(reach/chainLen,0,1);
    const EMA=0.12+0.78*Math.pow(straight,3);
    const Amus=Math.PI*legR*legR*0.6*muscle;            // 有効筋断面積
    const Fmax=SIGMA*Amus*EMA;                            // 地面反力の上限 [dyn]
    const leg={stroke:s,ids:ch.ids,foot,shin,hipL:sub(ch.pts[0].p,c),footL:sub(ch.pts[ch.pts.length-1].p,c),
      side:s.side||1,pair:s.pair||0,frac:s.frac||0,Fmax,EMA,legR,chainLen,phase:0,contact:false,load:0,digits:[],arm:false};
    R.legs.push(leg);
    R.renderStrokes.push({kind:'limb',group:'leg',nodes:ch.nodes});
    // 指: 足首(足)質点から伸びる
    const digs=R.strokes.filter(d=>d.group==='digit'&&d.legStroke===R.strokes.indexOf(s));
    const claw=R.g[22]*0.5,hoof=clamp((R.g[0]*0.6+R.g[2]*0.4)*0.6+R.g[2]*0.25-R.g[11]*0.3,0,1);
    digs.forEach(d=>{
      const pts=resample(d.P,2);const ids=[];
      for(let k=1;k<pts.length;k++)ids.push(addParticle(pts[k],'digit',{leg:R.legs.length-1}));
      const nodes=[{a:P(foot),r:pts[0].r}].concat(ids.map((id,k)=>({a:P(id),r:pts[k+1].r})));
      for(let k=0;k<nodes.length-1;k++)R.cons.push({type:'dist',A:nodes[k].a,B:nodes[k+1].a,rest:len(sub(pts[k].p,pts[k+1].p)),alpha:0});
      // 指の屈筋: すね→指の距離で関節角を保持（剛性=筋＋爪/蹄）
      const stiff=0.3+muscle*0.5+hoof*0.6+claw*0.3;
      if(shin!=null)ids.forEach((id,k)=>R.cons.push({type:'dist',A:P(shin),B:P(id),rest:len(sub(R.particles[shin].rest,pts[k+1].p)),stiffHz:4+stiff*10}));
      if(ids.length>=2)R.cons.push({type:'dist',A:P(foot),B:P(ids[1]),rest:len(sub(pts[0].p,pts[2].p)),stiffHz:4+stiff*10});
      leg.digits.push(ids[ids.length-1]);
      R.renderStrokes.push({kind:'limb',group:'digit',nodes});
    });
    // 脚内部の関節: 膝の向きを保つ柔らかい屈曲拘束（大腿→下腿）
    // 関節の筋は「出せる力の上限（σ·A·EMA）」つき → 体重が上限を超えると関節が屈して沈む
    const li=R.legs.length-1;
    for(let k=0;k+2<ch.nodes.length;k++)R.cons.push({type:'dist',A:ch.nodes[k].a,B:ch.nodes[k+2].a,rest:len(sub(ch.pts[k].p,ch.pts[k+2].p)),stiffHz:3+muscle*4,leg:li});
    ch.ids.slice(0,-1).forEach(id=>R.cons.push({type:'pose',i:id,stiffHz:2+muscle*2.5,leg:li}));
  });
  // ---- 放射腕（ヒトデ型）: 支持肢として扱う ----
  if(R.legs.length<2)arms.forEach((s,ai)=>{
    const ch=chainFrom(s,3,'arm');
    const legR=ch.pts.reduce((a,p)=>a+p.r,0)/ch.pts.length;
    const Fmax=SIGMA*Math.PI*legR*legR*0.5*muscle*0.35;
    R.legs.push({stroke:s,ids:ch.ids,foot:ch.ids[ch.ids.length-1],shin:ch.ids[ch.ids.length-2],hipL:sub(ch.pts[0].p,c),
      footL:sub(ch.pts[ch.pts.length-1].p,c),side:1,pair:ai,frac:ai/arms.length,Fmax,EMA:0.35,legR,chainLen:0,phase:0,contact:false,load:0,digits:[],arm:true});
    for(let k=0;k+2<ch.nodes.length;k++)R.cons.push({type:'dist',A:ch.nodes[k].a,B:ch.nodes[k+2].a,rest:len(sub(ch.pts[k].p,ch.pts[k+2].p)),stiffHz:3});
    R.renderStrokes.push({kind:'soft',group:'arm',nodes:ch.nodes});
  });
  // ---- 操作肢（腕）・尾: ぶら下がる質点チェーン＋姿勢ばね ----
  st.forEach(s=>{
    if(s.group==='leg'&&s.legRole==='manipulator'){
      const ch=chainFrom(s,Math.max(2,Math.min(4,s.segCount||3)),'arm');
      ch.ids.forEach(id=>R.cons.push({type:'pose',i:id,stiffHz:3+muscle*4}));
      R.renderStrokes.push({kind:'limb',group:'manip',nodes:ch.nodes,ids:ch.ids});
      // 手の指（操作肢の指）は手先質点に剛付け
      R.strokes.filter(d=>d.group==='digit'&&d.legStroke===R.strokes.indexOf(s)).forEach(d=>{d.decorTo=ch.ids[ch.ids.length-1];});
    }else if(s.group==='tail'&&s.depth===1){
      const segs=Math.max(2,Math.min(5,s.P.length-1));
      const ch=chainFrom(s,segs,'tail');
      for(let k=0;k+2<ch.nodes.length;k++)R.cons.push({type:'dist',A:ch.nodes[k].a,B:ch.nodes[k+2].a,rest:len(sub(ch.pts[k].p,ch.pts[k+2].p)),stiffHz:2+muscle*3});
      ch.ids.forEach(id=>R.cons.push({type:'pose',i:id,stiffHz:0.8+muscle*1.5}));
      R.renderStrokes.push({kind:'limb',group:'tail',nodes:ch.nodes});
    }
  });
  // 支持肢でない腕(放射腕を支持に使わなかった場合)は飾りとして扱う
  linkChains(R);   // 休息フレーム計算の前に質点チェーンの前後関係を張る
  // ---- 胴体（剛）として描くストローク ----
  st.forEach(s=>{
    const simulated=(s.group==='leg')||(s.group==='digit'&&!s.decorTo)||(s.group==='tail'&&s.depth===1)||(s.group==='arm'&&s.depth===1&&R.legs.some(l=>l.stroke===s));
    if(simulated)return;
    const nodes=s.P.map(p=>({a:nearestAnchor(R,p.p,s.decorTo),r:p.r,rw:p.rw,rh:p.rh}));
    R.renderStrokes.push({kind:s.kind,group:s.group||'decor',nodes,ellipse:s.group==='body'||s.group==='belly'});
  });
  R.organs.forEach(o=>{o.a=nearestAnchor(R,o.p,null);o.dirL=dirToLocal(R,o.a,o.dir);});
  // 脚の総合指標（表示用）
  R.totalMass=M+R.particles.reduce((a,p)=>a+p.m,0);
  R.stats.legs=R.legs.length;R.stats.mass=R.totalMass;
  R.stats.supportRatio=R.legs.reduce((a,l)=>a+l.Fmax,0)/(R.totalMass*GRAV);   // 筋力/体重（>1で起立可能）
  // 股関節高さ（フルード数の脚長 h）
  R.hipH=R.legs.length?R.legs.reduce((a,l)=>a+(l.hipL[2]-l.footL[2]),0)/R.legs.length:R.tb.pts.reduce((a,p)=>Math.max(a,p.r),1);
  R.hipH=Math.max(R.hipH,1);
  // 歩容の位相（Hildebrand / Wilson / メタクロナル波）
  assignPhases(R);
}

function assignPhases(R){
  const legs=R.legs.filter(l=>!l.arm);
  const pairs=new Set(legs.map(l=>l.pair)).size;
  legs.forEach(l=>{
    const L=l.side<0; // side -1 を左とみなす
    let ph;
    if(pairs<=1)ph=L?0:0.5;                                          // 二足
    else if(pairs===2){const front=l.pair===0;ph=front?(L?0.25:0.75):(L?0:0.5);} // 側対歩順 walk
    else if(pairs===3){ph=((l.pair%2===0)===L)?0:0.5;}                 // 交互三脚
    else{ph=((pairs-1-l.pair)*0.17+(L?0:0.5))%1;}                      // 後→前へ進む波
    l.phase=ph;
  });
  R.legs.filter(l=>l.arm).forEach((l,i,a)=>{l.phase=i/a.length;});
  R.trotPhases=legs.map(l=>pairs===2?((l.pair===0)===(l.side<0)?0.5:0):l.phase);
}

// 最寄りのアンカー（胴体ローカル or 質点ローカル）
function nearestAnchor(R,p,forceParticle){
  if(forceParticle!=null){const q=R.particles[forceParticle];return{t:'P',i:forceParticle,l:toLocal(restFrame(R,forceParticle),sub(p,q.rest))};}
  let best=null,bd=Infinity;
  if(R.tb){R.tb.pts.forEach(tp=>{const d=len(sub(p,add(R.restCom,tp.l)))-tp.r*0.5;if(d<bd){bd=d;best={t:'T',l:sub(p,R.restCom)};}});}
  R.particles.forEach((q,i)=>{const d=len(sub(p,q.rest));if(d<bd){bd=d;best={t:'P',i,l:toLocal(restFrame(R,i),sub(p,q.rest))};}});
  return best||{t:'T',l:sub(p,R.restCom||[0,0,0])};
}
function dirToLocal(R,a,dir){if(a.t==='T')return dir.slice();return toLocal(restFrame(R,a.i),dir);}
// 質点の休息フレーム（チェーン接線基準）
function restFrame(R,i){const q=R.particles[i];
  const prev=q.prevI!=null?R.particles[q.prevI].rest:null,next=q.nextI!=null?R.particles[q.nextI].rest:null;
  let t=next?sub(next,q.rest):prev?sub(q.rest,prev):[1,0,0];if(prev&&next)t=sub(next,prev);
  return basis(t,[0,0,1]);}

// ---------- 胴体のない柔軟チェーン（蠕虫・遊泳） ----------
function buildChain(R,body){
  const pts=resample(body.P,Math.min(12,body.P.length-1));
  const muscle=0.3+R.g[1]*0.7;
  pts.forEach((pt,k)=>{const m=RHO*Math.PI*pt.r*pt.r*(k?len(sub(pt.p,pts[k-1].p)):pt.r*2);
    R.particles.push({x:pt.p.slice(),px:pt.p.slice(),v:[0,0,0],r:pt.r,m,w:1/m,kind:'body',rest:pt.p.slice(),rw:pt.rw,rh:pt.rh,contact:false,
      prevI:k?k-1:null,nextI:k<pts.length-1?k+1:null});});
  R.chainN=pts.length;
  for(let k=0;k<pts.length-1;k++)R.cons.push({type:'dist',A:{t:'P',i:k},B:{t:'P',i:k+1},rest:len(sub(pts[k].p,pts[k+1].p)),alpha:0});
  for(let k=0;k+2<pts.length;k++)R.cons.push({type:'dist',A:{t:'P',i:k},B:{t:'P',i:k+2},rest:len(sub(pts[k].p,pts[k+2].p)),stiffHz:2+muscle*4});
  R.segLen=len(sub(pts[pts.length-1].p,pts[0].p))/Math.max(1,pts.length-1);
  R.renderStrokes.push({kind:'muscle',group:'body',nodes:pts.map((p,k)=>({a:{t:'P',i:k,l:[0,0,0]},r:p.r,rw:p.rw,rh:p.rh})),ellipse:true});
  R.strokes.forEach(s=>{if(s===body)return;
    R.renderStrokes.push({kind:s.kind,group:s.group||'decor',nodes:s.P.map(p=>({a:nearestAnchor(R,p.p,null),r:p.r,rw:p.rw,rh:p.rh})),ellipse:s.group==='belly'});});
  R.organs.forEach(o=>{o.a=nearestAnchor(R,o.p,null);o.dirL=dirToLocal(R,o.a,o.dir);});
  R.totalMass=R.particles.reduce((a,p)=>a+p.m,0);
  R.hipH=Math.max(1,pts.reduce((a,p)=>Math.max(a,p.r),0));
  R.stats={legs:0,mass:R.totalMass,supportRatio:0};
}

// ---------- 固着（植物）: 静的形状＋風による揺れ ----------
function buildStatic(R){
  R.strokes.forEach(s=>R.renderStrokes.push({kind:s.kind,group:s.group||'plant',nodes:s.P.map(p=>({a:{t:'S',l:p.p.slice()},r:p.r,rw:p.rw,rh:p.rh}))}));
  R.organs.forEach(o=>{o.a={t:'S',l:o.p.slice()};o.dirL=o.dir.slice();});
  let hmax=1;R.strokes.forEach(s=>s.P.forEach(p=>hmax=Math.max(hmax,p.p[2])));R.plantH=hmax;
  R.totalMass=0;R.stats={legs:0,mass:0,supportRatio:0};
}

// 初期配置: 接地点を地面へ
function place(R,opts){
  const x0=opts.x||0,y0=opts.y||0,e=opts.env(x0,y0);R.env=opts.env;
  const q=qaxis([0,0,1],R.heading);
  if(R.mode==='plant'){R.origin=[x0,y0,e.z];R.q=q;return;}
  let minZ=Infinity;
  const consider=p=>{minZ=Math.min(minZ,p);};
  if(R.tb){R.tb.pts.forEach(tp=>consider(R.restCom[2]+tp.l[2]-tp.r));R.particles.forEach(p=>consider(p.rest[2]-p.r));}
  else R.particles.forEach(p=>consider(p.rest[2]-p.r));
  const lift=e.z-minZ+0.02;
  const world=p=>{const l=qrot(q,[p[0],p[1],p[2]]);return[l[0]+x0,l[1]+y0,l[2]+lift];};
  if(R.tb){R.standH=R.restCom[2]+lift-e.z;R.legs.forEach(l=>{l.planted=false;l.stance=true;});R.tb.x=world(R.restCom);R.tb.q=q.slice();R.tb.px=R.tb.x.slice();R.tb.pq=q.slice();R.tb.v=[0,0,0];R.tb.w=[0,0,0];}
  R.particles.forEach(p=>{p.x=world(p.rest);p.px=p.x.slice();p.v=[0,0,0];});
  R.flipT=0;
}

// ---------- 汎用XPBD位置補正（端点=剛体上の点 or 質点 or 固定） ----------
function anchorWorld(R,a){
  if(a.t==='P')return R.particles[a.i].x;
  if(a.t==='T')return add(R.tb.x,qrot(R.tb.q,a.l));
  return a.p;
}
function invMassAlong(R,a,n,pin){
  if(pin)return 0;
  if(a.t==='P')return R.particles[a.i].w;
  if(a.t==='T'){const tb=R.tb,r=qrot(tb.q,a.l),rn=qinvrot(tb.q,cross(r,n));
    return 1/tb.M+rn[0]*rn[0]*tb.Iinv[0]+rn[1]*rn[1]*tb.Iinv[1]+rn[2]*rn[2]*tb.Iinv[2];}
  return 0;
}
function applyImpulse(R,a,p,pin){
  if(pin)return;
  if(a.t==='P'){const q=R.particles[a.i];q.x=add(q.x,mul(p,q.w));return;}
  if(a.t==='T'){const tb=R.tb;tb.x=add(tb.x,mul(p,1/tb.M));
    const r=qrot(tb.q,a.l),tq=qinvrot(tb.q,cross(r,p));
    const dw=qrot(tb.q,[tq[0]*tb.Iinv[0],tq[1]*tb.Iinv[1],tq[2]*tb.Iinv[2]]);
    const dq=qmul([0,dw[0],dw[1],dw[2]],tb.q);
    tb.q=qnormalize([tb.q[0]+0.5*dq[0],tb.q[1]+0.5*dq[1],tb.q[2]+0.5*dq[2],tb.q[3]+0.5*dq[3]]);}
}
// C = c（n方向の誤差）を解消。A は -n 側へ、B は +n 側へ動く。戻り値=Δλ
function solve(R,A,B,n,c,alpha,h,maxL,pinA,pinB){
  const wA=invMassAlong(R,A,n,pinA),wB=invMassAlong(R,B,n,pinB);
  const den=wA+wB+alpha/(h*h);if(den<=0)return 0;
  let dl=-c/den;if(maxL!=null)dl=clamp(dl,-maxL,maxL);
  applyImpulse(R,A,mul(n,dl),pinA);applyImpulse(R,B,mul(n,-dl),pinB);
  return dl;
}
// 固有振動数[Hz]指定の柔らかさ → コンプライアンス α=1/k, k=m·ω²
const alphaFromHz=(hz,m)=>1/(m*Math.pow(2*Math.PI*hz,2));

// ================================================================
// step(R, dt) — 1フレーム進める（内部でサブステップ）
// ================================================================
function step(R,dt,subs){
  if(R.mode==='plant'){R.t+=dt;return;}
  dt=Math.min(dt,1/30);
  control(R,dt);
  const NS=subs||SUBSTEPS,h=dt/NS;
  R.particles.forEach(p=>p.fn=0);R.legs.forEach(l=>l.tg=0);
  for(let s=0;s<NS;s++)substep(R,h);
  // 地面反力（GRF）: 立脚の支持力（VMCで筋力上限つき）。表示・検証用
  R.legs.forEach(l=>{l.load=l.tg/NS;});   // 各立脚が胴体に与えた支持力の平均
  R.t+=dt;
  // 転倒からの立ち直り（体軸が大きく傾いたまま数秒経過したら起き直る）
  if(R.tb&&R.mode==='legged'){const up=qrot(R.tb.q,[0,0,1]);
    if(up[2]<0.25){R.flipT+=dt;if(R.flipT>3){const fw=qrot(R.tb.q,[1,0,0]);R.heading=Math.atan2(fw[1],fw[0]);place(R,{x:R.tb.x[0],y:R.tb.x[1],env:R.env});}}else R.flipT=0;}
}

// 制御（毎フレーム）: 目標速度 → 歩容パラメータ
function control(R,dt){
  const pos=center(R);
  let vd=[0,0,0];
  if(R.goal){const d=sub(R.goal,pos);d[2]=0;const dist=len(d);
    if(dist>R.teleportDist){place(R,{x:R.goal[0],y:R.goal[1],env:R.env});return;}
    const vmax=R.vmax||maxSpeed(R);
    if(dist>R.hipH*0.6)vd=mul(norm(d),Math.min(vmax,(dist-R.hipH*0.6)*0.9));}
  // 目標速度は急変させない（筋の応答時間）
  R.vSm=R.vSm?add(mul(R.vSm,1-Math.min(1,dt*2.5)),mul(vd,Math.min(1,dt*2.5))):vd;vd=R.vSm;
  R.vDes=vd;
  const speed=len(vd);
  // フルード数で歩容を決める（Alexander & Jayes 1983）
  const hh=R.hipH,Fr=speed*speed/(GRAV*hh);
  R.Fr=Fr;
  if(R.legs.length){
    const stride=speed>1e-3?Math.max(0.35*hh,hh*2.3*Math.pow(Math.max(Fr,1e-4),0.3)):0;
    const freq=speed>1e-3?clamp(speed/stride,0.6,4.5):0;
    R.stride=Math.min(stride,hh*2.2);R.freq=freq;
    R.duty=Fr<0.5?clamp(0.75-Fr*0.4,0.55,0.75):clamp(0.45-(Fr-0.5)*0.1,0.3,0.45);
    R.gaitName=speed<1e-3?'静止立位':Fr<0.5?'歩行':'走行';
    if(freq>0)R.cycle=(R.cycle+freq*dt)%1;
    if(R.tb&&!R.canFly)legPhases(R,dt);
  }
  if(speed>1e-3)R.headingDes=Math.atan2(vd[1],vd[0]);
}
function maxSpeed(R){
  const motor=R.g[17];
  // 巡航は歩行域（Fr<0.5）。運動遺伝子が高い個体のみ走行域へ（Alexander & Jayes 1983）
  if(R.mode==='legged')return Math.sqrt((0.04+motor*0.4)*GRAV*R.hipH)*Math.min(1,R.stats.supportRatio);
  if(R.mode==='chain')return R.segLen*(1+motor*3);
  return 10+motor*30;
}
function center(R){
  if(R.tb)return R.tb.x;
  if(!R.particles.length)return R.origin?R.origin.slice():[0,0,0];   // 固着（植物）は根元
  let c=[0,0,0];R.particles.forEach(p=>c=add(c,p.x));return mul(c,1/R.particles.length);
}

function substep(R,h){
  const env=R.env;
  // ---- 予測 ----
  R.particles.forEach(p=>{
    p.px=p.x.slice();
    const wz=R.gw(p.x[0],p.x[1]);
    let gz=-GRAV;
    if(wz!=null&&p.x[2]<wz){gz*=1-RHO_W/RHO;           // 浮力
      p.v=mul(p.v,Math.exp(-h*4));}                                // 水の抵抗（簡易）
    p.v[2]+=gz*h;p.v=mul(p.v,1-h*0.4);
    p.x=add(p.x,mul(p.v,h));
  });
  const tb=R.tb;
  if(tb){
    tb.px=tb.x.slice();tb.pq=tb.q.slice();
    const e=env(tb.x[0],tb.x[1]);let gz=-GRAV;
    const inWater=e.water!=null&&tb.x[2]<e.water;
    if(inWater){gz*=1-RHO_W/RHO;tb.v=mul(tb.v,Math.exp(-h*3));tb.w=mul(tb.w,Math.exp(-h*3));}
    if(R.canFly)gz=hover(R,e,h);
    tb.v[2]+=gz*h;
    if(R.mode==='float'||R.canFly||inWater)tb.v=add(tb.v,mul(sub(R.vDes,[tb.v[0],tb.v[1],0]),Math.min(1,h*(R.canFly?3:inWater?1.5:0.8))*(R.canFly?1:0.6)));
    if(R.mode==='legged'&&!R.canFly)gaitForce(R,h);
    posture(R,h);
    tb.x=add(tb.x,mul(tb.v,h));
    const dq=qmul([0,tb.w[0],tb.w[1],tb.w[2]],tb.q);
    tb.q=qnormalize([tb.q[0]+0.5*h*dq[0],tb.q[1]+0.5*h*dq[1],tb.q[2]+0.5*h*dq[2],tb.q[3]+0.5*h*dq[3]]);
  }
  // ---- 拘束 ----
  R.cons.forEach(c=>{
    if(c.type==='dist'){const pa=anchorWorld(R,c.A),pb=anchorWorld(R,c.B),d=sub(pa,pb),l=len(d);if(l<1e-9)return;
      let alpha=c.alpha||0;if(c.stiffHz){const mA=c.A.t==='P'?R.particles[c.A.i].m:tb?tb.M:1,mB=c.B.t==='P'?R.particles[c.B.i].m:tb?tb.M:1;alpha=alphaFromHz(c.stiffHz,Math.min(mA,mB));}
      solve(R,c.A,c.B,mul(d,1/l),l-c.rest,alpha,h,c.leg!=null?R.legs[c.leg].Fmax*h*h:null);}
    else if(c.type==='pose'&&tb){const p=R.particles[c.i],tgt=add(tb.x,qrot(tb.q,p.poseL)),d=sub(p.x,tgt),l=len(d);if(l<1e-9)return;
      solve(R,{t:'P',i:c.i},{t:'T',l:p.poseL},mul(d,1/l),l,alphaFromHz(c.stiffHz,p.m),h,c.leg!=null?R.legs[c.leg].Fmax*h*h:null);}
  });
  if(R.mode==='chain')undulate(R,h);
  if(R.mode==='legged'&&!R.canFly)gaitFeet(R,h);
  // ---- 接地（質点）＋摩擦 ----
  R.particles.forEach((p,i)=>contactParticle(R,p,i,h));
  if(tb)contactTorso(R,h);
  // ---- 速度更新 ----
  R.particles.forEach(p=>{p.v=mul(sub(p.x,p.px),1/h);});
  if(tb){tb.v=mul(sub(tb.x,tb.px),1/h);
    let dq=qmul(tb.q,qconj(tb.pq));if(dq[0]<0)dq=dq.map(v=>-v);
    tb.w=[2*dq[1]/h,2*dq[2]/h,2*dq[3]/h];}
}

// 飛行: 揚力で目標高度を維持（羽ばたきの平均揚力として扱う）
function hover(R,e,h){const tb=R.tb,zt=Math.max(e.z,e.water!=null?e.water:-1e9)+R.hipH*4;
  return clamp(GRAV*0+((zt-tb.x[2])*30-tb.v[2]*8),-GRAV,GRAV);}

// 姿勢制御（仮想モデル制御）: 接地肢が出せる範囲のトルクで体を水平・目標方位へ
function posture(R,h){
  const tb=R.tb;if(R.mode==='float'&&!R.canFly)return;
  const nC=R.legs.filter(l=>l.contact).length;
  let tmax;
  if(R.canFly)tmax=Infinity;
  else{if(nC===0)return;
    tmax=R.legs.reduce((a,l)=>a+((l.contact||l.planted)?l.Fmax*Math.hypot(l.hipL[0],l.hipL[1])*0.6:0),0);}
  const up=qrot(tb.q,[0,0,1]),fw=qrot(tb.q,[1,0,0]);
  const e=R.env(tb.x[0],tb.x[1]);
  const upD=norm(add(mul(e.n,0.5),[0,0,0.5]));
  const eTilt=cross(up,upD);
  let yawErr=0;if(R.headingDes!=null){const cur=Math.atan2(fw[1],fw[0]);yawErr=Math.atan2(Math.sin(R.headingDes-cur),Math.cos(R.headingDes-cur));}
  const wn=2*Math.PI*1.6;
  const err=add(eTilt,mul(upD,clamp(yawErr,-0.6,0.6)*0.7));
  const wb=qinvrot(tb.q,tb.w),eb=qinvrot(tb.q,err);
  let tau=[0,1,2].map(k=>tb.I[k]*(wn*wn*eb[k]-2*wn*wb[k]));
  const tl=len(tau);if(tl>tmax)tau=mul(tau,tmax/tl);
  const dw=qrot(tb.q,[tau[0]*tb.Iinv[0]*h,tau[1]*tb.Iinv[1]*h,tau[2]*tb.Iinv[2]*h]);
  tb.w=add(tb.w,dw);
}

// ================================================================
// 歩行制御（仮想モデル制御 VMC: Pratt et al. 2001 ＋ Raibert型の着地点）
//  ・立脚（接地して固定された足）が胴体に与える力 F を計算:
//      鉛直 Fz = M(g + ωn²(z目標−z) − 2ζωn·vz)  … 上限 Σ(立脚の Fmax=σ·A·EMA)
//      水平 Fxy = M·kv(v目標−v)                 … 上限 静止摩擦円錐 μs·Fz
//    → 筋力が足りなければ体は沈み、腹が地面に着く（二乗三乗則）。滑る地面では進めない。
//  ・遊脚は持ち上げて着地点へ運ぶ: 着地点 = 股関節直下 + v·T立脚/2 + k(v−v目標)
//  ・脚の位相はフルード数で決まる歩幅・周期・デューティ比（Alexander & Jayes 1983）と
//    Hildebrand/Wilson の位相差から
// ================================================================
function legPhases(R,dt){
  const tb=R.tb,speed=len(R.vDes);
  // 静止中でも足が定位置から大きくずれたら踏み直す
  let need=speed>1e-3;
  if(!need)R.legs.forEach(l=>{if(l.planted){const nom=add(tb.x,qrot(tb.q,l.footL)),d=sub(R.particles[l.foot].x,nom);d[2]=0;if(len(d)>R.hipH*0.45)need=true;}});
  if(need&&!R.freq){R.freq=1.4;R.stride=R.hipH*0.5;R.duty=0.7;}
  const run=R.Fr>=0.5;
  R.legs.forEach((l,li)=>{
    let stance=true,s=0;
    if(need&&R.freq){
      const ph=((R.cycle+(run&&R.trotPhases[li]!=null&&!l.arm?R.trotPhases[li]:l.phase))%1+1)%1;
      const beta=R.duty||0.7;
      if(ph>=beta){stance=false;s=(ph-beta)/(1-beta);}
    }
    const foot=R.particles[l.foot];
    if(!stance&&l.stance!==false){l.liftPos=foot.x.slice();l.planted=false;}   // 離地
    if(stance&&l.stance===false){l.planted=false;}                             // 着地待ち
    l.stance=stance;l.swingS=s;
    foot.swing=!stance;l.digits.forEach(i=>R.particles[i].swing=!stance);
  });
  if(need&&speed<=1e-3)R.cycle=(R.cycle+R.freq*dt)%1;
}
function gaitForce(R,h){
  const tb=R.tb,st=R.legs.filter(l=>l.stance&&l.planted);
  R.nStance=st.length;
  // 腹這い前進: 腹が地面に着いている（筋力不足の大型個体・管足で這う放射体）ときは、
  // 体側の筋/管足で地面を押して這う。推進力は体重×係数まで（滑りやすい腹ほど小さい）
  if(R.bellyContact){const arms=R.legs.some(l=>l.arm),M=R.totalMass,cap=(arms?0.3:0.1)*M*GRAV*MU_K;
    let Fx=M*2*(R.vDes[0]-tb.v[0]),Fy=M*2*(R.vDes[1]-tb.v[1]);const f=Math.hypot(Fx,Fy);if(f>cap){Fx*=cap/f;Fy*=cap/f;}
    tb.v[0]+=Fx/M*h;tb.v[1]+=Fy/M*h;}
  if(!st.length)return;
  const e=R.env(tb.x[0],tb.x[1]),M=R.totalMass;
  const zDes=e.z+R.standH;
  const wn=2*Math.PI*2.0,zeta=0.9;
  const Fz=clamp(M*(GRAV+wn*wn*(zDes-tb.x[2])-2*zeta*wn*tb.v[2]),0,st.reduce((a,l)=>a+l.Fmax,0));
  let Fx=M*4*(R.vDes[0]-tb.v[0]),Fy=M*4*(R.vDes[1]-tb.v[1]);
  const ft=Math.hypot(Fx,Fy),fm=MU_S*Fz;if(ft>fm){Fx*=fm/ft;Fy*=fm/ft;}
  tb.v[0]+=Fx/M*h;tb.v[1]+=Fy/M*h;tb.v[2]+=Fz/M*h;
  st.forEach(l=>{l.tg+=Fz/st.length;});
  R.supportF=Fz;
}
function gaitFeet(R,h){
  const tb=R.tb;
  const Tst=R.freq?(R.duty||0.7)/R.freq:0.5;
  R.legs.forEach(l=>{
    const foot=R.particles[l.foot];
    if(l.stance){
      if(l.planted){const eg=R.env(l.pin[0],l.pin[1]);l.pin[2]=eg.z+foot.r;foot.x=l.pin.slice();foot.w=0;return;}   // 固定足は常に地表に接する
      foot.w=1/foot.m;
      // 着地: 足（指）が接地したらその場で固定
      if(l.contact){l.planted=true;l.pin=foot.x.slice();foot.w=0;}
      else{const e=R.env(foot.x[0],foot.x[1]);foot.x[2]=Math.max(e.z+foot.r,foot.x[2]-h*60*R.hipH);}
      return;
    }
    foot.w=1/foot.m;
    // 遊脚の着地点（Raibert）: 股関節の定位置 + v·T/2 + k(v−v目標)
    const nom=add(tb.x,qrot(tb.q,l.footL));
    const td=[nom[0]+tb.v[0]*Tst*0.5+0.08*(tb.v[0]-R.vDes[0]),nom[1]+tb.v[1]*Tst*0.5+0.08*(tb.v[1]-R.vDes[1]),0];
    const s=l.swingS,sm=s*s*(3-2*s),st=l.liftPos||foot.x;
    const e=R.env(td[0],td[1]);
    const p=[st[0]+(td[0]-st[0])*sm,st[1]+(td[1]-st[1])*sm,0];
    const gz=R.env(p[0],p[1]).z;
    p[2]=Math.max(gz,st[2]*(1-sm)+(e.z+foot.r)*sm)+foot.r*0.2+Math.sin(Math.PI*s)*R.hipH*0.3;
    foot.x=p;
  });
}

// 蠕虫/遊泳: 頭→尾へ進む屈曲波（側方変位拘束）
function undulate(R,h){
  const n=R.chainN,P=R.particles;
  const motor=R.g[17],freq=0.8+motor*1.6,A=R.segLen*(0.25+motor*0.25);
  const head=P[n-1].x,neck=P[n-2].x,fw=norm(sub(head,neck));
  let turn=0;if(R.headingDes!=null){const cur=Math.atan2(fw[1],fw[0]);turn=clamp(Math.atan2(Math.sin(R.headingDes-cur),Math.cos(R.headingDes-cur)),-1,1);}
  const moving=len(R.vDes)>1e-3;
  for(let i=1;i<n-1;i++){
    const a=P[i-1],b=P[i],c=P[i+1];
    const t=sub(c.x,a.x);t[2]=0;const tl=len(t);if(tl<1e-9)continue;
    const side=[-t[1]/tl,t[0]/tl,0];
    const mid=mul(add(a.x,c.x),0.5);
    const lat=dot(sub(b.x,mid),side);
    const wave=moving?A*Math.sin(2*Math.PI*(freq*R.t+(n-1-i)/(n*0.9))):0;
    const bias=(i>n*0.6?turn*A*0.8:0);
    const C=lat-(wave+bias);
    const k=0.35;                                        // 筋の追従度
    b.x=add(b.x,mul(side,-C*k*0.6667));
    a.x=add(a.x,mul(side,C*k*0.1667));c.x=add(c.x,mul(side,C*k*0.1667));
  }
}

// 質点の接地と摩擦（静止/動摩擦, 蠕虫は異方性）
function contactParticle(R,p,i,h){
  const z0=R.gz(p.x[0],p.x[1]);
  if(z0+p.r-p.x[2]<=-p.r*0.15){p.contact=false;return;}       // 高速判定（地面から十分離れている）
  const e=R.env(p.x[0],p.x[1]);
  const pen=(e.z+p.r-p.x[2])*e.n[2];
  p.contact=pen>-p.r*0.15;
  if(pen<=0)return;
  p.x=add(p.x,mul(e.n,pen));p.fn+=pen*p.m/(h*h);
  let dx=sub(p.x,p.px);dx=sub(dx,mul(e.n,dot(dx,e.n)));
  const dl=len(dx);if(dl<1e-12)return;
  if(R.mode==='chain'&&p.kind==='body'){
    // 異方性摩擦: 前進 < 後退 < 横（ヘビ/ミミズの体表）
    const n=R.chainN,nx=R.particles[Math.min(n-1,i+1)].x,pv=R.particles[Math.max(0,i-1)].x;
    const tg=norm(sub(nx,pv)),f=dot(dx,tg),lat=sub(dx,mul(tg,f));
    const muF=f>0?0.1:0.25,muL=0.6;
    const cf=Math.min(1,muF*pen*8/Math.max(Math.abs(f),1e-9)),cl=Math.min(1,muL*pen*8/Math.max(len(lat),1e-9));
    p.x=sub(p.x,add(mul(tg,f*cf),mul(lat,cl)));return;
  }
  if(p.swing)return;                       // 遊脚は持ち上げ中（摩擦で引きずらない）
  if(dl<MU_S*pen)p.x=sub(p.x,dx);
  else p.x=sub(p.x,mul(dx,Math.min(MU_K*pen/dl,1)));
}
function contactTorso(R,h){
  const tb=R.tb;let any=false;
  tb.pts.forEach(tp=>{
    const w=add(tb.x,qrot(tb.q,tp.l));if(R.gz(w[0],w[1])+tp.r-w[2]<=0)return;
    const e=R.env(w[0],w[1]);
    const pen=(e.z+tp.r-w[2])*e.n[2];if(pen<=0)return;any=true;
    const A={t:'T',l:tp.l};
    solve(R,A,{t:'S',p:[0,0,0]},mul(e.n,-1),pen,0,h,null,false,true);
    const w2=add(tb.x,qrot(tb.q,tp.l)),wp=add(tb.px,qrot(tb.pq,tp.l));
    let dx=sub(w2,wp);dx=sub(dx,mul(e.n,dot(dx,e.n)));const dl=len(dx);
    // 這っている間は腹側の体表を滑らせる（推進は gaitForce の這い力）
    const crawl=len(R.vDes)>1e-3,ms=crawl?0.15:MU_S,mk=crawl?0.1:MU_K;
    if(dl>1e-12){const c=dl<ms*pen?dl:dl*Math.min(mk*pen/dl,1);solve(R,A,{t:'S',p:[0,0,0]},mul(dx,1/dl),c,0,h,null,false,true);}
  });
  R.bellyContact=any;
  // 脚の接地判定（足 or 指先が地面に触れているか）
  R.legs.forEach(l=>{l.contact=R.particles[l.foot].contact||l.digits.some(d=>R.particles[d].contact);});
}

// ================================================================
// 描画用: 各アンカーの現在位置・フレーム
// ================================================================
function particleFrame(R,i){
  const q=R.particles[i];
  const prev=q.prevI!=null?R.particles[q.prevI].x:null,next=q.nextI!=null?R.particles[q.nextI].x:null;
  let t=next&&prev?sub(next,prev):next?sub(next,q.x):prev?sub(q.x,prev):[1,0,0];
  const up=R.tb?qrot(R.tb.q,[0,0,1]):[0,0,1];
  return basis(t,up);
}
function frameAt(R,a){
  if(a.t==='T'){const q=R.tb.q;return[qrot(q,[1,0,0]),qrot(q,[0,1,0]),qrot(q,[0,0,1])];}
  if(a.t==='P')return particleFrame(R,a.i);
  return R.plantFrame;
}
function pointAt(R,a,frameCache){
  if(a.t==='T')return add(R.tb.x,qrot(R.tb.q,a.l));
  if(a.t==='P'){const p=R.particles[a.i].x;if(!a.l||(a.l[0]===0&&a.l[1]===0&&a.l[2]===0))return p;
    const F=frameCache?frameCache(a.i):particleFrame(R,a.i);return add(p,fromLocal(F,a.l));}
  // 植物: 根元基準＋風の揺れ（高さの2乗に比例）
  const l=a.l,hgt=Math.max(0,l[2])/R.plantH,sw=Math.sin(R.t*1.3+R.origin[0]*0.01)*0.07+Math.sin(R.t*2.9+l[2]*0.05)*0.025;
  const v=qrot(R.q,[l[0]+sw*hgt*hgt*R.plantH,l[1]+sw*0.5*hgt*hgt*R.plantH,l[2]]);
  return add(R.origin,v);
}
// 粒子フレームの前方向に合わせ、描画用に連結チェーンへ prev/next を張る
function linkChains(R){
  R.renderStrokes.forEach(rs=>{const ids=rs.nodes.filter(n=>n.a.t==='P').map(n=>n.a.i);
    for(let k=0;k<ids.length;k++){const p=R.particles[ids[k]];if(p.prevI==null&&k>0)p.prevI=ids[k-1];if(p.nextI==null&&k<ids.length-1)p.nextI=ids[k+1];}});
}

// 支持多角形と重心投影（詳細ビューの可視化用）
function supportInfo(R){
  if(!R.tb)return null;
  const pts=[];R.legs.forEach(l=>{if(!l.contact)return;[l.foot].concat(l.digits).forEach(i=>{const p=R.particles[i];if(p.contact)pts.push(p.x);});});
  // 全質量の重心
  let M=R.tb.M,c=mul(R.tb.x,R.tb.M);R.particles.forEach(p=>{M+=p.m;c=add(c,mul(p.x,p.m));});c=mul(c,1/M);
  const hull=convexHull2D(pts);
  const inside=hull.length>=3&&pointInHull(hull,c);
  return{com:c,hull,inside,legsDown:R.legs.filter(l=>l.contact).length,loads:R.legs.map(l=>l.load),weight:M*GRAV};
}
function convexHull2D(P){if(P.length<3)return P.slice();const a=P.slice().sort((p,q)=>p[0]-q[0]||p[1]-q[1]);
  const cr=(o,p,q)=>(p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0]);const lo=[],up=[];
  for(const p of a){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],p)<=0)lo.pop();lo.push(p);}
  for(let i=a.length-1;i>=0;i--){const p=a[i];while(up.length>=2&&cr(up[up.length-2],up[up.length-1],p)<=0)up.pop();up.push(p);}
  up.pop();lo.pop();return lo.concat(up);}
function pointInHull(H,p){for(let i=0;i<H.length;i++){const a=H[i],b=H[(i+1)%H.length];if((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])<0)return false;}return true;}

function create(model,opts){const R=build(model,opts);R.gz=opts.groundZ||((x,y)=>opts.env(x,y).z);R.gw=opts.water||((x,y)=>opts.env(x,y).water);linkChains(R);R.teleportDist=opts.teleportDist||1e9;R.plantFrame=[[1,0,0],[0,1,0],[0,0,1]];return R;}

return{create,step,center,pointAt,frameAt,particleFrame,supportInfo,place,GRAV,SIGMA,
  setGoal(R,x,y){R.goal=[x,y,0];},maxSpeed};
})();

