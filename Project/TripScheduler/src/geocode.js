'use strict';

/**
 * OpenStreetMap Nominatim を使った地名→緯度経度のジオコーディング。
 * APIキー不要。Nominatimの利用ポリシー（https://operations.osmfoundation.org/policies/nominatim/）
 * に従い、識別可能なUser-Agentを送り、同時並行・高頻度のリクエストは避けること。
 * Node.js/ブラウザ両対応のUMD形式。
 */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = mod;
  else root.TripSchedulerGeocode = mod;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const ENDPOINT = 'https://nominatim.openstreetmap.org/search';
  const USER_AGENT = 'study-tripscheduler/1.0 (+https://github.com/kouzimiso/study)';

/**
 * @param {string} query 地名・住所
 * @param {{fetchImpl?: typeof fetch, countryCodes?: string, timeoutMs?: number}} [options]
 * @returns {Promise<{lat:number, lng:number, name:string}|null>}
 */
async function geocodeOnce(query, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) throw new Error('fetch is not available in this environment');
  const params = new URLSearchParams({
    q: query,
    format: 'json',
    limit: '3',
    'accept-language': 'ja',
  });
  if (options.countryCodes) params.set('countrycodes', options.countryCodes);

  const res = await fetchImpl(`${ENDPOINT}?${params.toString()}`, {
    // User-Agent はブラウザのfetchでは "forbidden header name" で設定できない
    // （設定してもブラウザに無視される）。Node.js環境（CLI/テスト）でのみ送る。
    headers:
      typeof window === 'undefined'
        ? { Accept: 'application/json', 'User-Agent': USER_AGENT }
        : { Accept: 'application/json' },
    signal: typeof AbortSignal !== 'undefined' && AbortSignal.timeout ? AbortSignal.timeout(options.timeoutMs || 8000) : undefined,
  });
  if (!res.ok) return null;
  const data = await res.json();
  if (!data.length) return null;
  return {
    lat: parseFloat(data[0].lat),
    lng: parseFloat(data[0].lon),
    name: data[0].display_name.split(',')[0],
  };
}

/**
 * 「日本国内向けの絞り込み」→「"<query> 日本"で再試行」の順に試す。
 * @param {string} query
 * @param {{fetchImpl?: typeof fetch, timeoutMs?: number}} [options]
 * @returns {Promise<{lat:number, lng:number, name:string}|null>}
 */
async function geocodeLocation(query, options = {}) {
  if (!query || !query.trim()) return null;
  const attempts = [
    () => geocodeOnce(query, { ...options, countryCodes: 'jp' }),
    () => geocodeOnce(`${query} 日本`, options),
  ];
  for (const attempt of attempts) {
    try {
      const result = await attempt();
      if (result) return result;
    } catch (err) {
      // 次の候補を試す
    }
  }
  return null;
}

  return { geocodeLocation, geocodeOnce, ENDPOINT };
});
