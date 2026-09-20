'use strict';

/**
 * ルートカタログ（data/routes.json）と訪問履歴（data/visitHistory.json）から
 * 「一度行ったルートは記録し、次は別の場所を優先する」形でN日分のルートを選ぶ。
 * 依存ライブラリなし。
 */

const CROWD_RISK_ORDER = { low: 0, medium: 1, high: 2 };

/**
 * ルートごとの最終訪問日からの経過日数を計算する。未訪問は Infinity。
 * @param {object} route
 * @param {{routeId: string, visitedOn: string}[]} visitHistory
 * @param {Date} today
 * @returns {number}
 */
function daysSinceLastVisit(route, visitHistory, today) {
  const visits = visitHistory
    .filter((v) => v.routeId === route.id)
    .map((v) => new Date(v.visitedOn).getTime())
    .filter((t) => !Number.isNaN(t));

  if (visits.length === 0) return Infinity;

  const lastVisit = Math.max(...visits);
  return Math.round((today.getTime() - lastVisit) / (1000 * 60 * 60 * 24));
}

/**
 * N日分のルートを選ぶ。
 *
 * 優先順位：
 *   1. maxCrowdRisk を超える混雑リスクのルートは除外（デフォルト 'medium' まで許可、'high' は除外）
 *   2. 未訪問のルートを最優先
 *   3. 訪問済みの中では、最後に行ってから日数が経っているものを優先
 *
 * @param {object[]} routes data/routes.json の配列
 * @param {{routeId: string, visitedOn: string}[]} visitHistory data/visitHistory.json の配列
 * @param {number} days 選ぶ日数
 * @param {{maxCrowdRisk?: 'low'|'medium'|'high', today?: Date, excludeIds?: string[]}} [options]
 * @returns {{route: object, daysSinceLastVisit: number, reason: string}[]}
 */
function selectRoutesForTrip(routes, visitHistory, days, options = {}) {
  const maxCrowdRisk = options.maxCrowdRisk || 'medium';
  const today = options.today || new Date();
  const excludeIds = new Set(options.excludeIds || []);
  const maxRiskLevel = CROWD_RISK_ORDER[maxCrowdRisk];

  const candidates = routes
    .filter((route) => !excludeIds.has(route.id))
    .filter((route) => CROWD_RISK_ORDER[route.crowdRisk] <= maxRiskLevel)
    .map((route) => {
      const elapsed = daysSinceLastVisit(route, visitHistory, today);
      return {
        route,
        daysSinceLastVisit: elapsed,
        reason: elapsed === Infinity ? '未訪問' : `前回訪問から${elapsed}日経過`,
      };
    });

  // 経過日数（未訪問優先）を第一基準に、同点の場合はまだ選んでいない
  // areaDirection（方角）を優先することで、3日間が同じ方向に偏らないようにする。
  const selected = [];
  const usedAreaDirections = new Set();
  const remaining = [...candidates];

  for (let i = 0; i < days && remaining.length > 0; i += 1) {
    remaining.sort((a, b) => {
      if (a.daysSinceLastVisit !== b.daysSinceLastVisit) {
        return b.daysSinceLastVisit - a.daysSinceLastVisit; // Infinity（未訪問）が先頭
      }
      const aUsed = usedAreaDirections.has(a.route.areaDirection) ? 1 : 0;
      const bUsed = usedAreaDirections.has(b.route.areaDirection) ? 1 : 0;
      if (aUsed !== bUsed) return aUsed - bUsed;
      return a.route.name.localeCompare(b.route.name, 'ja');
    });
    const pick = remaining.shift();
    selected.push(pick);
    if (pick.route.areaDirection) usedAreaDirections.add(pick.route.areaDirection);
  }

  return selected;
}

module.exports = {
  daysSinceLastVisit,
  selectRoutesForTrip,
};
