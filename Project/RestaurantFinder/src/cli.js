#!/usr/bin/env node
'use strict';

const path = require('path');
const { rankRestaurants } = require('./scoring');
const { searchRestaurants, getPlaceDetails, toScoringInput } = require('./googlePlaces');

/**
 * 使い方:
 *   GOOGLE_PLACES_API_KEY=xxx node src/cli.js "渋谷 ラーメン"
 *   node src/cli.js --demo        # APIキーなしでサンプルデータを使ってランキング表示を確認
 */
async function main() {
  const args = process.argv.slice(2);
  const isDemo = args.includes('--demo');
  const query = args.filter((a) => a !== '--demo').join(' ');
  const apiKey = process.env.GOOGLE_PLACES_API_KEY;

  let restaurants;

  if (isDemo || !apiKey) {
    if (!apiKey && !isDemo) {
      console.error(
        '[info] GOOGLE_PLACES_API_KEY が未設定のため、デモデータでランキングを表示します。'
      );
    }
    // eslint-disable-next-line global-require
    restaurants = require(path.join(__dirname, '..', 'test', 'fixtures', 'sample-restaurants.json'));
  } else {
    if (!query) {
      console.error('検索キーワードを指定してください。例: node src/cli.js "渋谷 ラーメン"');
      process.exitCode = 1;
      return;
    }
    const places = await searchRestaurants(query, apiKey);
    if (places.length === 0) {
      console.log('該当する店舗が見つかりませんでした。');
      return;
    }
    const details = await Promise.all(
      places.map((p) => getPlaceDetails(p.id, apiKey))
    );
    restaurants = details.map(toScoringInput);
  }

  const ranked = rankRestaurants(restaurants);

  console.log(`\n=== 評価基準ベース ランキング${query ? `（${query}）` : '（デモ）'} ===\n`);
  ranked.forEach((entry, index) => {
    const name = entry.restaurant.name || entry.restaurant.id;
    console.log(`${index + 1}. ${name}  総合スコア: ${entry.score}`);
    console.log(
      `   内訳: 信頼度補正評価=${entry.breakdown.bayesianAverage} / ` +
        `リピート言及率=${entry.breakdown.repeatMentionRatio} / ` +
        `具体性=${entry.breakdown.specificityRatio} / ` +
        `二極化=${entry.breakdown.polarizationScore} / ` +
        `投稿バースト=${entry.breakdown.burstinessScore}`
    );
    if (entry.restaurant.googleMapsUri) {
      console.log(`   ${entry.restaurant.googleMapsUri}`);
    }
    console.log('');
  });
}

main().catch((err) => {
  console.error('[error]', err.message);
  process.exitCode = 1;
});
