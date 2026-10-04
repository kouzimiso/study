/**
 * Physics — 物理演算（全て純粋）
 * earth-arch.md IF:
 *   canFly(g)                    g -> bool
 *   mode(g, isWater)             (g,bool) -> 'ground'|'water'|'air'
 *   placement(mode,minZ,size,t)  (...) -> zshift
 *
 * 依存: なし（完全独立）
 * window.Physics を上書きして差し替え可能。
 */
window.Physics = {
  canFly: g => g[17] > 0.68 && g[16] < 0.35,

  mode(g, isWater) {
    if (isWater)                    return 'water';
    if (window.Physics.canFly(g))  return 'air';
    return 'ground';
  },

  placement(mode, minZ, size, t) {
    if (mode === 'water') return -minZ + size * 0.5 + Math.sin(t * 1.5) * size * 0.3;
    if (mode === 'air')   return -minZ + size * 2.2 + Math.sin(t * 2.0) * size * 0.4;
    return -minZ; // ground: 最下点を地表(z=0)へ
  },
};
