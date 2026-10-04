/**
 * Breeding — 交叉・交配（全て純粋）
 * earth-arch.md IF:
 *   cross(a,b,opts)      (g,g,{rate,amt,dominant}) -> g
 *   compatibility(a,b)   (g,g) -> number[0..1]
 *
 * 依存: window.Genome, window.MathUtil
 * window.Breeding を上書きして差し替え可能。
 */
(function() {
  const GC = window._GC || 24;
  const cu = () => window.MathUtil ? window.MathUtil.clamp01 : v => Math.max(0, Math.min(1, v));

  window.Breeding = {
    cross(a, b, { rate = 0.07, amt = 0.22, dominant = 0.5 } = {}) {
      const clamp = cu();
      const g = new Float32Array(GC);
      for (let i = 0; i < GC; i++) {
        let v = Math.random() < dominant ? a[i] : b[i];
        if (Math.random() < rate) v += (Math.random() - 0.5) * amt;
        g[i] = clamp(v);
      }
      return g;
    },
    compatibility: (a, b) => 1 - window.Genome.distance(a, b),
  };
})();
