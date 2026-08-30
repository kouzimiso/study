'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  bayesianAverage,
  polarizationScore,
  repeatMentionRatio,
  specificityRatio,
  burstinessScore,
  scoreRestaurant,
  rankRestaurants,
} = require('../src/scoring');

test('bayesianAverage: レビュー0件はglobalMeanに一致する', () => {
  assert.equal(bayesianAverage(5, 0, 3.5), 3.5);
});

test('bayesianAverage: レビュー件数が多いほど実評価に近づく', () => {
  const fewReviews = bayesianAverage(5, 1, 3.5, 50);
  const manyReviews = bayesianAverage(5, 5000, 3.5, 50);
  assert.ok(fewReviews < manyReviews);
  assert.ok(manyReviews > 4.9);
});

test('polarizationScore: 星1と星5に二極化した分布は高スコア', () => {
  const polarized = polarizationScore([40, 0, 0, 0, 60]);
  const balanced = polarizationScore([5, 10, 60, 15, 10]);
  assert.ok(polarized > balanced);
});

test('polarizationScore: 片側だけの極端な分布は二極化とみなさない', () => {
  const oneSided = polarizationScore([0, 0, 0, 0, 100]);
  assert.equal(oneSided, 0);
});

test('repeatMentionRatio: リピート言及を含むレビューの比率を返す', () => {
  const reviews = [
    { text: 'また来ます、美味しかった' },
    { text: '初めて行きました' },
    { text: '何度もリピートしてます' },
  ];
  assert.equal(repeatMentionRatio(reviews), 2 / 3);
});

test('repeatMentionRatio: レビューが空なら0', () => {
  assert.equal(repeatMentionRatio([]), 0);
});

test('specificityRatio: 定型句のみの短いレビューは具体性なしと判定', () => {
  const reviews = [
    { text: '美味しかった' },
    { text: '近所に住んで5年、週2で通ってます。焼き魚定食の脂ののりが季節でちゃんと変わるのが分かる。' },
  ];
  assert.equal(specificityRatio(reviews), 0.5);
});

test('burstinessScore: 短期間に集中投稿されたレビューは高スコア', () => {
  const burstDates = [
    '2026-01-10', '2026-01-10', '2026-01-11', '2026-01-11', '2026-01-11',
    '2025-01-01',
  ].map((date) => ({ date }));
  const spreadDates = [
    '2025-01-01', '2025-03-01', '2025-05-01', '2025-07-01', '2025-09-01', '2025-11-01',
  ].map((date) => ({ date }));
  assert.ok(burstinessScore(burstDates) > burstinessScore(spreadDates));
});

test('burstinessScore: レビューが少なすぎる場合は0', () => {
  assert.equal(burstinessScore([{ date: '2026-01-01' }]), 0);
});

test('scoreRestaurant: スコアは0〜100の範囲に収まる', () => {
  const { score } = scoreRestaurant({
    rating: 4.5,
    reviewCount: 100,
    reviews: [
      { rating: 5, date: '2025-01-01', text: 'また来たいと思えるくらい美味しかったです。何度も通っています。' },
    ],
  });
  assert.ok(score >= 0 && score <= 100);
});

test('rankRestaurants: 地に足の着いた高評価店が、二極化した話題店より上位になる', () => {
  const solidRestaurant = {
    id: 'solid',
    rating: 4.3,
    reviewCount: 180,
    reviews: [
      { rating: 5, date: '2025-11-02', text: '近所に住んで5年、週2で通ってます。焼き魚定食の脂ののりが季節でちゃんと変わるのが分かる。また今度も行きます。' },
      { rating: 4, date: '2025-09-14', text: '友人に勧められて初訪問。出汁の香りが強くて、家庭的だけど手を抜いていない味でした。' },
      { rating: 5, date: '2025-06-01', text: '何度もリピートしてます。大将が魚の仕入れの話をしてくれるのも楽しい。' },
      { rating: 4, date: '2025-03-20', text: 'ランチのコスパがとても良い。定食の副菜が日替わりで飽きない。' },
      { rating: 3, date: '2024-12-05', text: '普通に美味しかったです。' },
    ],
  };
  const hypedRestaurant = {
    id: 'hyped',
    rating: 4.6,
    reviewCount: 40,
    reviews: [
      { rating: 5, date: '2026-01-10', text: '最高でした！' },
      { rating: 5, date: '2026-01-10', text: '美味しかったです。' },
      { rating: 5, date: '2026-01-11', text: 'おすすめです！' },
      { rating: 5, date: '2026-01-11', text: '大満足！' },
      { rating: 1, date: '2026-01-12', text: '接客が最悪でした。二度と行きません。' },
    ],
  };

  const ranked = rankRestaurants([hypedRestaurant, solidRestaurant]);
  assert.equal(ranked[0].restaurant.id, 'solid');
});
