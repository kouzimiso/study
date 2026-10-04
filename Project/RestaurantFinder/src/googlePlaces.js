'use strict';

/**
 * Google Places API (New) との連携。
 *
 * 注意：Places API (New) の Place Details は `reviews` を最大5件までしか
 * 返さない仕様上の制限がある。そのため EVALUATION_CRITERIA.md にある
 * 「バースト検知」「二極化検知」は、取得できた最大5件のサンプルに基づく
 * 参考値であり、全レビューの統計ではない点に注意。より精度を上げるには
 * 別途スクレイピングや他データソースとの併用が必要（利用規約を確認のこと）。
 *
 * 参照: https://developers.google.com/maps/documentation/places/web-service/place-details
 */

const PLACES_API_BASE = 'https://places.googleapis.com/v1';

const SEARCH_FIELD_MASK = [
  'places.id',
  'places.displayName',
  'places.rating',
  'places.userRatingCount',
  'places.priceLevel',
  'places.googleMapsUri',
  'places.location',
].join(',');

const DETAILS_FIELD_MASK = [
  'id',
  'displayName',
  'rating',
  'userRatingCount',
  'priceLevel',
  'reviews',
  'googleMapsUri',
  'location',
].join(',');

/**
 * @param {string} query 例: "渋谷 ラーメン"
 * @param {string} apiKey Google Cloud の Places API キー
 * @param {{languageCode?: string, fetchImpl?: typeof fetch}} [options]
 * @returns {Promise<object[]>} places 配列（id, displayName, rating, userRatingCount, priceLevel, googleMapsUri）
 */
async function searchRestaurants(query, apiKey, options = {}) {
  if (!apiKey) throw new Error('Google Places API key is required');
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) throw new Error('fetch is not available in this environment');

  const res = await fetchImpl(`${PLACES_API_BASE}/places:searchText`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Goog-Api-Key': apiKey,
      'X-Goog-FieldMask': SEARCH_FIELD_MASK,
    },
    body: JSON.stringify({
      textQuery: query,
      languageCode: options.languageCode || 'ja',
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Places searchText failed: ${res.status} ${body}`);
  }
  const data = await res.json();
  return data.places || [];
}

/**
 * 指定 place の詳細（レビュー最大5件を含む）を取得する。
 * @param {string} placeId
 * @param {string} apiKey
 * @param {{languageCode?: string, fetchImpl?: typeof fetch}} [options]
 * @returns {Promise<object>} place 詳細
 */
async function getPlaceDetails(placeId, apiKey, options = {}) {
  if (!apiKey) throw new Error('Google Places API key is required');
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) throw new Error('fetch is not available in this environment');

  const res = await fetchImpl(`${PLACES_API_BASE}/places/${encodeURIComponent(placeId)}`, {
    method: 'GET',
    headers: {
      'X-Goog-Api-Key': apiKey,
      'X-Goog-FieldMask': DETAILS_FIELD_MASK,
      'Accept-Language': options.languageCode || 'ja',
    },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Place Details failed: ${res.status} ${body}`);
  }
  return res.json();
}

/**
 * Places API (New) のレスポンス形式を、scoring.js が期待する
 * { rating, reviewCount, reviews: [{text, rating, date}] } 形式に変換する。
 * @param {object} placeDetails getPlaceDetails() の戻り値
 * @returns {object}
 */
function toScoringInput(placeDetails) {
  const reviews = (placeDetails.reviews || []).map((review) => ({
    text: review.text && review.text.text ? review.text.text : '',
    rating: review.rating,
    date: review.publishTime,
  }));

  return {
    id: placeDetails.id,
    name: placeDetails.displayName ? placeDetails.displayName.text : placeDetails.id,
    rating: placeDetails.rating || 0,
    reviewCount: placeDetails.userRatingCount || 0,
    priceLevel: placeDetails.priceLevel,
    googleMapsUri: placeDetails.googleMapsUri,
    lat: placeDetails.location ? placeDetails.location.latitude : undefined,
    lng: placeDetails.location ? placeDetails.location.longitude : undefined,
    reviews,
  };
}

module.exports = {
  searchRestaurants,
  getPlaceDetails,
  toScoringInput,
};
