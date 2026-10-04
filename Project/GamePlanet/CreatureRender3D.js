/**
 * CreatureRender3D.js — 生物の3D描画（Gfx3D）
 *   ・手続き的皮膚シェーダー creatureMaterial（湿った皮膚/鱗/毛皮/甲板/樹皮/卵殻）
 *   ・InstancedMesh のプール Pool と、Rig を描く CreatureLayer（幼体の体型・呼吸・まばたき・接地影・卵）
 *   ・共有 WebGL レンダラ getRenderer
 * GamePlanet.html と creature-test.html から読み込む（classic script・グローバル定数 Gfx3D を定義）。
 * 依存: THREE（r128）、Rig（CreatureRig.js。描画時に参照）
 */
/* ==== gp3d-render (v17 実3D/物理/多細胞化) ==== */
// ================================================================
// Gfx3D — 地域ビュー/ミクロビュー/生物プレビューの実3Dレンダラ（Three.js r128）
//   ・生物: Rig の各ノード/器官を InstancedMesh（テーパー付きカプセル・楕円体・円錐）で描画
//   ・地域: 地形ハイトフィールド(頂点色+影)・波打つ水面・時代別の空/霧・熱水噴出孔の噴煙
//   ・ミクロ: 堆積物の海底・岩・噴出孔・マリンスノー・半透明細胞膜＋核・結合・鞭毛
// 座標変換: シミュ(x前,y左,z上) → three(x, z, -y)
// ================================================================
const Gfx3D = (function(){
'use strict';
const T3=v=>[v[0],v[2],-v[1]];
const clamp=(v,a,b)=>v<a?a:v>b?b:v;

// ---------- テーパー楕円カプセル用マテリアル（instance属性 aR=(ra,rb,ex,ez)） ----------
function tubeMaterial(base){
  const m=base||new THREE.MeshStandardMaterial({roughness:0.62,metalness:0.0});
  m.onBeforeCompile=sh=>{
    sh.vertexShader=sh.vertexShader
      .replace('#include <common>','#include <common>\nattribute vec4 aR;')
      .replace('#include <beginnormal_vertex>','#include <beginnormal_vertex>\nobjectNormal.x/=max(aR.z,1e-3);objectNormal.z/=max(aR.w,1e-3);objectNormal=normalize(objectNormal);')
      .replace('#include <begin_vertex>','#include <begin_vertex>\nfloat rad_=mix(aR.x,aR.y,clamp(position.y,0.0,1.0));transformed.x*=rad_*aR.z;transformed.z*=rad_*aR.w;');
  };
  return m;
}
function cylGeo(seg){const g=new THREE.CylinderGeometry(1,1,1,seg||12,1,true);g.translate(0,0.5,0);return g;}

// ---------- v18 皮膚シェーダー（インスタンス属性 aS=(皮膚の種類, 幼体斑紋, 模様の周波数, 濡れ)） ----------
//   種類 0=滑らか/湿った皮膚 1=鱗 2=毛皮 3=キチン/甲板 4=樹皮/種皮 5=卵殻（斑点）
//   ・手続き的ノイズのバンプ（法線摂動）で皮膚の凹凸・鱗・毛並みを出す
//   ・カウンターシェーディング（背は濃く腹は淡い）、色むら、溝の擬似AO、毛皮の縁の透過光
//   ・幼体の白い斑点（シカの子のような隠蔽色）
const SKIN_GLSL=`
varying vec4 vS;varying vec3 vLP;varying vec3 vWN;
float hsh_(vec3 p){p=fract(p*0.3183099+0.1);p*=17.0;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}
float vn_(vec3 x){vec3 i=floor(x),f=fract(x);f=f*f*(3.0-2.0*f);
  return mix(mix(mix(hsh_(i),hsh_(i+vec3(1,0,0)),f.x),mix(hsh_(i+vec3(0,1,0)),hsh_(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hsh_(i+vec3(0,0,1)),hsh_(i+vec3(1,0,1)),f.x),mix(hsh_(i+vec3(0,1,1)),hsh_(i+vec3(1,1,1)),f.x),f.y),f.z);}
float vor_(vec3 x){vec3 i=floor(x),f=fract(x);float d=8.0;
  for(int a=-1;a<=1;a++)for(int b=-1;b<=1;b++)for(int c=-1;c<=1;c++){vec3 o=vec3(float(a),float(b),float(c));
    vec3 r=o+vec3(hsh_(i+o),hsh_(i+o+13.1),hsh_(i+o+27.7))-f;d=min(d,dot(r,r));}
  return sqrt(d);}
float skinH_(vec3 p,float k){
  if(k<0.5)return vn_(p*0.7)*0.55+vn_(p*2.6)*0.25;                                   // 湿った皮膚
  if(k<1.5)return smoothstep(0.0,0.55,vor_(p*1.1))*0.9+vn_(p*4.0)*0.1;               // 鱗
  if(k<2.5)return vn_(vec3(p.x*4.0,p.y*0.7,p.z*4.0))*0.65+vn_(p*9.0)*0.35;           // 毛並み
  if(k<3.5)return 0.75-0.75*(1.0-smoothstep(0.0,0.09,abs(fract(p.y*0.16)-0.5)))+vn_(p*1.5)*0.25; // 甲板の節
  if(k<4.5)return vn_(vec3(p.x*1.6,p.y*0.18,p.z*1.6))*0.8+vn_(p*3.0)*0.2;            // 樹皮
  return vn_(p*1.2)*0.3;                                                              // 卵殻
}`;
function creatureMaterial(opts){
  opts=opts||{};
  const m=opts.base||new THREE.MeshStandardMaterial({roughness:opts.roughness!=null?opts.roughness:0.62,metalness:0.0});
  m.extensions={derivatives:true};
  // onBeforeCompile の関数ソースが同一だと three.js がプログラムを共有してしまうため、チューブ用と区別する
  m.customProgramCacheKey=()=>'gp-skin-'+(opts.tube?'tube':'solid');
  m.onBeforeCompile=sh=>{
    let vs=sh.vertexShader.replace('#include <common>','#include <common>\nattribute vec4 aS;varying vec4 vS;varying vec3 vLP;varying vec3 vWN;'+(opts.tube?'\nattribute vec4 aR;':''));
    if(opts.tube)vs=vs.replace('#include <beginnormal_vertex>','#include <beginnormal_vertex>\nobjectNormal.x/=max(aR.z,1e-3);objectNormal.z/=max(aR.w,1e-3);objectNormal=normalize(objectNormal);');
    vs=vs.replace('#include <begin_vertex>','#include <begin_vertex>\n'+(opts.tube?'float rad_=mix(aR.x,aR.y,clamp(position.y,0.0,1.0));transformed.x*=rad_*aR.z;transformed.z*=rad_*aR.w;\n':'')+
      'vS=aS;\n#ifdef USE_INSTANCING\nvLP=vec3(transformed.x*length(instanceMatrix[0].xyz),transformed.y*length(instanceMatrix[1].xyz),transformed.z*length(instanceMatrix[2].xyz));\nvWN=normalize(mat3(modelMatrix)*mat3(instanceMatrix)*objectNormal);\n#else\nvLP=transformed;vWN=normalize(mat3(modelMatrix)*objectNormal);\n#endif\n'+
      (opts.tube?'':'')
    );
    sh.vertexShader=vs;
    sh.fragmentShader=sh.fragmentShader
      .replace('#include <common>','#include <common>\n'+SKIN_GLSL)
      .replace('#include <color_fragment>',`#include <color_fragment>
        vec3 P_=vLP*max(vS.z,0.01);float k_=vS.x;float h_=skinH_(P_,k_);
        // アンチエイリアス: 1ピクセルに模様の1周期以上が入るほど遠い/小さいときは凹凸を平均値へ
        float mf_=k_<0.5?2.6:k_<1.5?3.0:k_<2.5?6.0:k_<3.5?1.2:k_<4.5?2.5:1.2;
        float aa_=clamp(1.6-length(fwidth(P_))*mf_*1.4,0.0,1.0);h_=mix(0.5,h_,aa_);
        float up_=vWN.y;
        diffuseColor.rgb*=0.84+0.3*vn_(P_*0.22+7.0);                          // 色むら
        diffuseColor.rgb*=mix(0.78,1.08,h_);                                   // 溝の擬似AO
        if(k_<4.5)diffuseColor.rgb*=mix(1.16,0.84,smoothstep(-0.55,0.75,up_)); // カウンターシェーディング
        if(k_>4.5)diffuseColor.rgb*=1.0-0.6*(1.0-smoothstep(0.12,0.2,vor_(P_*0.9+2.0)))*step(0.6,hsh_(floor(P_*0.9+2.0))); // 卵殻の斑点
        if(vS.y>0.01){float sp_=1.0-smoothstep(0.2,0.3,vor_(P_*0.55+3.1));
          diffuseColor.rgb=mix(diffuseColor.rgb,min(vec3(1.0),diffuseColor.rgb*1.6+0.12),sp_*vS.y*smoothstep(-0.1,0.5,up_));}`)
      .replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
        roughnessFactor=mix(roughnessFactor,0.2,vS.w);
        if(k_>1.5&&k_<2.5)roughnessFactor=max(roughnessFactor,0.85);
        if(k_>2.5&&k_<3.5)roughnessFactor*=0.6;
        if(k_>4.5)roughnessFactor=0.42;`)
      .replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
        {// 凹凸の高さは模様の大きさに比例（＝傾きが一定）。細かすぎる模様は aa_ で平らにする
         float bs_=(k_<0.5?0.12:k_<1.5?0.3:k_<2.5?0.18:k_<3.5?0.25:k_<4.5?0.4:0.08)/(max(vS.z,0.01)*mf_)*aa_;
         vec3 dpx_=dFdx(-vViewPosition),dpy_=dFdy(-vViewPosition);
         float dhx_=dFdx(h_)*bs_,dhy_=dFdy(h_)*bs_;
         vec3 r1_=cross(dpy_,normal),r2_=cross(normal,dpx_);float det_=dot(dpx_,r1_);
         vec3 gr_=sign(det_)*(dhx_*r1_+dhy_*r2_);
         normal=normalize(abs(det_)*normal-gr_);}`)
      .replace('#include <emissivemap_fragment>',`#include <emissivemap_fragment>
        {float fr_=pow(1.0-abs(dot(normal,normalize(vViewPosition))),3.0);
         totalEmissiveRadiance+=diffuseColor.rgb*fr_*(k_>1.5&&k_<2.5?0.28:0.08);}`);
  };
  return m;
}

// ---------- インスタンスプール ----------
class Pool{
  constructor(scene,geo,mat,max,opts){
    opts=opts||{};
    this.max=max;this.n=0;
    if(opts.tube){this.aR=new THREE.InstancedBufferAttribute(new Float32Array(max*4),4);this.aR.setUsage(THREE.DynamicDrawUsage);geo.setAttribute('aR',this.aR);}
    if(opts.skin){this.aS=new THREE.InstancedBufferAttribute(new Float32Array(max*4),4);this.aS.setUsage(THREE.DynamicDrawUsage);geo.setAttribute('aS',this.aS);this.cur=[0,0,0.3,0];}
    this.mesh=new THREE.InstancedMesh(geo,mat,max);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.setColorAt(0,new THREE.Color(1,1,1));this.mesh.instanceColor.setUsage(THREE.DynamicDrawUsage);
    this.mesh.frustumCulled=false;
    this.mesh.castShadow=opts.shadow!==false;this.mesh.receiveShadow=!!opts.receive;
    if(opts.renderOrder!=null)this.mesh.renderOrder=opts.renderOrder;
    scene.add(this.mesh);
  }
  begin(){this.n=0;}
  // X,Y,Z: three空間の列ベクトル（スケール込み）, P: 位置
  push(X,Y,Z,P,c,aR){
    if(this.n>=this.max)return;const i=this.n++,a=this.mesh.instanceMatrix.array,o=i*16;
    a[o]=X[0];a[o+1]=X[1];a[o+2]=X[2];a[o+3]=0;a[o+4]=Y[0];a[o+5]=Y[1];a[o+6]=Y[2];a[o+7]=0;
    a[o+8]=Z[0];a[o+9]=Z[1];a[o+10]=Z[2];a[o+11]=0;a[o+12]=P[0];a[o+13]=P[1];a[o+14]=P[2];a[o+15]=1;
    const ca=this.mesh.instanceColor.array;ca[i*3]=c[0];ca[i*3+1]=c[1];ca[i*3+2]=c[2];
    if(aR&&this.aR){const r=this.aR.array;r[i*4]=aR[0];r[i*4+1]=aR[1];r[i*4+2]=aR[2];r[i*4+3]=aR[3];}
    if(this.aS){const r=this.aS.array,k=this.cur;r[i*4]=k[0];r[i*4+1]=k[1];r[i*4+2]=k[2];r[i*4+3]=k[3];}
  }
  end(){this.mesh.count=this.n;this.mesh.instanceMatrix.needsUpdate=true;this.mesh.instanceColor.needsUpdate=true;if(this.aR)this.aR.needsUpdate=true;if(this.aS)this.aS.needsUpdate=true;}
}

// ---------- 生物描画（Rig → インスタンス） ----------
const v3={add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]],sub:(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]],mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s],
  cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],len:a=>Math.hypot(a[0],a[1],a[2]),
  norm:a=>{const l=Math.hypot(a[0],a[1],a[2])||1;return[a[0]/l,a[1]/l,a[2]/l];},dot:(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2]};
