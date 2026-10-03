'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { buildIndexHtml } = require('../src/buildIndexHtml');

const sampleRoutes = [
  {
    id: 'a',
    name: '真鶴・湯河原ルート',
    crowdRisk: 'low',
    searchCenter: { lat: 35.15, lng: 139.13 },
    highlights: ['真鶴岬'],
    tags: ['海', '温泉'],
    accessFromOfuna: { car: '約1時間' },
    recommendedDurationHours: 7,
    notes: 'テストノート',
  },
];

const sampleItinerary = [
  {
    date: '2026-09-21',
    start: '09:00',
    end: '10:00',
    title: '真鶴岬散策',
    location: '真鶴岬',
    description: '絶景',
    category: 'sightseeing',
    routeId: 'a',
  },
];

test('buildIndexHtml: 4つのタブとLeaflet読み込みを含む', () => {
  const html = buildIndexHtml({ routes: sampleRoutes, visitHistory: [], itinerary: sampleItinerary });
  assert.match(html, /data-tab="itinerary"/);
  assert.match(html, /data-tab="routes"/);
  assert.match(html, /data-tab="map"/);
  assert.match(html, /data-tab="hotel"/);
  assert.match(html, /leaflet\.min\.js/);
});

test('buildIndexHtml: 訪問履歴が無いRouteは「未訪問」になる', () => {
  const html = buildIndexHtml({ routes: sampleRoutes, visitHistory: [], itinerary: [] });
  assert.match(html, /未訪問/);
});

test('buildIndexHtml: 訪問済みRouteは経過日数が表示される', () => {
  const html = buildIndexHtml(
    { routes: sampleRoutes, visitHistory: [{ routeId: 'a', visitedOn: '2026-09-11' }], itinerary: [] },
    { today: new Date('2026-09-21T00:00:00Z') }
  );
  assert.match(html, /前回訪問から10日/);
});

test('buildIndexHtml: 店名・タイトルに含まれるHTMLタグはエスケープされる(埋め込みデータ経由)', () => {
  const routes = [{ ...sampleRoutes[0], name: '<img src=x onerror=alert(1)>' }];
  const html = buildIndexHtml({ routes, visitHistory: [], itinerary: [] });
  assert.doesNotMatch(html, /<img src=x onerror=alert\(1\)>/);
});

test('buildIndexHtml: scriptタグの中にJSONが安全に埋め込まれ、構文エラーにならない', () => {
  const html = buildIndexHtml({ routes: sampleRoutes, visitHistory: [], itinerary: sampleItinerary });
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.equal(scripts.length, 1);
  assert.doesNotThrow(() => new Function(scripts[0]));
});

test('buildIndexHtml: タイトルをオプションで変更できる', () => {
  const html = buildIndexHtml(
    { routes: [], visitHistory: [], itinerary: [] },
    { title: 'カスタムタイトル' }
  );
  assert.match(html, /<title>カスタムタイトル<\/title>/);
});

test('buildIndexHtml: 実データ(data/routes.json等)で生成できる', () => {
  // eslint-disable-next-line global-require
  const routes = require('../data/routes.json');
  // eslint-disable-next-line global-require
  const visitHistory = require('../data/visitHistory.json');
  // eslint-disable-next-line global-require
  const itinerary = require('../data/silver-week-2026.json');
  const html = buildIndexHtml({ routes, visitHistory, itinerary });
  assert.ok(html.length > 1000);
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.doesNotThrow(() => new Function(scripts[0]));
});
