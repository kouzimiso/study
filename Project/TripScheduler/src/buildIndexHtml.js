'use strict';

/**
 * TripSchedulerのデータ（routes.json / visitHistory.json）を1つのHTMLページに
 * 埋め込んで、ブラウザで開くだけで見られるGUIを生成する。
 *
 * - 「現地プラン作成」タブ：地点を指定して動的にOSM上のスポットを検索し、
 *   旅程（時間割）を自動生成するメイン機能。検索結果は自動的に
 *   「ルートカタログ」タブの検索履歴にも追記される
 * - 「ルートカタログ」タブ：手動登録のRoute一覧（訪問履歴バッジ付き）＋
 *   「現地プラン作成」タブで検索するたびに増える検索履歴（ブラウザの
 *   localStorageに保存、このページ単体では他の端末と共有されない）
 * - 「地図」タブ：Leaflet地図（CDN）にRouteの検索中心座標と、検索履歴の
 *   中心座標をマーカー表示
 * - 「楽天ホテル検索」タブ：ブラウザから直接 openapi.rakuten.co.jp を呼ぶ。
 *   APIキーはブラウザのlocalStorageにのみ保存し、このファイルやリポジトリには書き込まない
 *   （楽天API側のCORSはAccess-Control-Allow-Origin: *で許可されているため直接呼べる。
 *   ただし「アプリ登録」で設定したApplication URLとブラウザのRefererが一致する必要がある。
 *   このページはGitHub Pages等、登録したURL上で開くことを想定）。
 *
 * 旧「旅程」タブ（`data/silver-week-2026.json`という固定データを表示するだけの
 * タブ）は、「現地プラン作成」タブが同じカード表示で動的に旅程を作れるように
 * なったため廃止した（固定データ自体や.ics/ガントチャート変換CLIは
 * `src/planTrip.js`等として引き続き使える）。
 */

const fs = require('fs');
const path = require('path');

