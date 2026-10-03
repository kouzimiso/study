'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { parseTravelMinutes, addMinutes, buildDaySchedule } = require('../src/buildDaySchedule');

test('parseTravelMinutes: "約1時間" は60分', () => {
  assert.equal(parseTravelMinutes('約1時間'), 60);
});

test('parseTravelMinutes: "約40分" は40分', () => {
  assert.equal(parseTravelMinutes('約40分'), 40);
});

test('parseTravelMinutes: "約1時間強" は60分(「強」は無視し時間部分のみ採用)', () => {
  assert.equal(parseTravelMinutes('約1時間強'), 60);
});

test('parseTravelMinutes: "約1時間半〜（渋滞時はそれ以上）" は90分', () => {
  assert.equal(parseTravelMinutes('約1時間半〜（渋滞時はそれ以上）'), 90);
});

test('parseTravelMinutes: 空文字・未定義はフォールバック値', () => {
  assert.equal(parseTravelMinutes(''), 60);
  assert.equal(parseTravelMinutes(undefined, 45), 45);
});

test('addMinutes: 分を加算してHH:MM形式を返す', () => {
  assert.equal(addMinutes('09:00', 90), '10:30');
  assert.equal(addMinutes('23:30', 45), '24:15');
});

test('buildDaySchedule: 移動(往路)→観光→昼食→温泉→休憩→移動(帰路)の順になる', () => {
  const route = {
    id: 'manazuru-yugawara',
    name: '真鶴・湯河原 絶景と日帰り温泉ルート',
    accessFromOfuna: { car: '約1時間' },
    highlights: ['真鶴岬・三ツ石'],
    foodStops: [{ name: '真鶴港周辺の海鮮店', note: '地魚' }],
    onsenStops: [{ name: '湯河原温泉の日帰り入浴施設', note: '' }],
    wifiPowerStops: [{ name: '湯河原駅周辺のカフェ', note: '' }],
    recommendedDurationHours: 7,
  };

  const events = buildDaySchedule(route, '2026-09-21');
  const categories = events.map((e) => e.category);
  assert.deepEqual(categories, ['move', 'sightseeing', 'food', 'onsen', 'work', 'move']);
  assert.equal(events[0].start, '09:00');
  assert.ok(events.every((e) => e.date === '2026-09-21'));
  assert.ok(events.every((e) => e.routeId === 'manazuru-yugawara'));
});

test('buildDaySchedule: 全イベントの時間がrecommendedDurationHours付近に収まる', () => {
  const route = {
    id: 'yabitsu-miyagase',
    name: 'ヤビツ峠・宮ヶ瀬 絶景ワインディングルート',
    accessFromOfuna: { car: '約1時間' },
    highlights: ['ヤビツ峠からの富士山・大山の眺望', '宮ヶ瀬湖畔の景観'],
    foodStops: [{ name: 'ヤビツ峠レストハウス', note: '通年営業' }],
    recommendedDurationHours: 6,
  };
  const events = buildDaySchedule(route, '2026-09-23', { startTime: '08:00' });
  const last = events[events.length - 1];
  const [h, m] = last.end.split(':').map(Number);
  const totalMinutesUsed = h * 60 + m - 8 * 60;
  assert.ok(totalMinutesUsed <= 6 * 60 + 60, `6時間程度に収まるはず: ${totalMinutesUsed}分`);
});

test('buildDaySchedule: onsenStops/wifiPowerStopsが無いルートでもエラーにならない', () => {
  const route = {
    id: 'miura-west-coast',
    name: '三浦半島西海岸 佐島・秋谷・荒崎ルート',
    accessFromOfuna: { car: '約40分' },
    highlights: ['佐島マリーナ', '秋谷海岸・立石公園', '荒崎公園'],
    foodStops: [{ name: '佐島の漁港食堂', note: '' }],
    recommendedDurationHours: 6,
  };
  const events = buildDaySchedule(route, '2026-09-22');
  assert.ok(events.some((e) => e.category === 'food'));
  assert.ok(!events.some((e) => e.category === 'onsen'));
  assert.ok(!events.some((e) => e.category === 'work'));
});

test('buildDaySchedule: 実データ(data/routes.json)の全ルートでエラーなく生成できる', () => {
  // eslint-disable-next-line global-require
  const routes = require('../data/routes.json');
  routes.forEach((route) => {
    const events = buildDaySchedule(route, '2026-09-21');
    assert.ok(events.length >= 2); // 最低、往路・帰路の移動は入る
    assert.equal(events[0].category, 'move');
    assert.equal(events[events.length - 1].category, 'move');
  });
});
