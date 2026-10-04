'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  buildSpotsQuery,
  buildSpotsQueryBbox,
  classifySpotTags,
  findSpotsAround,
  findSpotsInBbox,
  haversineMeters,
} = require('../src/overpassSpots');

function makeFetchStub(responses) {
  let call = 0;
  return async () => {
    const r = responses[call];
    call += 1;
    if (r.throw) throw r.throw;
    return { ok: r.ok !== false, status: r.status || 200, json: async () => r.body };
  };
}

test('buildSpotsQuery: 指定した座標・半径・タイプを含むクエリを生成する', () => {
  const q = buildSpotsQuery(35.15, 139.13, 1500, ['sightseeing', 'food']);
  assert.match(q, /around:1500,35\.15,139\.13/);
  assert.match(q, /tourism/);
  assert.match(q, /amenity.*restaurant/);
});

test('classifySpotTags: tourismタグから観光地と判定する', () => {
  assert.equal(classifySpotTags({ tourism: 'attraction' }, ['sightseeing']), 'sightseeing');
  assert.equal(classifySpotTags({ historic: 'shrine' }, ['sightseeing']), 'sightseeing');
});

test('classifySpotTags: amenityタグから飲食店と判定する', () => {
  assert.equal(classifySpotTags({ amenity: 'restaurant' }, ['food']), 'food');
});

test('classifySpotTags: 該当しなければnull', () => {
  assert.equal(classifySpotTags({ amenity: 'parking' }, ['food', 'sightseeing']), null);
});

test('haversineMeters: 同一地点は0', () => {
  assert.equal(haversineMeters(35.0, 139.0, 35.0, 139.0), 0);
});

test('haversineMeters: 既知の2点間でおおよそ正しい距離を返す（東京駅-横浜駅 約27km）', () => {
  const d = haversineMeters(35.6812, 139.7671, 35.4658, 139.6228);
  assert.ok(d > 25000 && d < 29000, `expected ~27km, got ${d}`);
});

test('findSpotsAround: Overpass結果を分類・重複排除・距離付きで返す', async () => {
  const fetchImpl = makeFetchStub([
    {
      ok: true,
      body: {
        elements: [
          { id: 1, lat: 35.151, lon: 139.145, tags: { name: '真鶴岬', tourism: 'attraction' } },
          { id: 2, lat: 35.151, lon: 139.145, tags: { name: '真鶴岬', tourism: 'attraction' } }, // 重複
          { id: 3, lat: 35.1, lon: 139.1, tags: { name: '座標なし施設' } }, // nameだけでtypeに合致しない
          { id: 4, lat: 35.15, lon: 139.15, tags: { name: '食堂A', amenity: 'restaurant' } },
        ],
      },
    },
  ]);
  const spots = await findSpotsAround(35.1511, 139.1448, 1500, ['sightseeing', 'food'], {
    fetchImpl,
    endpoints: ['https://a.example'],
  });
  assert.equal(spots.length, 2);
  assert.ok(spots.some((s) => s.name === '真鶴岬' && s.type === 'sightseeing'));
  assert.ok(spots.some((s) => s.name === '食堂A' && s.type === 'food'));
  spots.forEach((s) => assert.ok(typeof s.distanceMeters === 'number'));
});

test('findSpotsAround: 無効なtypesだけならfetchせず空配列', async () => {
  let called = false;
  const fetchImpl = async () => { called = true; return { ok: true, json: async () => ({ elements: [] }) }; };
  const spots = await findSpotsAround(35.0, 139.0, 1000, ['unknown-type'], { fetchImpl });
  assert.deepEqual(spots, []);
  assert.equal(called, false);
});

test('findSpotsAround: 外部から渡したAbortSignal（キャンセルボタン相当）で全ミラーが中断される', async () => {
  const controller = new AbortController();
  controller.abort();
  const abortError = new Error('aborted');
  abortError.name = 'AbortError';
  let calls = 0;
  const fetchImpl = async (url, init) => {
    calls += 1;
    if (init.signal && init.signal.aborted) throw abortError;
    throw new Error('should not reach here');
  };
  await assert.rejects(
    () => findSpotsAround(35.0, 139.0, 1000, ['food'], {
      fetchImpl,
      signal: controller.signal,
      endpoints: ['https://a.example', 'https://b.example'],
    }),
    /aborted/
  );
  assert.equal(calls, 2, '両方のミラーに中断済みのsignalが渡っているはず');
});

test('buildSpotsQueryBbox: 矩形(bbox)を含むクエリを生成する（around:は使わない）', () => {
  const q = buildSpotsQueryBbox([35.1, 139.1, 35.2, 139.2], ['sightseeing', 'food']);
  assert.match(q, /\(35\.1,139\.1,35\.2,139\.2\)/);
  assert.doesNotMatch(q, /around:/);
  assert.match(q, /tourism/);
  assert.match(q, /amenity.*restaurant/);
});

test('findSpotsInBbox: Overpass結果を分類・重複排除して返す（距離は持たない）', async () => {
  const fetchImpl = makeFetchStub([
    {
      ok: true,
      body: {
        elements: [
          { id: 1, lat: 35.15, lon: 139.15, tags: { name: '鶴岡八幡宮', tourism: 'attraction' } },
          { id: 2, lat: 35.15, lon: 139.15, tags: { name: '鶴岡八幡宮', tourism: 'attraction' } }, // 重複
          { id: 3, lat: 35.16, lon: 139.16, tags: { name: '食堂B', amenity: 'restaurant' } },
        ],
      },
    },
  ]);
  const spots = await findSpotsInBbox([35.1, 139.1, 35.2, 139.2], ['sightseeing', 'food'], {
    fetchImpl,
    endpoints: ['https://a.example'],
  });
  assert.equal(spots.length, 2);
  assert.ok(spots.every((s) => !('distanceMeters' in s)));
  assert.ok(spots.some((s) => s.name === '鶴岡八幡宮' && s.type === 'sightseeing'));
  assert.ok(spots.some((s) => s.name === '食堂B' && s.type === 'food'));
});

test('findSpotsInBbox: 無効なtypesだけならfetchせず空配列', async () => {
  let called = false;
  const fetchImpl = async () => { called = true; return { ok: true, json: async () => ({ elements: [] }) }; };
  const spots = await findSpotsInBbox([35.0, 139.0, 35.1, 139.1], ['unknown-type'], { fetchImpl });
  assert.deepEqual(spots, []);
  assert.equal(called, false);
});
