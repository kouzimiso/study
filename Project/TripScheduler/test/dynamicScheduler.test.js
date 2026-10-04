'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  estimateTravelMinutes,
  selectSpotsForDay,
  orderSpotsGreedy,
  buildDynamicDaySchedule,
} = require('../src/dynamicScheduler');

const center = { lat: 35.3556, lng: 139.5309, name: '大船駅' };

const sampleSpots = [
  { id: 's1', name: '観光地A', type: 'sightseeing', lat: 35.36, lng: 139.54, distanceMeters: 600, hours: null },
  { id: 's2', name: '観光地B', type: 'sightseeing', lat: 35.37, lng: 139.55, distanceMeters: 1800, hours: '09:00-17:00' },
  { id: 's3', name: '観光地C', type: 'sightseeing', lat: 35.38, lng: 139.56, distanceMeters: 3000, hours: null },
  { id: 's4', name: '食堂A', type: 'food', lat: 35.355, lng: 139.53, distanceMeters: 300, hours: null },
  { id: 's5', name: 'カフェA', type: 'wifi', lat: 35.354, lng: 139.532, distanceMeters: 400, hours: null },
];

test('estimateTravelMinutes: 車は徒歩より速く見積もる', () => {
  const car = estimateTravelMinutes(10000, 'car');
  const walk = estimateTravelMinutes(10000, 'walk');
  assert.ok(car < walk);
});

test('estimateTravelMinutes: 最低5分を保証する', () => {
  assert.equal(estimateTravelMinutes(10, 'car'), 5);
});

test('selectSpotsForDay: カテゴリごとの上限を守りつつ近い順に選ぶ', () => {
  const selected = selectSpotsForDay(sampleSpots, { maxByType: { sightseeing: 2, food: 1, wifi: 1 } });
  const sightseeingCount = selected.filter((s) => s.type === 'sightseeing').length;
  assert.equal(sightseeingCount, 2);
  assert.ok(selected.some((s) => s.name === '観光地A'));
  assert.ok(selected.some((s) => s.name === '観光地B'));
  assert.ok(!selected.some((s) => s.name === '観光地C')); // 上限超過で除外
});

test('orderSpotsGreedy: 中心から最も近い順に巡回する（最近傍法）', () => {
  const ordered = orderSpotsGreedy(center, [sampleSpots[2], sampleSpots[0], sampleSpots[3]]);
  assert.equal(ordered[0].name, '食堂A'); // 300m, 一番近い
});

test('buildDynamicDaySchedule: 移動→滞在の繰り返しで、最後に出発地点に戻る', () => {
  const selected = selectSpotsForDay(sampleSpots, { maxByType: { sightseeing: 1, food: 1 } });
  const events = buildDynamicDaySchedule(center, '2026-11-01', selected, { startTime: '09:00', mode: 'car' });

  assert.equal(events[0].category, 'move');
  assert.equal(events[events.length - 1].category, 'move');
  assert.ok(events[events.length - 1].title.includes('大船駅'));
  assert.ok(events.every((e) => e.date === '2026-11-01'));
  // 時刻が単調増加しているか
  for (let i = 1; i < events.length; i++) {
    assert.ok(events[i].start >= events[i - 1].start);
  }
});

test('buildDynamicDaySchedule: returnToCenter=falseなら帰路イベントを追加しない', () => {
  const selected = [sampleSpots[0]];
  const events = buildDynamicDaySchedule(center, '2026-11-01', selected, { returnToCenter: false });
  // move(往路) + 滞在 の2件のみ
  assert.equal(events.length, 2);
  assert.equal(events[1].category, 'sightseeing');
});

test('buildDynamicDaySchedule: スポットが0件なら移動イベントも生成されない', () => {
  const events = buildDynamicDaySchedule(center, '2026-11-01', [], {});
  assert.deepEqual(events, []);
});
