'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { estimateTravelMinutes, buildRouteSchedule } = require('../src/dynamicScheduler');

const from = { lat: 35.3556, lng: 139.5309, name: '大船駅' };
const to = { lat: 35.45, lng: 139.63, name: '鎌倉駅' };

const orderedStops = [
  { id: 's1', name: '観光地A', type: 'sightseeing', lat: 35.36, lng: 139.54, hours: null },
  { id: 's4', name: '食堂A', type: 'food', lat: 35.4, lng: 139.58, hours: '11:00-14:00' },
];

test('estimateTravelMinutes: 車は徒歩より速く見積もる', () => {
  const car = estimateTravelMinutes(10000, 'car');
  const walk = estimateTravelMinutes(10000, 'walk');
  assert.ok(car < walk);
});

test('estimateTravelMinutes: 最低5分を保証する', () => {
  assert.equal(estimateTravelMinutes(10, 'car'), 5);
});

test('buildRouteSchedule: 出発地→スポット→目的地の順に移動・滞在イベントを積む', () => {
  const events = buildRouteSchedule(from, to, '2026-11-01', orderedStops, { startTime: '09:00', mode: 'car' });

  // move, stay, move, stay, move（最後は目的地への移動）
  assert.equal(events.length, 5);
  assert.equal(events[0].category, 'move');
  assert.equal(events[1].category, 'sightseeing');
  assert.equal(events[1].title, '観光地A');
  assert.equal(events[2].category, 'move');
  assert.equal(events[3].category, 'food');
  assert.equal(events[3].title, '食堂A');
  assert.equal(events[4].category, 'move');
  assert.ok(events[4].title.includes('鎌倉駅'));
  assert.ok(events.every((e) => e.date === '2026-11-01'));
  // 時刻が単調増加しているか
  for (let i = 1; i < events.length; i++) {
    assert.ok(events[i].start >= events[i - 1].start);
  }
});

test('buildRouteSchedule: 立ち寄り先が0件でも出発地→目的地の移動イベントは生成する', () => {
  const events = buildRouteSchedule(from, to, '2026-11-01', [], { startTime: '09:00', mode: 'car' });
  assert.equal(events.length, 1);
  assert.equal(events[0].category, 'move');
  assert.ok(events[0].title.includes('大船駅'));
  assert.ok(events[0].title.includes('鎌倉駅'));
});

test('buildRouteSchedule: 出発地と目的地が同じ（往復ルート）でも動く', () => {
  const events = buildRouteSchedule(from, from, '2026-11-01', orderedStops, { startTime: '09:00', mode: 'car' });
  assert.equal(events.length, 5);
  assert.ok(events[4].title.includes('大船駅'));
});

test('buildRouteSchedule: stopsの滞在時間はタイプごとの目安に応じて変わる（onsenは長め）', () => {
  const stops = [{ id: 's9', name: '温泉', type: 'onsen', lat: 35.4, lng: 139.6, hours: null }];
  const events = buildRouteSchedule(from, to, '2026-11-01', stops, { startTime: '09:00', mode: 'car' });
  const stay = events.find((e) => e.category === 'onsen');
  const stayMinutes = (
    parseInt(stay.end.split(':')[0], 10) * 60 + parseInt(stay.end.split(':')[1], 10)
  ) - (
    parseInt(stay.start.split(':')[0], 10) * 60 + parseInt(stay.start.split(':')[1], 10)
  );
  assert.equal(stayMinutes, 90);
});
