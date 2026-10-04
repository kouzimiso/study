/**
 * Evolution.js — 微生物から「魚・トカゲ・ネズミの祖先」までの進化段階（グレード）
 *
 * GamePlanet.html と creature-test.html から読み込む（classic script・グローバル定数 Evo を定義）。
 *
 * 考え方:
 *   ・各系統は進化段階 grade（0〜9）を持ち、子は親の段階を受け継ぐ
 *   ・次の段階へ進むには「大気の酸素」と「必要な遺伝子（接着・神経・筋肉・感覚…）」の条件がそろい、
 *     そのうえで繁殖のたびに小さな確率で革新が起きる（主要な進化的移行: Maynard Smith & Szathmáry 1995）
 *   ・段階ごとに遺伝子の上限（体の大きさ・神経・筋肉・装甲…）があり、上限を超える形質は生まれない
 *     → その段階に達するまで魚・トカゲ・ネズミのような生物は現れない
 *   ・見た目（形態）も段階で制限する。CreatureEngine に渡す遺伝子を段階に合わせて調整する（phenotype）
 *
 * 依存（呼び出し時に参照）: CreatureEngine（形態生成）、trophic(g)（植物かどうかの判定）
 * 公開: Evo.GRADES / Evo.world / assign / canAdvance / constrain / phenotype / build / label / colonyCells / onAdvance
 */
