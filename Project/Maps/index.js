import { fetchVacantHotelCount, fetchNearbyHotelNos, RakutenRateLimitError, sleep } from "./rakuten.js";

// ---- 設定値 ----
const TARGET_DATE_RANGE_DAYS = 16; // 「今日から何日先まで」を巡回更新の対象にするか
const BATCH_SIZE_PER_RUN = 30; // 1回のCron実行で処理するホテル数（無料枠のsubrequest上限対策）
const REQUEST_INTERVAL_MS = 250; // 楽天APIへの連続リクエスト間隔
const NEIGHBOR_CHECK_STALE_DAYS = 30; // 何日以上前の担当範囲計算を「要チェック」とみなすか
const NEIGHBOR_CHECK_BATCH_SIZE = 30;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    try {
      if (url.pathname === "/api/heatmap") return await handleHeatmap(url, env);
      if (url.pathname === "/api/status") return await handleStatus(url, env);
      if (url.pathname === "/api/refresh" && request.method === "POST")
        return await handleRefresh(url, env, ctx);
      if (url.pathname === "/api/admin/dirty-hotels") return await handleDirtyHotels(env);
      return json({ error: "not_found" }, 404);
    } catch (err) {
      return json({ error: "internal_error", message: String(err) }, 500);
    }
  },

  async scheduled(event, env, ctx) {
    // JSTの曜日で「日々の空室巡回」と「周辺構成チェック」を使い分ける
    // （どちらも重い処理なので同時には走らせない）
    const isSunday = new Date(Date.now() + 9 * 3600 * 1000).getUTCDay() === 0;
    if (isSunday) {
      ctx.waitUntil(runNeighborCheckJob(env));
    } else {
      ctx.waitUntil(runVacancyBatchJob(env));
    }
  },
};

// ---------- HTTPハンドラー ----------

async function handleHeatmap(url, env) {
  const date = url.searchParams.get("date") || todayJST();
  const rows = await env.DB.prepare(
    `SELECT h.hotel_no, h.name, h.lat, h.lng, t.radius_km, v.hotel_count
       FROM hotels h
       JOIN hotel_territory t ON t.hotel_no = h.hotel_no
       JOIN vacancy_snapshots v ON v.hotel_no = h.hotel_no
      WHERE v.stay_date = ?`
  )
    .bind(date)
    .all();

  const features = (rows.results || []).map((r) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [r.lng, r.lat] },
    properties: {
      hotelNo: r.hotel_no,
      name: r.name,
      radiusKm: r.radius_km,
      hotelCount: r.hotel_count,
    },
  }));

  return json({ type: "FeatureCollection", date, features });
}

async function handleStatus(url, env) {
  const date = url.searchParams.get("date") || todayJST();
  const row = await env.DB.prepare(
    `SELECT MAX(fetched_at) AS fetched_at, COUNT(*) AS hotel_count
       FROM vacancy_snapshots WHERE stay_date = ?`
  )
    .bind(date)
    .first();

  const fetchedAt = row?.fetched_at || null;
  const fetchedToday = fetchedAt ? fetchedAt.slice(0, 10) === todayJST() : false;

  return json({
    date,
    exists: (row?.hotel_count || 0) > 0,
    fetchedAt,
    needsConfirmBeforeRefresh: !fetchedToday,
  });
}

async function handleRefresh(url, env, ctx) {
  const date = url.searchParams.get("date");
  if (!date) return json({ error: "date is required" }, 400);

  const row = await env.DB.prepare(
    `SELECT MAX(fetched_at) AS fetched_at FROM vacancy_snapshots WHERE stay_date = ?`
  )
    .bind(date)
    .first();
  const fetchedToday = row?.fetched_at ? row.fetched_at.slice(0, 10) === todayJST() : false;

  if (fetchedToday) {
    return json({ status: "already_updated_today", date }, 200);
  }

  await setVacancyJob(env, date);
  ctx.waitUntil(runVacancyBatchJob(env));
  return json({ status: "refresh_started", date }, 202);
}

async function handleDirtyHotels(env) {
  const rows = await env.DB.prepare(
    `SELECT h.hotel_no, h.name, h.lat, h.lng, t.radius_km
       FROM hotel_territory t JOIN hotels h ON h.hotel_no = t.hotel_no
      WHERE t.dirty = 1`
  ).all();
  return json({ dirtyHotels: rows.results || [] });
}

// ---------- ジョブ1：日々の空室巡回（ホテルの担当範囲ごとに検索） ----------

