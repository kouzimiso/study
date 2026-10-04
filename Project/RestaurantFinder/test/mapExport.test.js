'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { generateMapHtml, scoreToColor } = require('../src/mapExport');

test('scoreToColor: 高スコアほど緑寄り、低スコアほど赤寄りのhslになる', () => {
  const low = scoreToColor(0);
  const high = scoreToColor(100);
  assert.equal(low, 'hsl(0, 70%, 45%)');
  assert.equal(high, 'hsl(120, 70%, 45%)');
});

test('generateMapHtml: 座標のある店舗のみ地図データに含める', () => {
  const ranked = [
    {
      restaurant: { id: 'a', name: '店A', lat: 35.0, lng: 139.0, googleMapsUri: 'https://maps.google.com/a' },
      score: 80,
      breakdown: { bayesianAverage: 4, repeatMentionRatio: 0.5, specificityRatio: 0.5, polarizationScore: 0, burstinessScore: 0 },
    },
    {
      restaurant: { id: 'b', name: '店B（座標なし）' },
      score: 60,
      breakdown: { bayesianAverage: 3, repeatMentionRatio: 0, specificityRatio: 0, polarizationScore: 0, burstinessScore: 0 },
    },
  ];

  const html = generateMapHtml(ranked);
  assert.match(html, /店A/);
  assert.match(html, /座標情報がないため地図に表示していません/);
  assert.match(html, /leaflet\.min\.js/);
});

test('generateMapHtml: 店名に含まれるHTMLタグはエスケープされる', () => {
  const ranked = [
    {
      restaurant: { id: 'xss', name: '<img src=x onerror=alert(1)>', lat: 35.0, lng: 139.0 },
      score: 50,
      breakdown: { bayesianAverage: 3, repeatMentionRatio: 0, specificityRatio: 0, polarizationScore: 0, burstinessScore: 0 },
    },
  ];

  const html = generateMapHtml(ranked);
  assert.doesNotMatch(html, /<img src=x onerror=alert\(1\)>/);
});

test('generateMapHtml: 座標を持つ店舗が1件もなくてもエラーにならない', () => {
  const html = generateMapHtml([]);
  assert.match(html, /leaflet\.min\.js/);
});
