import {
  fetchVacantHotelCount,
  fetchVacantHotels,
  fetchHotelFacilities,
  RakutenRateLimitError,
  sleep,
  validateCredentials,
  credentialsFromRequest,
  serverCredentials,
  hasCredentials,
} from "./rakuten.js";
import { cellsWithinCircle, snapToCell, jitterPoint, encodeCell, CELL_RADIUS_KM } from "./grid.js";
import { fetchPlaceSeeds, fetchPois } from "./overpass.js";

// ---- 設定値 ----
// 楽天APIへの連続リクエスト間隔。エラーメッセージ("Try again in 1 seconds")から見て
// 実際の制限は概ね1秒に1回程度とみられるため、それを下回らない間隔にする
// （rakuten.js側にも429時のリトライを実装済みだが、そもそも自滅的に制限を踏みにいかない）。
const REQUEST_INTERVAL_MS = 1100;
const MAX_SEARCH_RADIUS_KM = 12; // 1回の検索で許可する最大半径
const MAX_CELLS_PER_SEARCH = 40; // 1回の検索で分解するセルの上限（API呼び出し回数の目安）
// 範囲検索は「①発見フェーズ（実在ホテルを見つける）」→「②空室確認フェーズ（発見済みホテルの
// 場所だけ空室を調べる）」の2段構成。①を優先すると何も表示されない回が増えるため、
// まず②に予算を回し、余った分を①に使う（新しいエリアでは自然と①中心になる）。
const AREA_SAMPLE_FETCH_BUDGET = 25; // 範囲検索1回（ボタン1押下）で使う楽天APIの呼び出し回数の合計上限
const AREA_DISCOVERY_MIN_BUDGET = 6; // ①発見フェーズに最低限確保する呼び出し回数（②だけに予算を使い切らせない）
const AREA_SAMPLE_MAX_ATTEMPTS = 200; // ①発見フェーズの乱数サンプリング試行上限
const SEED_BIAS_RATIO = 0.8; // 街・集落の座標が取れた場合に、その周辺を優先する割合（残りは完全ランダムで取りこぼしを防ぐ）
const SEED_SPREAD_KM = 10; // 街・集落の中心からどの程度散らしてサンプリングするか
const HOTELS_PER_AREA_QUERY_LIMIT = 1000; // 範囲検索1回でDBから読む既知ホテル数の上限（CPU保護）
// 観光地POIは日付を持たない半永久データとしてサーバー側でキャッシュする。
// ホテル用グリッド(4km)とは別に、POI用の粗いカバレッジ格子(約5.5km四方)で
// 「いつスイープしたか」を記録し、一定日数が過ぎたら再取得して閉園等の変化を取り込む。
const POI_CELL_DEG = 0.05;
const POI_STALE_DAYS = 30;
const POI_SWEEP_CHECK_LIMIT = 60; // 再取得が必要か確認するセル数の上限（広い範囲でのCPU保護）
const POI_MAX_ESTIMATED_CELLS = 4000; // これを超える範囲は広すぎるとしてスイープをスキップ

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
      if (url.pathname === "/api/pois") return await handlePois(url, env);
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

