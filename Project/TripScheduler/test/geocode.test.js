'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { geocodeLocation, geocodeOnce } = require('../src/geocode');

function makeFetchStub(responses) {
  let call = 0;
  return async () => {
    const r = responses[call];
    call += 1;
    if (r === undefined) throw new Error('no more stubbed responses');
    if (r.throw) throw r.throw;
    return { ok: r.ok !== false, status: r.status || 200, json: async () => r.body };
  };
}

test('geocodeOnce: 最初の候補を lat/lng/name に変換する', async () => {
  const fetchImpl = makeFetchStub([
    { ok: true, body: [{ lat: '35.3556', lon: '139.5309', display_name: '大船駅, 鎌倉市, 神奈川県, 日本' }] },
  ]);
  const result = await geocodeOnce('大船駅', { fetchImpl });
  assert.deepEqual(result, { lat: 35.3556, lng: 139.5309, name: '大船駅' });
});

test('geocodeOnce: 結果が0件ならnull', async () => {
  const fetchImpl = makeFetchStub([{ ok: true, body: [] }]);
  const result = await geocodeOnce('存在しない場所xyz', { fetchImpl });
  assert.equal(result, null);
});

test('geocodeLocation: 1回目が失敗しても2回目（日本付き再試行）で成功する', async () => {
  const fetchImpl = makeFetchStub([
    { ok: true, body: [] },
    { ok: true, body: [{ lat: '35.0', lon: '139.0', display_name: 'テスト地点' }] },
  ]);
  const result = await geocodeLocation('あいまいな地名', { fetchImpl });
  assert.deepEqual(result, { lat: 35.0, lng: 139.0, name: 'テスト地点' });
});

test('geocodeLocation: 空文字はnullを返しfetchしない', async () => {
  let called = false;
  const fetchImpl = async () => { called = true; };
  const result = await geocodeLocation('', { fetchImpl });
  assert.equal(result, null);
  assert.equal(called, false);
});

test('geocodeLocation: 全滅したらnull', async () => {
  const fetchImpl = makeFetchStub([{ ok: false, status: 503 }, { ok: false, status: 503 }]);
  const result = await geocodeLocation('どこか', { fetchImpl });
  assert.equal(result, null);
});
