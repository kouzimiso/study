'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { daysSinceLastVisit, selectRoutesForTrip } = require('../src/selectRoutes');

const sampleRoutes = [
  { id: 'a', name: 'ルートA', crowdRisk: 'low' },
  { id: 'b', name: 'ルートB', crowdRisk: 'medium' },
  { id: 'c', name: 'ルートC', crowdRisk: 'high' },
  { id: 'd', name: 'ルートD', crowdRisk: 'low' },
];

test('daysSinceLastVisit: 未訪問はInfinityを返す', () => {
  assert.equal(daysSinceLastVisit(sampleRoutes[0], [], new Date('2026-09-20')), Infinity);
});

test('daysSinceLastVisit: 最終訪問日からの経過日数を返す', () => {
  const history = [{ routeId: 'a', visitedOn: '2026-09-10' }];
  assert.equal(daysSinceLastVisit(sampleRoutes[0], history, new Date('2026-09-20')), 10);
});

test('daysSinceLastVisit: 複数回訪問している場合は最新の訪問日を使う', () => {
  const history = [
    { routeId: 'a', visitedOn: '2026-01-01' },
    { routeId: 'a', visitedOn: '2026-09-15' },
  ];
  assert.equal(daysSinceLastVisit(sampleRoutes[0], history, new Date('2026-09-20')), 5);
});

test('selectRoutesForTrip: crowdRisk=highはデフォルトで除外される', () => {
  const selected = selectRoutesForTrip(sampleRoutes, [], 4, { today: new Date('2026-09-20') });
  assert.ok(!selected.some((s) => s.route.id === 'c'));
});

test('selectRoutesForTrip: 未訪問のルートが訪問済みより優先される', () => {
  const history = [{ routeId: 'a', visitedOn: '2020-01-01' }]; // 大昔に訪問済み
  const selected = selectRoutesForTrip(sampleRoutes, history, 1, { today: new Date('2026-09-20') });
  // b, d は未訪問（Infinity）なので、大昔に訪問した a より先に選ばれる
  assert.notEqual(selected[0].route.id, 'a');
});

test('selectRoutesForTrip: 訪問済み同士では経過日数が長い方が優先される', () => {
  const history = [
    { routeId: 'a', visitedOn: '2026-09-01' }, // 19日前
    { routeId: 'b', visitedOn: '2026-09-15' }, // 5日前
    { routeId: 'd', visitedOn: '2026-09-18' }, // 2日前
  ];
  const selected = selectRoutesForTrip(sampleRoutes, history, 3, { today: new Date('2026-09-20') });
  assert.deepEqual(
    selected.map((s) => s.route.id),
    ['a', 'b', 'd']
  );
});

test('selectRoutesForTrip: excludeIdsで明示的に除外できる', () => {
  const selected = selectRoutesForTrip(sampleRoutes, [], 4, {
    today: new Date('2026-09-20'),
    excludeIds: ['a'],
  });
  assert.ok(!selected.some((s) => s.route.id === 'a'));
});

test('selectRoutesForTrip: 実データ(routes.json/visitHistory.json)で3日分を選べる', () => {
  // eslint-disable-next-line global-require
  const routes = require('../data/routes.json');
  // eslint-disable-next-line global-require
  const visitHistory = require('../data/visitHistory.json');
  const selected = selectRoutesForTrip(routes, visitHistory, 3, { today: new Date('2026-09-20') });
  assert.equal(selected.length, 3);
  // サンプル履歴にある三崎・城ヶ島(crowdRisk:high)はそもそも除外対象
  assert.ok(!selected.some((s) => s.route.id === 'misaki-jogashima'));
});
