'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { convertEventsToGanttPlanList } = require('../src/toGanttPlanList');

const sampleEvents = [
  {
    date: '2026-09-21',
    start: '09:00',
    end: '10:00',
    title: '真鶴岬散策',
    location: '真鶴岬',
    description: '絶景',
    category: 'sightseeing',
    routeId: 'manazuru-yugawara',
  },
  {
    date: '2026-09-21',
    start: '10:00',
    end: '11:00',
    title: '昼食',
    location: '真鶴港',
    description: '海鮮',
    category: 'food',
    routeId: 'manazuru-yugawara',
  },
  {
    date: '2026-09-22',
    start: '09:00',
    end: '10:00',
    title: '佐島散策',
    location: '佐島',
    description: '',
    category: 'sightseeing',
    routeId: 'miura-west-coast',
  },
];

const sampleRoutes = [
  { id: 'manazuru-yugawara', name: '真鶴・湯河原ルート', notes: '箱根より空いている' },
  { id: 'miura-west-coast', name: '三浦半島西海岸ルート', notes: '' },
];

test('convertEventsToGanttPlanList: 日付ごとに1つのPlanを作る', () => {
  const planList = convertEventsToGanttPlanList(sampleEvents);
  assert.equal(Object.keys(planList).length, 2);
});

test('convertEventsToGanttPlanList: Planのtodoにその日の全イベントが入る', () => {
  const planList = convertEventsToGanttPlanList(sampleEvents, { routes: sampleRoutes });
  const day1 = planList['真鶴・湯河原ルート（2026-09-21）'];
  assert.ok(day1);
  assert.equal(day1.todo.length, 2);
  assert.equal(day1.todo[0].name, '真鶴岬散策');
  assert.equal(day1.todo[0].start, '2026-09-21 09:00');
  assert.equal(day1.todo[0].end, '2026-09-21 10:00');
});

test('convertEventsToGanttPlanList: PlanのscheduleはPlanのアクセス開始・終了になる', () => {
  const planList = convertEventsToGanttPlanList(sampleEvents, { routes: sampleRoutes });
  const day1 = planList['真鶴・湯河原ルート（2026-09-21）'];
  assert.equal(day1.schedule.start, '2026-09-21 09:00');
  assert.equal(day1.schedule.end, '2026-09-21 11:00');
});

test('convertEventsToGanttPlanList: categoryがtodoのtypeに反映される', () => {
  const planList = convertEventsToGanttPlanList(sampleEvents, { routes: sampleRoutes });
  const day1 = planList['真鶴・湯河原ルート（2026-09-21）'];
  assert.equal(day1.todo[0].type, 'sightseeing');
  assert.equal(day1.todo[1].type, 'food');
});

test('convertEventsToGanttPlanList: routesを渡さない場合は汎用名になる', () => {
  const planList = convertEventsToGanttPlanList(sampleEvents);
  assert.ok(Object.keys(planList).some((name) => name.startsWith('旅程（')));
});

test('convertEventsToGanttPlanList: 各Planが仕様上必須のフィールドを持つ', () => {
  const planList = convertEventsToGanttPlanList(sampleEvents, { routes: sampleRoutes });
  Object.values(planList).forEach((plan) => {
    assert.equal(plan.type, 'todo');
    assert.ok('schedule' in plan);
    assert.ok(Array.isArray(plan.todo));
    plan.todo.forEach((t) => {
      assert.ok('name' in t);
      assert.ok('complete' in t);
      assert.ok('start' in t);
      assert.ok('end' in t);
    });
  });
});

test('convertEventsToGanttPlanList: 実データ(silver-week-2026.json/routes.json)を変換できる', () => {
  // eslint-disable-next-line global-require
  const events = require('../data/silver-week-2026.json');
  // eslint-disable-next-line global-require
  const routes = require('../data/routes.json');
  const planList = convertEventsToGanttPlanList(events, { routes });
  assert.equal(Object.keys(planList).length, 3); // 9/21, 9/22, 9/23
  const totalTodo = Object.values(planList).reduce((sum, plan) => sum + plan.todo.length, 0);
  assert.equal(totalTodo, events.length);
});
