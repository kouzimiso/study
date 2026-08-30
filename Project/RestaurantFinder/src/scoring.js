'use strict';

/**
 * EVALUATION_CRITERIA.md の基準をロジック化したスコアリングモジュール。
 * 依存ライブラリなし（Node標準機能のみ）。
 */

const REPEAT_KEYWORDS = [
  'また来', 'また行', 'また食べ', 'リピート', '通っ', '常連',
  '何度も', '何回も', '回目', 'また訪れ', 'また利用',
];

const GENERIC_PHRASES = [
  '美味しかった', '美味しいです', 'よかったです', '最高でした',
  'また来たい', 'おすすめです', '大満足',
];

/**
 * レビュー件数に応じて全体平均へ引き寄せるベイズ平均（信頼度補正）。
 * 件数が少ないほど globalMean に近づき、極端な平均値が過大評価されない。
 *
 * @param {number} rating 対象店の平均評価（0-5）
 * @param {number} reviewCount レビュー件数
 * @param {number} globalMean ジャンル全体などの平均評価（デフォルト3.5）
 * @param {number} minVotes 「信頼するために必要な最低件数」の目安（デフォルト50）
 * @returns {number} 補正後の平均評価（0-5）
 */
function bayesianAverage(rating, reviewCount, globalMean = 3.5, minVotes = 50) {
  if (reviewCount <= 0) return globalMean;
  return (minVotes * globalMean + reviewCount * rating) / (minVotes + reviewCount);
}

/**
 * 星の分布（[1星,2星,3星,4星,5星]の件数）から二極化度合いを検知する。
 * 星1と星5の比率が両方高い（中間が薄い）ほど1に近づく。
 *
 * @param {number[]} distribution 長さ5の配列
 * @returns {number} 0（二極化なし）〜1（強い二極化）
 */
function polarizationScore(distribution) {
  const total = distribution.reduce((a, b) => a + b, 0);
  if (total === 0) return 0;
  const [one, , , , five] = distribution;
  const extremeRatio = (one + five) / total;
  const lowRatio = one / total;
  const highRatio = five / total;
  // 両端がそれぞれ一定割合以上ないと「二極化」とは言えない
  const bothSidesPresent = Math.min(lowRatio, highRatio) > 0.05 ? 1 : 0;
  return bothSidesPresent * extremeRatio;
}

/**
 * レビュー本文中に再来店を示す語がどれだけ含まれるかの比率。
 * @param {{text?: string}[]} reviews
 * @returns {number} 0-1
 */
function repeatMentionRatio(reviews) {
  const withText = reviews.filter((r) => r.text && r.text.trim().length > 0);
  if (withText.length === 0) return 0;
  const matches = withText.filter((r) =>
    REPEAT_KEYWORDS.some((kw) => r.text.includes(kw))
  );
  return matches.length / withText.length;
}

/**
 * レビュー本文の「具体性」を簡易推定する。
 * 定型的な絶賛フレーズのみで短いレビューは具体性が低いとみなし、
 * 一定以上の文字数かつ定型句以外の記述を含むレビューの比率を返す。
 *
 * @param {{text?: string}[]} reviews
 * @param {number} minLength 具体的とみなす最低文字数（デフォルト40）
 * @returns {number} 0-1
 */
function specificityRatio(reviews, minLength = 40) {
  const withText = reviews.filter((r) => r.text && r.text.trim().length > 0);
  if (withText.length === 0) return 0;
  const specific = withText.filter((r) => {
    const text = r.text.trim();
    if (text.length < minLength) return false;
    const isGenericOnly = GENERIC_PHRASES.some(
      (phrase) => text.replace(/[\s。、！!]/g, '') === phrase.replace(/[\s。、！!]/g, '')
    );
    return !isGenericOnly;
  });
  return specific.length / withText.length;
}

/**
 * 短期間にレビューが不自然に集中していないかを検知する。
 * 同一日付（または近接日）に集中したレビューの比率が高いほどペナルティが増す。
 *
 * @param {{date?: string|number|Date}[]} reviews ISO日付文字列 or Date
 * @param {number} windowDays 「近接」とみなす日数幅（デフォルト3日）
 * @returns {number} 0（自然な分散）〜1（強い集中＝バースト）
 */
