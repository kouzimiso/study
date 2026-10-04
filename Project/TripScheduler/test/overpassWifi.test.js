'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { buildWifiQuery, fetchOverpass, findWifiPowerSpots } = require('../src/overpassWifi');

function makeFetchStub(responses) {
  let call = 0;
  return async () => {
    const r = responses[call];
    call += 1;
    if (r.throw) throw r.throw;
    return {
      ok: r.ok !== false,
      status: r.status || (r.ok === false ? 500 : 200),
      json: async () => r.body,
    };
  };
}

test('buildWifiQuery: 座標と半径を含むOverpass QLを生成する', () => {
  const q = buildWifiQuery(35.15, 139.13, 1500);
  assert.match(q, /around:1500,35\.15,139\.13/);
  assert.match(q, /amenity.*cafe\|restaurant\|fast_food/);
});

test('fetchOverpass: 最初のエンドポイントが成功すればそれを返す', async () => {
  const fetchImpl = makeFetchStub([{ ok: true, body: { elements: [{ id: 1 }] } }]);
  const data = await fetchOverpass('query', { fetchImpl, endpoints: ['https://a.example'] });
  assert.deepEqual(data, { elements: [{ id: 1 }] });
});

test('fetchOverpass: 最初が失敗したら次のエンドポイントにフォールバックする', async () => {
  const fetchImpl = makeFetchStub([
    { ok: false, status: 502 },
    { ok: true, body: { elements: [] } },
  ]);
  const data = await fetchOverpass('query', {
    fetchImpl,
    endpoints: ['https://a.example', 'https://b.example'],
  });
  assert.deepEqual(data, { elements: [] });
});

test('fetchOverpass: 全エンドポイントが失敗したら例外を投げる', async () => {
  const fetchImpl = makeFetchStub([
    { throw: new Error('reset') },
    { ok: false, status: 502 },
  ]);
  await assert.rejects(
    () => fetchOverpass('query', { fetchImpl, endpoints: ['https://a.example', 'https://b.example'] }),
    /error 502|reset/
  );
});

test('findWifiPowerSpots: internet_accessタグ付きの候補を先頭に並べる', async () => {
  const fetchImpl = makeFetchStub([
    {
      ok: true,
      body: {
        elements: [
          { id: 1, lat: 35.1, lon: 139.1, tags: { name: 'カフェA', amenity: 'cafe' } },
          { id: 2, lat: 35.2, lon: 139.2, tags: { name: 'カフェB', amenity: 'cafe', internet_access: 'wlan' } },
        ],
      },
    },
  ]);
  const spots = await findWifiPowerSpots(35.15, 139.15, 1500, { fetchImpl, endpoints: ['https://a.example'] });
  assert.equal(spots.length, 2);
  assert.equal(spots[0].name, 'カフェB');
  assert.equal(spots[0].internetAccess, 'wlan');
  assert.equal(spots[1].name, 'カフェA');
  assert.equal(spots[1].internetAccess, null);
});

test('findWifiPowerSpots: 座標が欠けている要素は除外する', async () => {
  const fetchImpl = makeFetchStub([
    {
      ok: true,
      body: { elements: [{ id: 1, tags: { name: '座標なし' } }] },
    },
  ]);
  const spots = await findWifiPowerSpots(35.15, 139.15, 1500, { fetchImpl, endpoints: ['https://a.example'] });
  assert.equal(spots.length, 0);
});
