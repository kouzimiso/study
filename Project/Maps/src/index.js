import {
  fetchVacantHotelCount,
  fetchVacantHotels,
  RakutenRateLimitError,
  sleep,
  validateCredentials,
  credentialsFromRequest,
  serverCredentials,
  hasCredentials,
} from "./rakuten.js";
import { cellsWithinCircle, snapToCell, jitterPoint, estimateCellCount, encodeCell } from "./grid.js";
import { fetchPlaceSeeds } from "./overpass.js";

// ---- 設定値 ----
const REQUEST_INTERVAL_MS = 200; // 楽天APIへの連続リクエスト間隔
const MAX_SEARCH_RADIUS_KM = 12; // 1回の検索で許可する最大半径
const MAX_CELLS_PER_SEARCH = 40; // 1回の検索で分解するセルの上限（API呼び出し回数の目安）
const AREA_SAMPLE_FETCH_BUDGET = 25; // 範囲検索1回（ボタン1押下）で新規に楽天APIを呼ぶ最大回数
const AREA_SAMPLE_MAX_ATTEMPTS = 200; // 乱数サンプリングの試行上限（重複・検索済みセルのスキップ分の余裕）
const SEED_BIAS_RATIO = 0.8; // 街・集落の座標が取れた場合に、その周辺を優先する割合（残りは完全ランダムで取りこぼしを防ぐ）
const SEED_SPREAD_KM = 10; // 街・集落の中心からどの程度散らしてサンプリングするか

// フロントエンド（Cloudflare Pages等）からのクロスオリジン呼び出しを許可する
const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers":
    "content-type, x-rakuten-app-id, x-rakuten-access-key, x-rakuten-affiliate-id, x-rakuten-referer",
  "access-control-max-age": "86400",
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    try {
      if (request.method === "OPTIONS") return corsPreflight();
      if (url.pathname === "/api/config") return await handleConfig(env);
      if (url.pathname === "/api/settings" && request.method === "POST")
        return await handleSettings(request, env);
      if (url.pathname === "/api/search") return await handleSearch(url, request, env);
      if (url.pathname === "/api/search-area") return await handleSearchArea(url, request, env);
      if (url.pathname === "/api/hotels") return await handleHotels(url, request, env);
      if (url.pathname === "/api/heatmap") return await handleHeatmap(url, env);
      if (url.pathname === "/api/status") return await handleStatus(url, env);
      return json({ error: "not_found" }, 404);
    } catch (err) {
      if (err instanceof RakutenRateLimitError) {
        return json(
          { error: "rate_limited", message: "楽天APIの呼び出し制限に達しました。少し時間をおいて再試行してください。" },
          429
        );
      }
      return json({ error: "internal_error", message: String(err) }, 500);
    }
  },
};

// ---------- HTTPハンドラー ----------

