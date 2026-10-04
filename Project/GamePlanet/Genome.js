/**
 * Genome — 遺伝子（全て純粋・非破壊）
 * earth-arch.md IF:
 *   random()               () -> Float32Array(24)
 *   distance(a,b)          (g,g) -> number[0..1]
 *   mutate(g,rate,amt)     (g,num,num) -> g
 *   forEnvironment(t,w,h)  (num,bool,num) -> g
 *   serialize(g)           g -> number[]
 *   deserialize(arr)       number[] -> g
 *
 * 依存: window.MathUtil, window._GC（遺伝子数=24）
 * window.Genome を上書きして完全差し替え可能。
 */
(function() {
  const GC = window._GC || 24;
  const cu = window.MathUtil ? window.MathUtil.clamp01 : v => Math.max(0, Math.min(1, v));

  window.Genome = {
    SIZE: GC,
    clamp: cu,

    random() {
      const g = new Float32Array(GC);
      for (let i = 0; i < GC; i++) g[i] = Math.random();
      return g;
    },

    distance(a, b) {
      let d = 0;
      for (let i = 0; i < GC; i++) d += Math.abs(a[i] - b[i]);
      return d / GC;
    },

    mutate(g, rate = 0.07, amt = 0.22) {
      const o = new Float32Array(g);
      for (let i = 0; i < GC; i++)
        if (Math.random() < rate)
          o[i] = cu(o[i] + (Math.random() - 0.5) * amt);
      return o;
    },

    forEnvironment(temp, isWater, h2s) {
      const g = new Float32Array(GC);
      for (let i = 0; i < GC; i++) g[i] = Math.random() * 0.5;
      g[16] = Math.random() * 0.3;
      g[12] = 0.5 + Math.random() * 0.3;
      if (temp > 400) {
        g[18] = 0.65 + Math.random() * 0.35;
        g[14] = 0.6  + Math.random() * 0.4;
        g[10] = 0.4  + Math.random() * 0.3;
      } else if (isWater) {
        g[20] = 0.55 + Math.random() * 0.4;
        g[13] = 0.35 + Math.random() * 0.35;
        g[19] = 0.4  + Math.random() * 0.3;
      } else {
        g[8]  = 0.4  + Math.random() * 0.3;
        g[12] = 0.5  + Math.random() * 0.4;
      }
      if (h2s > 0.3) g[14] = Math.max(g[14], 0.55);
      return g;
    },

    serialize:   g   => Array.from(g).map(v => +v.toFixed(4)),
    deserialize: arr => {
      const g = new Float32Array(GC);
      for (let i = 0; i < GC && i < arr.length; i++)
        g[i] = cu(+arr[i] || 0);
      return g;
    },
  };
})();
