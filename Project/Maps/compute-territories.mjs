// scripts/compute-territories.mjs
//
// hotels.json（sync-hotels.mjsが出力したホテル一覧）を読み込み、
// 各ホテルについて「最近傍ホテルとの距離」から担当範囲(検索半径)を計算し、
// hotel_territory テーブルへのUPSERT文（territories.sql）を生成する。
//
// 考え方:
//   - ホテルが密集している場所（都市部）ほど最近傍ホテルとの距離が近い
//     → 担当範囲を狭くして、隣のホテルの担当範囲と重複しすぎないようにする
//   - ホテルが疎な場所（郊外・地方）は最近傍ホテルとの距離が遠い
//     → 楽天APIの上限である3.0kmまで担当範囲を広げてカバーする
//   - 半径 = min(3.0km, 最近傍ホテルまでの距離 / 2)　（両ホテルの担当範囲がちょうど接する形）
//
// この計算は基本的に初回だけの重い処理。以降はWorker側の「周辺構成チェック」で
// 変化がなければ再計算不要（hotel_territory.dirty=1が立ったホテルだけ再計算すればよい）。
//
// 使い方:
//   node scripts/compute-territories.mjs hotels.json > territories.sql
//   wrangler d1 execute rakuten-vacancy-db --remote --file=territories.sql

import { readFileSync } from "node:fs";

const MIN_RADIUS_KM = 0.1;
const MAX_RADIUS_KM = 3.0;
const BUCKET_DEG = 0.05; // 緯度経度バケットの粒度（近傍探索の高速化用）

const inputPath = process.argv[2] || "hotels.json";
const hotels = JSON.parse(readFileSync(inputPath, "utf-8"));
console.error(`ホテル数: ${hotels.length}`);

// バケットインデックスを構築（"latIdx,lngIdx" -> ホテル配列）
const buckets = new Map();
function bucketKey(lat, lng) {
  const li = Math.floor(lat / BUCKET_DEG);
  const lj = Math.floor(lng / BUCKET_DEG);
  return `${li},${lj}`;
}
for (const h of hotels) {
  const key = bucketKey(h.lat, h.lng);
  if (!buckets.has(key)) buckets.set(key, []);
  buckets.get(key).push(h);
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

// 指定ホテルの周囲（バケットのring）にいる候補ホテルを集める。ringを広げながら十分な候補が集まるまで探索。
function nearbyCandidates(hotel, ringStart = 1) {
  const li = Math.floor(hotel.lat / BUCKET_DEG);
  const lj = Math.floor(hotel.lng / BUCKET_DEG);
  let ring = ringStart;
  let candidates = [];
  while (candidates.length < 2 && ring <= 20) {
    candidates = [];
    for (let di = -ring; di <= ring; di++) {
      for (let dj = -ring; dj <= ring; dj++) {
        const key = `${li + di},${lj + dj}`;
        const arr = buckets.get(key);
        if (arr) candidates.push(...arr);
      }
    }
    ring += 1;
  }
  return candidates;
}

const results = [];
for (const hotel of hotels) {
  const candidates = nearbyCandidates(hotel).filter((c) => c.hotelNo !== hotel.hotelNo);

  let nearest = null;
  let nearestDist = Infinity;
  for (const c of candidates) {
    const d = haversineKm(hotel.lat, hotel.lng, c.lat, c.lng);
    if (d < nearestDist) {
      nearestDist = d;
      nearest = c;
    }
  }

  const radiusKm = nearest
    ? Math.max(MIN_RADIUS_KM, Math.min(MAX_RADIUS_KM, Math.round((nearestDist / 2) * 10) / 10))
    : MAX_RADIUS_KM; // 周囲に他のホテルが全く無い場合は上限まで広げる

  // 半径内にある近隣ホテルNoの集合（周辺構成の変化検知に使う）
  const neighborCandidates = nearbyCandidates(hotel, Math.max(1, Math.ceil(radiusKm / (BUCKET_DEG * 111))));
  const neighborSet = neighborCandidates
    .filter((c) => c.hotelNo !== hotel.hotelNo && haversineKm(hotel.lat, hotel.lng, c.lat, c.lng) <= radiusKm)
    .map((c) => c.hotelNo)
    .sort((a, b) => a - b)
    .join(",");

  results.push({
    hotelNo: hotel.hotelNo,
    radiusKm,
    nearestHotelNo: nearest?.hotelNo ?? null,
    nearestKm: nearest ? Math.round(nearestDist * 100) / 100 : null,
    neighborSet,
  });
}

const now = new Date().toISOString();
const lines = results.map(
  (r) =>
    `INSERT INTO hotel_territory (hotel_no, radius_km, nearest_neighbor_hotel_no, nearest_neighbor_km, neighbor_set, computed_at, checked_at, dirty) ` +
    `VALUES (${r.hotelNo}, ${r.radiusKm}, ${r.nearestHotelNo ?? "NULL"}, ${r.nearestKm ?? "NULL"}, '${r.neighborSet}', '${now}', '${now}', 0) ` +
    `ON CONFLICT(hotel_no) DO UPDATE SET radius_km=excluded.radius_km, nearest_neighbor_hotel_no=excluded.nearest_neighbor_hotel_no, ` +
    `nearest_neighbor_km=excluded.nearest_neighbor_km, neighbor_set=excluded.neighbor_set, computed_at=excluded.computed_at, checked_at=excluded.checked_at, dirty=0;`
);

console.log(lines.join("\n"));
console.error(`territories.sql 相当の${lines.length}件を標準出力に書き出しました`);
