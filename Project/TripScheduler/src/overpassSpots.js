'use strict';

/**
 * OpenStreetMap Overpass APIで、指定座標の周辺にある観光地・飲食店・
 * Wifi/電源スポット・温泉銭湯をまとめて検索する。APIキー不要。
 * `Test/travel-route-planner.html`（既存の個人プロトタイプ）のSPOT_TYPES/
 * fetchOverpassのロジックを参考に、Node.js（CommonJS）側でテストできる
 * 形に整理したもの。Node.js/ブラウザ両対応のUMD形式。
 */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = mod;
  else root.TripSchedulerOverpassSpots = mod;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const DEFAULT_ENDPOINTS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.openstreetmap.ru/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
  ];

  const USER_AGENT = 'study-tripscheduler/1.0 (+https://github.com/kouzimiso/study)';

  /**
   * 複数のAbortSignal（タイムアウト用・呼び出し元のキャンセルボタン用など）を
   * 1つにまとめる。`AbortSignal.any()`は比較的新しいAPIのため、どの環境でも
   * 動くようにイベントリスナーで手動合成する。signalが1つも無ければ
   * undefinedを返す（fetchにsignal:undefinedを渡しても無視されるだけ）。
   * @param {(AbortSignal|undefined|null)[]} signals
   * @returns {AbortSignal|undefined}
   */
  function combineSignals(signals) {
    const valid = signals.filter(Boolean);
    if (valid.length === 0) return undefined;
    if (valid.length === 1) return valid[0];
    if (typeof AbortController === 'undefined') return valid[0];
    const controller = new AbortController();
    valid.forEach((s) => {
      if (s.aborted) controller.abort(s.reason);
      else s.addEventListener('abort', () => controller.abort(s.reason), { once: true });
    });
    return controller.signal;
  }

/**
 * スポット種別の定義。`selectors` は Overpass QL の `node[...]` 部分（複数可、OR相当）。
 */
const SPOT_TYPES = {
  sightseeing: {
    label: '観光地',
    selectors: [
      'node["tourism"~"^(attraction|museum|gallery|viewpoint|artwork|theme_park)$"]["name"]',
      'node["historic"~"^(monument|castle|temple|shrine)$"]["name"]',
    ],
  },
  food: {
    label: '飲食店',
    selectors: ['node["amenity"~"^(restaurant|cafe|fast_food|food_court)$"]["name"]'],
  },
  wifi: {
    label: 'Wifi/電源',
    selectors: ['node["amenity"~"^(cafe|restaurant|fast_food|internet_cafe)$"]["name"]'],
  },
  onsen: {
    label: '温泉・銭湯',
    selectors: [
      'node["amenity"="public_bath"]["name"]',
      'node["leisure"="sauna"]["name"]',
      'node["tourism"="hotel"]["name"]["bath"]',
    ],
  },
};

/**
 * @param {number} lat
 * @param {number} lng
 * @param {number} radiusMeters
 * @param {string[]} types SPOT_TYPES のキー配列
 * @returns {string} Overpass QL
 */
function buildSpotsQuery(lat, lng, radiusMeters, types) {
  const lines = [];
  types.forEach((type) => {
    const def = SPOT_TYPES[type];
    if (!def) return;
    def.selectors.forEach((sel) => {
      lines.push(`${sel}(around:${radiusMeters},${lat},${lng});`);
    });
  });
  return `[out:json][timeout:25];(\n${lines.join('\n')}\n);out body 100;`;
}

/**
 * 出発地〜目的地のルート沿いのスポットを探すためのクエリ。中心＋半径では
 * なく矩形（bbox）で絞り込む（`Test/travel-route-planner.html`の
 * fetchOverpass(bbox, types)と同じ考え方）。実際に「ルートから何m以内か」
 * の判定は、bboxの中からルート座標列（`src/routeLine.js`）を使って呼び出し
 * 元（ブラウザ側）で絞り込む。
 * @param {[number,number,number,number]} bbox [minLat, minLng, maxLat, maxLng]
 * @param {string[]} types
 * @returns {string} Overpass QL
 */
