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

async function fetchOverpassRaw(query, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) throw new Error('fetch is not available in this environment');
  const endpoints = options.endpoints || DEFAULT_ENDPOINTS;
  const timeoutMs = options.timeoutMs || 10000;
  const isBrowser = typeof window !== 'undefined';

  let lastError;
  for (const endpoint of endpoints) {
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
        signal: typeof AbortSignal !== 'undefined' && AbortSignal.timeout ? AbortSignal.timeout(timeoutMs) : undefined,
      });
      if (!res.ok) {
        lastError = new Error(`overpass error ${res.status} (${endpoint})`);
        if (isBrowser) console.warn('[TripScheduler] Overpass endpoint failed:', endpoint, res.status);
        continue;
      }
      return await res.json();
    } catch (err) {
      lastError = err;
      if (isBrowser) console.warn('[TripScheduler] Overpass endpoint error:', endpoint, err && err.message);
    }
  }
  throw lastError || new Error('no overpass endpoints configured');
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
      distanceMeters: Math.round(haversineMeters(lat, lng, el.lat, el.lon)),
      hours: el.tags.opening_hours || null,
      tags: el.tags,
    });
  });

  spots.sort((a, b) => a.distanceMeters - b.distanceMeters);
  return spots;
}

  return {
    SPOT_TYPES,
    buildSpotsQuery,
    classifySpotTags,
    fetchOverpassRaw,
    findSpotsAround,
    haversineMeters,
  };
});
