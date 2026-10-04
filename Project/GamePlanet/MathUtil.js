/**
 * MathUtil — 汎用数学ユーティリティ（純粋関数のみ）
 * earth-arch.md: 全モジュールが依存する基盤。副作用ゼロ。
 * window.MathUtil を上書きすることで差し替え可能。
 */
window.MathUtil = {
  // number -> number[0..1]
  clamp01: v => v < 0 ? 0 : v > 1 ? 1 : v,
  // (a,b,t) -> number  線形補間
  lerp: (a, b, t) => a + (b - a) * t,
  // (v, lo, hi) -> number  任意範囲クランプ
  clamp: (v, lo, hi) => v < lo ? lo : v > hi ? hi : v,
  // (v, mod) -> number  正の剰余（0以上）
  wrap: (v, mod) => ((v % mod) + mod) % mod,
  // (v01, n=10) -> string  ブロックバー
  blockBar(v, n = 10) {
    const k = Math.round(window.MathUtil.clamp01(v) * n);
    return '█'.repeat(k) + '░'.repeat(n - k);
  },
};
