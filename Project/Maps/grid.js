// 独自の緯度経度グリッドを生成する。
// 「市区町村相当」を目安に、初期値はセル一辺 6km 程度（検索半径 3.0km で円がほぼ内接するサイズ）。
// 楽天トラベル空室検索APIの searchRadius は 0.1〜3.0km までしか指定できないため、
// セルを大きくしすぎるとカバーしきれない点に注意（README参照）。

const EARTH_RADIUS_KM = 6371;

// 対象地域のバウンディングボックス（ざっくり）。将来的に全国分をここに追加していく想定。
export const REGIONS = {
  kanto: { minLat: 34.8, maxLat: 37.2, minLng: 138.3, maxLng: 140.9 },
  hokkaido: { minLat: 41.3, maxLat: 45.6, minLng: 139.3, maxLng: 145.9 },
};

function kmToLatDeg(km) {
  return km / (Math.PI * EARTH_RADIUS_KM / 180);
}

function kmToLngDeg(km, atLat) {
  const latRad = (atLat * Math.PI) / 180;
  return km / (Math.PI * EARTH_RADIUS_KM * Math.cos(latRad) / 180);
}

/**
 * 指定した地域・セルサイズでグリッドセル（中心座標＋検索半径）の配列を生成する。
 * @param {string} regionKey - REGIONS のキー
 * @param {number} cellSizeKm - セルの一辺の目安(km)
 * @returns {{region:string, lat:number, lng:number, radiusKm:number}[]}
 */
export function generateGrid(regionKey, cellSizeKm = 6) {
  const box = REGIONS[regionKey];
  if (!box) throw new Error(`unknown region: ${regionKey}`);

  const cells = [];
  const latStep = kmToLatDeg(cellSizeKm);
  // 検索半径は API 上限の 3.0km を超えないようにする
  const radiusKm = Math.min(3.0, Math.round((cellSizeKm / 2) * Math.sqrt(2) * 10) / 10);

  for (let lat = box.minLat; lat <= box.maxLat; lat += latStep) {
    const lngStep = kmToLngDeg(cellSizeKm, lat);
    for (let lng = box.minLng; lng <= box.maxLng; lng += lngStep) {
      cells.push({
        region: regionKey,
        lat: Math.round((lat + latStep / 2) * 1e6) / 1e6,
        lng: Math.round((lng + lngStep / 2) * 1e6) / 1e6,
        radiusKm,
      });
    }
  }
  return cells;
}

export function generateAllGrids(cellSizeKm = 6) {
  return Object.keys(REGIONS).flatMap((key) => generateGrid(key, cellSizeKm));
}