function burstinessScore(reviews, windowDays = 3) {
  const dates = reviews
    .map((r) => (r.date ? new Date(r.date).getTime() : null))
    .filter((t) => t !== null && !Number.isNaN(t))
    .sort((a, b) => a - b);
  if (dates.length < 5) return 0;

  const windowMs = windowDays * 24 * 60 * 60 * 1000;
  let maxInWindow = 0;
  let left = 0;
  for (let right = 0; right < dates.length; right += 1) {
    while (dates[right] - dates[left] > windowMs) {
      left += 1;
    }
    maxInWindow = Math.max(maxInWindow, right - left + 1);
  }
  const concentrationRatio = maxInWindow / dates.length;
  // 全体の1/3以上が数日間に集中していたら「バースト」とみなす
  return concentrationRatio > 0.34 ? Math.min(1, (concentrationRatio - 0.34) / 0.66 + 0.3) : 0;
}

/**
 * 星の分布配列を actual reviews（rating付き）から算出するヘルパー。
 * @param {{rating?: number}[]} reviews
 * @returns {number[]} 長さ5（インデックス0=星1 ... 4=星5）
 */
function buildDistribution(reviews) {
  const distribution = [0, 0, 0, 0, 0];
  reviews.forEach((r) => {
    const rating = Math.round(r.rating);
    if (rating >= 1 && rating <= 5) {
      distribution[rating - 1] += 1;
    }
  });
  return distribution;
}

const DEFAULT_WEIGHTS = {
  base: 0.55,
  repeatMention: 0.15,
  specificity: 0.15,
  polarizationPenalty: 0.1,
  burstPenalty: 0.05,
};

/**
 * 店舗データを総合スコア（0-100）に変換する。
 *
 * @param {object} restaurant
 * @param {number} restaurant.rating 平均評価（0-5）
 * @param {number} restaurant.reviewCount レビュー総数
 * @param {{text?: string, rating?: number, date?: string|number|Date}[]} [restaurant.reviews]
 *   サンプルレビュー（全件でなくてもよい。多いほど精度が上がる）
 * @param {number} [globalMean] ジャンル平均（デフォルト3.5）
 * @param {object} [weights] DEFAULT_WEIGHTS を上書きする重み
 * @returns {{score: number, breakdown: object}}
 */
function scoreRestaurant(restaurant, globalMean = 3.5, weights = DEFAULT_WEIGHTS) {
  const reviews = restaurant.reviews || [];
  const reviewCount = restaurant.reviewCount ?? reviews.length;
  const rating = restaurant.rating ?? 0;

  const base = bayesianAverage(rating, reviewCount, globalMean);
  const distribution = reviews.some((r) => typeof r.rating === 'number')
    ? buildDistribution(reviews)
    : restaurant.ratingDistribution || [0, 0, 0, 0, 0];

  const repeat = repeatMentionRatio(reviews);
  const specificity = specificityRatio(reviews);
  const polarization = polarizationScore(distribution);
  const burst = burstinessScore(reviews);

  const baseComponent = (base / 5) * 100 * weights.base;
  const repeatComponent = repeat * 100 * weights.repeatMention;
  const specificityComponent = specificity * 100 * weights.specificity;
  const polarizationComponent = -polarization * 100 * weights.polarizationPenalty;
  const burstComponent = -burst * 100 * weights.burstPenalty;

  const rawScore =
    baseComponent + repeatComponent + specificityComponent + polarizationComponent + burstComponent;
  const score = Math.max(0, Math.min(100, rawScore));

  return {
    score: Math.round(score * 10) / 10,
    breakdown: {
      bayesianAverage: Math.round(base * 100) / 100,
      repeatMentionRatio: Math.round(repeat * 100) / 100,
      specificityRatio: Math.round(specificity * 100) / 100,
      polarizationScore: Math.round(polarization * 100) / 100,
      burstinessScore: Math.round(burst * 100) / 100,
    },
  };
}

/**
 * 複数店舗をスコア順に並び替える。
 * @param {object[]} restaurants scoreRestaurant に渡せる店舗データの配列
 * @param {number} [globalMean]
 * @returns {{restaurant: object, score: number, breakdown: object}[]} スコア降順
 */
function rankRestaurants(restaurants, globalMean = 3.5) {
  return restaurants
    .map((restaurant) => ({ restaurant, ...scoreRestaurant(restaurant, globalMean) }))
    .sort((a, b) => b.score - a.score);
}

module.exports = {
  bayesianAverage,
  polarizationScore,
  repeatMentionRatio,
  specificityRatio,
  burstinessScore,
  buildDistribution,
  scoreRestaurant,
  rankRestaurants,
  DEFAULT_WEIGHTS,
};