function perpFrame(dir,up){let y=v3.norm(dir);let x=v3.cross(up,y);if(v3.len(x)<1e-5)x=v3.cross([1,0,0],y);if(v3.len(x)<1e-5)x=v3.cross([0,1,0],y);x=v3.norm(x);const z=v3.cross(x,y);return[x,y,z];}
function strokeCol(col,kind){let[r,g,b]=col;
  if(kind==='wood'){r=r*0.4+0.34;g=g*0.35+0.22;b=b*0.3+0.1;}
  else if(kind==='muscle'){r=Math.min(1,r*0.7+0.28);g=g*0.55;b=b*0.5;}
  else if(kind==='belly'){r=Math.min(1,r*0.5+0.42);g=Math.min(1,g*0.5+0.4);b=Math.min(1,b*0.45+0.38);}
  return[r,g,b];}
// sRGB→リニア（InstancedMeshの色はリニア空間で解釈されるため）
const lin=c=>c.map(v=>Math.pow(clamp(v,0,1),2.2));
function organColor(o,col){const[r,g,b]=col,k=o.type;
  switch(k){
    case'leaf':return[r*.4,Math.min(1,g+.35),b*.35];
    case'fruit':return[.85,g*.3+.18,b*.2];
    case'tooth':return[.97,.95,.88];
    case'claw':return[r*.35+.12,g*.3+.1,b*.28+.08];
    case'spike':return o.col||[.52,.45,.36];
    case'fin':return[Math.min(1,r+.15),Math.min(1,g+.15),Math.min(1,b+.2)];
    case'hoof':return[.14,.11,.09];
    case'ear':return[r*.75+.1,g*.6+.08,b*.55+.08];
    case'muzzle':return[Math.min(1,r*.7+.28),g*.55,b*.5];
    case'whisker':return[.9,.88,.84];
    case'hair':return[r*.55+.08,g*.5+.06,b*.45+.06];
    case'feather':return[Math.min(1,r*.85+.12),Math.min(1,g*.85+.12),Math.min(1,b*.9+.12)];
    case'scale':return[r*.6+.15,g*.65+.15,b*.5+.1];
    case'marking':case'stripe':return o.col||[r*.3,g*.3,b*.3];
    case'core':return[b,g*.6,r*.5];
    case'tentacle':return[r,g,b];
    default:return[r,g,b];
  }}

