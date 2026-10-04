/**
 * LifeCycle.js — 生物の成長段階（卵・種子・赤子 → 幼体 → 成体）と生存戦略（逃走/反撃/隠れる）
 *
 * GamePlanet.html と creature-test.html から読み込む（classic script・グローバル定義）。
 *
 * 公開するもの:
 *   rStage(g)  … 多細胞化の段階 {st, gt}（st=0 は単細胞）。地球の冷却（グローバル simY があれば参照、なければ現代扱い）に依存
 *   Life       … 成長・生存戦略のモジュール（API は末尾の return を参照）
 *
 * 呼び出し時に参照するグローバル関数（定義時には不要）:
 *   trophic(g) → 'plant'|'herbivore'|'carnivore'|'omnivore'|'detritivore'
 *   traits(g)  → {spd, armor, toxin, aggro, neural, life, ...}
 *   GamePlanet では LifeGfx への委譲関数が、テストページでは LifeGfx.js への委譲関数が担う。
 * イベント通知: Life.onEvent = (cat, data) => …（捕食による死亡などを 'EXTINCTION' で通知。GamePlanet はログへ送る）
 *
 * 個体オブジェクト o のフィールド（Life が読み書きするもの）:
 *   g(24遺伝子) u,v(位置 0..1) e(エネルギー) age alive id parentId
 *   stage('egg'|'juv'|'adult') dev(成熟度 0..1) bmode('seed'|'fission'|'egg'|'live') incub(孵化までの残り秒)
 *   strat('flee'|'fight'|'hide') act('idle'|'flee'|'fight'|'hide'|'hunt') mvU,mvV(このステップの移動量)
 *   prey/_threat/_threatT/chaseT/huntCd（狩りと逃走の内部状態）
 */

// 多細胞化の段階（st: 0=単細胞 1=群体 2〜3=分化）と性型（gt: 1=雌型 2=雄型）
function rStage(g){const m=(g[3]+g[9])*.5,cool=Math.max(0,Math.min(1,1-(typeof simY!=='undefined'?simY:0)/4.6e9)),es=g[3]*.5+g[16]*.3+(1-g[17])*.2,ss=g[17]*.5+(1-g[16])*.3+g[6]*.2;let st=0,gt=0;if(cool>.3&&m>.35)st=1;if(cool>.3&&m>.5&&Math.abs(es-ss)>.15)st=2;if(cool>.3&&m>.65&&Math.abs(es-ss)>.3)st=3;if(st>=2){if(es>ss+.1)gt=1;else if(ss>es+.1)gt=2;}return{st,gt};}