async function runVacancyBatchJob(env) {
  let job = await getJob(env, "vacancy");

  if (!job.stay_date) {
    const nextDate = await pickNextTargetDate(env);
    if (!nextDate) return;
    await setVacancyJob(env, nextDate);
    job = { stay_date: nextDate, cursor: 0 };
  }

  const rows = await env.DB.prepare(
    `SELECT h.hotel_no, h.lat, h.lng, t.radius_km
       FROM hotels h JOIN hotel_territory t ON t.hotel_no = h.hotel_no
      ORDER BY h.hotel_no`
  ).all();
  const allHotels = rows.results || [];

  const end = Math.min(job.cursor + BATCH_SIZE_PER_RUN, allHotels.length);
  let cursor = job.cursor;

  for (let i = job.cursor; i < end; i++) {
    const hotel = allHotels[i];
    try {
      const count = await fetchVacantHotelCount(
        { lat: hotel.lat, lng: hotel.lng, radiusKm: hotel.radius_km },
        job.stay_date,
        env
      );
      await env.DB.prepare(
        `INSERT INTO vacancy_snapshots (hotel_no, stay_date, hotel_count, fetched_at)
         VALUES (?, ?, ?, ?)
         ON CONFLICT(hotel_no, stay_date) DO UPDATE SET
           hotel_count = excluded.hotel_count, fetched_at = excluded.fetched_at`
      )
        .bind(hotel.hotel_no, job.stay_date, count, new Date().toISOString())
        .run();
      cursor = i + 1;
      await sleep(REQUEST_INTERVAL_MS);
    } catch (err) {
      if (err instanceof RakutenRateLimitError) break; // 次回のCron起動に持ち越す
      console.error(`hotel ${hotel.hotel_no} fetch failed:`, err);
      cursor = i + 1;
    }
  }

  if (cursor >= allHotels.length) {
    await setVacancyJob(env, null);
  } else {
    await setCursor(env, "vacancy", cursor);
  }
}

async function pickNextTargetDate(env) {
  const today = todayJST();
  for (let i = 0; i < TARGET_DATE_RANGE_DAYS; i++) {
    const date = addDaysStr(today, i);
    const row = await env.DB.prepare(
      `SELECT MAX(fetched_at) AS fetched_at FROM vacancy_snapshots WHERE stay_date = ?`
    )
      .bind(date)
      .first();
    const fetchedToday = row?.fetched_at ? row.fetched_at.slice(0, 10) === today : false;
    if (!fetchedToday) return date;
  }
  return null;
}

async function setVacancyJob(env, date) {
  await env.DB.prepare(
    `INSERT INTO job_state (job_type, stay_date, cursor, updated_at)
     VALUES ('vacancy', ?, 0, ?)
     ON CONFLICT(job_type) DO UPDATE SET stay_date = excluded.stay_date, cursor = 0, updated_at = excluded.updated_at`
  )
    .bind(date, new Date().toISOString())
    .run();
}

// ---------- ジョブ2：周辺ホテル構成の変化チェック（軽量・低頻度） ----------
// 担当範囲(radius_km)そのものの再計算はしない（重いのでオフラインスクリプトの役割）。
// ここでは「前回計算時と近隣ホテルの顔ぶれが変わっていないか」だけを確認し、
// 変わっていたら dirty=1 を立てて、運営側が compute-territories.mjs を再実行する目印にする。

async function runNeighborCheckJob(env) {
  const job = await getJob(env, "neighbor_check");
  const staleBefore = new Date(Date.now() - NEIGHBOR_CHECK_STALE_DAYS * 86400 * 1000).toISOString();

  const rows = await env.DB.prepare(
    `SELECT h.hotel_no, h.lat, h.lng, t.radius_km, t.neighbor_set
       FROM hotels h JOIN hotel_territory t ON t.hotel_no = h.hotel_no
      WHERE t.dirty = 0 AND (t.checked_at IS NULL OR t.checked_at < ?)
      ORDER BY h.hotel_no
      LIMIT ? OFFSET ?`
  )
    .bind(staleBefore, NEIGHBOR_CHECK_BATCH_SIZE, job.cursor)
    .all();
  const targets = rows.results || [];

  if (targets.length === 0) {
    await setCursor(env, "neighbor_check", 0); // 一周したので次回また先頭から
    return;
  }

  for (const hotel of targets) {
    try {
      const nos = await fetchNearbyHotelNos(hotel.lat, hotel.lng, hotel.radius_km, env);
      const currentSet = nos.filter((n) => n !== hotel.hotel_no).join(",");
      const changed = currentSet !== (hotel.neighbor_set || "");
      await env.DB.prepare(
        `UPDATE hotel_territory SET checked_at = ?, dirty = ? WHERE hotel_no = ?`
      )
        .bind(new Date().toISOString(), changed ? 1 : 0, hotel.hotel_no)
        .run();
      await sleep(REQUEST_INTERVAL_MS);
    } catch (err) {
      if (err instanceof RakutenRateLimitError) break;
      console.error(`neighbor check for hotel ${hotel.hotel_no} failed:`, err);
    }
  }

  await setCursor(env, "neighbor_check", job.cursor + targets.length);
}

// ---------- 共通ユーティリティ ----------

async function getJob(env, jobType) {
  const row = await env.DB.prepare(
    `SELECT stay_date, cursor FROM job_state WHERE job_type = ?`
  )
    .bind(jobType)
    .first();
  return row || { stay_date: null, cursor: 0 };
}

async function setCursor(env, jobType, cursor) {
  await env.DB.prepare(
    `INSERT INTO job_state (job_type, cursor, updated_at) VALUES (?, ?, ?)
     ON CONFLICT(job_type) DO UPDATE SET cursor = excluded.cursor, updated_at = excluded.updated_at`
  )
    .bind(jobType, cursor, new Date().toISOString())
    .run();
}

function todayJST() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}

function addDaysStr(dateStr, days) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
