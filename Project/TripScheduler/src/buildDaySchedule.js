'use strict';

/**
 * 1つのRoute（data/routes.json の要素）から、1日分のタイムライン
 * （TripSchedulerのイベント配列形式）を自動生成する。
 * これまでSILVER_WEEK_2026_PLAN.mdで手作業で行っていた「Routeの
 * highlights/foodStops/onsenStops/wifiPowerStopsを時間割に組む」部分を
 * ロジック化したもの（DESIGN.md Phase5）。
 *
 * 厳密な最適化ではなく、実用十分な近似解を返す：
 *   往路移動 → 観光(highlights) → （中間で昼食） → 温泉 → Wifi電源休憩 → 帰路移動
 *
 * Node.js（CommonJS）とブラウザ（<script>での直接読み込み、
 * window.TripSchedulerBuildDaySchedule）の両方で使えるUMD形式。
 * ブラウザでの利用は index.html（src/buildIndexHtml.js が生成）の
 * 「現地プラン作成」タブから。
 */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = mod;
  else root.TripSchedulerBuildDaySchedule = mod;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const DEFAULT_TRAVEL_MINUTES = 60;
const FOOD_MINUTES = 60;
const ONSEN_MINUTES = 120;
const WORK_MINUTES = 60;
const INTER_STOP_MINUTES = 15;
const MIN_HIGHLIGHT_MINUTES = 30;

/**
 * "約1時間"/"約40分"/"約1時間半〜"のような文字列から分数を推定する。
 * @param {string} text
 * @param {number} fallback
 * @returns {number}
 */
function parseTravelMinutes(text, fallback = DEFAULT_TRAVEL_MINUTES) {
  if (!text) return fallback;
  let minutes = 0;
  const hourMatch = text.match(/(\d+)\s*時間/);
  if (hourMatch) minutes += parseInt(hourMatch[1], 10) * 60;
  if (/半/.test(text)) minutes += 30;
  const minMatch = text.match(/(\d+)\s*分/);
  if (minMatch) minutes += parseInt(minMatch[1], 10);
  return minutes || fallback;
}

/**
 * "HH:MM" に分を加算する（24時を超える場合は翌日に繰り込まれるが、
 * 旅程1日の範囲内で使う想定のため折り返しは行わない）。
 * @param {string} time "HH:MM"
 * @param {number} minutes
 * @returns {string} "HH:MM"
 */
function addMinutes(time, minutes) {
  const [h, m] = time.split(':').map(Number);
  const total = h * 60 + m + minutes;
  const hh = Math.floor(total / 60);
  const mm = total % 60;
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
}

function makeEvent(date, start, end, title, location, description, category, routeId) {
  return { date, start, end, title, location, description, category, routeId };
}

/**
 * @param {object} route data/routes.json の1要素
 * @param {string} date "YYYY-MM-DD"
 * @param {{startTime?: string, interStopMinutes?: number}} [options]
 * @returns {object[]} TripSchedulerのイベント配列形式
 */
function buildDaySchedule(route, date, options = {}) {
  const startTime = options.startTime || '09:00';
  const interStopMinutes = options.interStopMinutes ?? INTER_STOP_MINUTES;
  const travelMinutes = parseTravelMinutes(route.accessFromOfuna && route.accessFromOfuna.car);
  const destLabel = (route.name || '').replace(/[　\s]*ルート.*$/, '').trim() || route.name;

  const events = [];
  let cursor = startTime;

  events.push(
    makeEvent(
      date,
      cursor,
      addMinutes(cursor, travelMinutes),
      `大船→${destLabel} 移動`,
      (route.accessFromOfuna && route.accessFromOfuna.car) || '',
      '',
      'move',
      route.id
    )
  );
  cursor = addMinutes(cursor, travelMinutes);

  const foodStop = route.foodStops && route.foodStops[0];
  const onsenStop = route.onsenStops && route.onsenStops[0];
  const workStop = route.wifiPowerStops && route.wifiPowerStops[0];
  const fixedTotal =
    (foodStop ? FOOD_MINUTES : 0) + (onsenStop ? ONSEN_MINUTES : 0) + (workStop ? WORK_MINUTES : 0);

  const highlights = route.highlights || [];
  const totalMinutes = (route.recommendedDurationHours || 6) * 60;
  const sightseeingBudget = Math.max(
    totalMinutes - travelMinutes * 2 - fixedTotal,
    highlights.length * MIN_HIGHLIGHT_MINUTES
  );
  const perHighlight = highlights.length
    ? Math.max(MIN_HIGHLIGHT_MINUTES, Math.floor(sightseeingBudget / highlights.length))
    : 0;
  const midpoint = Math.max(1, Math.ceil(highlights.length / 2));

  highlights.forEach((highlight, index) => {
    events.push(makeEvent(date, cursor, addMinutes(cursor, perHighlight), highlight, '', '', 'sightseeing', route.id));
    cursor = addMinutes(cursor, perHighlight);

    if (index === midpoint - 1 && foodStop) {
      events.push(
        makeEvent(date, cursor, addMinutes(cursor, FOOD_MINUTES), foodStop.name, '', foodStop.note || '', 'food', route.id)
      );
      cursor = addMinutes(cursor, FOOD_MINUTES);
    } else if (index < highlights.length - 1) {
      cursor = addMinutes(cursor, interStopMinutes);
    }
  });

  // highlightsが無いためfoodStopがまだ挟まれていない場合はここで入れる
  if (foodStop && !highlights.length) {
    events.push(
      makeEvent(date, cursor, addMinutes(cursor, FOOD_MINUTES), foodStop.name, '', foodStop.note || '', 'food', route.id)
    );
    cursor = addMinutes(cursor, FOOD_MINUTES);
  }

  if (onsenStop) {
    events.push(
      makeEvent(date, cursor, addMinutes(cursor, ONSEN_MINUTES), onsenStop.name, '', onsenStop.note || '', 'onsen', route.id)
    );
    cursor = addMinutes(cursor, ONSEN_MINUTES);
  }

  if (workStop) {
    events.push(
      makeEvent(date, cursor, addMinutes(cursor, WORK_MINUTES), workStop.name, '', workStop.note || '', 'work', route.id)
    );
    cursor = addMinutes(cursor, WORK_MINUTES);
  }

  events.push(makeEvent(date, cursor, addMinutes(cursor, travelMinutes), '帰路につく', '', '', 'move', route.id));

  return events;
}

  return {
    parseTravelMinutes,
    addMinutes,
    buildDaySchedule,
  };
});
