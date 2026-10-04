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
// ================================================================
const Life=(function(){
'use strict';
const c01=v=>v<0?0:v>1?1:v;
const wrapD=d=>((d+1.5)%1)-.5;
// イベント通知（ゲーム本体は Life.onEvent=logEvent を設定。未設定なら何もしない）
function emit(cat,data){if(typeof api.onEvent==='function')api.onEvent(cat,data);}
function dist(a,b){const du=wrapD(b.u-a.u),dv=b.v-a.v;return Math.sqrt(du*du+dv*dv);}
// 繁殖様式: seed=種子 / fission=分裂 / egg=卵生 / live=胎生（赤子で生まれる）
function birthMode(g){
  if(trophic(g)==='plant')return 'seed';
  if(rStage(g).st===0)return 'fission';
  // 神経・体格が大きく陸生ほど胎生寄り。水棲・小型・装甲（節足動物的）は卵生寄り
  const vivi=g[4]*.3+g[5]*.25+g[16]*.3+(1-g[20])*.2+g[7]*.1-g[2]*.15;
  return vivi>.52?'live':'egg';
}
// 成熟に要する時間（シミュ秒）。大型ほど長い
function devTime(g){return 7+g[16]*16+g[4]*4;}
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
function birth(o,parent){
  if(!o)return o;
  const mode=birthMode(o.g);o.bmode=mode;o.parentId=parent?parent.id:0;o.dev=0;o.age=0;
  if(mode==='seed'){o.stage='egg';o.incub=2.5+Math.random()*3;o.e=.3;}
  else if(mode==='egg'){o.stage='egg';o.incub=2+o.g[16]*3.5+Math.random();o.e=.35;}
  else if(mode==='live'){o.stage='juv';o.dev=.1;o.e=.45;}
  else {o.stage='juv';o.dev=.45;o.e=.3;}
  o.strat=chooseStrategy(o);o.act='idle';
  return o;
}
// 成長段階が付いていない個体（自然発生・散布・旧セーブ）は成体として扱う
function ensure(o){if(o.strat==null){if(o.stage==null){o.stage='adult';o.dev=1;}o.bmode=o.bmode||birthMode(o.g);o.strat=chooseStrategy(o);o.act='idle';}}

// ---- 毎ステップ: 発生・成長・幼体の死亡リスク。戻り値 false=死亡 ----
function develop(o,dt,tr,env){
  ensure(o);
  if(o.stage==='egg'){
    // 種子は水と栄養があるときに発芽が進む（休眠）。卵は胚発生（温度ストレスに弱い）
    const ok=o.bmode==='seed'?(env.water>.3||env.nu>.05?1:.25):1;
    o.incub-=dt*ok;o.e-=.002*dt;
    if(env.heat>.6&&Math.random()<(env.heat-.6)*.6*dt)return false;   // 胚の熱死
    if(o.incub<=0){o.stage='juv';o.dev=o.bmode==='seed'?.06:.08;o.e=Math.max(o.e,.3);o.hatchT=performance.now();o.strat=chooseStrategy(o,tr);}
    return true;
  }
  if(o.stage==='juv'){
    // 成長はエネルギーを消費。飢えていると成長が止まる
    if(o.e>.22){const r=1/devTime(o.g);o.dev+=r*dt*(o.e>.6?1.2:.7);o.e-=r*dt*.35;}
    // 寿命時間でも成熟（高速再生時の整合）
    o.dev=Math.max(o.dev,Math.min(1,o.age/(tr.life*.18)));
    // 幼体の偶発的な死（病気・事故・環境）: (1-dev)^2 に比例
    if(Math.random()<.035*(1-o.dev)*(1-o.dev)*dt)return false;
    if(o.dev>=1){o.dev=1;o.stage='adult';}
    o.strat=chooseStrategy(o,tr);
  }
  return true;
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
  if(!p){o.prey=null;o.chaseT=0;if(o.act==='hunt')o.act='idle';
    if(o.huntCd>0||o.e>eCap(o)*.8)return 0;
    let best=null,bs=0;
    for(let j=0;j<orgs.length;j++){const q=orgs[j];if(q===o||!q.alive)continue;
      if(trophic(q.g)==='plant')continue;
      if(q.parentId===o.id||o.parentId===q.id)continue;          // 自分の子・親は襲わない
      if(omni&&!(q.stage==='egg'||q.dev<.5))continue;             // 雑食は卵と小さな幼体のみ
      const d=dist(o,q);if(d>range)continue;
      // 隠れている個体は見つけにくい
      if(Math.random()<stealth(q)*(q.strat==='hide'?.95:.35))continue;
      const vul=1/(.25+defensePow(q)+(q.strat==='fight'?attackPow(q)*.5:0));
      const sc=(.3+q.e)*vul/(d+.004);
      if(sc>bs){bs=sc;best=q;}}
    if(!best)return 0;p=o.prey=best;o.chaseT=0;
  }
  const d=dist(o,p);
  // 見失う: 距離が開いた / 隠れた獲物を見失う / 追跡疲労
  o.chaseT=(o.chaseT||0)+dt;
  if(d>range*1.6||(p.act==='hide'&&Math.random()<stealth(p)*1.4*dt)||o.chaseT>3+tr.neural*4){
    o.prey=null;o.huntCd=1.2;o.act='idle';return 0;}
  p._threat=o;p._threatT=.6;
  o.act='hunt';
  const contact=.004+o.g[16]*.003;
  if(d>contact){
    const sp=Math.min(d,.0065*fleePow(o,tr)*dt);
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
    let gain=def.e*.6+.15*(.3+grow(def));
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
    else if(o.strat==='hide'){o.mvU=o.mvV=0;o.act='hide';}
    else {o.mvU=o.mvV=0;o.act='fight';o.e-=.01*dt;}
    return true;
  }
  o._threat=null;o._threatT=0;
  if(o.act!=='hunt')o.act='idle';
  // 平時: 幼体は親のそばに留まる（親が離れていれば寄っていく）
  if(o.stage==='juv'&&o.parentId&&o.bmode!=='seed'&&o.bmode!=='fission'){
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
const api={onEvent:null,growScale,birthMode,birth,ensure,develop,eCap,hunt,respond,fleePow,attackPow,defensePow,stealth,chooseStrategy,stageLabel,grow,devTime,STRAT_JP,STAGE_JP};
return api;
})();
