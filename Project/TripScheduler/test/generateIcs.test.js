'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { generateIcs, toIcsUtc, escapeIcsText } = require('../src/generateIcs');

test('toIcsUtc: JST 09:00 は UTC 00:00 に変換される', () => {
  assert.equal(toIcsUtc('2026-09-21', '09:00'), '20260921T000000Z');
});

test('toIcsUtc: JST 08:30 は前日UTCに繰り上がる', () => {
  assert.equal(toIcsUtc('2026-09-23', '08:30'), '20260922T233000Z');
});

test('escapeIcsText: カンマ・セミコロン・改行をエスケープする', () => {
  assert.equal(escapeIcsText('a,b;c\nd'), 'a\\,b\\;c\\nd');
});

test('generateIcs: VCALENDAR/VEVENTの基本構造を持つ', () => {
  const ics = generateIcs([
    { date: '2026-09-21', start: '09:00', end: '10:30', title: '大船フラワーセンター散策', location: '大船', description: 'テスト' },
  ]);
  assert.match(ics, /BEGIN:VCALENDAR/);
  assert.match(ics, /BEGIN:VEVENT/);
  assert.match(ics, /DTSTART:20260921T000000Z/);
  assert.match(ics, /DTEND:20260921T013000Z/);
  assert.match(ics, /SUMMARY:大船フラワーセンター散策/);
  assert.match(ics, /END:VEVENT/);
  assert.match(ics, /END:VCALENDAR/);
});

test('generateIcs: 各行がCRLFで終わる', () => {
  const ics = generateIcs([
    { date: '2026-09-21', start: '09:00', end: '10:00', title: 'x', location: '', description: '' },
  ]);
  assert.ok(ics.includes('\r\n'));
  assert.ok(!ics.split('\r\n').some((line) => line.includes('\n')));
});

test('generateIcs: サンプルデータ silver-week-2026.json を正しく変換できる', () => {
  // eslint-disable-next-line global-require
  const events = require('../data/silver-week-2026.json');
  const ics = generateIcs(events);
  const veventCount = (ics.match(/BEGIN:VEVENT/g) || []).length;
  assert.equal(veventCount, events.length);
});