// ================================================================
// Life — v18 ライフサイクル（卵・種子・出産 → 幼体 → 成体）と生存戦略
//   ・繁殖で生まれる個体は成体ではなく、卵/種子/赤子/分裂直後の小さな細胞として生まれる
//   ・成熟度 dev(0..1) に応じて体格・速度・攻撃・防御・エネルギー上限が伸びる
//     幼体は弱く、熱ストレス・事故・捕食で死にやすい（幼体死亡率が高い＝r/K選択の基本）
//   ・生存戦略: 💨逃走（速度）/ ⚔反撃（強さ）/ 🍃隠れる（隠密）を形質から選ぶ
//     成長で戦略は変わりうる（幼体は隠れ、成体は戦う 等）
//   ・捕食者は感覚範囲で獲物を探し、追跡→接触で力比べ。親が近ければ子を守って戦う
// v19: 生態系のバランス（根拠は設計メモ第6章）
//   ・隠れる型: 発見は「率」で起き、静止した隠蔽型はほぼ見つからない／見張り・凍結・至近での飛び出し・見失わせ
//   ・生活史のトレードオフ: 子の数×1匹あたりの投資＝一定の予算、多産ほど早熟・短命・広く分散
//   ・密度依存: 種内競争＞種間競争、過密の病気、捕食者の縄張り・干渉、探索像（多い種ほど見つかる）
//   ・最適採餌: 割に合わない獲物は満腹なら見送る、勝てない相手は襲わない
//   ・資源分割（体の大きさで得意な餌が違う）、外温性の低い維持費
// ================================================================
const Life=(function(){
'use strict';
const c01=v=>v<0?0:v>1?1:v;
const wrapD=d=>((d+1.5)%1)-.5;
// イベント通知（ゲーム本体は Life.onEvent=logEvent を設定。未設定なら何もしない）
function emit(cat,data){if(typeof api.onEvent==='function')api.onEvent(cat,data);}
function dist(a,b){const du=wrapD(b.u-a.u),dv=b.v-a.v;return Math.sqrt(du*du+dv*dv);}
// 繁殖様式: seed=種子 / fission=分裂 / egg=卵生 / live=胎生（赤子で生まれる）
// grade: 進化段階（Evolution.js）。省略時は段階による制限なし
//   単細胞〜群体（0〜2）は分裂、動物は有羊膜類（8）までは卵生、胎生はそれ以降。植物は陸上植物（7〜）になってから種子
function birthMode(g,grade){
  if(trophic(g)==='plant')return grade!=null&&grade<7?'fission':'seed';
  if(grade!=null){if(grade<=2)return 'fission';if(grade<=8)return 'egg';}
  if(rStage(g).st===0)return 'fission';
  // 神経・体格が大きく陸生ほど胎生寄り。水棲・小型・装甲（節足動物的）は卵生寄り
  const vivi=g[4]*.3+g[5]*.25+g[16]*.3+(1-g[20])*.2+g[7]*.1-g[2]*.15;
  return vivi>.52?'live':'egg';
}
// 成熟に要する時間（シミュ秒）。大型ほど長い（世代時間 ∝ 体重^1/4: Brown et al. 2004）。
// 多産（g[21]）ほど早く成熟する（早熟・多産・短命の r 型生活史: Pianka 1970, Stearns 1992）
function devTime(g){return (7+g[16]*16+g[4]*4)*(1-.35*g[21]);}
// 寿命の係数: 繁殖に注ぐ努力が大きいほど短命（繁殖のコスト: Williams 1966）
function lifeFactor(g){return 1-.35*g[21];}

// ================================================================
// 生活史のトレードオフ — 「強くて多産」は両立しない
//   ・1回の繁殖に使えるエネルギー（budget）は有限。子の数 n を増やすと1匹あたりの投資 q=budget/n が減る
//     （子の大きさと数のトレードオフ: Smith & Fretwell 1974。一腹卵数: Lack 1947）
//   ・投資の小さい子は孵化/出生時の発達が低く、蓄えも少なく、幼体期の死亡率が高い
//   ・大きな体は少数の大きな子を産む（大型ほど一腹の数が少ない）
// ================================================================
function clutchSize(g,grade){
  const f=g[21],bm=birthMode(g,grade);
  if(bm==='fission')return 1;
  if(bm==='seed')return 1+Math.round(f*f*12);
  if(bm==='live')return 1+Math.round(Math.pow(f,1.5)*7*Math.max(0,1-g[16]));
  return 1+Math.round(Math.pow(f,1.5)*16*Math.max(0,1.1-g[16]));
}
// 子をばらまく半径（UV）。多産ほど広く散らす（多産・小型の子は分散で空いた場所に入り込む:
// 競争–分散のトレードオフ Tilman 1994）。過密による病気を避ける効果もある
function birthSpread(n){return .006+.005*Math.sqrt(n);}
// 次の繁殖までの間隔 [s]。大型ほど妊娠・抱卵期間が長く（∝ 体重^1/4: Western 1979, Brown et al. 2004）、
// 多産な種ほど短い周期で繰り返し産む
function breedInterval(g){return (2.5+5*g[16])*(1-.4*g[21]);}
function broodBudget(g){return .3+.3*g[21]+.15*g[16];}
// 繁殖計画: 産む数 n、使うエネルギー budget、1匹あたりの投資 perChild、子の質 quality(0..1)、繁殖に必要な蓄え threshold
function reproPlan(g,grade){
  const n=clutchSize(g,grade),budget=broodBudget(g),perChild=budget/n;
  return{n,budget,perChild,quality:c01(perChild/.35),threshold:budget+.45};
}
// 成長段階係数
const grow=o=>o.stage==='egg'?0:(o.dev==null?1:o.dev);
// ---- 能力値（成熟度で伸びる） ----
function fleePow(o,tr){tr=tr||traits(o.g);const m=grow(o);return tr.spd*(0.3+0.7*Math.pow(m,0.8))*(0.75+o.g[7]*0.25+o.g[1]*0.15);}
function attackPow(o,tr){tr=tr||traits(o.g);const m=grow(o);
  return (tr.aggro*.45+tr.toxin*.3+o.g[1]*.25+o.g[16]*.55)*(0.12+0.88*Math.pow(m,1.3));}
function defensePow(o,tr){tr=tr||traits(o.g);if(o.stage==='egg')return .04+o.g[2]*.06;const m=grow(o);
  return (tr.armor*.6+o.g[16]*.5+tr.toxin*.25)*(0.18+0.82*m);}
function stealth(o){const g=o.g,m=grow(o);
  if(o.stage==='egg')return c01(.35+g[0]*.35);
  return c01((1-g[16])*.4+g[0]*.2+(1-g[17])*.12+(1-m)*.3+g[7]*.05);}
// 戦略の選択（その時点の能力で最も有利なもの）
function chooseStrategy(o,tr){
  if(o.stage==='egg')return 'hide';
  tr=tr||traits(o.g);
  // 反撃は攻撃性・装甲・毒が高い個体ほど選ぶ（おとなしい草食は戦うより逃げるか隠れる）
  const temper=.45+tr.aggro*.8+tr.armor*.35+tr.toxin*.4;
  const f=fleePow(o,tr)*1.45, a=(attackPow(o,tr)*.5+defensePow(o,tr)*.5)*temper, h=stealth(o)*1.15;
  return f>=a&&f>=h?'flee':a>=h?'fight':'hide';
}
const STRAT_JP={flee:'💨逃走',fight:'⚔反撃',hide:'🍃隠れる'};
const STAGE_JP={egg:'🥚卵',seed:'🌰種子',juv:'🐣幼体',adult:'成体'};
function stageLabel(o){
  if(o.stage==='egg')return o.bmode==='seed'?STAGE_JP.seed:STAGE_JP.egg;
  if(o.stage==='juv')return o.bmode==='seed'?'🌱若芽':o.bmode==='fission'?'🦠娘細胞':STAGE_JP.juv;
  return STAGE_JP.adult;
}
// 生まれた直後の初期化（繁殖でのみ呼ぶ。散布・自然発生は成体のまま）
// quality: 親の1匹あたり投資から決まる子の質（reproPlan().quality）。省略時は親の遺伝子から計算
function birth(o,parent,quality){
  if(!o)return o;
  const mode=birthMode(o.g,o.grade);o.bmode=mode;o.parentId=parent?parent.id:0;o.dev=0;o.age=0;
  const q=quality!=null?quality:reproPlan(parent?parent.g:o.g,parent?parent.grade:o.grade).quality;o.qual=q;
  if(mode==='seed'){o.stage='egg';o.incub=2.5+Math.random()*3;o.e=.15+.2*q;}
  // 小さな卵は早く孵るが、未熟な状態で生まれる
  else if(mode==='egg'){o.stage='egg';o.incub=(1.2+o.g[16]*3)*(.6+.4*q)+Math.random()*.5;o.e=.15+.3*q;}
  else if(mode==='live'){o.stage='juv';o.dev=.05+.1*q;o.e=.25+.3*q;}
  else {o.stage='juv';o.dev=.45;o.e=.3;}
  o.strat=chooseStrategy(o);o.act='idle';
  return o;
}
// 成長段階が付いていない個体（自然発生・散布・旧セーブ）は成体として扱う
function ensure(o){if(o.strat==null){if(o.stage==null){o.stage='adult';o.dev=1;}o.bmode=o.bmode||birthMode(o.g,o.grade);o.strat=chooseStrategy(o);o.act='idle';}}

// ---- 毎ステップ: 発生・成長・幼体の死亡リスク。戻り値 false=死亡 ----
function develop(o,dt,tr,env){
  ensure(o);
  if(o.stage==='egg'){
    // 種子は水と栄養があるときに発芽が進む（休眠）。卵は胚発生（温度ストレスに弱い）
    const ok=o.bmode==='seed'?(env.water>.3||env.nu>.05?1:.25):1;
    o.incub-=dt*ok;o.e-=.002*dt;
    if(env.heat>.6&&Math.random()<(env.heat-.6)*.6*dt)return false;   // 胚の熱死
    if(o.incub<=0){o.stage='juv';o.dev=o.bmode==='seed'?.06:.04+.08*(o.qual!=null?o.qual:.5);o.e=Math.max(o.e,.3);o.hatchT=performance.now();o.strat=chooseStrategy(o,tr);}
    return true;
  }
  if(o.stage==='juv'){
    // 成長はエネルギーを消費。飢えていると成長が止まる
    if(o.e>.22){const r=1/devTime(o.g);o.dev+=r*dt*(o.e>.6?1.2:.7);o.e-=r*dt*.35;}
    // 寿命時間でも成熟（高速再生時の整合）
    o.dev=Math.max(o.dev,Math.min(1,o.age/(tr.life*.18)));
    // 幼体の偶発的な死（病気・事故・環境）: (1-dev)^2 に比例。小さく生まれた子ほど死にやすい（Smith & Fretwell 1974）
    if(Math.random()<.035*(1-o.dev)*(1-o.dev)*(1.6-.9*(o.qual!=null?o.qual:.7))*dt)return false;
    if(o.dev>=1){o.dev=1;o.stage='adult';}
    o.strat=chooseStrategy(o,tr);
  }
  return true;
}
// ================================================================
// 密度依存性 — 1種だけが増えすぎない仕組み
//   ・種内競争は種間競争より強い（同じ餌・同じ場所を使う）。これが共存を安定させる条件（Chesson 2000）
//   ・過密になると病気が広がる（密度依存の病原体: Janzen 1970 / Connell 1971、微生物では "Kill the Winner": Thingstad 2000）
//   ・捕食者は多い獲物を優先して狙う（探索像・スイッチング: Tinbergen 1960, Murdoch 1969）→ 少数派が守られる
// 「同種」は遺伝子の平均差 < 0.1 とみなす（種ラベル sp があればそれを優先）
// ================================================================
function geneDist(a,b){let s=0;for(let i=0;i<24;i++)s+=Math.abs(a[i]-b[i]);return s/24;}
// 種ラベル sp を持つ個体（テストのアリーナ等）はラベルで判定。ゲームでは遺伝子の近さで判定する
const sameSpecies=(a,b)=>(a.sp!=null&&b.sp!=null)?a.sp===b.sp:geneDist(a.g,b.g)<.1;
const CROWD_R=.03;
// 周囲の同種・同じ栄養段階の他種の数を数えて o._nSame / o._nOther に入れる（0.5秒ごと）
function crowding(o,orgs,dt){
  o._crT=(o._crT||0)-dt;if(o._crT>0)return;o._crT=.45+Math.random()*.15;
  const tc=trophic(o.g);let same=0,other=0;
  // 肉食動物は縄張りを持つので、同種どうしが干渉しあう範囲が広い（縄張り制による密度調節）
  const R=tc==='carnivore'?CROWD_R*2.2:CROWD_R;
  for(let j=0;j<orgs.length;j++){const q=orgs[j];if(q===o||!q.alive||q.stage==='egg')continue;
    const du=Math.abs(wrapD(q.u-o.u));if(du>R)continue;const dv=Math.abs(q.v-o.v);if(dv>R||du*du+dv*dv>R*R)continue;
    if(sameSpecies(o,q))same++;else if(trophic(q.g)===tc)other++;}
  o._nSame=same;o._nOther=other;
}
// 代謝の型: 神経維持（g[5]）が低い種は外温性（変温）、高い種は内温性（恒温）。
//   外温動物の維持代謝は同じ体重の内温動物の1/10〜1/20（Pough 1980, Nagy 2005）。少ない餌で生きられるので、
//   動き回らずに隠れて待つ暮らしが成り立つ。ゲームでは差を大きく緩めて 0.55〜1.0 倍にする
function endothermy(g){return c01((g[5]-.25)/.4);}
function metabolicFactor(g){return .55+.45*endothermy(g);}
// 餌のすみ分け（資源分割）: 大きな体は粗い餌（草・繊維・菌類）を、小さな体は細かく質の高い餌（種子・微生物）を効率よく食べる
//   体の大きさによるすみ分け（Hutchinson 1959）、資源の分割（MacArthur 1958）。
//   同じ餌を同じ効率で使う2種は共存できない（競争排除則: Gause 1934, Hardin 1960）
//   中間の大きさのジェネラリストはどちらも食べられるが、どちらも専門家ほど上手くない（凹型のトレードオフ）
function dietWeights(g){const s=g[16];return{fine:1.6*Math.pow(1-s,1.2),coarse:1.6*Math.pow(s,1.2)};}
// 餌の取り分（種内競争 0.18 ＞ 種間競争 0.03）
function foodFactor(o){return 1/(1+.18*(o._nSame||0)+.03*(o._nOther||0));}
// 過密による病気の死亡率 [1/s]（同種が4個体を超えると急増。病原体は種ごとに違うので他種は巻き込まない）
function diseaseRate(o){const n=o._nSame||0;return n>4?.01*Math.pow(n-4,1.3):0;}

// ---- 発見 — 捕食者が獲物に気づく確率（このステップ内） ----
//   動いている獲物は見つかりやすく、背景に溶け込む効果は静止しているときに最大
//   （Ioannou & Krause 2009: 隠蔽色の動物がじっとしている理由。Stevens & Merilaita 2009）
function detectProb(o,tr,q,d,range,dt){
  const cryptic=q.strat==='hide'||q.stage==='egg',still=!q._moving,st=stealth(q);
  // 静止した隠蔽型は背景とほぼ見分けがつかない。動くと隠蔽効果の大半を失う
  const vis=cryptic&&still?.06*Math.pow(1-st,2):1-st*(cryptic?.55:.4);
  const near=1-.75*Math.min(1,(d/range)*(d/range));
  // 探索像: よく出会う（多い）種ほど見つけやすくなる（Tinbergen 1960）。少数派は見落とされやすい
  const img=Math.min(2.5,1+.25*(q._nSame||0));
  const lam=4*(.5+tr.neural)*vis*near*img;      // 発見率 [1/s]
  return 1-Math.exp(-lam*dt);
}
// この個体を狙う捕食者か（隠れる型の見張り用）
function isPredatorOf(p,o){
  if(!p.alive||p===o||(p.stage!=='adult'&&p.dev<.4)||p.id===o.parentId||p.parentId===o.id)return false;
  const tc=trophic(p.g),ag=traits(p.g).aggro;
  if(tc==='carnivore')return ag>.4;
  return tc==='omnivore'&&ag>.5&&(o.stage==='egg'||o.dev<.5);
}

// エネルギー上限（体が小さいほど蓄えられない）
const eCap=o=>o.stage==='adult'?2.5:o.stage==='egg'?.6:.55+1.95*o.dev;

// ---- 捕食者の狩り（追跡→接触で力比べ）。戻り値=得たエネルギー ----
function hunt(o,oi,tr,dt,orgs){
  if(o.stage!=='adult'&&o.dev<.4)return 0;
  const tc=trophic(o.g),omni=tc==='omnivore';
  o.huntCd=Math.max(0,(o.huntCd||0)-dt);
  let p=o.prey&&o.prey.alive?o.prey:null;
  const range=.018+tr.neural*.03+o.g[7]*.015;
  o._lostT=Math.max(0,(o._lostT||0)-dt);
  if(!p){o.prey=null;o.chaseT=0;if(o.act==='hunt')o.act='idle';
    if(o.huntCd>0||o.e>eCap(o)*.8)return 0;
    let best=null,bs=0,bestCt=1;
    for(let j=0;j<orgs.length;j++){const q=orgs[j];if(q===o||!q.alive)continue;
      if(trophic(q.g)==='plant')continue;
      if(q.parentId===o.id||o.parentId===q.id)continue;          // 自分の子・親は襲わない
      if(sameSpecies(o,q))continue;                                // 同種は襲わない（共食いは扱わない）
      if(o._lostId===q.id&&o._lostT>0)continue;                   // 見失った獲物はしばらく諦めて別の場所を探す
      // 勝てない相手は襲わない（成体のサイやゾウはほとんど捕食されない。狙われるのは子）
      if(attackPow(o,tr)<(defensePow(q)+(q.strat==='fight'?attackPow(q)*.8:0))*.7)continue;
      if(omni&&!(q.stage==='egg'||q.dev<.5))continue;             // 雑食は卵と小さな幼体のみ
      const d=dist(o,q);if(d>range)continue;
      // 発見できたか（隠れている・静止している個体は見つけにくい）
      if(Math.random()>detectProb(o,tr,q,d,range,dt))continue;
      const vul=1/(.25+defensePow(q)+(q.strat==='fight'?attackPow(q)*.5:0));
      // 捕まえやすさ（速さの比）。得られるエネルギー÷追跡の手間が大きい獲物を選ぶ
      // （最適採餌: Charnov 1976, Stephens & Krebs 1986）→ 幼体・遅い個体・弱った個体が狙われる
      const ct=Math.min(1,Math.pow(fleePow(o,tr)*1.3/(fleePow(q)+.05),2));
      // 多い種ほど狙われる（探索像・スイッチング）
      const sc=(.3+q.e)*vul*ct/(d+.004)*(1+.3*(q._nSame||0));
      if(sc>bs){bs=sc;best=q;bestCt=ct;}}
    if(!best)return 0;
    // 割に合わない獲物（捕まえにくい）は、飢えていなければ見送る（最適食物選択: Charnov 1976。空腹ほど選り好みしない）
    if(bestCt<.3&&o.e>eCap(o)*.3)return 0;
    p=o.prey=best;o.chaseT=0;
  }
  const d=dist(o,p);
  // 見失う: 距離が開いた / 隠れた獲物を見失う / 追跡疲労
  o.chaseT=(o.chaseT||0)+dt;
  // 静止して背景に溶け込んだ獲物は追跡中でも見失いやすい
  if(d>range*1.6||(p.act==='hide'&&!p._moving&&Math.random()<stealth(p)*3*dt)||o.chaseT>3+tr.neural*4){
    o.prey=null;o.huntCd=1.2;o.act='idle';o._lostId=p.id;o._lostT=8;return 0;}
  p._threat=o;p._threatT=.6;
  o.act='hunt';
  const contact=.004+o.g[16]*.003;
  if(d>contact){
    // 最後の突進: 近づいたら短く加速する（追跡型捕食者の加速と待ち伏せ）
    const sp=Math.min(d,.0065*fleePow(o,tr)*(d<.015?1.6:1)*dt);
    o.mvU=wrapD(p.u-o.u)/d*sp;o.mvV=(p.v-o.v)/d*sp;o.e-=.02*dt;
    return 0;
  }
  // 接触: 親（成体）が近くにいれば子を守って代わりに戦う
  let def=p;
  if(p.stage!=='adult'&&p.parentId){const par=orgs.find(q=>q.id===p.parentId&&q.alive);
    if(par&&par.stage==='adult'&&dist(par,p)<.02&&par.strat!=='hide'){def=par;def.act='fight';par._guardT=1.2;}}
  const atk=attackPow(o,tr)*(.75+Math.random()*.5);
  const fightBack=def.act==='fight'||def.strat==='fight';
  const dv=(defensePow(def)*(fightBack?1.4:1)+(fightBack?attackPow(def)*.8:0))*(.75+Math.random()*.5);
  o.prey=null;o.huntCd=1.5;o.act='idle';
  if(atk>dv){
    def.alive=false;def._cause=def.stage==='egg'?'卵を捕食':def.stage==='juv'?'幼体を捕食':'捕食';
    emit('EXTINCTION',{cause:def._cause,gen:def.gen,age:+(def.age||0).toFixed(1)});
    // 捕食者どうしの干渉（獲物の横取り等）で、混み合うほど取り分が減る（Beddington 1975; DeAngelis et al. 1975）
    let gain=(def.e*.6+.15*(.3+grow(def)))/(1+.15*(o._nSame||0));
    // 有毒の獲物は食べた側も傷つく
    const tx=def.g[11];if(tx>.55)gain-=(tx-.55)*1.6;
    return gain;
  }
  // 撃退: 捕食者は負傷。反撃が強烈なら返り討ち
  o.e-=.18*Math.min(2,dv/(atk+1e-3));
  if(fightBack&&dv>atk*1.7&&o.stage==='adult'){o.e=-1;o._cause='返り討ち';}
  return 0;
}

// ---- 被食者の反応と移動（戦略に従う）。o.mvU/mvV に移動量を書く ----
function respond(o,tr,dt,orgs){
  if(o.stage==='egg'){o.mvU=o.mvV=0;o.act='hide';return true;}
  o._burstCd=Math.max(0,(o._burstCd||0)-dt);
  const t=o._threat;
  if(o._threatT>0&&t&&t.alive){
    o._threatT-=dt;
    const d=dist(o,t)+1e-6,du=wrapD(o.u-t.u)/d,dv=(o.v-t.v)/d;
    // 幼体は親（成体・戦う/逃げる）のもとへ逃げ込む
    if(o.stage==='juv'&&o.parentId){const par=orgs.find(q=>q.id===o.parentId&&q.alive);
      if(par&&par.stage==='adult'&&par.strat==='fight'&&dist(o,par)<.05){
        const pd=dist(o,par)+1e-6,sp=Math.min(pd,.0075*fleePow(o,tr)*dt);
        o.mvU=wrapD(par.u-o.u)/pd*sp;o.mvV=(par.v-o.v)/pd*sp;o.act='flee';o.e-=.02*dt;return true;}}
    if(o.strat==='flee'){const sp=.0078*fleePow(o,tr)*dt;o.mvU=du*sp;o.mvV=dv*sp;o.act='flee';o.e-=.03*dt;}
    else if(o.strat==='hide'){
      // 隠れる型: 基本はじっとして見失わせる（freezing）。至近距離まで迫られたら一瞬だけ全力で飛び出し、また身を潜める
      // （逃走開始距離の最適化: Ydenberg & Dill 1986, Cooper & Frederick 2007。凍結と逃走の組み合わせ: Eilam 2005）
      if(d<.011&&!(o._burstCd>0)){o._burstT=.7;o._burstCd=3;}
      if(o._burstT>0){o._burstT-=dt;const sp=.0078*fleePow(o,tr)*2.2*dt;o.mvU=du*sp;o.mvV=dv*sp;o.act='flee';o.e-=.04*dt;}
      else{o.mvU=o.mvV=0;o.act='hide';}}
    else {o.mvU=o.mvV=0;o.act='fight';o.e-=.01*dt;}
    return true;
  }
  o._threat=null;o._threatT=0;
  if(o.act!=='hunt')o.act='idle';
  // 隠れる型の見張り: 近くに捕食者がいたら、狙われる前から動きを止めて潜む
  if(o.strat==='hide'){
    o._vigT=(o._vigT||0)-dt;
    if(o._vigT<=0){o._vigT=.3;const r=.035+o.g[7]*.04;
      for(let j=0;j<orgs.length;j++){const p=orgs[j];if(isPredatorOf(p,o)&&dist(o,p)<r){o._freezeT=1.5;break;}}}
    if(o._freezeT>0){o._freezeT-=dt;o.mvU=o.mvV=0;o.act='hide';return true;}
    // 平時も動くのは短い時間だけで、多くの時間はじっと休む（動きが少ないほど見つかりにくい）
    o._phaseT=(o._phaseT||0)-dt;
    if(o._phaseT<=0){o._resting=!o._resting;o._phaseT=o._resting?1.5+Math.random()*1.5:1.5+Math.random();}
    if(o._resting){o.mvU=o.mvV=0;return true;}
  }
  // 平時: 胎生の幼体は親のそばに留まる（子育てをするのは主に胎生。卵から孵った子は独り立ちして散らばる）
  if(o.stage==='juv'&&o.parentId&&o.bmode==='live'){
    const par=orgs.find(q=>q.id===o.parentId&&q.alive);
    if(par){const d=dist(o,par);if(d>.008&&d<.08){const sp=Math.min(d-.006,.003*fleePow(o,tr)*dt+.0004*dt);
      o.mvU=wrapD(par.u-o.u)/d*sp;o.mvV=(par.v-o.v)/d*sp;return true;}}
  }
  return false;
}
// 成長による体格倍率（生まれたては成体の約26%、分裂直後は約55%）。
// 0.04 刻みで量子化し、描画側の物理リグを作り直す回数を抑える
function growScale(o){
  if(o.stage!=='juv')return 1;
  const m=o.dev||0,f=o.bmode==='fission'?0.55+0.45*m:0.26+0.74*Math.pow(m,0.75);
  return Math.round(f*25)/25;
}
const api={onEvent:null,breedInterval,birthSpread,dietWeights,endothermy,metabolicFactor,clutchSize,broodBudget,reproPlan,lifeFactor,crowding,foodFactor,diseaseRate,detectProb,isPredatorOf,geneDist,sameSpecies,growScale,birthMode,birth,ensure,develop,eCap,hunt,respond,fleePow,attackPow,defensePow,stealth,chooseStrategy,stageLabel,grow,devTime,STRAT_JP,STAGE_JP};
return api;
})();