// 指定日付・地点の空室を検索する（オンデマンド）。
// ・地点は全国共通グリッドのセルに分解される
// ・同じセルを「今日」誰かが検索済みならAPIを呼ばずにキャッシュを再利用（結果がたまる）
// ・未取得のセルだけ楽天APIを呼び、結果をvacancy_cellsに保存する
async function handleSearch(url, request, env) {
  const rawDate = url.searchParams.get("date");
  const lat = Number(url.searchParams.get("lat"));
  const lng = Number(url.searchParams.get("lng"));
  if (
    !rawDate ||
    url.searchParams.get("lat") == null ||
    url.searchParams.get("lng") == null ||
    !Number.isFinite(lat) ||
    !Number.isFinite(lng) ||
    Math.abs(lat) > 90 ||
    Math.abs(lng) > 180
  ) {
    return json({ error: "date, lat, lng が必要です（lat/lng は数値）" }, 400);
  }
  const date = rawDate;
  const radiusKm = Math.min(
    Math.max(Number(url.searchParams.get("radiusKm") || "3") || 3, 0.1),
    MAX_SEARCH_RADIUS_KM
  );

  // 自分のキー(ヘッダ) → サーバー側キー(env) の順で解決
  const creds = credentialsFromRequest(request, env) || serverCredentials(env);
  if (!hasCredentials(creds)) {
    return json({ error: "no_rakuten_key", message: "楽天APIキーが未設定です（設定画面から入力してください）" }, 400);
  }

  const cells = cellsWithinCircle(lat, lng, radiusKm);
  if (cells.length > MAX_CELLS_PER_SEARCH) {
    return json({ error: "radius_too_large", message: "検索範囲が広すぎます（半径を小さくしてください）" }, 400);
  }

  const today = todayJST();
  const features = [];
  const stats = { fetchedCells: 0, cachedCells: 0 };
  let rateLimited = false;

  for (const cell of cells) {
    const [clat, clng] = encodeCell(cell.lat, cell.lng);
    const cached = await getCachedCell(env, date, clat, clng);
    if (cached && cached.fetched_at.slice(0, 10) === today) {
      stats.cachedCells += 1; // 今日検索済みのセルは再利用
      features.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [cell.lng, cell.lat] },
        properties: { radiusKm: cell.radiusKm, hotelCount: cached.hotel_count, cached: true },
      });
      continue;
    }
    try {
      const count = await fetchVacantHotelCount(
        { lat: cell.lat, lng: cell.lng, radiusKm: cell.radiusKm },
        date,
        creds
      );
      await upsertCell(env, date, clat, clng, cell.radiusKm, count);
      stats.fetchedCells += 1;
      features.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [cell.lng, cell.lat] },
        properties: { radiusKm: cell.radiusKm, hotelCount: count, cached: false },
      });
      await sleep(REQUEST_INTERVAL_MS);
    } catch (err) {
      if (err instanceof RakutenRateLimitError) {
        rateLimited = true; // 制限に達したらここまで。検索済みセルは保存されている
        break;
      }
      console.error(`cell (${clat},${clng}) search failed:`, err);
    }
  }

  return json({
    type: "FeatureCollection",
    date,
    features,
    stats,
    partial: rateLimited,
    message: rateLimited
      ? "検索中に楽天APIのレート制限に達しました。ここまでに検索できた地点は反映されています。"
      : undefined,
  });
}

