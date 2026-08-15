// Overpass API（OpenStreetMap）から、範囲検索のサンプリングを陸地・人口集積地に
// 寄せるための補助データ（街・集落の座標）を取得する。
//
// 範囲検索は表示範囲内をランダムサンプリングするが、完全に一様ランダムだと海上や
// 山中など宿が存在しえない場所にも均等に検索を打ってしまい、限られた楽天APIの
// 呼び出し回数を無駄にする。街・集落の座標が分かれば、その周辺を優先的にサンプリング
// することで、同じ呼び出し回数でもホテルが見つかる可能性が高い場所を狙える。

const OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter";
const OVERPASS_TIMEOUT_MS = 6000;
// Overpassの利用ポリシーは識別可能なUser-Agentを送ることを明示的に求めている。
// Cloudflare Workersのfetch()は既定でUser-Agentを送らないため明示的に付与する。
const OVERPASS_HEADERS = {
  "content-type": "application/x-www-form-urlencoded",
  "user-agent": "rakuten-vacancy-worker/1.0 (+https://github.com/kouzimiso/study)",
};

// 実機で確認したところ、CloudflareWorkers→overpass-api.deの経路は断続的に不安定で、
// 5xx（521など、Cloudflare側が相手サーバーに接続できないエラー）が時々発生する。
// クエリ自体の問題ではなく一過性のことが多いため、少し待ってリトライする。
const OVERPASS_MAX_RETRIES = 3;
const OVERPASS_RETRY_BACKOFF_MS = 1000;

async function fetchOverpassWithRetry(query, timeoutMs) {
  let lastErr;
  for (let attempt = 0; attempt <= OVERPASS_MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(OVERPASS_ENDPOINT, {
        method: "POST",
        headers: OVERPASS_HEADERS,
        body: query,
        signal: AbortSignal.timeout(timeoutMs),
      });
      if (res.ok || res.status < 500 || attempt >= OVERPASS_MAX_RETRIES) return res;
      lastErr = new Error(`overpass error ${res.status}`);
    } catch (err) {
      lastErr = err;
      if (attempt >= OVERPASS_MAX_RETRIES) throw err;
    }
    await new Promise((resolve) => setTimeout(resolve, OVERPASS_RETRY_BACKOFF_MS * (attempt + 1)));
  }
  throw lastErr;
}

/**
 * 指定範囲内の「街・集落」ノードの座標一覧を取得する。
 * 取得できない・失敗した場合は空配列を返す（呼び出し側で完全ランダムサンプリングに
 * フォールバックさせるため、失敗を例外にはしない）。
 * @returns {Promise<{lat:number, lng:number}[]>}
 */
export async function fetchPlaceSeeds(south, west, north, east) {
  const bbox = `${south},${west},${north},${east}`;
  const query = `[out:json][timeout:10];node["place"~"^(city|town|village|hamlet)$"](${bbox});out body 300;`;
  try {
    const res = await fetchOverpassWithRetry(query, OVERPASS_TIMEOUT_MS);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.elements || [])
      .filter((el) => Number.isFinite(el.lat) && Number.isFinite(el.lon))
      .map((el) => ({ lat: el.lat, lng: el.lon }));
  } catch {
    return [];
  }
}

/**
 * 指定範囲内の観光地POI（tourism=attraction/museum/viewpoint/gallery/artwork）を取得する。
 * サーバー側でDBにキャッシュし、みんなで共有・再利用するために使う（handlePois参照）。
 * 失敗した場合は例外を投げる（呼び出し側でキャッシュ済みデータのみで応答を続けるため）。
 * @returns {Promise<{osmId:number, name:string|null, lat:number, lng:number, tourismType:string|null}[]>}
 */
export async function fetchPois(south, west, north, east) {
  const bbox = `${south},${west},${north},${east}`;
  const query = `[out:json][timeout:20];node["tourism"~"^(attraction|museum|viewpoint|gallery|artwork)$"](${bbox});out body 500;`;
  const res = await fetchOverpassWithRetry(query, 18000);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`overpass error ${res.status}: ${body.slice(0, 300)}`);
  }
  const data = await res.json();
  return (data.elements || [])
    .filter((el) => Number.isFinite(el.lat) && Number.isFinite(el.lon) && el.id != null)
    .map((el) => ({
      osmId: el.id,
      name: el.tags?.name || null,
      lat: el.lat,
      lng: el.lon,
      tourismType: el.tags?.tourism || null,
    }));
}
