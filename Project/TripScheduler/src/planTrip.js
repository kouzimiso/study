#!/usr/bin/env node
'use strict';

/**
 * ルート選定（selectRoutesForTrip）と日内スケジューリング（buildDaySchedule）を
 * つないで、N日分の旅程イベント配列を一括生成するCLI。
 * 出力はそのまま src/generateIcs.js / src/toGanttPlanList.js に渡せる形式。
 *
 * 使い方:
 *   node src/planTrip.js 3
 *   node src/planTrip.js 3 --start-date=2026-09-21 --out=data/my-trip.json
 *   node src/planTrip.js 3 --max-crowd-risk=low --exclude=atsugi-onsenkyo
 */

const fs = require('fs');
const path = require('path');
const { selectRoutesForTrip } = require('./selectRoutes');
const { buildDaySchedule } = require('./buildDaySchedule');

function parseArgs(argv) {
  const positional = [];
  const options = {};
  argv.forEach((arg) => {
    const match = arg.match(/^--([^=]+)=(.*)$/);
    if (match) {
      options[match[1]] = match[2];
    } else {
      positional.push(arg);
    }
  });
  return { positional, options };
}

function addDays(dateStr, days) {
  // "YYYY-MM-DD" はローカルタイムゾーンの影響を受けないよう、常にUTC基準で演算する
  // （+09:00 のオフセットを経由すると日付が前日にずれるため使わない）。
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/**
 * @param {object[]} routes data/routes.json
 * @param {{routeId: string, visitedOn: string}[]} visitHistory data/visitHistory.json
 * @param {number} days
 * @param {{startDate?: string, dayStartTime?: string, maxCrowdRisk?: string,
 *   excludeIds?: string[], today?: Date}} [options]
 * @returns {{events: object[], selection: object[]}}
 */
function planTrip(routes, visitHistory, days, options = {}) {
  const startDate = options.startDate || addDays(new Date().toISOString().slice(0, 10), 1);
  const selection = selectRoutesForTrip(routes, visitHistory, days, {
    today: options.today,
    maxCrowdRisk: options.maxCrowdRisk,
    excludeIds: options.excludeIds,
  });

  const events = selection.flatMap((entry, index) => {
    const date = addDays(startDate, index);
    return buildDaySchedule(entry.route, date, { startTime: options.dayStartTime });
  });

  return { events, selection };
}

function main() {
  const { positional, options } = parseArgs(process.argv.slice(2));
  const days = parseInt(positional[0], 10) || 3;

  const routes = require(path.resolve(__dirname, '..', 'data', 'routes.json'));
  const visitHistory = require(path.resolve(__dirname, '..', 'data', 'visitHistory.json'));

  const { events, selection } = planTrip(routes, visitHistory, days, {
    startDate: options['start-date'],
    dayStartTime: options['day-start-time'],
    maxCrowdRisk: options['max-crowd-risk'],
    excludeIds: options.exclude ? options.exclude.split(',') : undefined,
  });

  console.error('選定されたルート:');
  selection.forEach((entry, index) => {
    console.error(`  Day${index + 1}: ${entry.route.name}（${entry.reason}）`);
  });

  const outPath = options.out ? path.resolve(options.out) : null;
  const json = JSON.stringify(events, null, 2);
  if (outPath) {
    fs.writeFileSync(outPath, json, 'utf8');
    console.error(`生成しました: ${outPath}`);
  } else {
    console.log(json);
  }
}

if (require.main === module) {
  main();
}

module.exports = { planTrip, addDays };
