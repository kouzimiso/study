#!/usr/bin/env node
'use strict';

/**
 * data/routes.json の各Routeについて、`searchCenter`（検索の中心座標）を使って
 * OpenStreetMap Overpass APIからWifi/電源の目安になりそうなカフェ等を検索し、
 * `wifiPowerStops` を拡充する。
 *
 * 【重要】このセッションの実行環境ではOverpass系エンドポイントへの接続が不安定で、
 * ライブでの動作確認ができていない（src/overpassWifi.js のコメント参照）。
 * 安定したネットワークから実行し、結果を確認した上で --write を使うこと。
 *
 * 使い方:
 *   node src/updateWifiPowerStops.js            # dry-run：見つかった候補を表示するだけ
 *   node src/updateWifiPowerStops.js --write     # data/routes.json を実際に更新
 *   node src/updateWifiPowerStops.js --radius=2000
 */

const fs = require('fs');
const path = require('path');
const { findWifiPowerSpots } = require('./overpassWifi');

const ROUTES_PATH = path.resolve(__dirname, '..', 'data', 'routes.json');

function parseArgs(argv) {
  const options = { write: false, radius: 1500 };
  argv.forEach((arg) => {
    if (arg === '--write') options.write = true;
    const radiusMatch = arg.match(/^--radius=(\d+)$/);
    if (radiusMatch) options.radius = parseInt(radiusMatch[1], 10);
  });
  return options;
}

/**
 * Overpassの検索結果を、既存の `route.wifiPowerStops` に無い名前だけ追加する。
 * `internet_access` タグが確認できた候補のみ採用する（タグ無しは参考情報が薄いため）。
 * @param {object} route
 * @param {object[]} spots findWifiPowerSpots() の戻り値
 * @returns {object[]} 更新後の wifiPowerStops
 */
function mergeWifiPowerStops(route, spots) {
  const existingNames = new Set((route.wifiPowerStops || []).map((s) => s.name));
  const confirmed = spots.filter((s) => s.name && s.internetAccess && !existingNames.has(s.name));
  const additions = confirmed.map((s) => ({
    name: s.name,
    note: `Overpass確認済み（internet_access=${s.internetAccess}）`,
    lat: s.lat,
    lng: s.lng,
    osmId: s.osmId,
  }));
  return [...(route.wifiPowerStops || []), ...additions];
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const routes = JSON.parse(fs.readFileSync(ROUTES_PATH, 'utf8'));

  for (const route of routes) {
    if (!route.searchCenter) {
      console.error(`[skip] ${route.name}: searchCenter未設定`);
      continue;
    }
    try {
      const spots = await findWifiPowerSpots(route.searchCenter.lat, route.searchCenter.lng, options.radius);
      const confirmedCount = spots.filter((s) => s.internetAccess).length;
      console.error(`[ok] ${route.name}: ${spots.length}件取得（internet_access確認済み${confirmedCount}件）`);
      if (options.write) {
        route.wifiPowerStops = mergeWifiPowerStops(route, spots);
      } else {
        spots
          .filter((s) => s.internetAccess)
          .slice(0, 5)
          .forEach((s) => console.error(`    - ${s.name}（${s.internetAccess}）`));
      }
    } catch (err) {
      console.error(`[error] ${route.name}: ${err.message}`);
    }
  }

  if (options.write) {
    fs.writeFileSync(ROUTES_PATH, JSON.stringify(routes, null, 2) + '\n', 'utf8');
    console.error(`更新しました: ${ROUTES_PATH}`);
  } else {
    console.error('dry-runで終了（--write で data/routes.json に反映）');
  }
}

if (require.main === module) {
  main();
}

module.exports = { mergeWifiPowerStops };
