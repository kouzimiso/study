// ユーザーが指定した「任意の地点・半径」を、全国共通のグリッドセルに量子化する。
// セル中心をグローバル格子（緯度・経度の固定間隔）に揃えることで、異なる人が近い場所を
// 検索しても同じセルを共有でき、結果が自然に「たまる」。
//
// 楽天APIの searchRadius 上限(3.0km)を超えないように、格子間隔4kmに対して
// セル検索半径を2.8km（格子の内接円 ≒ 4km × √2 / 2 ≈ 2.83km を下回る値）にしている。

const EARTH_RADIUS_KM = 6371;

export const CELL_SIZE_KM = 4; // グローバル格子の間隔
export const CELL_RADIUS_KM = 2.8; // 1セルあたりの楽天API検索半径（3.0km以下）

function kmToLatDeg(km) {
  return km / ((Math.PI * EARTH_RADIUS_KM) / 180);
}

function kmToLngDeg(km, atLat) {
  const latRad = (atLat * Math.PI) / 180;
  return km / ((Math.PI * EARTH_RADIUS_KM * Math.cos(latRad)) / 180);
}

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function round6(x) {
  return Math.round(x * 1e6) / 1e6;
}

/**
 * 指定地点を中心に半径 radiusKm 内にあるグローバル格子のセル中心を返す。
 * 結果は日付をまたいで同じ座標になる（量子化されている）ため、DBのキャッシュキーに使える。
 * @param {number} lat
 * @param {number} lng
 * @param {number} radiusKm
 * @returns {{lat:number, lng:number, radiusKm:number}[]}
 */
export function cellsWithinCircle(lat, lng, radiusKm) {
  const latStep = kmToLatDeg(CELL_SIZE_KM);
  const latSpan = radiusKm * kmToLatDeg(1);
  const minRow = Math.floor((lat - latSpan) / latStep);
  const maxRow = Math.ceil((lat + latSpan) / latStep);
  const cells = [];

  for (let row = minRow; row <= maxRow; row++) {
    const cellLat = round6(row * latStep);
    const lngStep = kmToLngDeg(CELL_SIZE_KM, cellLat);
    const lngSpan = radiusKm * kmToLngDeg(1, cellLat);
    const minCol = Math.floor((lng - lngSpan) / lngStep);
    const maxCol = Math.ceil((lng + lngSpan) / lngStep);
    for (let col = minCol; col <= maxCol; col++) {
      const cellLng = round6(col * lngStep);
      if (haversineKm(lat, lng, cellLat, cellLng) <= radiusKm) {
        cells.push({ lat: cellLat, lng: cellLng, radiusKm: CELL_RADIUS_KM });
      }
    }
  }
  return cells;
}

/**
 * 任意の緯度経度を、cellsWithinCircle と同じグローバル格子上の最寄りセル中心にスナップする。
 * 表示範囲（矩形）からの乱数サンプリングで使う：範囲全体を列挙せずに済むため、
 * ズームアウトして表示範囲が広大になっても軽量に動作する。
 * @returns {{lat:number, lng:number, radiusKm:number}}
 */
export function snapToCell(lat, lng) {
  const latStep = kmToLatDeg(CELL_SIZE_KM);
  const cellLat = round6(Math.round(lat / latStep) * latStep);
  const lngStep = kmToLngDeg(CELL_SIZE_KM, cellLat);
  const cellLng = round6(Math.round(lng / lngStep) * lngStep);
  return { lat: cellLat, lng: cellLng, radiusKm: CELL_RADIUS_KM };
}

/**
 * 指定地点から半径 spreadKm 内のランダムな地点を返す（街・集落の周辺をサンプリングする
 * ために使う）。数km〜十数km程度の広がりであれば、度換算の簡易近似で十分。
 */
export function jitterPoint(lat, lng, spreadKm) {
  const dLat = (spreadKm / 111) * (Math.random() * 2 - 1);
  const dLng = (spreadKm / (111 * Math.max(0.1, Math.cos((lat * Math.PI) / 180)))) * (Math.random() * 2 - 1);
  return { lat: lat + dLat, lng: lng + dLng };
}

/**
 * 指定した矩形範囲に含まれるグローバル格子のセル数のおおまかな見積もり
 * （実際にセルを列挙せずに算出。範囲内の検索カバー率＝検索率の分母に使う）。
 */
export function estimateCellCount(south, west, north, east) {
  const latStep = kmToLatDeg(CELL_SIZE_KM);
  const midLat = (south + north) / 2;
  const lngStep = kmToLngDeg(CELL_SIZE_KM, midLat);
  const rows = Math.ceil((north - south) / latStep) + 1;
  const cols = Math.ceil((east - west) / lngStep) + 1;
  return Math.max(0, rows) * Math.max(0, cols);
}

/** セルのキャッシュキー（度 × 1e6 の整数）。DBに格納する形式。 */
export function encodeCell(lat, lng) {
  return [Math.round(lat * 1e6), Math.round(lng * 1e6)];
}