// 形質 → 皮膚の種類（0=湿った皮膚 1=鱗 2=毛皮 3=キチン/甲板 4=樹皮）
function skinKind(R){const g=R.g||[];
  if(R.mode==='plant')return 4;
  if(R.mode==='float')return 0;
  if((g[20]||0)>.55)return 0;                 // 水棲: ぬめりのある皮膚
  if((g[2]||0)>.62)return 3;                  // 高装甲: 甲板・キチン
  if((g[0]||0)>.5&&(g[4]||0)<.55)return 1;    // 厚い外皮で神経が控えめ: 鱗（爬虫類的）
  if((g[16]||0)>.3)return 2;                  // 中〜大型の陸生: 毛皮
  return 0;}
class CreatureLayer{
  constructor(scene,max){
    max=max||12000;
    // v18: 胴・肢・頭は手続き的皮膚シェーダー（鱗/毛並み/湿った皮膚/甲板/樹皮/卵殻）
    this.tube=new Pool(scene,cylGeo(18),creatureMaterial({tube:true,roughness:0.62}),max,{tube:true,skin:true});
    this.ball=new Pool(scene,new THREE.SphereGeometry(1,20,14),creatureMaterial({roughness:0.62}),max,{skin:true});
    this.ellip=new Pool(scene,new THREE.SphereGeometry(1,18,12),creatureMaterial({roughness:0.55}),max,{skin:true});
    const cg=new THREE.ConeGeometry(1,1,10);cg.translate(0,0.5,0);
    this.cone=new Pool(scene,cg,new THREE.MeshStandardMaterial({roughness:0.45}),max);
    // 眼: 角膜の濡れた反射（クリアコート）
    this.eye=new Pool(scene,new THREE.SphereGeometry(1,16,12),new THREE.MeshPhysicalMaterial({roughness:0.25,metalness:0.0,clearcoat:1.0,clearcoatRoughness:0.04}),2000);
    this.flat=new Pool(scene,new THREE.SphereGeometry(1,12,8),new THREE.MeshStandardMaterial({roughness:0.7,side:THREE.DoubleSide,transparent:true,opacity:0.88}),max,{shadow:true});
    // 寒天質の卵（水中の卵塊）
    this.jelly=new Pool(scene,new THREE.SphereGeometry(1,14,10),new THREE.MeshPhysicalMaterial({roughness:0.05,metalness:0,transparent:true,opacity:0.42,clearcoat:1,depthWrite:false}),3000,{shadow:false,renderOrder:3});
    // 接地影（足元の柔らかい接触影。シャドウマップの粗さを補い、地面に立っている感じを出す）
    const bg=new THREE.PlaneGeometry(2,2);bg.rotateX(-Math.PI/2);
    const bm=new THREE.MeshBasicMaterial({map:soft(),color:0x000000,transparent:true,opacity:0.5,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-4,polygonOffsetUnits:-4});
    this.blob=new Pool(scene,bg,bm,4000,{shadow:false,renderOrder:1});
    this.pools=[this.tube,this.ball,this.ellip,this.cone,this.eye,this.flat,this.jelly,this.blob];
  }
  setSkin(k){this.tube.cur=k;this.ball.cur=k;this.ellip.cur=k;}
  // 接地影: (x,y)=シミュ座標, z=地面高, r=半径
  addBlob(x,y,z,r){this.blob.push([r,0,0],[0,1,0],[0,0,r],[x,z+0.4,-y],[1,1,1]);}
  // 卵・種子・卵塊（o: 個体, P: シミュ座標, prog: 発生の進み 0..1）
  addEgg(o,P,size,prog,t,water){
    const g=o.g,rnd=hash2(o.id,7,3),wob=prog>0.72?Math.sin(t*(10+rnd*6)+rnd*9)*0.35*(prog-0.72)/0.28:0;
    const fw=[Math.cos(wob),0,Math.sin(wob)],up=[-Math.sin(wob),0,Math.cos(wob)];
    if(o.bmode==='seed'){
      // 種子（樹皮質の種皮）→ 発芽が近づくと芽が出る
      this.setSkin([4,0,1.4,0]);const c=lin([.42,.3,.17]);
      this.ellip.push(T3([size*.7,0,0]),T3([0,size*.5,0]),T3([0,0,size*.45]),T3([P[0],P[1],P[2]+size*.4]),c);
      if(prog>0.55){const h=size*(prog-0.55)*4;this.cone.push(T3([size*.18,0,0]),T3([0,0,h]),T3([0,size*.18,0]),T3([P[0],P[1],P[2]+size*.6]),lin([.35,.75,.25]));}
      return;}
    if(water){
      // 水中: 寒天質の卵（カエル/魚の卵塊のように透明な殻の中に胚が見える）
      const e=size*(0.35+prog*0.45);
      this.jelly.push(T3([size,0,0]),T3([0,size,0]),T3([0,0,size]),[P[0],P[2]+size,-P[1]],lin([.75,.85,.8]));
      this.setSkin([0,0,1,0.8]);
      this.ellip.push(T3(v3.mul(fw,e*(1+prog*.5))),T3([0,e,0]),T3(v3.mul(up,e)),T3([P[0],P[1],P[2]+size]),lin([.12,.11,.1].map((v,i)=>v+(o._col?o._col[i]*.25:0))));
      return;}
    // 陸上: 斑点のある硬い殻の卵（孵化前に揺れる）
    const base=g[11]>.55?[.62,.72,.66]:g[20]>.5?[.86,.84,.74]:[.93,.9,.82];
    this.setSkin([5,0,2.2,0]);
    this.ellip.push(T3(v3.mul(fw,size*.78)),T3([0,size*.78,0]),T3(v3.mul(up,size*1.05)),T3([P[0],P[1],P[2]+size*0.95]),lin(base));
  }
  begin(){this.pools.forEach(p=>p.begin());}
  end(){this.pools.forEach(p=>p.end());}
  // R: Rig, opts:{sel, tint, juv(0..1 幼さ), t(時刻), crouch(隠れる), puff(威嚇), camo([r,g,b] 隠蔽色), pant(呼吸の速さ倍率), groundZ}
  add(R,opts){
    opts=opts||{};
    const fc={};const F=i=>fc[i]||(fc[i]=Rig.particleFrame(R,i));
    const upRef=R.tb?Rig.frameAt(R,{t:'T'})[2]:[0,0,1];
    const juv=opts.juv||0,t=opts.t||0,seed=opts.seed||0;
    // 姿勢の演出: 隠れる=身を低く伏せる / 威嚇=体を膨らませて立ち上がる（足は地面に残る）
    const C0=Rig.center(R),gz0=opts.groundZ!=null?opts.groundZ:C0[2]-R.hipH;
    const sxy=opts.puff?1.08:opts.crouch?1.05:1,sz=opts.puff?1.15:opts.crouch?0.62:1;
    const xf=(sxy!==1||sz!==1)?p=>[C0[0]+(p[0]-C0[0])*sxy,C0[1]+(p[1]-C0[1])*sxy,gz0+(p[2]-gz0)*sz]:p=>p;
    const pos=a=>xf(Rig.pointAt(R,a,F));
    const camo=opts.camo,ck=opts.camoK||0;
    const tint=c=>{let o=c;
      // 幼体は淡く柔らかい色
      if(juv>0)o=[o[0]+(Math.min(1,o[0]*1.1+.1)-o[0])*juv*.5,o[1]+(Math.min(1,o[1]*1.1+.09)-o[1])*juv*.5,o[2]+(Math.min(1,o[2]*1.05+.06)-o[2])*juv*.5];
      if(camo&&ck>0)o=[o[0]+(camo[0]-o[0])*ck,o[1]+(camo[1]-o[1])*ck,o[2]+(camo[2]-o[2])*ck];
      if(opts.sel)o=[Math.min(1,o[0]*1.15+.05),Math.min(1,o[1]*1.15+.05),Math.min(1,o[2]*1.1+.05)];return lin(o);};
    // 皮膚の種類（形質から）と模様の周波数（体の大きさに合わせる）
    const g=R.g||[],sk=opts.skin!=null?opts.skin:skinKind(R);
    const freq=clamp(0.55/Math.max(0.15,R.scale||1),0.1,3);
    const wet=sk===0?0.75:0;
    // 呼吸: 胴が周期的に膨らむ（小さい・若い・興奮しているほど速い）
    const br=(1.6+juv*2.2+(opts.pant||0)*3)/Math.sqrt(Math.max(0.3,R.scale||1));
    const breath=1+Math.sin(t*br*Math.PI*2*0.35+seed*6.28)*(0.025+(opts.pant?0.02:0));
    let ext=0;
    R.renderStrokes.forEach(rs=>{
      const col=tint(strokeCol(R.color,rs.kind));
      const isBody=rs.group==='body'||rs.group==='belly';
      const rk=(isBody?breath:1)*(opts.puff?1.06:1);
      this.setSkin([rs.kind==='wood'?4:(rs.group==='digit'&&sk===2?0:sk),isBody||rs.group==='leg'?juv*(opts.spots||0):0,freq,rs.kind==='leaf'?0.3:wet]);
      const P=rs.nodes.map(n=>pos(n.a));
      for(let k=0;k<rs.nodes.length;k++){
        const n=rs.nodes[k],p=P[k],r=n.r*rk,r1=k<rs.nodes.length-1?rs.nodes[k+1].r*rk:r;
        const ex=rs.ellipse&&n.rw?n.rw/n.r:1,ez=rs.ellipse&&n.rh?n.rh/n.r:1;
        const dx=p[0]-C0[0],dy=p[1]-C0[1];ext=Math.max(ext,Math.hypot(dx,dy)+r*0.6);
        if(k<rs.nodes.length-1){
          const q=P[k+1],d=v3.sub(q,p),L=v3.len(d);
          if(L>1e-6){const fr=perpFrame(d,upRef);
            const ex2=rs.ellipse&&rs.nodes[k+1].rw?(n.rw+rs.nodes[k+1].rw)/(n.r+rs.nodes[k+1].r):ex;
            const ez2=rs.ellipse&&rs.nodes[k+1].rh?(n.rh+rs.nodes[k+1].rh)/(n.r+rs.nodes[k+1].r):ez;
            this.tube.push(T3(fr[0]),T3(v3.mul(fr[1],L)),T3(fr[2]),T3(p),col,[r,r1,ex2,ez2]);}
        }
        const dir=k<P.length-1?v3.sub(P[k+1],p):k>0?v3.sub(p,P[k-1]):[1,0,0];
        const fr=perpFrame(dir,upRef);
        this.ball.push(T3(v3.mul(fr[0],r*ex)),T3(v3.mul(fr[1],r)),T3(v3.mul(fr[2],r*ez)),T3(p),col);
      }
    });
    // 接地影
    if(R.mode!=='plant'&&opts.blob!==false){const lift=Math.max(0,C0[2]-gz0-R.hipH*1.2);const a=Math.max(0.15,0.75-lift/Math.max(20,R.hipH*6));
      this.addBlob(C0[0],C0[1],gz0,Math.max(4,ext*1.15+R.hipH*0.3)*(1.25-a*0.35));}
    // まばたき（数秒ごとに一瞬まぶたを閉じる）
    const blink=opts.t!=null&&((t*0.31+seed*3.7)%1)<0.035?0.12:1;
    this.setSkin([sk,0,freq*1.4,wet]);
    const minO=opts.minOrgan||0;
    R.organs.forEach(o=>{
      if(minO&&o.size<minO&&o.type!=='eye'&&o.type!=='head')return;
      const p=pos(o.a);
      let fr=o.a.t==='T'?Rig.frameAt(R,o.a):o.a.t==='P'?F(o.a.i):(R.plantFrame);
      const dirW=v3.norm([fr[0][0]*o.dirL[0]+fr[1][0]*o.dirL[1]+fr[2][0]*o.dirL[2],fr[0][1]*o.dirL[0]+fr[1][1]*o.dirL[1]+fr[2][1]*o.dirL[2],fr[0][2]*o.dirL[0]+fr[1][2]*o.dirL[1]+fr[2][2]*o.dirL[2]]);
      // 幼体の体型（ベビースキーマ）: 頭と目が大きく、鼻先は短く、角・牙・爪・棘は未発達
      const JS={head:1+.5*juv,eye:1+.6*juv,ear:1+.25*juv,muzzle:1-.35*juv,tooth:1-.7*juv,claw:1-.6*juv,spike:1-.8*juv,hoof:1-.3*juv}[o.type]||1;
      const B=perpFrame(dirW,upRef),s=Math.max(0.05,o.size)*JS,col=tint(organColor(o,R.color));
      const put=(pool,sx,sy,sz,off)=>{const pp=off?v3.add(p,v3.mul(dirW,off)):p;pool.push(T3(v3.mul(B[0],sx)),T3(v3.mul(B[1],sy)),T3(v3.mul(B[2],sz)),T3(pp),col);};
      switch(o.type){
        case'eye':{const bz=blink;this.eye.push(T3(v3.mul(B[0],s)),T3(v3.mul(B[1],s)),T3(v3.mul(B[2],s*bz)),T3(p),bz<1?col:lin([.93,.91,.86]));
          if(bz<1)break;
          const iris=lin([Math.min(1,R.color[0]*.5+.12),Math.min(1,R.color[1]*.42+.08),Math.min(1,R.color[2]*.4+.08)]);
          this.eye.push(T3(v3.mul(B[0],s*.62)),T3(v3.mul(B[1],s*.5)),T3(v3.mul(B[2],s*.62)),T3(v3.add(p,v3.mul(dirW,s*.62))),iris);
          this.eye.push(T3(v3.mul(B[0],s*.3)),T3(v3.mul(B[1],s*.3)),T3(v3.mul(B[2],s*.3)),T3(v3.add(p,v3.mul(dirW,s*.82))),[0.005,0.004,0.005]);
          // 角膜のハイライト（光源側の小さな白点）
          this.eye.push(T3(v3.mul(B[0],s*.12)),T3(v3.mul(B[1],s*.12)),T3(v3.mul(B[2],s*.12)),T3(v3.add(v3.add(p,v3.mul(dirW,s*.86)),v3.mul(B[2],s*.32))),[3,3,3]);break;}
        case'head':put(this.ellip,s*.78,s*1.05,s*.72,s*.15);break;
        case'muzzle':put(this.ellip,s*.55,s*1.0,s*.5,s*.5);break;
        case'core':case'fruit':case'tentacle':put(this.ellip,s,s,s);break;
        case'ear':put(this.flat,s*.45,s*.9,s*.12,s*.4);break;
        case'leaf':put(this.flat,s*.5,s*1.0,s*.06,s*.8);break;
        case'fin':put(this.flat,s*.5,s*.9,s*.05,s*.5);break;
        case'marking':put(this.flat,s*.75,s*.12,s*.6);break;
        case'stripe':put(this.flat,s*1.1,s*.08,s*.28);break;
        case'scale':put(this.flat,s*.45,s*.12,s*.45);break;
        case'tooth':case'claw':put(this.cone,s*.35,s*1.2,s*.35);break;
        case'spike':put(this.cone,s*.22,s*0.75,s*.22);break;
        case'hoof':put(this.cone,s*.6,s*.9,s*.6);break;
        case'whisker':put(this.cone,s*.05,s*2.2,s*.05);break;
        case'hair':put(this.cone,s*.12,s*.6,s*.12);break;
        case'feather':put(this.flat,s*.35,s*1.05,s*.06,s*.5);break;
        case'digit':put(this.ellip,s*.35,s*.55,s*.3);break;
        default:put(this.ellip,s*.5,s*.5,s*.5);
      }
    });
  }
}

