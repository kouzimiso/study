'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { planTrip, addDays } = require('../src/planTrip');

const sampleRoutes = [
  {
    id: 'a',
    name: 'ルートA',
    crowdRisk: 'low',
    areaDirection: '東',
    accessFromOfuna: { car: '約30分' },
    highlights: ['見どころA'],
    recommendedDurationHours: 4,
  },
  {
    id: 'b',
    name: 'ルートB',
    crowdRisk: 'low',
    areaDirection: '西',
    accessFromOfuna: { car: '約40分' },
    highlights: ['見どころB'],
    recommendedDurationHours: 4,
  },
];

test('addDays: 日付をN日進める', () => {
  assert.equal(addDays('2026-09-21', 1), '2026-09-22');
  assert.equal(addDays('2026-09-21', 2), '2026-09-23');
});

test('planTrip: 選定したルート数だけ連続した日付にイベントが割り当てられる', () => {
  const { events, selection } = planTrip(sampleRoutes, [], 2, {
    startDate: '2026-09-21',
    today: new Date('2026-09-20'),
  });
  assert.equal(selection.length, 2);
  const dates = [...new Set(events.map((e) => e.date))];
  assert.deepEqual(dates, ['2026-09-21', '2026-09-22']);
});

test('planTrip: 生成イベントはgenerateIcs/toGanttPlanListが要求するフィールドを持つ', () => {
  const { events } = planTrip(sampleRoutes, [], 2, {
    startDate: '2026-09-21',
    today: new Date('2026-09-20'),
  });
  events.forEach((e) => {
    assert.ok(e.date && e.start && e.end && e.title);
    assert.ok('category' in e);
    assert.ok('routeId' in e);
  });
});

test('planTrip: 実データ(data/routes.json, data/visitHistory.json)で3日分を生成できる', () => {
  // eslint-disable-next-line global-require
  const routes = require('../data/routes.json');
  // eslint-disable-next-line global-require
  const visitHistory = require('../data/visitHistory.json');
  const { events, selection } = planTrip(routes, visitHistory, 3, {
    startDate: '2026-09-21',
    today: new Date('2026-09-20'),
  });
  assert.equal(selection.length, 3);
  assert.ok(events.length > 0);
});