function escapeForScriptTag(json) {
  return json.replace(/</g, '\\u003c');
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const CROWD_RISK_LABEL = { low: '空いている傾向', medium: 'やや混雑', high: '激混み想定' };
const CROWD_RISK_COLOR = { low: '#45B08C', medium: '#E8C22C', high: '#C1503A' };

function daysSince(dateStr, today) {
  const diff = today.getTime() - new Date(`${dateStr}T00:00:00Z`).getTime();
  return Math.round(diff / (1000 * 60 * 60 * 24));
}

/**
 * @param {{routes: object[], visitHistory: object[]}} data
 * @param {{title?: string, today?: Date}} [options]
 * @returns {string} 完成したHTML文字列
 */
function buildIndexHtml(data, options = {}) {
  const title = escapeHtml(options.title || 'TripScheduler');
  const today = options.today || new Date();

  // 動的プランナー用のロジック（Node.js/ブラウザ両対応のUMDモジュール）をそのまま
  // <script>として埋め込む。ブラウザではwindow.TripScheduler*に展開される。
  const embeddedModules = ['buildDaySchedule.js', 'overpassSpots.js', 'geocode.js', 'dynamicScheduler.js', 'routeLine.js']
    .map((file) => fs.readFileSync(path.join(__dirname, file), 'utf8'))
    .join('\n');

  const lastVisitByRoute = new Map();
  (data.visitHistory || []).forEach((v) => {
    const prev = lastVisitByRoute.get(v.routeId);
    if (!prev || v.visitedOn > prev) lastVisitByRoute.set(v.routeId, v.visitedOn);
  });

  const routesWithVisit = (data.routes || []).map((route) => {
    const lastVisit = lastVisitByRoute.get(route.id);
    return {
      ...route,
      visitStatus: lastVisit ? `前回訪問から${daysSince(lastVisit, today)}日` : '未訪問',
    };
  });

  const payload = {
    routes: routesWithVisit,
    generatedAt: today.toISOString(),
  };
  const payloadJson = escapeForScriptTag(JSON.stringify(payload));

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
<style>
  :root {
    --bg-deep:#0E1517; --panel:#16211F; --panel-border:#283835;
    --text-primary:#EAF3EE; --text-muted:#8CA39B;
    --accent:#45B08C; --accent-dim:#2C6E58;
    --warn:#E8C22C; --danger:#C1503A;
  }
  * { box-sizing: border-box; }
  html, body { margin:0; background:var(--bg-deep); color:var(--text-primary);
    font-family: 'Hiragino Sans', 'Yu Gothic', system-ui, sans-serif; }
  header { padding:16px 20px; border-bottom:1px solid var(--panel-border); }
  header h1 { margin:0; font-size:18px; letter-spacing:.02em; }
  header p { margin:4px 0 0; font-size:12px; color:var(--text-muted); }
  nav { display:flex; gap:4px; padding:0 16px; border-bottom:1px solid var(--panel-border);
    overflow-x:auto; }
  nav button { background:none; border:none; color:var(--text-muted); padding:12px 16px;
    font-size:13px; cursor:pointer; border-bottom:2px solid transparent; white-space:nowrap; }
  nav button.active { color:var(--accent); border-bottom-color:var(--accent); }
  main { padding:16px 20px 40px; max-width:900px; margin:0 auto; }
  .tab { display:none; }
  .tab.active { display:block; }
  .day-card { background:var(--panel); border:1px solid var(--panel-border); border-radius:12px;
    padding:14px 16px; margin-bottom:16px; }
  .day-card h2 { margin:0 0 10px; font-size:15px; color:var(--accent); }
  .event-row { display:flex; gap:12px; padding:8px 0; border-top:1px solid var(--panel-border); }
  .event-row:first-child { border-top:none; }
  .event-time { flex:0 0 90px; font-size:12px; color:var(--text-muted); font-family:monospace; }
  .event-body .title { font-size:13px; }
  .event-body .meta { font-size:11px; color:var(--text-muted); margin-top:2px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px;
    margin-right:6px; }
  .route-card { background:var(--panel); border:1px solid var(--panel-border); border-radius:12px;
    padding:14px 16px; margin-bottom:14px; }
  .route-card h3 { margin:0 0 6px; font-size:14px; }
  .route-card .notes { font-size:12px; color:var(--text-muted); margin:6px 0; }
  .tag { display:inline-block; background:var(--accent-dim); color:var(--text-primary);
    border-radius:6px; padding:2px 8px; font-size:11px; margin:2px 4px 0 0; }
  #map { height:480px; border-radius:12px; margin-top:8px; }
  .field { margin-bottom:10px; }
  .field label { display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px; }
  .field input { width:100%; padding:8px 10px; border-radius:8px; border:1px solid var(--panel-border);
    background:#0B1011; color:var(--text-primary); font-size:13px; }
  .btn { background:var(--accent); color:#06120D; border:none; border-radius:8px;
    padding:10px 16px; font-size:13px; cursor:pointer; font-weight:600; }
  .btn.secondary { background:none; border:1px solid var(--panel-border); color:var(--text-primary); }
  .hint { font-size:11px; color:var(--text-muted); line-height:1.6; margin-top:10px; }
  .result-list { margin-top:12px; }
  .result-item { padding:8px 0; border-top:1px solid var(--panel-border); font-size:13px; }
  .row { display:flex; gap:10px; flex-wrap:wrap; }
  .row .field { flex:1 1 140px; }
</style>
</head>
<body>
<header>
  <h1>${title}</h1>
  <p>地点を指定して動的に組む旅程プランナーと、検索するたびに増えるRouteカタログ、ホテル検索をまとめたページ</p>
</header>
<nav>
  <button data-tab="planner" class="active">現地プラン作成</button>
  <button data-tab="routes">ルートカタログ</button>
  <button data-tab="map">地図</button>
  <button data-tab="hotel">楽天ホテル検索</button>
</nav>
<main>
  <section id="tab-routes" class="tab"></section>
  <section id="tab-map" class="tab">
    <div id="map"></div>
    <p class="hint">緑系の丸=手動登録のRouteカタログ（色は混雑リスクの目安：緑=空いている傾向／黄=やや混雑／赤=激混み想定）、青の四角=「現地プラン作成」タブの検索履歴。マーカーをクリックすると詳細を表示します。</p>
  </section>
  <section id="tab-planner" class="tab active">
    <div id="dp-file-warning" class="route-card" style="display:none;border-color:#E8C22C;">
      <h3 style="color:#E8C22C;">⚠️ file:// で開いています</h3>
      <p class="notes">
        このページを <code>file://</code> で直接開くと、ブラウザは
        <code>Origin: null</code> としてリクエストを送るため、
        overpass-api.de 等のサーバーがCORSヘッダーを返さず、
        スポット検索が失敗することがあります（コンソールに
        <code>No 'Access-Control-Allow-Origin' header is present</code>
        と出ていたら、これが原因です）。<br/><br/>
        <strong>回避策</strong>：このフォルダでローカルサーバーを起動してから、
        <code>http://localhost:8000/index.html</code> のようなURLで開いてください。
        例：<code>npx serve .</code> または <code>python -m http.server 8000</code>。
        GitHub Pages等で公開して開くのでも構いません。
      </p>
    </div>
    <div class="route-card">
      <h3>地点から動的にプランを作る</h3>
      <p class="notes">
        地名を入力すると、その周辺のOpenStreetMap上の観光地・飲食店・Wifi/電源カフェ・
        温泉銭湯を検索し、1日あたりの立ち寄り先を自動で選んで時間割を組みます
        （APIキー不要、ブラウザから直接OSMに問い合わせます）。
      </p>
      <div class="row">
        <div class="field" style="flex:2 1 200px;">
          <label>地点（地名・駅名など）</label>
          <input id="dp-location" type="text" placeholder="例：鎌倉駅" />
        </div>
        <div class="field" style="flex:0 0 auto;align-self:flex-end;">
          <button class="btn secondary" id="dp-use-gps" type="button">📍 現在地を使う</button>
        </div>
      </div>
      <div class="row">
        <div class="field"><label>検索半径(km)</label><input id="dp-radius" type="number" value="2" min="0.5" max="10" step="0.5" /></div>
        <div class="field"><label>日数</label><input id="dp-days" type="number" value="1" min="1" max="7" step="1" /></div>
        <div class="field"><label>移動手段</label>
          <select id="dp-mode" style="width:100%;padding:8px;border-radius:8px;background:#0B1011;color:#EAF3EE;border:1px solid #283835;">
            <option value="walk">徒歩</option>
            <option value="bike">自転車</option>
            <option value="car" selected>車</option>
          </select>
        </div>
      </div>
      <div class="row">
        <div class="field"><label>開始日</label><input id="dp-start-date" type="date" /></div>
        <div class="field"><label>1日目の開始時刻</label><input id="dp-start-time" type="time" value="09:00" /></div>
      </div>
      <div class="field">
        <label>検索するスポットの種類</label>
        <div style="display:flex;gap:14px;flex-wrap:wrap;font-size:12px;">
          <label style="display:flex;align-items:center;gap:4px;white-space:nowrap;"><input type="checkbox" id="dp-cat-sightseeing" checked /> 観光地</label>
          <label style="display:flex;align-items:center;gap:4px;white-space:nowrap;"><input type="checkbox" id="dp-cat-food" checked /> 飲食店</label>
          <label style="display:flex;align-items:center;gap:4px;white-space:nowrap;"><input type="checkbox" id="dp-cat-wifi" checked /> Wifi/電源</label>
          <label style="display:flex;align-items:center;gap:4px;white-space:nowrap;"><input type="checkbox" id="dp-cat-onsen" /> 温泉・銭湯</label>
        </div>
      </div>
      <button class="btn" id="dp-go" type="button">🔍 検索してスケジュールを作る</button>
      <p id="dp-status" class="hint"></p>
    </div>
    <div id="dp-map-wrap" class="route-card" style="display:none;">
      <h3>検索結果マップ</h3>
      <div id="dp-map" style="height:360px;border-radius:12px;"></div>
      <p id="dp-map-note" class="hint"></p>
    </div>
    <div id="dp-result"></div>
  </section>
  <section id="tab-hotel" class="tab">
    <div class="route-card">
      <h3>楽天トラベルAPI キー設定</h3>
      <p class="notes">
        キーはこの端末のブラウザ（localStorage）にのみ保存され、サーバーには送信されません。
        楽天API側のCORSはブラウザからの直接アクセスを許可していますが、
        「アプリ登録」で設定したApplication URLとこのページの実際のURLのRefererが
        一致しないと <code>HTTP_REFERRER_NOT_ALLOWED</code> で失敗します。
      </p>
      <div class="row">
        <div class="field"><label>Application ID</label><input id="rk-app-id" type="text" /></div>
        <div class="field"><label>Access Key</label><input id="rk-access-key" type="text" /></div>
        <div class="field"><label>Affiliate ID（任意）</label><input id="rk-affiliate-id" type="text" /></div>
      </div>
      <button class="btn secondary" id="rk-save">このブラウザに保存</button>
    </div>
    <div class="route-card">
      <h3>検索</h3>
      <div class="field">
        <label>対象Route（選ぶと緯度経度を自動入力）</label>
        <select id="rk-route-select" style="width:100%;padding:8px;border-radius:8px;background:#0B1011;color:#EAF3EE;border:1px solid #283835;"></select>
      </div>
      <div class="row">
        <div class="field"><label>緯度</label><input id="rk-lat" type="text" /></div>
        <div class="field"><label>経度</label><input id="rk-lng" type="text" /></div>
        <div class="field"><label>半径(km, 0.1-3.0)</label><input id="rk-radius" type="text" value="3.0" /></div>
      </div>
      <div class="row">
        <div class="field"><label>チェックイン日（空欄なら空室を問わず施設検索）</label><input id="rk-checkin" type="date" /></div>
      </div>
      <button class="btn" id="rk-search">検索する</button>
      <div id="rk-result" class="result-list"></div>
    </div>
  </section>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"><\/script>
<script>
` + embeddedModules + `
  const DATA = JSON.parse(${JSON.stringify(payloadJson)});
  const CROWD_COLOR = ${JSON.stringify(CROWD_RISK_COLOR)};
  const CROWD_LABEL = ${JSON.stringify(CROWD_RISK_LABEL)};
  const CATEGORY_LABEL = { move:'移動', sightseeing:'観光', food:'食事', onsen:'温泉', work:'Wifi/電源' };
  const CATEGORY_COLOR = { move:'#8CA39B', sightseeing:'#45B08C', food:'#E8C22C', onsen:'#5EA8E8', work:'#B98AE0' };

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ─── 検索履歴（ルートカタログの自動追加分）───
  // 「現地プラン作成」タブで検索するたびに1件追加される。サーバーを
  // 持たないページなので、この端末のブラウザのlocalStorageにのみ保存する
  // （他の端末・他のブラウザとは共有されない）。
  const SEARCH_HISTORY_KEY = 'tripscheduler_searchHistory';
  const SEARCH_HISTORY_LIMIT = 200;

  function loadSearchHistory() {
    try {
      const raw = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY) || '[]');
      return Array.isArray(raw) ? raw : [];
    } catch (err) {
      return [];
    }
  }

  function saveSearchHistoryEntry(entry) {
    const list = loadSearchHistory();
    list.unshift(entry);
    try {
      localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(list.slice(0, SEARCH_HISTORY_LIMIT)));
    } catch (err) {
      // localStorageが使えない（プライベートモード等）場合は履歴への追加のみ諦める
    }
  }

  function deleteSearchHistoryEntry(id) {
    const list = loadSearchHistory().filter((e) => e.id !== id);
    try {
      localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(list));
    } catch (err) {
      // 無視
    }
  }

  function clearSearchHistory() {
    try {
      localStorage.removeItem(SEARCH_HISTORY_KEY);
    } catch (err) {
      // 無視
    }
  }

  function buildDayCardsHtml(events) {
    const byDate = new Map();
    events.forEach((e) => {
      if (!byDate.has(e.date)) byDate.set(e.date, []);
      byDate.get(e.date).push(e);
    });
    const dates = [...byDate.keys()].sort();
    return dates.map((date) => {
      const dayEvents = byDate.get(date).slice().sort((a, b) => a.start.localeCompare(b.start));
      const rows = dayEvents.map((e) => {
        const color = CATEGORY_COLOR[e.category] || '#8CA39B';
        const label = CATEGORY_LABEL[e.category] || e.category || '';
        return '<div class="event-row">' +
          '<div class="event-time">' + escapeHtml(e.start) + '-' + escapeHtml(e.end) + '</div>' +
          '<div class="event-body">' +
            '<div class="title">' +
              '<span class="badge" style="background:' + color + '22;color:' + color + ';">' + escapeHtml(label) + '</span>' +
              escapeHtml(e.title) +
            '</div>' +
            '<div class="meta">' + escapeHtml(e.location || '') + (e.description ? ' / ' + escapeHtml(e.description) : '') + '</div>' +
          '</div>' +
        '</div>';
      }).join('');
      return '<div class="day-card"><h2>' + escapeHtml(date) + '</h2>' + rows + '</div>';
    }).join('');
  }

  function buildSearchHistoryCardHtml(entry) {
    const typeLabels = (entry.types || []).map((t) => CATEGORY_LABEL[t] || t).join('・');
    const usedTotal = (entry.usedCounts || []).reduce((sum, n) => sum + n, 0);
    return '<div class="route-card" data-search-id="' + escapeHtml(entry.id) + '">' +
      '<h3>📍 ' + escapeHtml(entry.centerName || '検索地点') + '</h3>' +
      '<span class="badge" style="background:#5EA8E822;color:#5EA8E8;">現地プラン作成の検索履歴</span>' +
      '<p class="notes">' +
        escapeHtml(new Date(entry.searchedAt).toLocaleString('ja-JP')) + ' / 半径' + escapeHtml(entry.radiusKm) + 'km / ' +
        escapeHtml(entry.days) + '日分 / ' + escapeHtml({ walk: '徒歩', bike: '自転車', car: '車' }[entry.mode] || entry.mode) +
      '</p>' +
      '<p class="notes">対象: ' + escapeHtml(typeLabels) + ' / 周辺' + escapeHtml(entry.totalSpots) + '件中' + escapeHtml(usedTotal) + '件を採用</p>' +
      '<button class="btn secondary" data-del-search-id="' + escapeHtml(entry.id) + '" style="font-size:11px;padding:4px 10px;">この履歴を削除</button>' +
    '</div>';
  }

  function renderRoutes() {
    const curatedHtml = DATA.routes.map((route) => {
      const riskColor = CROWD_COLOR[route.crowdRisk] || '#8CA39B';
      const riskLabel = CROWD_LABEL[route.crowdRisk] || route.crowdRisk || '';
      const tags = (route.tags || []).map((t) => '<span class="tag">' + escapeHtml(t) + '</span>').join('');
      const highlights = (route.highlights || []).map((h) => '<li>' + escapeHtml(h) + '</li>').join('');
      return '<div class="route-card">' +
        '<h3>' + escapeHtml(route.name) + '</h3>' +
        '<span class="badge" style="background:' + riskColor + '22;color:' + riskColor + ';">' + escapeHtml(riskLabel) + '</span>' +
        '<span class="badge" style="background:#8CA39B22;color:#8CA39B;">' + escapeHtml(route.visitStatus) + '</span>' +
        '<p class="notes">' + escapeHtml(route.areaDirection || '') + ' / 車' + escapeHtml((route.accessFromOfuna && route.accessFromOfuna.car) || '') + ' / 目安' + escapeHtml(route.recommendedDurationHours || '') + '時間</p>' +
        (highlights ? '<ul style="margin:6px 0 0;padding-left:18px;font-size:12px;">' + highlights + '</ul>' : '') +
        '<p class="notes">' + escapeHtml(route.notes || '') + '</p>' +
        tags +
      '</div>';
    }).join('');

    const history = loadSearchHistory();
    const historyHtml = history.length
      ? '<h2 style="font-size:14px;margin:18px 0 10px;color:var(--text-muted);">🔎 現地プラン作成の検索履歴（' + history.length + '件・この端末のブラウザにのみ保存）' +
          '<button class="btn secondary" id="routes-clear-history" style="font-size:11px;padding:3px 8px;margin-left:8px;">すべて削除</button>' +
        '</h2>' +
        history.map(buildSearchHistoryCardHtml).join('')
      : '';

    document.getElementById('tab-routes').innerHTML = curatedHtml + historyHtml;

    document.querySelectorAll('[data-del-search-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        deleteSearchHistoryEntry(btn.getAttribute('data-del-search-id'));
        renderRoutes();
        if (leafletMap) renderSearchHistoryMarkers();
      });
    });
    const clearBtn = document.getElementById('routes-clear-history');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (!confirm('検索履歴をすべて削除しますか？（手動登録のRouteカタログは消えません）')) return;
        clearSearchHistory();
        renderRoutes();
        if (leafletMap) renderSearchHistoryMarkers();
      });
    }
  }

  let leafletMap = null;
  let searchHistoryLayer = null;

  function renderSearchHistoryMarkers() {
    if (!leafletMap) return;
    if (searchHistoryLayer) leafletMap.removeLayer(searchHistoryLayer);
    searchHistoryLayer = L.layerGroup();
    loadSearchHistory().forEach((entry) => {
      if (typeof entry.centerLat !== 'number' || typeof entry.centerLng !== 'number') return;
      const marker = L.rectangle(
        [[entry.centerLat - 0.003, entry.centerLng - 0.003], [entry.centerLat + 0.003, entry.centerLng + 0.003]],
        { color: '#5EA8E8', fillColor: '#5EA8E8', fillOpacity: 0.7, weight: 1.5 }
      );
      marker.bindPopup(
        '<strong>' + escapeHtml(entry.centerName || '検索地点') + '</strong>（検索履歴）<br/>' +
        '<span style="font-size:11px;color:#555;">' + escapeHtml(new Date(entry.searchedAt).toLocaleString('ja-JP')) + '</span>'
      );
      searchHistoryLayer.addLayer(marker);
    });
    searchHistoryLayer.addTo(leafletMap);
  }

  function renderMap() {
    const withCenter = DATA.routes.filter((r) => r.searchCenter);
    const map = L.map('map');
    leafletMap = map;
    // OpenStreetMap公式タイル（{s}.tile.openstreetmap.org）は利用ポリシーが厳格化され、
    // ブラウザからの直接アクセスが「Access blocked」で拒否されることが増えたため、
    // 日本国内限定のアプリであることを踏まえ、無料・APIキー不要・出典明記のみで使える
    // 国土地理院（GSI）の淡色地図タイルを使う。
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', {
      attribution: '地図: <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>',
      maxZoom: 18,
    }).addTo(map);

    const history = loadSearchHistory();
    const boundPoints = withCenter.map((r) => [r.searchCenter.lat, r.searchCenter.lng])
      .concat(history.filter((h) => typeof h.centerLat === 'number').map((h) => [h.centerLat, h.centerLng]));

    if (boundPoints.length === 0) {
      map.setView([35.3556, 139.5309], 10);
      renderSearchHistoryMarkers();
      return;
    }
    withCenter.forEach((route) => {
      const color = CROWD_COLOR[route.crowdRisk] || '#8CA39B';
      const marker = L.circleMarker([route.searchCenter.lat, route.searchCenter.lng], {
        radius: 10, color, fillColor: color, fillOpacity: 0.85, weight: 2,
      }).addTo(map);
      const tags = (route.tags || []).join(' / ');
      marker.bindPopup(
        '<strong>' + escapeHtml(route.name) + '</strong><br/>' +
        escapeHtml(CROWD_LABEL[route.crowdRisk] || '') + '<br/>' +
        '<span style="font-size:11px;color:#555;">' + escapeHtml(tags) + '</span>'
      );
    });
    renderSearchHistoryMarkers();
    map.fitBounds(L.latLngBounds(boundPoints), { padding: [40, 40] });
  }

  function initHotelTab() {
    const select = document.getElementById('rk-route-select');
    DATA.routes.filter((r) => r.searchCenter).forEach((route) => {
      const opt = document.createElement('option');
      opt.value = JSON.stringify(route.searchCenter);
      opt.textContent = route.name;
      select.appendChild(opt);
    });
    select.addEventListener('change', () => {
      if (!select.value) return;
      const c = JSON.parse(select.value);
      document.getElementById('rk-lat').value = c.lat;
      document.getElementById('rk-lng').value = c.lng;
    });

    ['rk-app-id', 'rk-access-key', 'rk-affiliate-id'].forEach((id) => {
      const key = 'tripscheduler_' + id;
      const saved = localStorage.getItem(key);
      if (saved) document.getElementById(id).value = saved;
    });
    document.getElementById('rk-save').addEventListener('click', () => {
      ['rk-app-id', 'rk-access-key', 'rk-affiliate-id'].forEach((id) => {
        localStorage.setItem('tripscheduler_' + id, document.getElementById(id).value.trim());
      });
      alert('このブラウザに保存しました。');
    });

    document.getElementById('rk-search').addEventListener('click', async () => {
      const appId = document.getElementById('rk-app-id').value.trim();
      const accessKey = document.getElementById('rk-access-key').value.trim();
      const affiliateId = document.getElementById('rk-affiliate-id').value.trim();
      const lat = document.getElementById('rk-lat').value.trim();
      const lng = document.getElementById('rk-lng').value.trim();
      const radius = document.getElementById('rk-radius').value.trim() || '3.0';
      const checkin = document.getElementById('rk-checkin').value;
      const resultEl = document.getElementById('rk-result');

      if (!appId || !accessKey) { alert('Application ID と Access Key を入力してください。'); return; }
      if (!lat || !lng) { alert('緯度・経度を入力するか、対象Routeを選んでください。'); return; }

      resultEl.innerHTML = '<p class="hint">検索中…</p>';
      try {
        const params = new URLSearchParams({
          applicationId: appId, accessKey, format: 'json', formatVersion: '2',
          datumType: '1', latitude: lat, longitude: lng, searchRadius: radius,
          hits: '10', responseType: 'large',
        });
        if (affiliateId) params.set('affiliateId', affiliateId);
        let endpoint = 'https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731';
        if (checkin) {
          endpoint = 'https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426';
          const checkout = new Date(checkin + 'T00:00:00Z');
          checkout.setUTCDate(checkout.getUTCDate() + 1);
          params.set('checkinDate', checkin);
          params.set('checkoutDate', checkout.toISOString().slice(0, 10));
          params.set('adultNum', '2');
        }
        const res = await fetch(endpoint + '?' + params.toString());
        const data = await res.json();
        if (data.errors) {
          resultEl.innerHTML = '<p class="hint" style="color:#C1503A;">エラー: ' + escapeHtml(data.errors.errorMessage || JSON.stringify(data.errors)) + '</p>';
          return;
        }
        const hotels = (data.hotels || []).map((h) => {
          const parts = Array.isArray(h) ? h : [h];
          const basic = (parts.find((p) => p && p.hotelBasicInfo) || {}).hotelBasicInfo || {};
          return basic;
        });
        if (hotels.length === 0) {
          resultEl.innerHTML = '<p class="hint">該当する施設が見つかりませんでした。</p>';
          return;
        }
        resultEl.innerHTML = hotels.map((h) =>
          '<div class="result-item"><strong>' + escapeHtml(h.hotelName || '(名称不明)') + '</strong>' +
          (h.hotelInformationUrl ? ' — <a href="' + escapeHtml(h.hotelInformationUrl) + '" target="_blank" rel="noopener" style="color:#45B08C;">詳細</a>' : '') +
          '</div>'
        ).join('');
      } catch (err) {
        resultEl.innerHTML = '<p class="hint" style="color:#C1503A;">通信エラー: ' + escapeHtml(err.message) + '</p>';
      }
    });
  }

  // ─── 現地プラン作成タブ：地点を指定し、OSM上の周辺スポットから動的に
  // スケジュールを組む（Test/travel-route-planner.html の考え方を踏襲）───
  let dpMap = null;

  function addDaysISO(dateStr, days) {
    const d = new Date(dateStr + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 10);
  }

  const DAY_LINE_COLORS = ['#45B08C', '#5EA8E8', '#E8C22C', '#B98AE0', '#C1503A', '#E8955B', '#8CA39B'];

  /**
   * @param {{lat:number,lng:number,name?:string}} center
   * @param {object[]} spots findSpotsAround()が返した全候補（採用/不採用を含む）
   * @param {object[]} events buildDynamicDaySchedule()が返したイベント配列（複数日分）
   * @param {{lat:number,lng:number}[][]} dayWaypoints 日ごとの巡回順（中心→スポット→…→中心）の座標配列
   * @param {'walk'|'bike'|'car'} mode
   */
  async function renderPlannerMap(center, spots, events, dayWaypoints, mode) {
    const mapWrap = document.getElementById('dp-map-wrap');
    mapWrap.style.display = 'block';
    if (!dpMap) {
      dpMap = L.map('dp-map');
      L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', {
        attribution: '地図: <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>',
        maxZoom: 18,
      }).addTo(dpMap);
    } else {
      dpMap.eachLayer((layer) => { if (!(layer instanceof L.TileLayer)) dpMap.removeLayer(layer); });
    }
    setTimeout(() => dpMap.invalidateSize(), 0);

    const noteEl = document.getElementById('dp-map-note');
    noteEl.textContent = '経路を計算中…';

    const usedSpotIds = new Set(events.filter((e) => e.spotId).map((e) => e.spotId));
    const bounds = [[center.lat, center.lng]];
    L.marker([center.lat, center.lng]).addTo(dpMap)
      .bindPopup('<strong>' + escapeHtml(center.name || '出発地点') + '</strong>（出発地点）');

    spots.forEach((spot) => {
      const used = usedSpotIds.has(spot.id);
      const color = used ? (CATEGORY_COLOR[spot.type] || '#45B08C') : '#4A5A55';
      const marker = L.circleMarker([spot.lat, spot.lng], {
        radius: used ? 9 : 5, color, fillColor: color, fillOpacity: used ? 0.9 : 0.35, weight: used ? 2 : 1,
      }).addTo(dpMap);
      marker.bindPopup(
        '<strong>' + escapeHtml(spot.name) + '</strong><br/>' +
        escapeHtml(CATEGORY_LABEL[spot.type] || spot.type) + (used ? '（スケジュールに採用）' : '')
      );
      bounds.push([spot.lat, spot.lng]);
    });

    dpMap.fitBounds(bounds, { padding: [40, 40] });

    // 日ごとの巡回ルートをOSRM（失敗時は直線近似）で描画する
    // （Test/travel-route-planner.htmlのルート表示を踏襲）。
    let anyFallback = false;
    let anyReal = false;
    for (let dayIdx = 0; dayIdx < (dayWaypoints || []).length; dayIdx++) {
      const points = dayWaypoints[dayIdx];
      if (!points || points.length < 2) continue;
      let line;
      try {
        line = await TripSchedulerRouteLine.fetchRouteLine(points, mode);
      } catch (err) {
        line = { coords: points.map((p) => [p.lng, p.lat]), real: false };
      }
      if (line.real) anyReal = true; else anyFallback = true;
      const latlngs = line.coords.map((c) => [c[1], c[0]]);
      const color = DAY_LINE_COLORS[dayIdx % DAY_LINE_COLORS.length];
      L.polyline(latlngs, {
        color, weight: 4, opacity: 0.75, dashArray: line.real ? null : '7,7',
      }).addTo(dpMap).bindPopup((dayIdx + 1) + '日目の移動ルート' + (line.real ? '' : '（直線近似）'));
    }

    if (anyFallback && anyReal) {
      noteEl.textContent = '一部の日は道路ルートAPI（OSRM）が応答しなかったため、直線（破線）で近似表示しています。';
    } else if (anyFallback && !anyReal) {
      noteEl.textContent = '道路ルートAPI（OSRM）に接続できなかったため、すべて直線（破線）で近似表示しています。';
    } else {
      noteEl.textContent = '';
    }
  }

  function initPlannerTab() {
    const statusEl = document.getElementById('dp-status');
    const resultEl = document.getElementById('dp-result');
    const locInput = document.getElementById('dp-location');

    if (location.protocol === 'file:') {
      document.getElementById('dp-file-warning').style.display = 'block';
    }

    function setStatus(msg, isError) {
      statusEl.textContent = msg;
      statusEl.style.color = isError ? '#C1503A' : '';
    }

    document.getElementById('dp-use-gps').addEventListener('click', () => {
      if (!navigator.geolocation) { setStatus('このブラウザは現在地取得に対応していません', true); return; }
      setStatus('現在地を取得中…');
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          locInput.value = '現在地';
          locInput.dataset.lat = pos.coords.latitude;
          locInput.dataset.lng = pos.coords.longitude;
          setStatus('現在地を取得しました（' + pos.coords.latitude.toFixed(4) + ', ' + pos.coords.longitude.toFixed(4) + '）');
        },
        () => setStatus('現在地の取得に失敗しました。地名を入力してください。', true),
        { timeout: 10000 }
      );
    });

    locInput.addEventListener('input', () => {
      delete locInput.dataset.lat;
      delete locInput.dataset.lng;
    });

    document.getElementById('dp-go').addEventListener('click', async () => {
      const radiusKm = parseFloat(document.getElementById('dp-radius').value) || 2;
      const days = Math.max(1, Math.min(7, parseInt(document.getElementById('dp-days').value, 10) || 1));
      const mode = document.getElementById('dp-mode').value;
      const startDateInput = document.getElementById('dp-start-date').value;
      const startTime = document.getElementById('dp-start-time').value || '09:00';

      const types = [];
      if (document.getElementById('dp-cat-sightseeing').checked) types.push('sightseeing');
      if (document.getElementById('dp-cat-food').checked) types.push('food');
      if (document.getElementById('dp-cat-wifi').checked) types.push('wifi');
      if (document.getElementById('dp-cat-onsen').checked) types.push('onsen');
      if (types.length === 0) { setStatus('スポットの種類を1つ以上選んでください', true); return; }

      resultEl.innerHTML = '';

      let center;
      if (locInput.dataset.lat && locInput.dataset.lng) {
        center = { lat: parseFloat(locInput.dataset.lat), lng: parseFloat(locInput.dataset.lng), name: '現在地' };
      } else {
        const query = locInput.value.trim();
        if (!query) { setStatus('地点を入力するか、現在地を使ってください', true); return; }
        setStatus('地点を検索中…（Nominatimへ問い合わせています）');
        let geo;
        try {
          geo = await TripSchedulerGeocode.geocodeLocation(query);
        } catch (err) {
          setStatus('地点検索でエラーが発生しました: ' + err.message, true);
          return;
        }
        if (!geo) { setStatus('「' + query + '」が見つかりませんでした。別の表記で試してください。', true); return; }
        center = { lat: geo.lat, lng: geo.lng, name: geo.name };
      }

      setStatus('周辺のスポットを検索中…（OpenStreetMap Overpass APIへ問い合わせています。混雑時は最大20秒ほどかかります）');
      let spots;
      try {
        spots = await TripSchedulerOverpassSpots.findSpotsAround(center.lat, center.lng, Math.round(radiusKm * 1000), types);
      } catch (err) {
        const isTimeout = /timed out|AbortError/i.test((err && err.name) || '') || /timed out/i.test((err && err.message) || '');
        setStatus(
          'Overpass APIへの接続に失敗しました（' + err.message + '）。' +
          (isTimeout
            ? '複数のOverpassミラーすべてが混雑等で20秒以内に応答しませんでした。' +
              '少し時間をおいて再試行するか、検索半径を狭めてみてください。'
            : '広告ブロッカーやセキュリティ系の拡張機能（uBlock Origin等）が ' +
              'overpass-api.de 系のドメインをブロックしていないか確認してください' +
              '（一度シークレットウィンドウで試すと切り分けられます）。') +
          '詳細はブラウザの開発者ツール（F12）のConsoleタブにも出力しています。',
          true
        );
        return;
      }

      if (spots.length === 0) {
        setStatus('半径' + radiusKm + 'km以内にスポットが見つかりませんでした。半径を広げるか種類を増やしてみてください。');
        return;
      }

      const remaining = spots.slice();
      const allEvents = [];
      const usedCounts = [];
      const dayWaypoints = [];
      const baseDate = startDateInput || new Date().toISOString().slice(0, 10);

      for (let i = 0; i < days; i++) {
        const date = addDaysISO(baseDate, i);
        const daySpots = TripSchedulerDynamicScheduler.selectSpotsForDay(remaining, {});
        daySpots.forEach((s) => {
          const idx = remaining.findIndex((r) => r.id === s.id);
          if (idx >= 0) remaining.splice(idx, 1);
        });
        usedCounts.push(daySpots.length);
        const events = TripSchedulerDynamicScheduler.buildDynamicDaySchedule(center, date, daySpots, {
          startTime: i === 0 ? startTime : '09:00',
          mode,
        });
        allEvents.push(...events);

        // 地図にルートを描くための、その日の巡回順（中心→スポット→…→中心）。
        // buildDynamicDaySchedule()の内部で使っている順序決定ロジックと同じ
        // orderSpotsGreedy()を使うことで、表示されるルートと時間割の順序を一致させる。
        const ordered = TripSchedulerDynamicScheduler.orderSpotsGreedy(center, daySpots);
        if (ordered.length > 0) {
          dayWaypoints.push([
            { lat: center.lat, lng: center.lng },
            ...ordered.map((s) => ({ lat: s.lat, lng: s.lng })),
            { lat: center.lat, lng: center.lng },
          ]);
        } else {
          dayWaypoints.push([]);
        }
      }

      if (allEvents.length === 0) {
        setStatus('スケジュールを生成できるスポットがありませんでした。半径や種類を見直してください。');
        return;
      }

      setStatus('✅ 周辺' + spots.length + '件のスポットから ' + days + '日分のスケジュールを作成しました（使用: ' + usedCounts.join('件 / ') + '件）');
      resultEl.innerHTML = buildDayCardsHtml(allEvents);
      safeRun(() => renderPlannerMap(center, spots, allEvents, dayWaypoints, mode), 'planner');

      // この検索結果を「ルートカタログ」タブの検索履歴に自動追加する
      // （検索するたびに増えていく方式。この端末のブラウザにのみ保存）。
      saveSearchHistoryEntry({
        id: 'search-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8),
        searchedAt: new Date().toISOString(),
        centerName: center.name || locInput.value.trim() || '検索地点',
        centerLat: center.lat,
        centerLng: center.lng,
        radiusKm,
        days,
        mode,
        types,
        totalSpots: spots.length,
        usedCounts,
      });
      safeRun(renderRoutes, 'routes');
      if (leafletMap) safeRun(renderSearchHistoryMarkers, 'map');
    });
  }

  let mapInitialized = false;

  document.querySelectorAll('nav button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('nav button').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
      // 地図はdisplay:noneのコンテナに対してL.map()するとサイズが0になり、
      // fitBounds()のズーム計算が狂う。タブが最初に表示されたタイミングで
      // 初期化することで、コンテナが正しいサイズを持った状態で計算させる。
      if (btn.dataset.tab === 'map' && !mapInitialized) {
        mapInitialized = true;
        safeRun(renderMap, 'map');
      }
    });
  });

  function reportSafeRunError(label, err) {
    console.error(label + ' failed:', err);
    const el = document.getElementById('tab-' + label);
    if (el) el.insertAdjacentHTML('beforeend', '<p class="hint" style="color:#C1503A;">' + label + ' の初期化に失敗しました: ' + escapeHtml(err.message) + '</p>');
  }

  // fnが戻り値としてPromiseを返す場合（renderPlannerMap等）も、同期関数と
  // 同じように例外（reject）をキャッチしてエラー表示する。
  function safeRun(fn, label) {
    try {
      const result = fn();
      if (result && typeof result.catch === 'function') {
        result.catch((err) => reportSafeRunError(label, err));
      }
    } catch (err) {
      reportSafeRunError(label, err);
    }
  }

  safeRun(renderRoutes, 'routes');
  safeRun(initPlannerTab, 'planner');
  safeRun(initHotelTab, 'hotel');
<\/script>
</body>
</html>
`;
}

function main() {
  const [, , routesArg, visitHistoryArg, outArg] = process.argv;
  const routesPath = path.resolve(routesArg || path.join(__dirname, '..', 'data', 'routes.json'));
  const visitHistoryPath = path.resolve(
    visitHistoryArg || path.join(__dirname, '..', 'data', 'visitHistory.json')
  );
  const outPath = path.resolve(outArg || path.join(__dirname, '..', 'index.html'));

  const routes = JSON.parse(fs.readFileSync(routesPath, 'utf8'));
  const visitHistory = JSON.parse(fs.readFileSync(visitHistoryPath, 'utf8'));

  const html = buildIndexHtml({ routes, visitHistory });
  fs.writeFileSync(outPath, html, 'utf8');
  console.log(`生成しました: ${outPath}`);
}

if (require.main === module) {
  main();
}

module.exports = { buildIndexHtml };