function buildSpotsQueryBbox(bbox, types) {
  const [minLat, minLng, maxLat, maxLng] = bbox;
  const lines = [];
  types.forEach((type) => {
    const def = SPOT_TYPES[type];
    if (!def) return;
    def.selectors.forEach((sel) => {
      lines.push(`${sel}(${minLat},${minLng},${maxLat},${maxLng});`);
    });
  });
  return `[out:json][timeout:25];(\n${lines.join('\n')}\n);out body 150;`;
}

/**
 * Overpass要素のタグから、リクエストされたタイプのうちどれに該当するか判定する。
 * 複数当てはまる場合は types の順で最初に一致したものを返す。
 * @param {object} tags
 * @param {string[]} types
 * @returns {string|null}
 */
function classifySpotTags(tags, types) {
  tags = tags || {};
  const tourism = tags.tourism || '';
  const historic = tags.historic || '';
  const amenity = tags.amenity || '';
  const leisure = tags.leisure || '';

  for (const type of types) {
    if (type === 'sightseeing' && (/^(attraction|museum|gallery|viewpoint|artwork|theme_park)$/.test(tourism) || /^(monument|castle|temple|shrine)$/.test(historic))) {
      return 'sightseeing';
    }
    if (type === 'food' && /^(restaurant|cafe|fast_food|food_court)$/.test(amenity)) {
      return 'food';
    }
    if (type === 'onsen' && (amenity === 'public_bath' || leisure === 'sauna' || (tourism === 'hotel' && tags.bath))) {
      return 'onsen';
    }
    if (type === 'wifi' && /^(cafe|restaurant|fast_food|internet_cafe)$/.test(amenity)) {
      return 'wifi';
    }
  }
  return null;
}

/**
 * 複数のOverpassミラーへ同時に問い合わせ、最初に成功したものを採用する。
 * ミラーごとに混雑度・レイテンシの差が大きいため、1つずつ順番に試して
 * 1つあたり長めのタイムアウトを待つ（直列）方式だと、合計の待ち時間が
 * 「ミラー数×タイムアウト」まで伸びてしまう。並列（Promise.any）にすれば、
 * 一番早く応答したミラーの時間だけで済む。
 * なお `[out:json][timeout:25]` でサーバー側に25秒の処理猶予を伝えている
 * ため、クライアント側のタイムアウトをそれより短くすると、サーバーが
 * まだ処理中でも「signal timed out」として先に失敗扱いになってしまう。
 * `options.signal` を渡すと（例：UIの「キャンセル」ボタン）、タイムアウト
 * 前でもユーザーの意思で中断できる。両方を1つのsignalに合成して全ミラーに
 * 共有するので、どちらが先に発火してもすべてのミラーへのリクエストが
 * まとめて中断される。
 */
async function fetchOverpassRaw(query, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) throw new Error('fetch is not available in this environment');
  const endpoints = options.endpoints || DEFAULT_ENDPOINTS;
  const timeoutMs = options.timeoutMs || 20000;
  const isBrowser = typeof window !== 'undefined';
  const timeoutSignal = typeof AbortSignal !== 'undefined' && AbortSignal.timeout ? AbortSignal.timeout(timeoutMs) : undefined;
  const signal = combineSignals([options.signal, timeoutSignal]);

  const attempts = endpoints.map((endpoint) =>
    (async () => {
      try {
        const res = await fetchImpl(endpoint, {
          method: 'POST',
          mode: 'cors',
          // Content-Type を明示すると、サーバーによってはボディを
          // urlencodedフォームとして解釈しようとして失敗することがある
          // （Overpass APIはボディをそのまま生クエリとして受け付けるため、
          // 指定しないほうが安全）。User-Agent はブラウザのfetchでは
          // "forbidden header name" で設定できない（ブラウザが無視する）ため、
          // Node.js環境（CLI/テスト）でのみ付与する。
          headers: isBrowser ? undefined : { 'content-type': 'text/plain', 'user-agent': USER_AGENT },
          body: query,
          signal,
        });
        if (!res.ok) {
          throw new Error(`overpass error ${res.status} (${endpoint})`);
        }
        return await res.json();
      } catch (err) {
        if (isBrowser) console.warn('[TripScheduler] Overpass endpoint error:', endpoint, err && err.message);
        throw err;
      }
    })()
  );

  try {
    return await Promise.any(attempts);
  } catch (aggregateErr) {
    const errors = aggregateErr && aggregateErr.errors;
    throw (errors && errors[errors.length - 1]) || aggregateErr || new Error('no overpass endpoints configured');
  }
}

