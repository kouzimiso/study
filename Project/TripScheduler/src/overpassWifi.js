'use strict';

/**
 * OpenStreetMap Overpass API から、指定座標周辺のカフェ・レストラン等の
 * Wifi/電源情報（`internet_access` タグ）を検索する。APIキー不要。
 *
 * 複数のパブリックインスタンスを順にフォールバックする（Project/Maps/src/overpass.js
 * のコメントにもある通り、overpass-api.de への経路は断続的に不安定なため）。
 *
 * 【このリポジトリでの検証状況】
 * このセッションの実行環境からは、overpass-api.de / lz4.overpass-api.de への
 * 接続がトンネル中断、overpass.kumi.systems はタイムアウト、
 * overpass.nchc.org.tw は502で拒否された。overpass.osm.ch のみ接続はできたが、
 * 返るデータが空（レプリカが日本のデータを持っていない可能性）で、実データでの
 * 検証はできなかった。ロジック自体はモックfetchを使ったユニットテストで検証済み。
 * 実運用で使う際は、安定したネットワークから一度 `findWifiPowerSpots()` を
 * 試し、必要なら `endpoints` オプションで使えるインスタンスに絞ること。
 */

const DEFAULT_ENDPOINTS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
  'https://lz4.overpass-api.de/api/interpreter',
];

const USER_AGENT = 'study-tripscheduler/1.0 (+https://github.com/kouzimiso/study)';

/**
 * @param {number} lat
 * @param {number} lng
 * @param {number} radiusMeters
 * @returns {string} Overpass QL クエリ
 */
function buildWifiQuery(lat, lng, radiusMeters) {
  return (
    '[out:json][timeout:15];' +
    `node["amenity"~"^(cafe|restaurant|fast_food)$"](around:${radiusMeters},${lat},${lng});` +
    'out body 50;'
  );
}

/**
 * 複数のOverpassエンドポイントを順に試す。全滅した場合は最後のエラーを投げる。
 * @param {string} query
 * @param {{fetchImpl?: typeof fetch, endpoints?: string[], timeoutMs?: number}} [options]
 * @returns {Promise<object>} Overpass APIのJSONレスポンス
 */
async function fetchOverpass(query, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) throw new Error('fetch is not available in this environment');
  const endpoints = options.endpoints || DEFAULT_ENDPOINTS;
  const timeoutMs = options.timeoutMs || 15000;

  let lastError;
  for (const endpoint of endpoints) {
    try {
      const res = await fetchImpl(endpoint, {
        method: 'POST',
        headers: {
          'content-type': 'application/x-www-form-urlencoded',
          'user-agent': USER_AGENT,
        },
        body: query,
        signal: typeof AbortSignal !== 'undefined' && AbortSignal.timeout ? AbortSignal.timeout(timeoutMs) : undefined,
      });
      if (!res.ok) {
        lastError = new Error(`overpass error ${res.status} (${endpoint})`);
        continue;
      }
      return await res.json();
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error('no overpass endpoints configured');
}

/**
 * 指定座標の周辺で、Wifi/電源の目安になりそうなカフェ・レストラン等を検索する。
 * `internet_access` タグ（wlan/yes等）が付いている候補を先頭に並べる。
 *
 * @param {number} lat
 * @param {number} lng
 * @param {number} [radiusMeters] デフォルト1500m
 * @param {{fetchImpl?: typeof fetch, endpoints?: string[], timeoutMs?: number}} [options]
 * @returns {Promise<{osmId: number, name: string|null, lat: number, lng: number,
 *   amenity: string|null, internetAccess: string|null}[]>}
 */
async function findWifiPowerSpots(lat, lng, radiusMeters = 1500, options = {}) {
  const query = buildWifiQuery(lat, lng, radiusMeters);
  const data = await fetchOverpass(query, options);
  const spots = (data.elements || [])
    .filter((el) => Number.isFinite(el.lat) && Number.isFinite(el.lon) && el.id != null)
    .map((el) => ({
      osmId: el.id,
      name: (el.tags && el.tags.name) || null,
      lat: el.lat,
      lng: el.lon,
      amenity: (el.tags && el.tags.amenity) || null,
      internetAccess: (el.tags && el.tags.internet_access) || null,
    }));

  spots.sort((a, b) => (b.internetAccess ? 1 : 0) - (a.internetAccess ? 1 : 0));
  return spots;
}

module.exports = {
  DEFAULT_ENDPOINTS,
  buildWifiQuery,
  fetchOverpass,
  findWifiPowerSpots,
};
