// scripts/sync-hotels.mjs
//
// 対象地域のホテル一覧（施設番号・座標）を楽天トラベル施設検索APIで収集し、
// hotels テーブルへのINSERT文（hotels.sql）を生成するローカル実行用スクリプト。
//
// 一度だけ（または地域を広げるたびに）実行すればよい重い処理のため、
// Cloudflare Workerではなくローカル/CIのNode.jsで動かす想定。
//
// 使い方:
//   RAKUTEN_APP_ID=xxx RAKUTEN_ACCESS_KEY=yyy node scripts/sync-hotels.mjs > hotels.sql
//   （その後） wrangler d1 execute rakuten-vacancy-db --remote --file=hotels.sql
//
// Node.js 18以降（組み込みfetch使用）が必要です。

import { generateAllGrids } from "../src/grid.js";
import { writeFileSync } from "node:fs";

const APP_ID = process.env.RAKUTEN_APP_ID;
const ACCESS_KEY = process.env.RAKUTEN_ACCESS_KEY;
const CELL_SIZE_KM = Number(process.env.SYNC_CELL_SIZE_KM || 5); // ホテル収集用の巡回タイルサイズ
const REQUEST_INTERVAL_MS = 300;

if (!APP_ID || !ACCESS_KEY) {
  console.error("環境変数 RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY を設定してください");
  process.exit(1);
}

const ENDPOINT = "https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731";

async function fetchHotelsInTile(cell) {
  const found = new Map();
  let page = 1;
  // 1タイルあたり最大3000件（100ページ×30件）まで。通常のタイルサイズでは far below this。
  while (page <= 100) {
    const params = new URLSearchParams({
      applicationId: APP_ID,
      accessKey: ACCESS_KEY,
      format: "json",
      formatVersion: "2",
      datumType: "1",
      latitude: String(cell.lat),
      longitude: String(cell.lng),
      searchRadius: String(cell.radiusKm),
      hits: "30",
      page: String(page),
      responseType: "small",
      elements: "hotelNo,hotelName,latitude,longitude",
    });

    const res = await fetch(`${ENDPOINT}?${params.toString()}`);
    if (res.status === 404) break; // 該当なし
    if (res.status === 429) {
      console.error("rate limited, waiting 5s...");
      await sleep(5000);
      continue;
    }
    if (!res.ok) {
      console.error(`error ${res.status} at tile (${cell.lat},${cell.lng})`);
      break;
    }
    const data = await res.json();
    const hotels = data?.hotels ?? [];
    for (const h of hotels) {
      const basic = h.hotelBasicInfo ?? h;
      if (basic?.hotelNo) {
        found.set(basic.hotelNo, {
          hotelNo: basic.hotelNo,
          name: basic.hotelName,
          lat: basic.latitude,
          lng: basic.longitude,
        });
      }
    }
    const pageCount = data?.pagingInfo?.pageCount ?? 1;
    if (page >= pageCount) break;
    page += 1;
    await sleep(REQUEST_INTERVAL_MS);
  }
  return found;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function sqlEscape(str) {
  if (str == null) return "NULL";
  return `'${String(str).replace(/'/g, "''")}'`;
}

async function main() {
  const tiles = generateAllGrids(CELL_SIZE_KM);
  console.error(`巡回タイル数: ${tiles.length}`);

  const allHotels = new Map(); // hotelNo -> {name, lat, lng, region}

  for (let i = 0; i < tiles.length; i++) {
    const tile = tiles[i];
    process.stderr.write(`[${i + 1}/${tiles.length}] ${tile.region} (${tile.lat},${tile.lng}) ... `);
    try {
      const found = await fetchHotelsInTile(tile);
      for (const [no, h] of found) {
        if (!allHotels.has(no)) {
          allHotels.set(no, { ...h, region: tile.region });
        }
      }
      console.error(`${found.size}件`);
    } catch (err) {
      console.error(`失敗: ${err}`);
    }
    await sleep(REQUEST_INTERVAL_MS);
  }

  console.error(`合計ユニークホテル数: ${allHotels.size}`);

  // compute-territories.mjs の入力用に、生データもJSONで保存しておく
  writeFileSync("hotels.json", JSON.stringify([...allHotels.values()], null, 0));
  console.error("hotels.json を書き出しました（compute-territories.mjs の入力に使用）");

  const now = new Date().toISOString();
  const lines = [];
  for (const h of allHotels.values()) {
    lines.push(
      `INSERT INTO hotels (hotel_no, name, lat, lng, region, synced_at) VALUES (${h.hotelNo}, ${sqlEscape(
        h.name
      )}, ${h.lat}, ${h.lng}, ${sqlEscape(h.region)}, ${sqlEscape(now)}) ` +
        `ON CONFLICT(hotel_no) DO UPDATE SET name=excluded.name, lat=excluded.lat, lng=excluded.lng, synced_at=excluded.synced_at;`
    );
  }
  console.log(lines.join("\n"));
}

main();