const Evo=(function(){
'use strict';
const c01=v=>v<0?0:v>1?1:v;
// ---- 段階の定義（年代は地球史での目安） ----
const GRADES=[
  {name:'原核生物',sub:'細菌・古細菌。核をもたない小さな細胞',ago:'約38億年前',rep:'シアノバクテリア・古細菌',plant:'シアノバクテリア'},
  {name:'真核生物（単細胞）',sub:'核とミトコンドリアをもつ大きな細胞',ago:'約18億年前',rep:'アメーバ・鞭毛虫',plant:'単細胞の藻類'},
  {name:'群体',sub:'分裂した細胞が離れずに集まる',ago:'約10億年前',rep:'ボルボックス・襟鞭毛虫の群体',plant:'群体性の藻類'},
  {name:'単純な多細胞体',sub:'体細胞と生殖細胞の分業',ago:'約8〜6億年前',rep:'海綿・平板動物',plant:'多細胞の藻類（海藻）'},
  {name:'組織と神経網',sub:'放射相称・刺胞動物型',ago:'約5.8億年前（エディアカラ紀）',rep:'クラゲ・イソギンチャク',plant:'多細胞の藻類（海藻）'},
  {name:'左右相称動物',sub:'前後・左右・中枢神経と筋肉',ago:'約5.55億年前',rep:'キンベレラ・イカリア（蠕虫）',plant:'多細胞の藻類（海藻）'},
  {name:'カンブリア爆発',sub:'眼と硬い殻。原始的な魚と節足動物',ago:'約5.3億年前',rep:'ハイコウイクチス（魚）・三葉虫',plant:'多細胞の藻類（海藻）'},
  {name:'四肢動物の祖先',sub:'肉鰭と肺。ひれが脚になる',ago:'約3.75億年前（デボン紀）',rep:'ティクターリク・イクチオステガ',plant:'陸上植物'},
  {name:'有羊膜類',sub:'乾燥に耐える卵で陸上に産卵',ago:'約3.1億年前（石炭紀）',rep:'ヒロノムス（トカゲとネズミの共通祖先）',plant:'陸上植物'},
  {name:'多様化（制限なし）',sub:'爬虫類・哺乳類・鳥類などへの自由な放散',ago:'約2.5億年前〜',rep:'トカゲ・ネズミ・恐竜…',plant:'陸上植物'},
];
const MAXG=GRADES.length-1;   // 9 = 制限なし

// ---- 次の段階へ進む条件（O2 は大気の酸素分圧: 0.21 ≈ 現在）----
//   真核生物の呼吸とステロール合成には酸素が要る。動物の出現は O2 ≳ 1〜4% PAL（Mills et al. 2014）、
//   カンブリア紀の大型捕食動物は 10〜25% PAL 以上（Sperling et al. 2013）、四肢動物の陸上化はデボン紀の
//   陸上植物の拡大後（Clack 2012）、有羊膜卵は乾燥した陸での産卵を可能にした（Carroll 1969; Sumida & Martin 1997）
const REQ=[
  null,
  {o2:.004,txt:'酸素 ≥ 0.4%（大酸化イベント後）',gene:g=>true},
  {o2:.004,txt:'接着 ≥ 0.5（分裂後も離れない）',gene:g=>g[3]>=.5},
  {o2:.006,txt:'接着 ≥ 0.6・幹細胞 ≥ 0.5（体細胞と生殖細胞の分業）',gene:g=>g[3]>=.6&&g[9]>=.5},
  {o2:.012,txt:'酸素 ≥ 1.2%（新原生代の酸化）・神経 ≥ 0.3（神経網）',gene:g=>g[4]>=.3},
  {o2:.02,txt:'酸素 ≥ 2%・筋肉 ≥ 0.45・神経 ≥ 0.4（中枢神経）',gene:g=>g[1]>=.45&&g[4]>=.4},
  {o2:.04,txt:'酸素 ≥ 4%・感覚 ≥ 0.45（眼）・運動 ≥ 0.5 または装甲 ≥ 0.35',gene:g=>g[7]>=.45&&(g[17]>=.5||g[2]>=.35)},
  {o2:.1,txt:'酸素 ≥ 10%・陸上植物がある・筋肉 ≥ 0.55・水適応 ≤ 0.65（肺と肉鰭）',gene:g=>g[1]>=.55&&g[20]<=.65,landPlants:true},
  {o2:.12,txt:'酸素 ≥ 12%・陸にいる・水適応 ≤ 0.5・外皮 ≥ 0.35（乾燥に耐える卵と皮膚）',gene:g=>g[20]<=.5&&g[0]>=.35,onLand:true},
  {o2:.15,txt:'酸素 ≥ 15%・神経維持 ≥ 0.5（活発な代謝）',gene:g=>g[5]>=.5,onLand:true},
];
// 植物の系統: 0→1→2→3（海藻）→7（陸上植物）。陸上化にはオゾン層（酸素）と陸に接していることが要る
const PLANT_LAND={o2:.04,txt:'酸素 ≥ 4%（オゾン層が紫外線を遮る）・陸に接している',gene:g=>true,onLand:true};

// ---- 段階ごとの遺伝子の上限（実際の遺伝子に適用。次の段階の条件より少し上に置き、進化の余地を残す） ----
// 16:体格 4:神経 7:感覚 1:筋肉 2:装甲 22:攻撃 17:運動
const CAPS=[
  {16:.06,4:.2,7:.3,1:.3,2:.3,22:.5},
  {16:.12,4:.3,7:.4,1:.4,2:.35},
  {16:.18,4:.3,7:.4,1:.45,2:.35},
  {16:.35,4:.35,7:.45,1:.5,2:.4},
  {16:.45,4:.45,7:.5,1:.5,2:.4},
  {16:.5,4:.55,7:.5,1:.65,2:.4},
  {16:.6,4:.65,7:.7,1:.7,2:.7},
  {16:.7,4:.7,7:.75,1:.8},
  {16:.75,4:.75,7:.8,1:.85},
  {},
];
const isPlant=g=>typeof trophic==='function'&&trophic(g)==='plant';
function nextGrade(grade,g){if(grade>=MAXG)return MAXG;if(isPlant(g))return grade<3?grade+1:grade<7?7:MAXG;return grade+1;}
function reqFor(grade,g){const n=nextGrade(grade,g);if(n===grade)return null;return isPlant(g)&&grade>=3&&grade<7?PLANT_LAND:REQ[n];}
// 次の段階へ進める条件がそろっているか。env: {O2, landPlants, onLand}
function canAdvance(grade,g,env){
  const r=reqFor(grade,g);if(!r)return false;
  if((env.O2||0)<r.o2)return false;
  if(r.landPlants&&!env.landPlants)return false;
  if(r.onLand&&!env.onLand)return false;
  return r.gene(g);
}
// 遺伝子を段階の上限に収める（その場で書き換える）
function constrain(g,grade){const c=CAPS[Math.max(0,Math.min(MAXG,grade|0))];for(const k in c)if(g[k]>c[k])g[k]=c[k];return g;}

// ---- 世界の記録（各段階に最初に到達した時刻と系統） ----
// first: 動物（と微生物）の系統が各段階に最初に到達した記録、firstPlant: 植物の系統の記録
const world={max:0,first:{},firstPlant:{},landPlants:false};
function record(o,grade,simY){
  const pl=isPlant(o.g),book=pl&&grade>=1?world.firstPlant:world.first;
  let fresh=false;
  if(!book[grade]){book[grade]={simY,g:Array.from(o.g),plant:pl,grade};fresh=true;}
  if(grade>world.max&&!pl)world.max=grade;
  if(pl&&grade>=7)world.landPlants=true;
  if(fresh&&grade>0&&typeof api.onAdvance==='function')api.onAdvance(grade,o);
}
function reset(){world.max=0;world.first={};world.firstPlant={};world.landPlants=false;}
// 個体に段階を割り当てる（誕生時に呼ぶ）。parent があれば受け継ぎ、条件がそろえば確率 pAdv で一段進む。
// parent がない場合は given（散布・移住で運ばれた系統の段階）か 0（自然発生）
function assign(o,parent,env,given){
  let grade=parent&&parent.grade!=null?parent.grade:(given!=null?Math.min(given,isPlant(o.g)?Math.max(world.max,7):world.max):0);
  if(parent&&Math.random()<(env.pAdv!=null?env.pAdv:.1)&&canAdvance(grade,o.g,env))grade=nextGrade(grade,o.g);
  o.grade=grade;constrain(o.g,grade);record(o,grade,env.simY);
  return grade;
}

// ---- 見た目: 段階に合わせて CreatureEngine に渡す遺伝子（34遺伝子）を調整する ----
const lo=(n,k,v)=>{if(n[k]>v)n[k]=v;},hi=(n,k,v)=>{if(n[k]<v)n[k]=v;};
function phenotype(g,grade){
  const n=Float32Array.from(CreatureEngine.padGenome(g));
  if(grade==null)return n;
  // 多細胞の動物（段階3以上）は、遺伝子上は小さくても微生物の姿にはしない
  if(grade>=3&&!isPlant(g))hi(n,16,.32);
  if(grade>=MAXG)return n;
  if(isPlant(g)){
    if(grade<3){lo(n,16,grade?.1:.05);n[27]=0;lo(n,1,.25);}           // 微細な藻類・シアノバクテリア
    else if(grade<7){hi(n,20,.85);}                                   // 海藻（水中のみ）
    return n;
  }
  if(grade<=2){lo(n,16,grade===0?.05:.1);n[27]=0;lo(n,1,.25);lo(n,20,.4);return n;}     // 単細胞（群体は描画側で複数並べる）
  // ここから動物の体
  n[30]=0;n[31]=0;                                                   // 角は有羊膜類まで出さない
  if(grade===3){                                                     // 海綿・平板動物型: 眼も口も肢もない柔らかい体
    n[16]=Math.max(.32,Math.min(n[16],.4));n[24]=0;n[28]=.15;lo(n,4,.15);lo(n,7,.15);lo(n,22,.1);lo(n,2,.1);lo(n,17,.25);n[20]=.3;n[27]=.1;lo(n,1,.3);
  }else if(grade===4){                                               // 刺胞動物型: 放射相称・触手・神経網（眼なし）
    hi(n,16,.3);n[28]=.75;n[29]=.3+n[29]*.4;n[24]=0;lo(n,4,.2);lo(n,7,.2);lo(n,22,.2);lo(n,2,.2);n[20]=.3;
  }else if(grade===5){                                               // 左右相称の蠕虫
    hi(n,16,.3);lo(n,28,.1);n[24]=0;lo(n,22,.3);lo(n,2,.25);n[20]=.3;
  }else if(grade===6){                                               // カンブリア紀: 節足動物 または 顎のない原始的な魚
    hi(n,16,.3);lo(n,28,.1);
    if(g[2]>=.35){n[24]=Math.max(.65,n[24]);hi(n,0,.3);hi(n,2,.35);hi(n,20,.8);}
    else{n[24]=0;hi(n,20,.85);lo(n,22,.35);}
  }else if(grade===7){                                               // 肉鰭類〜初期四肢動物: 4本の太い肢と水辺の体
    hi(n,16,.35);lo(n,28,.1);n[24]=Math.max(.3,Math.min(n[24],.4));n[20]=.62;lo(n,17,.55);lo(n,4,.6);lo(n,7,.5);lo(n,22,.6);hi(n,0,.5);
  }else{                                                             // 有羊膜類: 陸上の四足、鱗のある皮膚、羽毛・体毛はまだない
    hi(n,16,.35);lo(n,28,.1);n[24]=Math.max(.3,Math.min(n[24],.45));lo(n,20,.3);lo(n,17,.6);lo(n,4,.65);hi(n,0,.55);
  }
  return n;
}
function build(g,grade){const m=CreatureEngine.build(phenotype(g,grade));m.grade=grade;return m;}
// 段階が上がるほどエネルギーの使い方がうまくなる（餌から得るエネルギーの倍率）
//   真核化: ミトコンドリアで遺伝子あたりのエネルギーが桁違いに増えた（Lane & Martin 2010）。好気呼吸なので酸素が要る
//   多細胞化以降: 分業・大きな体・効率のよい採餌（Grosberg & Strathmann 2007）
function efficiency(grade,O2){const g=Math.min(grade||0,MAXG),ox=Math.min(1,(O2||0)/.02);return 1+(g>=1?.25*ox:0)+.15*Math.max(0,g-1);}
// 群体（段階2）を描くときの細胞数
function colonyCells(o){return 3+Math.round(c01(o.g[3])*6);}
function label(grade,g){const G=GRADES[Math.max(0,Math.min(MAXG,grade|0))];return g&&isPlant(g)?G.plant:G.name;}
// 次の段階の条件の説明（パネル表示用）
function nextReqText(grade,g){const r=reqFor(grade,g);return r?r.txt:'';}

const api={efficiency,GRADES,MAXG,REQ,CAPS,world,onAdvance:null,assign,canAdvance,constrain,nextGrade,phenotype,build,colonyCells,label,nextReqText,reset,record};
return api;
})();
