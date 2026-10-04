'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { buildOsrmUrl, fetchRouteLine, distanceToRouteMeters, routeProgressRatio } = require('../src/routeLine');

test('buildOsrmUrl: lng,lat順・;区切りで複数地点を含むURLを生成する', () => {
  const url = buildOsrmUrl(
    [
      { lat: 35.3, lng: 139.5 },
      { lat: 35.31, lng: 139.51 },
      { lat: 35.32, lng: 139.52 },
    ],
    'walk'
  );
  assert.match(url, /\/route\/v1\/foot\//);
  assert.match(url, /139\.5,35\.3;139\.51,35\.31;139\.52,35\.32/);
  assert.match(url, /overview=full/);
  assert.match(url, /geometries=geojson/);
});

test('buildOsrmUrl: モードごとにOSRMのprofileへ変換する', () => {
  const pt = [{ lat: 0, lng: 0 }, { lat: 1, lng: 1 }];
  assert.match(buildOsrmUrl(pt, 'car'), /\/car\//);
  assert.match(buildOsrmUrl(pt, 'bike'), /\/bike\//);
  assert.match(buildOsrmUrl(pt, 'walk'), /\/foot\//);
});

test('fetchRouteLine: OSRM成功時はジオメトリと距離・時間を返す(real:true)', async () => {
  const fetchImpl = async () => ({
    ok: true,
    json: async () => ({
      code: 'Ok',
      routes: [{ geometry: { coordinates: [[139.5, 35.3], [139.51, 35.31]] }, distance: 1234.5, duration: 600.4 }],
    }),
  });
  const result = await fetchRouteLine(
    [{ lat: 35.3, lng: 139.5 }, { lat: 35.31, lng: 139.51 }],
    'car',
    { fetchImpl }
  );
  assert.equal(result.real, true);
  assert.deepEqual(result.coords, [[139.5, 35.3], [139.51, 35.31]]);
  assert.equal(result.distanceMeters, 1235);
  assert.equal(result.durationSeconds, 600);
});

test('fetchRouteLine: OSRM失敗時は直線近似にフォールバックする(real:false)', async () => {
  const fetchImpl = async () => { throw new Error('network error'); };
  const points = [{ lat: 35.3, lng: 139.5 }, { lat: 35.4, lng: 139.6 }];
  const result = await fetchRouteLine(points, 'car', { fetchImpl });
  assert.equal(result.real, false);
  assert.deepEqual(result.coords, [[139.5, 35.3], [139.6, 35.4]]);
  assert.ok(result.distanceMeters > 0);
  assert.equal(result.durationSeconds, null);
});

test('fetchRouteLine: OSRMがcode!=="Ok"を返した場合もフォールバックする', async () => {
  const fetchImpl = async () => ({ ok: true, json: async () => ({ code: 'NoRoute', message: 'no route found' }) });
  const points = [{ lat: 0, lng: 0 }, { lat: 1, lng: 1 }];
  const result = await fetchRouteLine(points, 'car', { fetchImpl });
  assert.equal(result.real, false);
});

test('fetchRouteLine: 地点が1つ以下ならfetchせずreal:falseを返す', async () => {
  let called = false;
  const fetchImpl = async () => { called = true; };
  const result = await fetchRouteLine([{ lat: 0, lng: 0 }], 'car', { fetchImpl });
  assert.equal(called, false);
  assert.equal(result.real, false);
  assert.deepEqual(result.coords, [[0, 0]]);
});

// 東西に伸びる直線の経路（緯度35.00固定、経度139.00→139.10）
const STRAIGHT_EAST_ROUTE = [[139.0, 35.0], [139.1, 35.0]];

test('distanceToRouteMeters: 経路上の点は距離0に近い', () => {
  const d = distanceToRouteMeters(35.0, 139.05, STRAIGHT_EAST_ROUTE);
  assert.ok(d < 1, `expected ~0, got ${d}`);
});

test('distanceToRouteMeters: 経路から北に約111m離れた点はその分の距離になる', () => {
  const d = distanceToRouteMeters(35.001, 139.05, STRAIGHT_EAST_ROUTE);
  assert.ok(d > 100 && d < 120, `expected ~111m, got ${d}`);
});

test('distanceToRouteMeters: coordsが1点以下ならInfinity', () => {
  assert.equal(distanceToRouteMeters(35.0, 139.0, [[139.0, 35.0]]), Infinity);
  assert.equal(distanceToRouteMeters(35.0, 139.0, []), Infinity);
});

test('routeProgressRatio: 出発地点側は0に近く、目的地側は1に近い', () => {
  assert.ok(routeProgressRatio(35.0, 139.0, STRAIGHT_EAST_ROUTE) < 0.05);
  assert.ok(routeProgressRatio(35.0, 139.1, STRAIGHT_EAST_ROUTE) > 0.95);
});

test('routeProgressRatio: 中間地点は約0.5になる', () => {
  const r = routeProgressRatio(35.0, 139.05, STRAIGHT_EAST_ROUTE);
  assert.ok(r > 0.45 && r < 0.55, `expected ~0.5, got ${r}`);
});

test('routeProgressRatio: coordsが2点未満なら0', () => {
  assert.equal(routeProgressRatio(35.0, 139.0, [[139.0, 35.0]]), 0);
});
