// 楽天トラベル空室検索API（VacantHotelSearch）のクライアント。
// ドキュメント: https://webservice.rakuten.co.jp/documentation/vacant-hotel-search
//
// 注意点：
// - accessKey が必須（applicationId とは別に必要）
// - 緯度経度はデフォルトだと日本測地系・秒単位になるため、必ず datumType=1 を指定して
//   世界測地系（WGS84）・度単位で扱う
// - searchRadius は 0.1〜3.0km（小数点以下1桁まで）
// - hits=1 にして pagingInfo.recordCount だけを見れば、ヒット施設数の把握には十分
//   （レスポンス量を抑えてAPI呼び出しコストを下げる）

const ENDPOINT =
  "https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426";

/**
 * 指定したグリッドセル・日付で空室のある施設数を取得する。
 * @param {{lat:number, lng:number, radiusKm:number}} cell
 * @param {string} checkinDate - 'YYYY-MM-DD'
 * @param {{RAKUTEN_APP_ID:string, RAKUTEN_ACCESS_KEY:string, RAKUTEN_AFFILIATE_ID?:string}} env
 * @returns {Promise<number>} recordCount（空室のある施設数）。0件時やエラー時は0を返す。
 */
export async function fetchVacantHotelCount(cell, checkinDate, env) {
  const checkout = addDays(checkinDate, 1);

  const params = new URLSearchParams({
    applicationId: env.RAKUTEN_APP_ID,
    accessKey: env.RAKUTEN_ACCESS_KEY,
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
  if (env.RAKUTEN_AFFILIATE_ID) {
    params.set("affiliateId", env.RAKUTEN_AFFILIATE_ID);
  }

  const res = await fetch(`${ENDPOINT}?${params.toString()}`);

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

export class RakutenRateLimitError extends Error {}

const SIMPLE_HOTEL_ENDPOINT =
  "https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731";

/**
 * 指定座標・半径内にあるホテルNoの一覧を取得する（施設検索API、空室有無は問わない）。
 * 「周辺のホテル構成が前回と変わっていないか」を確認するための軽量チェックに使う。
 * @returns {Promise<number[]>} ソート済みhotelNo配列
 */
export async function fetchNearbyHotelNos(lat, lng, radiusKm, env) {
  const params = new URLSearchParams({
    applicationId: env.RAKUTEN_APP_ID,
    accessKey: env.RAKUTEN_ACCESS_KEY,
    format: "json",
    formatVersion: "2",
    datumType: "1",
    latitude: String(lat),
    longitude: String(lng),
    searchRadius: String(radiusKm),
    hits: "30",
    responseType: "small",
    elements: "hotelNo",
  });

  const res = await fetch(`${SIMPLE_HOTEL_ENDPOINT}?${params.toString()}`);
  if (res.status === 404) return [];
  if (res.status === 429) throw new RakutenRateLimitError("rakuten API rate limited (429)");
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`rakuten API error ${res.status}: ${body}`);
  }
  const data = await res.json();
  const nos = (data?.hotels ?? []).map((h) => (h.hotelBasicInfo ?? h).hotelNo);
  return nos.sort((a, b) => a - b);
}

function addDays(dateStr, days) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** 単純なsleep（レート制限対策でリクエスト間隔をあけるため） */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