/**
 * 距離（メートル）をざっくり計算する（Haversine）。
 */
function haversineMeters(lat1, lng1, lat2, lng2) {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * 指定座標の周辺のスポットを検索し、分類・重複排除・中心からの距離付きで返す。
 * @param {number} lat
 * @param {number} lng
 * @param {number} radiusMeters
 * @param {string[]} types
 * @param {{fetchImpl?: typeof fetch, endpoints?: string[], timeoutMs?: number}} [options]
 * @returns {Promise<{id:string, name:string, type:string, lat:number, lng:number,
 *   distanceMeters:number, hours:string|null, tags:object}[]>}
 */
async function findSpotsAround(lat, lng, radiusMeters, types, options = {}) {
  const validTypes = types.filter((t) => SPOT_TYPES[t]);
  if (validTypes.length === 0) return [];
  const query = buildSpotsQuery(lat, lng, radiusMeters, validTypes);
  const data = await fetchOverpassRaw(query, options);

  const spots = parseOverpassElements(data, validTypes).map((spot) => ({
    ...spot,
    distanceMeters: Math.round(haversineMeters(lat, lng, spot.lat, spot.lng)),
  }));
  spots.sort((a, b) => a.distanceMeters - b.distanceMeters);
  return spots;
}

/**
 * Overpass要素の配列から、名前付きで重複のないスポット配列を作る
 * （`findSpotsAround()`/`findSpotsInBbox()` の共通部分）。
 * @param {{elements?: object[]}} data fetchOverpassRaw()の戻り値
 * @param {string[]} validTypes
 * @returns {{id:string, name:string, type:string, lat:number, lng:number, hours:string|null, tags:object}[]}
 */
function parseOverpassElements(data, validTypes) {
  const seen = new Set();
  const spots = [];
  (data.elements || []).forEach((el) => {
    if (!Number.isFinite(el.lat) || !Number.isFinite(el.lon) || !el.tags || !el.tags.name) return;
    const key = `${el.tags.name}|${Math.round(el.lat * 1000)}|${Math.round(el.lon * 1000)}`;
    if (seen.has(key)) return;
    seen.add(key);

    const type = classifySpotTags(el.tags, validTypes);
    if (!type) return;

    spots.push({
      id: `osm-${el.id}`,
      name: el.tags.name,
      type,
      lat: el.lat,
      lng: el.lon,
      hours: el.tags.opening_hours || null,
      tags: el.tags,
    });
  });
  return spots;
}

/**
 * 矩形（bbox）内のスポットを検索する。出発地〜目的地のルート沿いの
 * スポットを探す用途で、`findSpotsAround()`と違い中心からの距離は持たない
 * （ルート上のどの位置にあるかは、呼び出し元が`src/routeLine.js`の
 * `distanceToRouteMeters()`/`routeProgressRatio()`で判定する）。
 * @param {[number,number,number,number]} bbox [minLat, minLng, maxLat, maxLng]
 * @param {string[]} types
 * @param {{fetchImpl?: typeof fetch, endpoints?: string[], timeoutMs?: number, signal?: AbortSignal}} [options]
 * @returns {Promise<{id:string, name:string, type:string, lat:number, lng:number, hours:string|null, tags:object}[]>}
 */
async function findSpotsInBbox(bbox, types, options = {}) {
  const validTypes = types.filter((t) => SPOT_TYPES[t]);
  if (validTypes.length === 0) return [];
  const query = buildSpotsQueryBbox(bbox, validTypes);
  const data = await fetchOverpassRaw(query, options);
  return parseOverpassElements(data, validTypes);
}

  return {
    SPOT_TYPES,
    buildSpotsQuery,
    buildSpotsQueryBbox,
    classifySpotTags,
    fetchOverpassRaw,
    findSpotsAround,
    findSpotsInBbox,
    haversineMeters,
  };
});