// ================================================================
// 共有レンダラ（オフスクリーン → 2Dキャンバスへ合成）
// ================================================================
let renderer=null,canvas=null;
function getRenderer(w,h){
  if(!renderer){canvas=document.createElement('canvas');
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});
    renderer.setPixelRatio(Math.min(1.5,devicePixelRatio||1));
    renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
    renderer.outputEncoding=THREE.sRGBEncoding;
    renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;}
  const cw=Math.max(1,Math.round(w)),ch=Math.max(1,Math.round(h));
  if(renderer._w!==cw||renderer._h!==ch){renderer.setSize(cw,ch,false);renderer._w=cw;renderer._h=ch;}
  return renderer;
}
function getCanvas(){return canvas;}

// ---------- 小さなユーティリティ ----------
function makeSoftSprite(){const c=document.createElement('canvas');c.width=c.height=64;const x=c.getContext('2d'),g=x.createRadialGradient(32,32,0,32,32,32);
  g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(0.4,'rgba(255,255,255,.5)');g.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=g;x.fillRect(0,0,64,64);return new THREE.CanvasTexture(c);}
let softTex=null;const soft=()=>softTex||(softTex=makeSoftSprite());
function hash2(i,j,s){let h=(i*374761393+j*668265263+s*1442695041)|0;h=Math.imul(h^(h>>>13),1274126177);return((h^(h>>>16))>>>0)/4294967295;}

return{Pool,CreatureLayer,creatureMaterial,skinKind,tubeMaterial,cylGeo,getRenderer,getCanvas,T3,lin,soft,hash2,perpFrame,v3};
})();
