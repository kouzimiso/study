#!/usr/bin/env node
'use strict';

/**
 * TripSchedulerのイベント配列（date, start, end, title, location, description,
 * category, routeId）を、WebGantt（Project/WebGantt）の PlanList JSON形式に
 * 変換する。同じ旅程データから .ics（カレンダー）と PlanList（ガントチャート）の
 * 両方を作れるようにするためのアダプタ。
 *
 * PlanList仕様（Project/WebGantt/README.md 準拠）：
 *   { "<Plan名>": { name, type, task_kind, priority, text,
 *       schedule: { start, end, completion },
 *       todo: [ { name, type, complete, status, start, end, text }, ... ] } }
 */

const fs = require('fs');
const path = require('path');

const CATEGORY_TYPE = {
  move: 'move',
  food: 'food',
  onsen: 'onsen',
  work: 'work',
  sightseeing: 'sightseeing',
};

function toPlanListDateTime(date, time) {
  return `${date} ${time}`;
}

function groupByDate(events) {
  const map = new Map();
  events.forEach((event) => {
    if (!map.has(event.date)) map.set(event.date, []);
    map.get(event.date).push(event);
  });
  return map;
}

/**
 * @param {object[]} events TripScheduler形式のイベント配列
 * @param {{routes?: object[]}} [options] routes を渡すと、各日のPlan名に
 *   ルート名を反映し、ルートの notes を Plan の text に載せる
 * @returns {object} PlanList JSON（WebGanttにそのまま読み込める形式）
 */
function convertEventsToGanttPlanList(events, options = {}) {
  const routes = options.routes || [];
  const routeById = new Map(routes.map((route) => [route.id, route]));
  const grouped = groupByDate(events);
  const planList = {};

  for (const [date, dayEvents] of grouped) {
    const sorted = [...dayEvents].sort((a, b) => a.start.localeCompare(b.start));
    const routeId = sorted[0] && sorted[0].routeId;
    const route = routeId ? routeById.get(routeId) : null;
    const planName = route ? `${route.name}（${date}）` : `旅程（${date}）`;

    const todo = sorted.map((event) => ({
      name: event.title,
      type: CATEGORY_TYPE[event.category] || 'sightseeing',
      complete: false,
      status: 'todo',
      start: toPlanListDateTime(event.date, event.start),
      end: toPlanListDateTime(event.date, event.end),
      text: [event.location, event.description].filter(Boolean).join(' / '),
    }));

    planList[planName] = {
      name: planName,
      type: 'todo',
      task_kind: 'human',
      priority: 'normal',
      text: route ? route.notes || '' : '',
      schedule: {
        start: toPlanListDateTime(date, sorted[0].start),
        end: toPlanListDateTime(date, sorted[sorted.length - 1].end),
        completion: '',
      },
      todo,
    };
  }

  return planList;
}

function main() {
  const [, , inputArg, outputArg, routesArg] = process.argv;
  if (!inputArg) {
    console.error('使い方: node src/toGanttPlanList.js <イベントJSON> [出力.json] [routes.json]');
    process.exitCode = 1;
    return;
  }
  const inputPath = path.resolve(inputArg);
  const events = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const routes = routesArg ? JSON.parse(fs.readFileSync(path.resolve(routesArg), 'utf8')) : [];

  const planList = convertEventsToGanttPlanList(events, { routes });
  const outputPath = path.resolve(outputArg || inputPath.replace(/\.json$/, '.planlist.json'));
  fs.writeFileSync(outputPath, JSON.stringify(planList, null, 2), 'utf8');
  console.log(`生成しました: ${outputPath}`);
}

if (require.main === module) {
  main();
}

module.exports = { convertEventsToGanttPlanList };
