'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { mergeWifiPowerStops } = require('../src/updateWifiPowerStops');

test('mergeWifiPowerStops: internet_access確認済みの新規候補のみ追加する', () => {
  const route = { wifiPowerStops: [{ name: '既存カフェ', note: '手動登録' }] };
  const spots = [
    { name: '既存カフェ', internetAccess: 'wlan', lat: 1, lng: 1 },
    { name: '新規カフェA', internetAccess: 'wlan', lat: 2, lng: 2, osmId: 10 },
    { name: '新規カフェB', internetAccess: null, lat: 3, lng: 3 },
  ];
  const merged = mergeWifiPowerStops(route, spots);
  assert.equal(merged.length, 2); // 既存1件 + 新規1件（タグ無しのBは除外、既存と重複するものは除外）
  assert.equal(merged[0].name, '既存カフェ');
  assert.equal(merged[1].name, '新規カフェA');
  assert.match(merged[1].note, /Overpass確認済み/);
});

test('mergeWifiPowerStops: wifiPowerStopsが未定義でもエラーにならない', () => {
  const route = {};
  const spots = [{ name: 'カフェC', internetAccess: 'yes', lat: 1, lng: 1 }];
  const merged = mergeWifiPowerStops(route, spots);
  assert.equal(merged.length, 1);
  assert.equal(merged[0].name, 'カフェC');
});

test('mergeWifiPowerStops: 候補が0件なら既存のまま変わらない', () => {
  const route = { wifiPowerStops: [{ name: '既存カフェ' }] };
  const merged = mergeWifiPowerStops(route, []);
  assert.deepEqual(merged, [{ name: '既存カフェ' }]);
});
