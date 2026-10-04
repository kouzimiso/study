'use strict';

/**
 * OSRM（Open Source Routing Machine、公開デモサーバー）を使って、複数の
 * 地点（出発地点→スポット1→スポット2→…）を順番に通る経路のジオメトリを
 * 取得する。`Test/travel-route-planner.html`（既存の個人プロトタイプ）の
 * fetchRoute() と同じ考え方だが、2点間だけでなく任意個の経由地を1回の
 * リクエストでつなげるように一般化している。APIキー不要。
 * OSRMが失敗・タイムアウトした場合は、各地点を直線でつないだ近似に
 * フォールバックする（`real:false`を返すので、呼び出し側は破線表示等で
 * 区別できる）。Node.js/ブラウザ両対応のUMD形式。
 */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = mod;
  else root.TripSchedulerRouteLine = mod;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const DEFAULT_ENDPOINT = 'https://router.project-osrm.org';
  const OSRM_PROFILE = { walk: 'foot', bike: 'bike', car: 'car' };

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
   * @param {{lat:number, lng:number}[]} points 2点以上
   * @param {'walk'|'bike'|'car'} mode
   * @param {string} [endpoint]
   * @returns {string}
   */
  function buildOsrmUrl(points, mode, endpoint = DEFAULT_ENDPOINT) {
    const profile = OSRM_PROFILE[mode] || OSRM_PROFILE.car;
    const coords = points.map((p) => `${p.lng},${p.lat}`).join(';');
    return `${endpoint}/route/v1/${profile}/${coords}?overview=full&geometries=geojson`;
  }

  // ─── 経路（coords、[lng,lat]の配列）に対する位置関係の計算 ───
  // `Test/travel-route-planner.html` の ptD/segD/distToRoute/routePct を
  // 踏襲した簡易な等長方位図法近似（短距離の経路沿い判定・順序付けには
  // 十分な精度。緯度によるcos補正はしていない点も含めて元実装と同じ）。

  function ptDistMeters(lng1, lat1, lng2, lat2) {
    return Math.sqrt((lng1 - lng2) ** 2 + (lat1 - lat2) ** 2) * 111320;
  }

  /**
   * 点(lng,lat)を線分(lng1,lat1)-(lng2,lat2)に投影した位置のパラメータt
   * （0=線分の始点側、1=終点側。線分の外側に投影される場合は0または1に
   * クランプする）。
   */
  function projectParam(lng, lat, lng1, lat1, lng2, lat2) {
    const dx = lng2 - lng1;
    const dy = lat2 - lat1;
    if (!dx && !dy) return 0;
    return Math.max(0, Math.min(1, ((lng - lng1) * dx + (lat - lat1) * dy) / (dx * dx + dy * dy)));
  }

  function segDistMeters(lng, lat, lng1, lat1, lng2, lat2) {
    const t = projectParam(lng, lat, lng1, lat1, lng2, lat2);
    return ptDistMeters(lng, lat, lng1 + t * (lng2 - lng1), lat1 + t * (lat2 - lat1));
  }

  /**
   * 地点(lat,lng)から経路(coords、[lng,lat]の配列)への最短距離（メートル）。
   * 経路沿いのスポット検索で「経路から何m以内か」を判定するのに使う。
   * @param {number} lat
   * @param {number} lng
   * @param {[number,number][]} coords fetchRouteLine()が返すcoords形式（[lng,lat]）
   * @returns {number} coordsが空/1点なら Infinity
   */
  function distanceToRouteMeters(lat, lng, coords) {
    if (!coords || coords.length < 2) return Infinity;
    let min = Infinity;
    for (let i = 0; i < coords.length - 1; i++) {
      const d = segDistMeters(lng, lat, coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]);
      if (d < min) min = d;
    }
    return min;
  }

  /**
   * 地点(lat,lng)が経路(coords)上のどのあたりか（出発地点側=0 〜 目的地側=1）。
   * 経路沿いのスポットを「出発地点からの順番」に並べるのに使う。
   * @param {number} lat
   * @param {number} lng
   * @param {[number,number][]} coords
   * @returns {number} 0〜1（coordsが2点未満なら0）
   */
  function routeProgressRatio(lat, lng, coords) {
    if (!coords || coords.length < 2) return 0;
    const segLens = [];
    let total = 0;
    for (let i = 0; i < coords.length - 1; i++) {
      const d = ptDistMeters(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]);
      segLens.push(d);
      total += d;
    }
    let bestDist = Infinity;
    let bestProgress = 0;
    let cumulative = 0;
    for (let i = 0; i < coords.length - 1; i++) {
      const [lng1, lat1] = coords[i];
      const [lng2, lat2] = coords[i + 1];
      const t = projectParam(lng, lat, lng1, lat1, lng2, lat2);
      const d = ptDistMeters(lng, lat, lng1 + t * (lng2 - lng1), lat1 + t * (lat2 - lat1));
      if (d < bestDist) {
        bestDist = d;
        // セグメント内の投影位置tをそのまま使うことで、座標点が少ない
        // （直線に近い）経路でも正確な位置を返す。
        bestProgress = cumulative + t * segLens[i];
      }
      cumulative += segLens[i];
    }
    return total > 0 ? bestProgress / total : 0;
  }

  function straightLineFallback(points) {
    let distanceMeters = 0;
    for (let i = 0; i < points.length - 1; i++) {
      distanceMeters += haversineMeters(points[i].lat, points[i].lng, points[i + 1].lat, points[i + 1].lng);
    }
    return {
      coords: points.map((p) => [p.lng, p.lat]),
      distanceMeters: Math.round(distanceMeters),
      durationSeconds: null,
      real: false,
    };
  }

  /**
   * 複数地点を順番に通る経路のジオメトリを取得する。失敗時は直線近似。
   * @param {{lat:number, lng:number}[]} points 2点以上（1点以下ならそのまま返す）
   * @param {'walk'|'bike'|'car'} [mode]
   * @param {{fetchImpl?: typeof fetch, endpoint?: string, timeoutMs?: number}} [options]
   * @returns {Promise<{coords:[number,number][], distanceMeters:number, durationSeconds:number|null, real:boolean}>}
   */
  async function fetchRouteLine(points, mode = 'car', options = {}) {
    if (!points || points.length < 2) {
      return {
        coords: (points || []).map((p) => [p.lng, p.lat]),
        distanceMeters: 0,
        durationSeconds: 0,
        real: false,
      };
    }

    const fetchImpl = options.fetchImpl || globalThis.fetch;
    if (!fetchImpl) return straightLineFallback(points);

    const timeoutMs = options.timeoutMs || 12000;
    const url = buildOsrmUrl(points, mode, options.endpoint);

    try {
      const res = await fetchImpl(url, {
        signal: typeof AbortSignal !== 'undefined' && AbortSignal.timeout ? AbortSignal.timeout(timeoutMs) : undefined,
      });
      if (!res.ok) throw new Error(`osrm error ${res.status}`);
      const data = await res.json();
      if (data.code !== 'Ok' || !data.routes || !data.routes[0]) throw new Error(data.message || 'osrm no route');
      return {
        coords: data.routes[0].geometry.coordinates,
        distanceMeters: Math.round(data.routes[0].distance),
        durationSeconds: Math.round(data.routes[0].duration),
        real: true,
      };
    } catch (err) {
      return straightLineFallback(points);
    }
  }

  return { OSRM_PROFILE, buildOsrmUrl, fetchRouteLine, distanceToRouteMeters, routeProgressRatio };
});
