/**
 * module-loader.js — モジュール差し替えシステム
 *
 * 使い方:
 *   ModuleLoader.load('Genome', './my-genome.js')
 *     → my-genome.js を動的ロードし window.Genome を上書き。
 *     → 同時にグローバル委譲ラッパー(gdist等)も自動更新。
 *
 *   ModuleLoader.reset('Genome')
 *     → インライン定義に戻す（ページリロードなし）
 *
 *   ModuleLoader.status()
 *     → 各モジュールの現在のソースを返す
 */
const ModuleLoader = (() => {
  // モジュール名 → 現在のソース ('inline' or URL)
  const _sources = {
    MathUtil: 'inline', Genome: 'inline', Breeding: 'inline',
    LifeGfx: 'inline', Model3D: 'inline', Terrain: 'inline',
    Physics: 'inline', Camera: 'inline',
    Clock: 'inline', Sim: 'inline', Ecology: 'inline', Renderer: 'inline',
  };

  // インライン定義のバックアップ（リセット用）
  const _defaults = {};
  const MODULE_NAMES = Object.keys(_sources);

  function _backup() {
    MODULE_NAMES.forEach(name => {
      if (window[name]) _defaults[name] = window[name];
    });
  }

  // 動的スクリプトロード → Promise
  function _loadScript(url) {
    return new Promise((resolve, reject) => {
      // 既存の同URLタグを削除（再ロード対応）
      document.querySelectorAll(`script[data-module-src="${url}"]`).forEach(s => s.remove());
      const s = document.createElement('script');
      s.src = url;
      s.setAttribute('data-module-src', url);
      s.onload  = () => resolve(url);
      s.onerror = () => reject(new Error(`Failed to load: ${url}`));
      document.head.appendChild(s);
    });
  }

  // 外部JSをロードしてモジュールを差し替える
  async function load(moduleName, url) {
    if (!MODULE_NAMES.includes(moduleName))
      throw new Error(`Unknown module: ${moduleName}`);
    try {
      await _loadScript(url);
      _sources[moduleName] = url;
      console.log(`[ModuleLoader] ${moduleName} loaded from ${url}`);
      _notifyChange(moduleName);
      return true;
    } catch(e) {
      console.error(`[ModuleLoader] ${moduleName} load failed:`, e);
      return false;
    }
  }

  // インライン定義にリセット
  function reset(moduleName) {
    if (_defaults[moduleName]) {
      window[moduleName] = _defaults[moduleName];
      _sources[moduleName] = 'inline';
      console.log(`[ModuleLoader] ${moduleName} reset to inline default`);
      _notifyChange(moduleName);
    }
  }

  // 全モジュールのソース状態を返す
  function status() {
    return { ..._sources };
  }

  // モジュール変更時のコールバック（UI更新用）
  const _listeners = [];
  function onChange(fn) { _listeners.push(fn); }
  function _notifyChange(name) {
    _listeners.forEach(fn => fn(name, _sources[name]));
  }

  // ページロード後にデフォルトをバックアップ
  if (document.readyState === 'complete') {
    _backup();
  } else {
    window.addEventListener('load', _backup);
  }

  return { load, reset, status, onChange };
})();

window.ModuleLoader = ModuleLoader;
