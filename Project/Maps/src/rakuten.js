// 楽天トラベルAPI（空室検索 / 施設検索）のクライアント。
// ドキュメント:
//   - 空室検索: https://webservice.rakuten.co.jp/documentation/vacant-hotel-search
//   - 施設検索: https://webservice.rakuten.co.jp/documentation/simple-hotel-search
//
// 注意点：
// - accessKey が必須（applicationId とは別に必要）
// - 緯度経度はデフォルトだと日本測地系・秒単位になるため、必ず datumType=1 を指定して
//   世界測地系（WGS84）・度単位で扱う
// - searchRadius は 0.1〜3.0km（小数点以下1桁まで）
// - hits=1 にして pagingInfo.recordCount だけを見れば、ヒット施設数の把握には十分
//   （レスポンス量を抑えてAPI呼び出しコストを下げる）
//
// クレデンシャルの扱い：
// - 通常のAPI呼び出しは `creds` オブジェクト { appId, accessKey, affiliateId } を受け取る。
// - リクエストヘッダ（x-rakuten-app-id / x-rakuten-access-key / x-rakuten-affiliate-id）で
//   ユーザー自身のキーが渡された場合はそちらを優先し、なければenvのサーバー側キーを使う。

const ENDPOINT =
  "https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426";

const SIMPLE_HOTEL_ENDPOINT =
  "https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731";

export class RakutenRateLimitError extends Error {}

/** 単純なsleep（レート制限対策でリクエスト間隔をあけるため） */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** キーが揃っている（API呼び出しに使える）かどうか */
export function hasCredentials(creds) {
  return Boolean(creds && creds.appId && creds.accessKey);
}

/**
 * リクエストヘッダからユーザー指定のクレデンシャルを取得する。
 * ヘッダが1つも無い場合は null（envフォールバックさせる）。ヘッダの片方だけの場合は
 * 足りない方をenvキーで補う（混在利用を許容）。
 * referer はフロントが自分自身のURL（location.href）を送ってくる。楽天API側が
 * 「アプリ登録」画面で設定したApplication URLとの照合にReferer/Originヘッダーを要求するため
 * （Workerからのサーバー間fetchはブラウザと違って自動で付かない。refererHeaders()参照）。
 * @returns {{appId:string, accessKey:string, affiliateId:string, referer:string}|null}
 */
export function credentialsFromRequest(request, env) {
  const appId = request?.headers.get("x-rakuten-app-id");
  const accessKey = request?.headers.get("x-rakuten-access-key");
  if (!appId && !accessKey) return null;
  return {
    appId: appId || env.RAKUTEN_APP_ID || "",
    accessKey: accessKey || env.RAKUTEN_ACCESS_KEY || "",
    affiliateId:
      request?.headers.get("x-rakuten-affiliate-id") || env.RAKUTEN_AFFILIATE_ID || "",
    referer: request?.headers.get("x-rakuten-referer") || env.RAKUTEN_REFERER || "",
  };
}

/** サーバー側envに設定されたキー */
export function serverCredentials(env) {
  return {
    appId: env.RAKUTEN_APP_ID || "",
    accessKey: env.RAKUTEN_ACCESS_KEY || "",
    affiliateId: env.RAKUTEN_AFFILIATE_ID || "",
    referer: env.RAKUTEN_REFERER || "",
  };
}

/**
 * 指定した座標・半径・日付で空室のある施設数を取得する。
 * @param {{lat:number, lng:number, radiusKm:number}} cell
 * @param {string} checkinDate - 'YYYY-MM-DD'
 * @param {{appId:string, accessKey:string, affiliateId?:string}} creds
 * @returns {Promise<number>} recordCount（空室のある施設数）。0件時や404時は0を返す。
 */
export async function fetchVacantHotelCount(cell, checkinDate, creds) {
  const checkout = addDays(checkinDate, 1);

  const params = new URLSearchParams({
    applicationId: creds.appId,
    accessKey: creds.accessKey,
    format: "json",
    formatVersion: "2",
    datumType: "1", // 世界測地系・度単位で緯度経度を扱う
    latitude: String(cell.lat),
    longitude: String(cell.lng),
    searchRadius: String(cell.radiusKm),
    checkinDate,
    checkoutDate: checkout,
    adultNum: "2",
    hits: "1", // 件数の把握だけが目的なので最小限に
    responseType: "small",
  });
  if (creds.affiliateId) {
    params.set("affiliateId", creds.affiliateId);
  }

  const res = await fetch(`${ENDPOINT}?${params.toString()}`, { headers: refererHeaders(creds) });

  if (res.status === 404) {
    // 該当エリアに空室施設が0件のときも404が返るケースがある
    return 0;
  }
  if (res.status === 429) {
    throw new RakutenRateLimitError("rakuten API rate limited (429)");
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`rakuten API error ${res.status}: ${body}`);
  }

  const data = await res.json();
  return data?.pagingInfo?.recordCount ?? 0;
}

/**
 * 指定した地点・日付で空室があるホテルの一覧を取得する（空室検索API, responseType=large）。
 * ヒートマップのセルをクリックしたときの詳細表示に使う。料金は1泊あたりの合計額。
 * @param {{lat:number, lng:number, radiusKm:number}} cell - 半径は0.1〜3.0km
 * @param {string} checkinDate
 * @param {{appId:string, accessKey:string, affiliateId?:string}} creds
 * @returns {Promise<{hotelNo:number, name:string, price?:number, url?:string|null}[]>}
 */
