// Overpass API（OpenStreetMap）から、範囲検索のサンプリングを陸地・人口集積地に
// 寄せるための補助データ（街・集落の座標）を取得する。
//
// 範囲検索は表示範囲内をランダムサンプリングするが、完全に一様ランダムだと海上や
// 山中など宿が存在しえない場所にも均等に検索を打ってしまい、限られた楽天APIの
// 呼び出し回数を無駄にする。街・集落の座標が分かれば、その周辺を優先的にサンプリング
// することで、同じ呼び出し回数でもホテルが見つかる可能性が高い場所を狙える。

const OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter";
const OVERPASS_TIMEOUT_MS = 6000;

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
    const res = await fetch(OVERPASS_ENDPOINT, {
      method: "POST",
      body: query,
      signal: AbortSignal.timeout(OVERPASS_TIMEOUT_MS),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.elements || [])
      .filter((el) => Number.isFinite(el.lat) && Number.isFinite(el.lon))
      .map((el) => ({ lat: el.lat, lng: el.lon }));
  } catch {
    return [];
  }
}
