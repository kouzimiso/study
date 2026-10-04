/**
 * LifeGfx — 生命グラフィック自動生成 + 表現型計算
 * earth-arch.md IF:
 *   build2D(g)      g -> Vis2D
 *   build3D(g)      g -> Model3D
 *   cellType(g)     g -> string
 *   color(g)        g -> [r,g,b]
 *   trophic(g)      g -> string
 *   traits(g)       g -> {spd,photo,chem,armor,neural,...}
 *   statusValue(g)  g -> number
 *
 * 依存: window.MathUtil（任意）
 * window.LifeGfx を上書きして差し替え可能。
 * 注意: build2D/build3D はホストのbuildBodyVis/buildBody3Dに依存。
 *       完全外部化する場合はそれらも同梱する。
 */
window.LifeGfx = {
  // ホストの描画関数に委譲（差し替え時はここを独自実装に変える）
  build2D: g => (typeof buildBodyVis !== 'undefined' ? buildBodyVis(g) : null),
  build3D: g => (typeof buildBody3D !== 'undefined' ? buildBody3D(g) : null),
  cellType: g => (typeof cellTypeFromGene !== 'undefined' ? cellTypeFromGene(g) : 'unknown'),

  color(g) {
    const r  = g[11] * 0.7 + g[22] * 0.3;
    const gr = g[13] * 0.6 + g[10] * 0.3;
    const b  = g[4]  * 0.5 + g[20] * 0.4;
    const m  = Math.sqrt(r*r + gr*gr + b*b) || 1;
    return [r/m, gr/m, b/m];
  },

  trophic(g) {
    const au = g[13] + g[14], he = g[12] + g[22];
    if (au > 0.9)                  return 'plant';
    if (au > 0.5 && he < 0.6)     return 'plant';
    if (g[22] > 0.6 && au < 0.35) return 'carnivore';
    if (g[10] > 0.5 && au < 0.45) return 'herbivore';
    if (au > 0.3  && he > 0.3)    return 'omnivore';
    return 'detritivore';
  },

  traits(g) {
    return {
      spd:    g[17] * (0.3 + g[1]*0.7) / (0.5 + g[2]*0.5),
      photo:  g[13],
      chem:   g[14],
      digest: g[8]*0.4  + g[10]*0.6,
      toxin:  g[11],
      armor:  g[0]*0.6  + g[2]*0.4,
      neural: (g[4]*0.5 + g[7]*0.5) * (0.4 + g[5]*0.6),
      heatT:  g[18], coldT: g[19], waterA: g[20],
      repro:  g[21], aggro: g[22],
      life:   1 + g[23]*5,
      mem:    (g[3] + g[9]) * 0.5,
      eRate:  g[12]*0.3 + g[13]*0.25 + g[14]*0.25 + g[15]*0.2,
      apR:    0.5 + g[15]*2 + g[6]*0.5,
    };
  },

  statusValue(g) {
    const tr = window.LifeGfx.traits(g);
    return 1 + g[16]*g[16]*4 + tr.aggro*3 + tr.neural*2
             + (g[0]*0.6 + g[2]*0.4)*2 + tr.eRate*2;
  },
};