// 指定した矩形範囲（地図の表示範囲）を統計的にサンプリング検索する（範囲検索）。
// ・広大な範囲を全部検索するのは非現実的（呼び出し回数・時間ともに）なうえ、密集した
//   都市部を隅々まで検索しても情報としての価値は低いので、範囲内をランダムにサンプリングする
// ・完全に一様ランダムだと海上・山中などホテルが存在しえない場所にも均等に検索してしまい
//   呼び出し回数を無駄にするため、Overpassで取得した街・集落の座標周辺を優先的に
//   サンプリングする（取得できない場合は従来通り完全ランダムにフォールバック）
// ・1回のボタン押下＝新規セルを最大 AREA_SAMPLE_FETCH_BUDGET 件だけ楽天APIで検索
// ・「検索率」（範囲内でどれだけ検索できたか）と「空き率」（検索済みのうち空きが
//   見つかった割合）を返す。検索率が低ければ空き率はまだ参考程度、という判断ができる
// ・ボタンを繰り返し押すたびに新しいセルがサンプリングされ、検索率が上がっていく
async function handleSearchArea(url, request, env) {
  const rawDate = url.searchParams.get("date");
  const south = Number(url.searchParams.get("south"));
  const west = Number(url.searchParams.get("west"));
  const north = Number(url.searchParams.get("north"));
  const east = Number(url.searchParams.get("east"));

  if (
    !rawDate ||
    ![south, west, north, east].every(Number.isFinite) ||
    south >= north ||
    west >= east ||
    Math.abs(south) > 90 ||
    Math.abs(north) > 90 ||
    Math.abs(west) > 180 ||
    Math.abs(east) > 180
  ) {
    return json({ error: "date, south, west, north, east が必要です" }, 400);
  }
  const date = rawDate;

  const creds = credentialsFromRequest(request, env) || serverCredentials(env);
  if (!hasCredentials(creds)) {
    return json({ error: "no_rakuten_key", message: "楽天APIキーが未設定です（設定画面から入力してください）" }, 400);
  }

  const seeds = await fetchPlaceSeeds(south, west, north, east);

  const today = todayJST();
  const seen = new Set();
  const features = [];
  let fetchedCells = 0;
  let attempts = 0;
  let rateLimited = false;

  while (fetchedCells < AREA_SAMPLE_FETCH_BUDGET && attempts < AREA_SAMPLE_MAX_ATTEMPTS) {
    attempts += 1;
    let lat, lng;
    if (seeds.length > 0 && Math.random() < SEED_BIAS_RATIO) {
      const seed = seeds[(Math.random() * seeds.length) | 0];
      ({ lat, lng } = jitterPoint(seed.lat, seed.lng, SEED_SPREAD_KM));
    } else {
      lat = south + Math.random() * (north - south);
      lng = west + Math.random() * (east - west);
    }
    const cell = snapToCell(lat, lng);
    const [clat, clng] = encodeCell(cell.lat, cell.lng);
    const key = `${clat},${clng}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const cached = await getCachedCell(env, date, clat, clng);
    if (cached && cached.fetched_at.slice(0, 10) === today) continue; // 今日検索済み：他の地点を試す

    try {
      const count = await fetchVacantHotelCount(
        { lat: cell.lat, lng: cell.lng, radiusKm: cell.radiusKm },
        date,
        creds
      );
      await upsertCell(env, date, clat, clng, cell.radiusKm, count);
      fetchedCells += 1;
      features.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [cell.lng, cell.lat] },
        properties: { radiusKm: cell.radiusKm, hotelCount: count, cached: false },
      });
      await sleep(REQUEST_INTERVAL_MS);
    } catch (err) {
      if (err instanceof RakutenRateLimitError) {
        rateLimited = true; // 制限に達したらここまで。もう一度押せば別の地点から続けられる
        break;
      }
      console.error(`cell (${clat},${clng}) search failed:`, err);
    }
  }

  const totalCellsEstimate = estimateCellCount(south, west, north, east);
  const areaStats = await getAreaStats(env, date, south, west, north, east);
  const searchRate = totalCellsEstimate > 0 ? Math.min(1, areaStats.searchedCells / totalCellsEstimate) : 0;
  const vacancyRate = areaStats.searchedCells > 0 ? areaStats.vacantCells / areaStats.searchedCells : null;

  return json({
    type: "FeatureCollection",
    date,
    features,
    stats: { fetchedCells, attempts },
    totalCellsEstimate,
    searchedCells: areaStats.searchedCells,
    vacantCells: areaStats.vacantCells,
    searchRate,
    vacancyRate,
    partial: rateLimited,
    message: rateLimited
      ? "楽天APIのレート制限に達しました。少し待ってから「この範囲を検索」をもう一度押してください。"
      : undefined,
  });
}

// 指定セル（ヒートマップの円をクリック）の空室ホテル一覧を返す。
// ・同じ日付・セルの詳細は当日中キャッシュ（hotel_details）を再利用
// ・未取得なら空室検索APIをhits=20で呼び、ホテル名・料金・アフィリエイトURLを返す
async function handleHotels(url, request, env) {
  const rawDate = url.searchParams.get("date");
  const lat = Number(url.searchParams.get("lat"));
  const lng = Number(url.searchParams.get("lng"));
  if (
    !rawDate ||
    url.searchParams.get("lat") == null ||
    url.searchParams.get("lng") == null ||
    !Number.isFinite(lat) ||
    !Number.isFinite(lng) ||
    Math.abs(lat) > 90 ||
    Math.abs(lng) > 180
  ) {
    return json({ error: "date, lat, lng が必要です（lat/lng は数値）" }, 400);
  }
  const date = rawDate;
  const radiusKm = Math.min(Math.max(Number(url.searchParams.get("radiusKm") || "2.8") || 2.8, 0.1), 3.0);

  const creds = credentialsFromRequest(request, env) || serverCredentials(env);
  if (!hasCredentials(creds)) {
    return json({ error: "no_rakuten_key", message: "楽天APIキーが未設定です（設定画面から入力してください）" }, 400);
  }

  const [clat, clng] = encodeCell(lat, lng);
  const today = todayJST();
  const cached = await getHotelCache(env, date, clat, clng);
  if (cached && cached.fetched_at.slice(0, 10) === today) {
    return json({ date, lat: clat / 1e6, lng: clng / 1e6, radiusKm, cached: true, hotels: JSON.parse(cached.payload) });
  }

  const hotels = await fetchVacantHotels({ lat, lng, radiusKm }, date, creds);
  await upsertHotelCache(env, date, clat, clng, hotels);
  return json({ date, lat: clat / 1e6, lng: clng / 1e6, radiusKm, cached: false, hotels });
}

// 指定日に検索済み（蓄積された）セルすべてを返す
async function handleHeatmap(url, env) {
  const date = url.searchParams.get("date") || todayJST();
  const rows = await env.DB.prepare(
    `SELECT lat, lng, radius_km, hotel_count, fetched_at
       FROM vacancy_cells WHERE date = ?`
  )
    .bind(date)
    .all();

  const features = (rows.results || []).map((r) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [r.lng / 1e6, r.lat / 1e6] },
    properties: {
      radiusKm: r.radius_km,
      hotelCount: r.hotel_count,
      fetchedAt: r.fetched_at,
    },
  }));

  return json({ type: "FeatureCollection", date, features });
}

// 指定日の蓄積状況（表示用）
async function handleStatus(url, env) {
  const date = url.searchParams.get("date") || todayJST();
  const row = await env.DB.prepare(
    `SELECT COUNT(*) AS cell_count, MAX(fetched_at) AS last_fetched_at
       FROM vacancy_cells WHERE date = ?`
  )
    .bind(date)
    .first();
  return json({
    date,
    exists: (row?.cell_count || 0) > 0,
    cellCount: row?.cell_count || 0,
    lastFetchedAt: row?.last_fetched_at || null,
  });
}

// サーバー側の設定状況（フロントの設定画面・キー未設定の案内に使う）
async function handleConfig(env) {
  return json({ serverKeyConfigured: hasCredentials(serverCredentials(env)) });
}

// キーの検証のみ（設定画面の「キーをテスト」）。サーバーには保存しない。
async function handleSettings(request, env) {
  const body = await request.json().catch(() => null);
  if (!body?.appId || !body?.accessKey) {
    return json({ ok: false, error: "appId と accessKey は必須です" }, 400);
  }
  const creds = {
    appId: String(body.appId).trim(),
    accessKey: String(body.accessKey).trim(),
    affiliateId: body.affiliateId ? String(body.affiliateId).trim() : "",
    referer: body.referer ? String(body.referer).trim() : "",
  };
  const result = await validateCredentials(creds);
  if (!result.ok) {
    return json(
      {
        ok: false,
        error: "invalid_credentials",
        status: result.status ?? null,
        detail: result.message ?? "",
      },
      400
    );
  }
  return json({ ok: true, checkedCount: result.count ?? 0 });
}

// ---------- DBヘルパー ----------

async function getCachedCell(env, date, lat, lng) {
  return env.DB.prepare(
    `SELECT hotel_count, fetched_at FROM vacancy_cells WHERE date = ? AND lat = ? AND lng = ?`
  )
    .bind(date, lat, lng)
    .first();
}

async function upsertCell(env, date, lat, lng, radiusKm, count) {
  await env.DB.prepare(
    `INSERT INTO vacancy_cells (date, lat, lng, radius_km, hotel_count, fetched_at)
     VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT(date, lat, lng) DO UPDATE SET
       hotel_count = excluded.hotel_count, fetched_at = excluded.fetched_at`
  )
    .bind(date, lat, lng, radiusKm, count, nowJSTISO())
    .run();
}

// 矩形範囲内で「今日」検索済みのセル数と、そのうち空きが見つかったセル数を集計する
// （検索率・空き率の算出に使う。日付をまたいだ古いデータは含めない）
async function getAreaStats(env, date, south, west, north, east) {
  const row = await env.DB.prepare(
    `SELECT COUNT(*) AS searched, SUM(CASE WHEN hotel_count > 0 THEN 1 ELSE 0 END) AS vacant
       FROM vacancy_cells
       WHERE date = ? AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?`
  )
    .bind(date, Math.round(south * 1e6), Math.round(north * 1e6), Math.round(west * 1e6), Math.round(east * 1e6))
    .first();
  return { searchedCells: row?.searched || 0, vacantCells: row?.vacant || 0 };
}

async function getHotelCache(env, date, lat, lng) {
  return env.DB.prepare(`SELECT payload, fetched_at FROM hotel_details WHERE date = ? AND lat = ? AND lng = ?`)
    .bind(date, lat, lng)
    .first();
}

async function upsertHotelCache(env, date, lat, lng, hotels) {
  await env.DB.prepare(
    `INSERT INTO hotel_details (date, lat, lng, payload, fetched_at)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(date, lat, lng) DO UPDATE SET
       payload = excluded.payload, fetched_at = excluded.fetched_at`
  )
    .bind(date, lat, lng, JSON.stringify(hotels), nowJSTISO())
    .run();
}

// ---------- 共通ユーティリティ ----------

function todayJST() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}

// fetched_at はJST基準のISO文字列で保存する（freshness判定の日付比較を
// todayJST() と常に一致させるため。表示上の時刻もJSTになる）
function nowJSTISO() {
  return new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString();
}

function corsPreflight() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...CORS_HEADERS,
    },
  });
}
