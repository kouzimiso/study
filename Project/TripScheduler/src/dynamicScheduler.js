'use strict';

/**
 * 動的に取得したスポット（src/overpassSpots.js の findSpotsAround() の戻り値）から、
 * 中心地点を起点にした1日分のタイムライン（TripSchedulerのイベント配列形式）を
 * 自動生成する。`buildDaySchedule.js` は事前定義されたRoute用、こちらは
 * 「地点を指定したら動的に周辺スポットから組む」用。
 * Node.js/ブラウザ両対応のUMD形式（依存する2モジュールもブラウザでは
 * window.TripSchedulerBuildDaySchedule / window.TripSchedulerOverpassSpots
 * として先に読み込んでおく必要がある）。
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory(require('./buildDaySchedule'), require('./overpassSpots'));
  } else {
    root.TripSchedulerDynamicScheduler = factory(root.TripSchedulerBuildDaySchedule, root.TripSchedulerOverpassSpots);
  }
})(typeof self !== 'undefined' ? self : this, function (buildDayScheduleMod, overpassSpotsMod) {
  'use strict';

  const { addMinutes } = buildDayScheduleMod;
  const { haversineMeters } = overpassSpotsMod;

  const TRAVEL_SPEED_KMH = { walk: 4, bike: 12, car: 25 };
  const STAY_MINUTES = { sightseeing: 60, food: 60, wifi: 45, onsen: 90 };
  const DEFAULT_MAX_BY_TYPE = { sightseeing: 3, food: 1, wifi: 1, onsen: 1 };

/**
 * @param {number} distanceMeters
 * @param {'walk'|'bike'|'car'} mode
 * @returns {number} 分（最低5分）
 */
function estimateTravelMinutes(distanceMeters, mode = 'car') {
  const speed = TRAVEL_SPEED_KMH[mode] || TRAVEL_SPEED_KMH.car;
  const hours = distanceMeters / 1000 / speed;
  return Math.max(5, Math.round(hours * 60));
}

/**
 * カテゴリごとの上限件数を守りつつ、中心から近い順にスポットを選ぶ。
 * @param {object[]} spots findSpotsAround() の戻り値
 * @param {{maxByType?: Record<string, number>}} [options]
 * @returns {object[]}
 */
function selectSpotsForDay(spots, options = {}) {
  const maxByType = { ...DEFAULT_MAX_BY_TYPE, ...(options.maxByType || {}) };
  const countByType = {};
  const selected = [];

  [...spots]
    .sort((a, b) => a.distanceMeters - b.distanceMeters)
    .forEach((spot) => {
      const max = maxByType[spot.type] ?? 0;
      const count = countByType[spot.type] || 0;
      if (count >= max) return;
      selected.push(spot);
      countByType[spot.type] = count + 1;
    });

  return selected;
}

/**
 * 中心地点から最近傍法で巡回順序を決める（厳密なTSPではなく実用十分な近似）。
 * @param {{lat:number, lng:number}} center
 * @param {object[]} spots
 * @returns {object[]}
 */
function orderSpotsGreedy(center, spots) {
  const remaining = [...spots];
  const ordered = [];
  let current = center;
  while (remaining.length) {
    let bestIdx = 0;
    let bestDist = Infinity;
    remaining.forEach((spot, idx) => {
      const d = haversineMeters(current.lat, current.lng, spot.lat, spot.lng);
      if (d < bestDist) {
        bestDist = d;
        bestIdx = idx;
      }
    });
    const next = remaining.splice(bestIdx, 1)[0];
    ordered.push(next);
    current = next;
  }
  return ordered;
}

function makeEvent(date, start, end, title, location, description, category, spotId) {
  return { date, start, end, title, location, description, category, spotId: spotId || undefined };
}

/**
 * 中心地点と選定済みスポットから、1日分のタイムラインを生成する。
 * 「中心→スポット1→スポット2→…→中心に戻る」の順に、移動時間を直線距離から
 * 概算（`mode`の速度換算）し、各スポットの滞在時間（種別ごとの目安）を積む。
 *
 * @param {{lat:number, lng:number, name?:string}} center
 * @param {string} date "YYYY-MM-DD"
 * @param {object[]} spots selectSpotsForDay() 等で選んだスポット配列
 * @param {{startTime?: string, mode?: 'walk'|'bike'|'car', returnToCenter?: boolean}} [options]
 * @returns {object[]} TripSchedulerのイベント配列形式
 */
function buildDynamicDaySchedule(center, date, spots, options = {}) {
  const startTime = options.startTime || '09:00';
  const mode = options.mode || 'car';
  const returnToCenter = options.returnToCenter !== false;
  const ordered = orderSpotsGreedy(center, spots);

  const events = [];
  let cursor = startTime;
  let currentPoint = center;
  let currentLabel = center.name || '出発地点';

  ordered.forEach((spot) => {
    const dist = haversineMeters(currentPoint.lat, currentPoint.lng, spot.lat, spot.lng);
    const travelMin = estimateTravelMinutes(dist, mode);
    events.push(
      makeEvent(date, cursor, addMinutes(cursor, travelMin), `${currentLabel}→${spot.name} 移動`, '', '', 'move', null)
    );
    cursor = addMinutes(cursor, travelMin);

    const stayMin = STAY_MINUTES[spot.type] || 60;
    const description = spot.hours ? `営業時間: ${spot.hours}` : '';
    events.push(makeEvent(date, cursor, addMinutes(cursor, stayMin), spot.name, '', description, spot.type, spot.id));
    cursor = addMinutes(cursor, stayMin);

    currentPoint = spot;
    currentLabel = spot.name;
  });

  if (returnToCenter && ordered.length > 0) {
    const backDist = haversineMeters(currentPoint.lat, currentPoint.lng, center.lat, center.lng);
    const backMin = estimateTravelMinutes(backDist, mode);
    events.push(
      makeEvent(date, cursor, addMinutes(cursor, backMin), `${currentLabel}→${center.name || '出発地点'} 移動`, '', '', 'move', null)
    );
  }

  return events;
}

  return {
    estimateTravelMinutes,
    selectSpotsForDay,
    orderSpotsGreedy,
    buildDynamicDaySchedule,
  };
});