export async function fetchVacantHotels(cell, checkinDate, creds) {
  const checkout = addDays(checkinDate, 1);
  const params = new URLSearchParams({
    applicationId: creds.appId,
    accessKey: creds.accessKey,
    format: "json",
    formatVersion: "2",
    datumType: "1",
    latitude: String(cell.lat),
    longitude: String(cell.lng),
    searchRadius: String(cell.radiusKm),
    checkinDate,
    checkoutDate: checkout,
    adultNum: "2",
    hits: "20",
    responseType: "large",
  });
  if (creds.affiliateId) {
    params.set("affiliateId", creds.affiliateId);
  }

  const res = await fetch(`${ENDPOINT}?${params.toString()}`, { headers: refererHeaders(creds) });
  if (res.status === 404) return [];
  if (res.status === 429) throw new RakutenRateLimitError("rakuten API rate limited (429)");
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`rakuten API error ${res.status}: ${body}`);
  }
  const data = await res.json();
  return (data?.hotels ?? [])
    .map((h) => {
      const b = h.hotelBasicInfo ?? {};
      const room = h.roomInfo?.[0];
      return {
        hotelNo: b.hotelNo,
        name: b.hotelName,
        price: room?.dailyCharge?.total,
        url: b.hotelInformationUrl || b.planListUrl || null,
      };
    })
    .filter((h) => h.hotelNo != null);
}

/**
 * 指定した地点周辺の実在ホテル一覧（名前・座標）を取得する（空室の有無を問わない、施設検索API）。
 * ・「①発見フェーズ」で実在するホテルの場所を集めるのに使う（件数は data.length で分かる）
 * ・満室のホテルも名前だけは表示したい（円クリックの一覧表示）ときにも使う
 * @param {{lat:number, lng:number, radiusKm:number}} cell
 * @param {{appId:string, accessKey:string, affiliateId?:string}} creds
 * @returns {Promise<{hotelNo:number, name:string, lat:number, lng:number}[]>}
 */
export async function fetchHotelFacilities(cell, creds) {
  const params = new URLSearchParams({
    applicationId: creds.appId,
    accessKey: creds.accessKey,
    format: "json",
    formatVersion: "2",
    datumType: "1",
    latitude: String(cell.lat),
    longitude: String(cell.lng),
    searchRadius: String(cell.radiusKm),
    hits: "30",
    responseType: "small",
    elements: "hotelNo,hotelName,latitude,longitude",
  });
  if (creds.affiliateId) {
    params.set("affiliateId", creds.affiliateId);
  }

  const res = await fetch(`${SIMPLE_HOTEL_ENDPOINT}?${params.toString()}`, { headers: refererHeaders(creds) });
  if (res.status === 404) return [];
  if (res.status === 429) throw new RakutenRateLimitError("rakuten API rate limited (429)");
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`rakuten API error ${res.status}: ${body}`);
  }
  const data = await res.json();
  return (data?.hotels ?? [])
    .map((h) => {
      const b = h.hotelBasicInfo ?? {};
      return { hotelNo: b.hotelNo, name: b.hotelName, lat: b.latitude, lng: b.longitude };
    })
    .filter((h) => h.hotelNo != null && Number.isFinite(h.lat) && Number.isFinite(h.lng));
}

/**
 * 指定したクレデンシャルが楽天APIで使えるか検証する（設定画面のキーテストに使用）。
 * 東京駅周辺の小さな範囲で施設検索を1回だけ呼び、エラーなしでレスポンスが返ればOK。
 * @returns {Promise<{ok:boolean, count?:number, status?:number, message?:string}>}
 */
export async function validateCredentials(creds) {
  const params = new URLSearchParams({
    applicationId: creds.appId,
    accessKey: creds.accessKey,
    format: "json",
    formatVersion: "2",
    datumType: "1",
    latitude: "35.6809",
    longitude: "139.7671",
    searchRadius: "0.1",
    hits: "1",
    responseType: "small",
    elements: "hotelNo",
  });

  try {
    const res = await fetch(`${SIMPLE_HOTEL_ENDPOINT}?${params.toString()}`, { headers: refererHeaders(creds) });
    if (res.status === 404) return { ok: true, count: 0 };
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      return { ok: false, status: res.status, message: body.slice(0, 300) };
    }
    const data = await res.json();
    return { ok: true, count: data?.pagingInfo?.recordCount ?? 0 };
  } catch (err) {
    return { ok: false, message: String(err) };
  }
}

// 楽天API側の「アプリ登録」で設定したApplication URLとの照合用にReferer/Originヘッダーを付ける。
// Workerからのサーバー間fetchはブラウザと違い自動で付かないため明示的に指定する。
// 実機検証済み: Refererだけでは REQUEST_CONTEXT_BODY_HTTP_REFERRER_MISSING (403) になり、
// Originを併せて送ることで解消する（2026年2月頃の楽天ウェブサービスAPI移行で必須化されたとみられる）。
function refererHeaders(creds) {
  if (!creds?.referer) return {};
  const headers = { Referer: creds.referer };
  try {
    headers.Origin = new URL(creds.referer).origin;
  } catch {
    // referer が不正なURL形式なら Origin は付けない（Refererのみで送る）
  }
  return headers;
}

function addDays(dateStr, days) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