// 指定した矩形範囲（地図の表示範囲）を2段構成で検索する（範囲検索）。
// ①発見フェーズ：実在するホテルの場所を施設検索(SimpleHotelSearch)で発見し、
//   hotels テーブルに恒久的に蓄積する（日付に依存しないので一度発見すれば永久に使える）。
//   街や海のどこに何があるか分からないので、Overpassの街・集落座標に寄せつつランダムに
//   セルを選び、まだ調べていないセルだけを施設検索する。
// ②空室確認フェーズ：①で実在が分かっているホテルの場所「だけ」を狙って空室検索する。
//   ランダムな座標を当てずっぽうで検索しないので、海や山中への無駄打ちが原理的に無い。
// 1回のボタン押下の呼び出し回数予算は②を優先し、余りを①に回す
// （知らない場所では自然と①中心になり、既知の場所では②中心になる）。
// 「検索率」は実在が分かっているホテルのうち今日空室確認できた割合、「空き率」は
// 確認済みのうち空きが見つかった割合。検索率が低ければ空き率はまだ参考程度、という判断ができる。
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

  const today = todayJST();
  const features = [];
  let vacancyChecked = 0;
  let hotelsDiscovered = 0;
  let rateLimited = false;
  let budget = AREA_SAMPLE_FETCH_BUDGET;
  let errorCount = 0;
  let lastErrorMessage;
  const MAX_CONSECUTIVE_ERRORS = 5; // 同じ原因で全予算を空回りさせないための早期打ち切り

  // ---- ②空室確認フェーズ：発見済みホテルの場所だけを狙う ----
  const vacancyBudget = budget - AREA_DISCOVERY_MIN_BUDGET;
  if (vacancyBudget > 0) {
    const candidateCells = await getUncheckedHotelCells(env, date, today, south, west, north, east);
    shuffle(candidateCells);
    let consecutiveErrors = 0;
    for (const c of candidateCells) {
      if (vacancyChecked >= vacancyBudget) break;
      try {
        const count = await fetchVacantHotelCount({ lat: c.lat, lng: c.lng, radiusKm: c.radiusKm }, date, creds);
        await upsertCell(env, date, c.clat, c.clng, c.radiusKm, count);
        vacancyChecked += 1;
        budget -= 1;
        consecutiveErrors = 0;
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [c.lng, c.lat] },
          properties: { radiusKm: c.radiusKm, hotelCount: count, cached: false },
        });
        await sleep(REQUEST_INTERVAL_MS);
      } catch (err) {
        if (err instanceof RakutenRateLimitError) {
          rateLimited = true;
          break;
        }
        errorCount += 1;
        consecutiveErrors += 1;
        lastErrorMessage = String(err?.message || err);
        console.error(`vacancy check (${c.clat},${c.clng}) failed:`, err);
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) break; // 同じ原因で空回りしている可能性が高い
        await sleep(REQUEST_INTERVAL_MS);
      }
    }
  }

  // ---- ①発見フェーズ：残り予算で新しい場所のホテルを発見する ----
  if (!rateLimited && budget > 0) {
    const seeds = await fetchPlaceSeeds(south, west, north, east);
    const seen = new Set();
    let attempts = 0;
    let consecutiveErrors = 0;

    while (budget > 0 && attempts < AREA_SAMPLE_MAX_ATTEMPTS) {
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

      const facility = await getCellFacility(env, clat, clng);
      if (facility) continue; // 発見済みセル（ホテル0件も含む）：スキップ

      try {
        const found = await fetchHotelFacilities({ lat: cell.lat, lng: cell.lng, radiusKm: cell.radiusKm }, creds);
        await upsertCellFacility(env, clat, clng, found.length);
        for (const h of found) {
          await upsertHotel(env, h);
        }
        hotelsDiscovered += found.length;
        budget -= 1;
        consecutiveErrors = 0;
        await sleep(REQUEST_INTERVAL_MS);
      } catch (err) {
        if (err instanceof RakutenRateLimitError) {
          rateLimited = true;
          break;
        }
        errorCount += 1;
        consecutiveErrors += 1;
        lastErrorMessage = String(err?.message || err);
        console.error(`facility discovery (${clat},${clng}) failed:`, err);
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) break; // 同じ原因で空回りしている可能性が高い
        await sleep(REQUEST_INTERVAL_MS);
      }
    }
  }

  const areaStats = await getHotelAreaStats(env, date, today, south, west, north, east);
  const searchRate = areaStats.knownHotels > 0 ? Math.min(1, areaStats.checkedHotels / areaStats.knownHotels) : 0;
  const vacancyRate = areaStats.checkedCells > 0 ? areaStats.vacantCells / areaStats.checkedCells : null;

  return json({
    type: "FeatureCollection",
    date,
    features,
    stats: { vacancyChecked, hotelsDiscovered, errorCount, lastErrorMessage },
    knownHotels: areaStats.knownHotels,
    checkedHotels: areaStats.checkedHotels,
    searchRate,
    vacancyRate,
    partial: rateLimited,
    message: rateLimited
      ? "楽天APIのレート制限に達しました。少し待ってから「この範囲を検索」をもう一度押してください。"
      : undefined,
  });
}

