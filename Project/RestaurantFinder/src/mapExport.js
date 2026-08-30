'use strict';

/**
 * rankRestaurants() の結果を、Leaflet.js を使った単一の自己完結HTMLファイル
 * （地図に店舗をスコア付きで表示するビューア）に変換する。
 * 依存ライブラリはCDN（cdnjs.cloudflare.com）から読み込むため、生成物は
 * ネット接続のあるブラウザで直接開けば動作する。
 */

/**
 * スコア（0-100）を 赤(低評価) → 緑(高評価) のグラデーション色に変換する。
 * @param {number} score
 * @returns {string} CSS の hsl() 色文字列
 */
function scoreToColor(score) {
  const clamped = Math.max(0, Math.min(100, score));
  const hue = (clamped / 100) * 120; // 0=赤, 120=緑
  return `hsl(${hue.toFixed(0)}, 70%, 45%)`;
}

function escapeForScriptTag(json) {
  // </script> を埋め込みJSON内に含めても script タグが終端しないようにする
  return json.replace(/</g, '\\u003c');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * @param {{restaurant: object, score: number, breakdown: object}[]} rankedEntries
 *   rankRestaurants() の戻り値
 * @param {{title?: string}} [options]
 * @returns {string} 完成したHTML文字列
 */
function generateMapHtml(rankedEntries, options = {}) {
  const title = escapeHtml(options.title || 'RestaurantFinder マップ');

  const points = rankedEntries
    .filter((entry) => typeof entry.restaurant.lat === 'number' && typeof entry.restaurant.lng === 'number')
    .map((entry) => ({
      name: entry.restaurant.name || entry.restaurant.id,
      lat: entry.restaurant.lat,
      lng: entry.restaurant.lng,
      score: entry.score,
      color: scoreToColor(entry.score),
      googleMapsUri: entry.restaurant.googleMapsUri || null,
      breakdown: entry.breakdown,
    }));

  const skippedCount = rankedEntries.length - points.length;
  const dataJson = escapeForScriptTag(JSON.stringify(points));

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
<style>
  html, body { margin:0; height:100%; font-family: system-ui, sans-serif; }
  #map { position:absolute; inset:0; }
  .legend {
    position:absolute; z-index:1000; top:12px; right:12px;
    background:rgba(20,20,20,.85); color:#eee; padding:10px 14px;
    border-radius:10px; font-size:12px; line-height:1.6;
    box-shadow:0 4px 14px rgba(0,0,0,.35);
  }
  .legend .bar {
    width:120px; height:8px; border-radius:4px; margin:6px 0;
    background:linear-gradient(90deg, hsl(0,70%,45%), hsl(60,70%,45%), hsl(120,70%,45%));
  }
  .legend .scale { display:flex; justify-content:space-between; width:120px; }
  .empty-notice {
    position:absolute; z-index:1000; top:12px; left:12px;
    background:rgba(20,20,20,.85); color:#eee; padding:8px 12px;
    border-radius:8px; font-size:12px;
  }
  .popup-score { font-weight:bold; }
  .popup-breakdown { font-size:11px; color:#555; margin-top:4px; }
</style>
</head>
<body>
<div id="map"></div>
<div class="legend">
  評価基準ベース総合スコア
  <div class="bar"></div>
  <div class="scale"><span>0</span><span>50</span><span>100</span></div>
</div>
${skippedCount > 0 ? `<div class="empty-notice">${skippedCount}件は座標情報がないため地図に表示していません</div>` : ''}
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"><\/script>
<script>
  const points = JSON.parse(${JSON.stringify(dataJson)});

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  const map = L.map('map');
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);

  if (points.length === 0) {
    map.setView([35.681236, 139.767125], 12); // フォールバック：東京駅
  } else {
    const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lng]));
    points.forEach((p) => {
      const marker = L.circleMarker([p.lat, p.lng], {
        radius: 10,
        color: p.color,
        fillColor: p.color,
        fillOpacity: 0.85,
        weight: 2,
      }).addTo(map);

      const link = p.googleMapsUri && /^https:\\/\\//.test(p.googleMapsUri)
        ? '<div><a href="' + escapeHtml(p.googleMapsUri) + '" target="_blank" rel="noopener">Googleマップで見る</a></div>'
        : '';
      marker.bindPopup(
        '<div><strong>' + escapeHtml(p.name) + '</strong></div>' +
        '<div class="popup-score">総合スコア: ' + p.score + '</div>' +
        '<div class="popup-breakdown">' +
        '信頼度補正評価=' + p.breakdown.bayesianAverage +
        ' / リピート言及率=' + p.breakdown.repeatMentionRatio +
        ' / 具体性=' + p.breakdown.specificityRatio +
        ' / 二極化=' + p.breakdown.polarizationScore +
        ' / 投稿バースト=' + p.breakdown.burstinessScore +
        '</div>' + link
      );
    });
    map.fitBounds(bounds, { padding: [40, 40] });
  }
<\/script>
</body>
</html>
`;
}

module.exports = {
  generateMapHtml,
  scoreToColor,
};
