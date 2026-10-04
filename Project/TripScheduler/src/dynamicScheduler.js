'use strict';

/**
 * 出発地〜目的地（from→to）と、その間に選んだ立ち寄り先（stops）から、
 * 1日分のタイムライン（TripSchedulerのイベント配列形式）を自動生成する。
 * `buildDaySchedule.js` は事前定義されたRoute（`data/routes.json`）用、
 * こちらは「ルートプランナーのように出発地〜目的地を指定し、その沿線の
 * 候補から選んだ立ち寄り先」を時間割に展開する用。
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

function makeEvent(date, start, end, title, location, description, category, spotId) {
  return { date, start, end, title, location, description, category, spotId: spotId || undefined };
}

/**
 * 出発地〜目的地と、ルート上の順序で並んだ立ち寄り先（stops）から、1日分の
 * タイムラインを生成する。「出発地→スポット1→…→スポットN→目的地」の順に、
 * 移動時間を直線距離から概算（`mode`の速度換算）し、各スポットの滞在時間
 * （種別ごとの目安）を積む。出発地と目的地が同じ地点に戻ってくる前提は
 * 置かない（往復ルートなら呼び出し側で from===to を渡せばよい）。
 *
 * @param {{lat:number, lng:number, name?:string}} from
 * @param {{lat:number, lng:number, name?:string}} to
 * @param {string} date "YYYY-MM-DD"
 * @param {object[]} stops ルート上の順序で並んだ立ち寄り先配列
 *   （`id`/`name`/`lat`/`lng`/`type`/`hours`を持つ）
 * @param {{startTime?: string, mode?: 'walk'|'bike'|'car'}} [options]
 * @returns {object[]} TripSchedulerのイベント配列形式
 */
function buildRouteSchedule(from, to, date, stops, options = {}) {
  const startTime = options.startTime || '09:00';
  const mode = options.mode || 'car';

  const events = [];
  let cursor = startTime;
  let currentPoint = from;
  let currentLabel = from.name || '出発地点';

  (stops || []).forEach((spot) => {
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

  const finalDist = haversineMeters(currentPoint.lat, currentPoint.lng, to.lat, to.lng);
  const finalMin = estimateTravelMinutes(finalDist, mode);
  events.push(
    makeEvent(date, cursor, addMinutes(cursor, finalMin), `${currentLabel}→${to.name || '目的地'} 移動`, '', '', 'move', null)
  );

  return events;
}

  return {
    estimateTravelMinutes,
    buildRouteSchedule,
  };
});