// 指定セル（ヒートマップの円をクリック）のホテル一覧を返す。
// ・空室ありホテル（名前・料金・アフィリエイトURL）に加え、満室ホテルも名前だけ返す
//   （「空室が無かった」だけでは何も伝わらないため、満室ホテルの存在は分かるようにする）
// ・同じ日付・セルの詳細は当日中キャッシュ（hotel_details）を再利用
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
    const payload = JSON.parse(cached.payload);
    return json({ date, lat: clat / 1e6, lng: clng / 1e6, radiusKm, cached: true, ...payload });
  }

  const [vacantHotels, facilities] = await Promise.all([
    fetchVacantHotels({ lat, lng, radiusKm }, date, creds),
    fetchHotelFacilities({ lat, lng, radiusKm }, creds),
  ]);
  const vacantNos = new Set(vacantHotels.map((h) => h.hotelNo));
  const fullHotels = facilities.filter((f) => !vacantNos.has(f.hotelNo));

  const payload = { hotels: vacantHotels, fullHotels };
  await upsertHotelCache(env, date, clat, clng, payload);
  return json({ date, lat: clat / 1e6, lng: clng / 1e6, radiusKm, cached: false, ...payload });
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

// 指定した矩形範囲の観光地POIを返す（日付を持たない半永久データ、サーバー側でキャッシュ）。
// ・ホテルとは別に、POI用の粗いカバレッジ格子で「いつ最後にOverpassでスイープしたか」を
//   記録する。範囲内に未スイープ・または古い（POI_STALE_DAYS超）セルがあれば、
//   その矩形をまとめて1回Overpassに問い合わせて更新する（セル単位で何度も問い合わせない）
// ・以後はDBのキャッシュから返すだけなので、Overpassへの問い合わせ回数を大きく減らせる
//   （毎回ブラウザから直接叩いていた従来方式に比べ、みんなで共有・再利用できる）
async function handlePois(url, env) {
  const south = Number(url.searchParams.get("south"));
  const west = Number(url.searchParams.get("west"));
  const north = Number(url.searchParams.get("north"));
  const east = Number(url.searchParams.get("east"));
  if (
    ![south, west, north, east].every(Number.isFinite) ||
    south >= north ||
    west >= east ||
    Math.abs(south) > 90 ||
    Math.abs(north) > 90 ||
    Math.abs(west) > 180 ||
    Math.abs(east) > 180
  ) {
    return json({ error: "south, west, north, east が必要です" }, 400);
  }

  const minRow = Math.floor(south / POI_CELL_DEG);
  const maxRow = Math.ceil(north / POI_CELL_DEG);
  const minCol = Math.floor(west / POI_CELL_DEG);
  const maxCol = Math.ceil(east / POI_CELL_DEG);
  const estimatedCells = (maxRow - minRow + 1) * (maxCol - minCol + 1);

  if (estimatedCells <= POI_MAX_ESTIMATED_CELLS) {
    const staleBefore = new Date(Date.now() - POI_STALE_DAYS * 24 * 60 * 60 * 1000).toISOString();
    let needsSweep = false;
    let checked = 0;
    outer: for (let row = minRow; row <= maxRow; row++) {
      for (let col = minCol; col <= maxCol; col++) {
        checked += 1;
        if (checked > POI_SWEEP_CHECK_LIMIT) break outer;
        const clat = Math.round(row * POI_CELL_DEG * 1e6);
        const clng = Math.round(col * POI_CELL_DEG * 1e6);
        const coverage = await getPoiCoverage(env, clat, clng);
        if (!coverage || coverage.swept_at < staleBefore) {
          needsSweep = true;
          break outer;
        }
      }
    }

    if (needsSweep) {
      try {
        const pois = await fetchPois(south, west, north, east);
        const sweptAt = nowJSTISO();
        for (const p of pois) {
          await upsertPoi(env, p);
        }
        for (let row = minRow; row <= maxRow; row++) {
          for (let col = minCol; col <= maxCol; col++) {
            await upsertPoiCoverage(env, Math.round(row * POI_CELL_DEG * 1e6), Math.round(col * POI_CELL_DEG * 1e6), sweptAt);
          }
        }
      } catch (err) {
        console.error("POI sweep failed:", err);
        // 取得に失敗しても、キャッシュ済みのデータで応答は続ける
      }
    }
  }

  const latMin = Math.round(south * 1e6);
  const latMax = Math.round(north * 1e6);
  const lngMin = Math.round(west * 1e6);
  const lngMax = Math.round(east * 1e6);
  const rows = await env.DB.prepare(
    `SELECT osm_id, name, lat, lng, tourism_type FROM pois WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?`
  )
    .bind(latMin, latMax, lngMin, lngMax)
    .all();

  return json({
    elements: (rows.results || []).map((r) => ({
      id: r.osm_id,
      lat: r.lat / 1e6,
      lon: r.lng / 1e6,
      tags: { name: r.name, tourism: r.tourism_type },
    })),
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

// 矩形範囲内で、①発見済みホテルのうち今日空室確認できた割合（検索率）と、
// ②確認済みセルのうち空きが見つかった割合（空き率）を算出するための集計。
async function getHotelAreaStats(env, date, today, south, west, north, east) {
  const latMin = Math.round(south * 1e6);
  const latMax = Math.round(north * 1e6);
  const lngMin = Math.round(west * 1e6);
  const lngMax = Math.round(east * 1e6);

  const totalRow = await env.DB.prepare(
    `SELECT COUNT(*) AS total FROM hotels WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?`
  )
    .bind(latMin, latMax, lngMin, lngMax)
    .first();

  const checkedRow = await env.DB.prepare(
    `SELECT COUNT(*) AS checked
       FROM hotels h
       WHERE h.lat BETWEEN ? AND ? AND h.lng BETWEEN ? AND ?
         AND EXISTS (
           SELECT 1 FROM vacancy_cells vc
           WHERE vc.date = ? AND vc.lat = h.cell_lat AND vc.lng = h.cell_lng
             AND substr(vc.fetched_at, 1, 10) = ?
         )`
  )
    .bind(latMin, latMax, lngMin, lngMax, date, today)
    .first();

  const cellRow = await env.DB.prepare(
    `SELECT COUNT(*) AS checked_cells, SUM(CASE WHEN hotel_count > 0 THEN 1 ELSE 0 END) AS vacant_cells
       FROM vacancy_cells
       WHERE date = ? AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?`
  )
    .bind(date, latMin, latMax, lngMin, lngMax)
    .first();

  return {
    knownHotels: totalRow?.total || 0,
    checkedHotels: checkedRow?.checked || 0,
    checkedCells: cellRow?.checked_cells || 0,
    vacantCells: cellRow?.vacant_cells || 0,
  };
}

// 矩形範囲内で、発見済みホテルがあるのに「今日」まだ空室確認していないセルを返す
// （②空室確認フェーズの対象。ランダムな座標ではなく実在ホテルの場所だけを狙うために使う）。
async function getUncheckedHotelCells(env, date, today, south, west, north, east) {
  const latMin = Math.round(south * 1e6);
  const latMax = Math.round(north * 1e6);
  const lngMin = Math.round(west * 1e6);
  const lngMax = Math.round(east * 1e6);

  const rows = await env.DB.prepare(
    `SELECT DISTINCT h.cell_lat AS clat, h.cell_lng AS clng
       FROM hotels h
       WHERE h.lat BETWEEN ? AND ? AND h.lng BETWEEN ? AND ?
         AND NOT EXISTS (
           SELECT 1 FROM vacancy_cells vc
           WHERE vc.date = ? AND vc.lat = h.cell_lat AND vc.lng = h.cell_lng
             AND substr(vc.fetched_at, 1, 10) = ?
         )
       LIMIT ?`
  )
    .bind(latMin, latMax, lngMin, lngMax, date, today, HOTELS_PER_AREA_QUERY_LIMIT)
    .all();

  return (rows.results || []).map((r) => ({
    clat: r.clat,
    clng: r.clng,
    lat: r.clat / 1e6,
    lng: r.clng / 1e6,
    radiusKm: CELL_RADIUS_KM,
  }));
}

// Fisher-Yatesシャッフル（配列を破壊的に並び替える）。②の対象セルを地図全域に
// まんべんなく散らして選ぶために使う（DB取得順に偏らせないため）。
function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

async function getCellFacility(env, lat, lng) {
  return env.DB.prepare(`SELECT total_hotel_count FROM cell_facilities WHERE lat = ? AND lng = ?`)
    .bind(lat, lng)
    .first();
}

async function upsertCellFacility(env, lat, lng, totalHotelCount) {
  await env.DB.prepare(
    `INSERT INTO cell_facilities (lat, lng, total_hotel_count, checked_at)
     VALUES (?, ?, ?, ?)
     ON CONFLICT(lat, lng) DO UPDATE SET
       total_hotel_count = excluded.total_hotel_count, checked_at = excluded.checked_at`
  )
    .bind(lat, lng, totalHotelCount, nowJSTISO())
    .run();
}

// 発見したホテルを恒久データとして保存する（hotel_no で一意。既存なら名前・座標を更新）。
// ホテル自身の座標からそのホテルが属するグリッドセル（cell_lat/cell_lng）も計算して
// 一緒に保存する（vacancy_cellsとJOINして空室確認状況を調べるため）。
async function upsertHotel(env, hotel) {
  const hotelCell = snapToCell(hotel.lat, hotel.lng);
  const [hLatEnc, hLngEnc] = encodeCell(hotel.lat, hotel.lng);
  const [cLatEnc, cLngEnc] = encodeCell(hotelCell.lat, hotelCell.lng);
  await env.DB.prepare(
    `INSERT INTO hotels (hotel_no, name, lat, lng, cell_lat, cell_lng, discovered_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(hotel_no) DO UPDATE SET
       name = excluded.name, lat = excluded.lat, lng = excluded.lng,
       cell_lat = excluded.cell_lat, cell_lng = excluded.cell_lng`
  )
    .bind(hotel.hotelNo, hotel.name, hLatEnc, hLngEnc, cLatEnc, cLngEnc, nowJSTISO())
    .run();
}

async function getPoiCoverage(env, lat, lng) {
  return env.DB.prepare(`SELECT swept_at FROM poi_coverage WHERE lat = ? AND lng = ?`)
    .bind(lat, lng)
    .first();
}

async function upsertPoiCoverage(env, lat, lng, sweptAt) {
  await env.DB.prepare(
    `INSERT INTO poi_coverage (lat, lng, swept_at)
     VALUES (?, ?, ?)
     ON CONFLICT(lat, lng) DO UPDATE SET swept_at = excluded.swept_at`
  )
    .bind(lat, lng, sweptAt)
    .run();
}

async function upsertPoi(env, poi) {
  const [latEnc, lngEnc] = encodeCell(poi.lat, poi.lng);
  await env.DB.prepare(
    `INSERT INTO pois (osm_id, name, lat, lng, tourism_type, updated_at)
     VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT(osm_id) DO UPDATE SET
       name = excluded.name, lat = excluded.lat, lng = excluded.lng,
       tourism_type = excluded.tourism_type, updated_at = excluded.updated_at`
  )
    .bind(poi.osmId, poi.name, latEnc, lngEnc, poi.tourismType, nowJSTISO())
    .run();
}

async function getHotelCache(env, date, lat, lng) {
  return env.DB.prepare(`SELECT payload, fetched_at FROM hotel_details WHERE date = ? AND lat = ? AND lng = ?`)
    .bind(date, lat, lng)
    .first();
}

async function upsertHotelCache(env, date, lat, lng, payload) {
  await env.DB.prepare(
    `INSERT INTO hotel_details (date, lat, lng, payload, fetched_at)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(date, lat, lng) DO UPDATE SET
       payload = excluded.payload, fetched_at = excluded.fetched_at`
  )
    .bind(date, lat, lng, JSON.stringify(payload), nowJSTISO())
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
