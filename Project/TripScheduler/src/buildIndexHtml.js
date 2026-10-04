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
  .candidate-row { display:flex; gap:10px; align-items:flex-start; padding:9px 0;
    border-top:1px solid var(--panel-border); cursor:pointer; }
  .candidate-row:first-child { border-top:none; }
  .candidate-row input[type="checkbox"] { margin-top:3px; flex:0 0 auto; }
  .candidate-row .name { font-size:13px; }
  .candidate-row .meta { font-size:11px; color:var(--text-muted); margin-top:2px; }
  .route-combine-row { display:flex; gap:10px; align-items:center; padding:9px 0;
    border-top:1px solid var(--panel-border); }
  .route-combine-row:first-child { border-top:none; }
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
      <h3>出発地から目的地までのルートを作る</h3>
      <p class="notes">
        出発地・目的地を入力すると、その間の道なりルート（OSRM）沿いにある
        OpenStreetMap上の観光地・飲食店・Wifi/電源カフェ・温泉銭湯を検索します。
        候補から好きなものだけを選んで、名前を付けて「ルートカタログ」に
        登録できます（登録したルートは後で組み合わせて複数日の旅程にできます）。
        APIキー不要、ブラウザから直接OSM/OSRMに問い合わせます。
      </p>
      <div class="row">
        <div class="field" style="flex:2 1 200px;">
          <label>出発地</label>
          <input id="dp-from" type="text" placeholder="例：大船駅" />
        </div>
        <div class="field" style="flex:0 0 auto;align-self:flex-end;">
          <button class="btn secondary" id="dp-use-gps" type="button">📍 現在地を使う</button>
        </div>
      </div>
      <div class="row">
        <div class="field" style="flex:2 1 200px;">
          <label>目的地</label>
          <input id="dp-to" type="text" placeholder="例：鎌倉駅" />
        </div>
      </div>
      <div class="row">
        <div class="field"><label>ルートからの許容距離(km)</label><input id="dp-corridor" type="number" value="0.3" min="0.1" max="3" step="0.1" /></div>
        <div class="field"><label>移動手段</label>
          <select id="dp-mode" style="width:100%;padding:8px;border-radius:8px;background:#0B1011;color:#EAF3EE;border:1px solid #283835;">
            <option value="walk">徒歩</option>
            <option value="bike">自転車</option>
            <option value="car" selected>車</option>
          </select>
        </div>
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
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <button class="btn" id="dp-go" type="button">🔍 ルート沿いのスポットを探す</button>
        <button class="btn secondary" id="dp-cancel" type="button" style="display:none;">✕ キャンセル</button>
      </div>
      <p id="dp-status" class="hint"></p>
    </div>
    <div id="dp-map-wrap" class="route-card" style="display:none;">
      <h3>ルートと候補スポットのマップ</h3>
      <div id="dp-map" style="height:360px;border-radius:12px;"></div>
      <p id="dp-map-note" class="hint"></p>
    </div>
    <div id="dp-candidates-wrap" class="route-card" style="display:none;">
      <h3>候補スポット（チェックしたものがルートに入ります）</h3>
      <p class="notes">選んだ立ち寄り先は出発地からの順番に自動で並びます（並び替えはできません）。</p>
      <div id="dp-candidates"></div>
    </div>
    <div id="dp-preview-wrap" class="route-card" style="display:none;">
      <h3>プレビュー（実際の日付は、組み合わせて旅程にする時に指定します）</h3>
      <div id="dp-result"></div>
    </div>
    <div id="dp-register-wrap" class="route-card" style="display:none;">
      <h3>このルートをカタログに登録する</h3>
      <div class="row">
        <div class="field" style="flex:2 1 200px;">
          <label>ルート名</label>
          <input id="dp-route-name" type="text" placeholder="例：大船→鎌倉 観光ルート" />
        </div>
      </div>
      <button class="btn" id="dp-register" type="button">📌 ルートとして登録する</button>
      <p id="dp-register-status" class="hint"></p>
    </div>
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
  const MODE_LABEL = { walk: '徒歩', bike: '自転車', car: '車' };
  const DAY_LINE_COLORS = ['#45B08C', '#5EA8E8', '#E8C22C', '#B98AE0', '#C1503A', '#E8955B', '#8CA39B'];
  // OpenStreetMap公式タイルは利用ポリシーが厳格化され、ブラウザからの直接
  // アクセスが「Access blocked」で拒否されることが増えたため、日本国内限定の
  // アプリであることを踏まえ、無料・APIキー不要・出典明記のみで使える
  // 国土地理院（GSI）の淡色地図タイルを使う（複数の地図で共通）。
  const GSI_TILE_URL = 'https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png';
  const GSI_ATTRIBUTION = '地図: <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>';

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ─── 作成したルート（ルートカタログの新規登録分）───
  // 「現地プラン作成」タブで出発地〜目的地を指定して候補スポットを選び、
  // 名前を付けて「登録する」を押すたびに1件追加される。サーバーを
  // 持たないページなので、この端末のブラウザのlocalStorageにのみ保存する
  // （他の端末・他のブラウザとは共有されない）。
  const CUSTOM_ROUTES_KEY = 'tripscheduler_customRoutes';
  const CUSTOM_ROUTES_LIMIT = 200;

  function loadCustomRoutes() {
    try {
      const raw = JSON.parse(localStorage.getItem(CUSTOM_ROUTES_KEY) || '[]');
      return Array.isArray(raw) ? raw : [];
    } catch (err) {
      return [];
    }
  }

  function saveCustomRoute(route) {
    const list = loadCustomRoutes();
    list.unshift(route);
    try {
      localStorage.setItem(CUSTOM_ROUTES_KEY, JSON.stringify(list.slice(0, CUSTOM_ROUTES_LIMIT)));
    } catch (err) {
      // localStorageが使えない（プライベートモード等）場合は登録のみ諦める
    }
  }

  function deleteCustomRoute(id) {
    const list = loadCustomRoutes().filter((r) => r.id !== id);
    try {
      localStorage.setItem(CUSTOM_ROUTES_KEY, JSON.stringify(list));
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

  function routeCoordsOrStraight(route) {
    return route.coords || [[route.from.lng, route.from.lat], [route.to.lng, route.to.lat]];
  }

  function formatRouteDistanceDuration(route) {
    const parts = [];
    if (typeof route.distanceMeters === 'number') parts.push((route.distanceMeters / 1000).toFixed(1) + 'km');
    if (typeof route.durationSeconds === 'number') parts.push('約' + Math.round(route.durationSeconds / 60) + '分');
    if (parts.length === 0) return '';
    return parts.join(' / ') + (route.real === false ? '（直線近似）' : '');
  }

  function buildCustomRouteCardHtml(route) {
    const stopsByType = {};
    (route.stops || []).forEach((s) => { stopsByType[s.type] = (stopsByType[s.type] || 0) + 1; });
    const stopBadges = Object.keys(stopsByType).map((t) =>
      '<span class="badge" style="background:' + (CATEGORY_COLOR[t] || '#8CA39B') + '22;color:' + (CATEGORY_COLOR[t] || '#8CA39B') + ';">' +
        escapeHtml(CATEGORY_LABEL[t] || t) + ' ' + stopsByType[t] + '</span>'
    ).join('');
    const distDuration = formatRouteDistanceDuration(route);
    return '<div class="route-card" data-custom-route-id="' + escapeHtml(route.id) + '">' +
      '<div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">' +
        '<h3 style="flex:1;margin:0;">' + escapeHtml(route.name) + '</h3>' +
        '<label style="display:flex;align-items:center;gap:4px;font-size:11px;white-space:nowrap;">' +
          '<input type="checkbox" data-combine-id="' + escapeHtml(route.id) + '" /> 旅程に組み込む' +
        '</label>' +
      '</div>' +
      '<p class="notes">' + escapeHtml((route.from && route.from.name) || '') + ' → ' + escapeHtml((route.to && route.to.name) || '') +
        '（' + escapeHtml(MODE_LABEL[route.mode] || route.mode) + '）' +
        (distDuration ? ' ・ ' + escapeHtml(distDuration) : '') +
      '</p>' +
      (stopBadges || '<p class="notes" style="color:var(--text-muted);">立ち寄り先なし（直行ルート）</p>') +
      '<p class="notes" style="font-size:11px;">登録: ' + escapeHtml(new Date(route.createdAt).toLocaleString('ja-JP')) + '</p>' +
      '<button class="btn secondary" data-del-custom-route-id="' + escapeHtml(route.id) + '" style="font-size:11px;padding:4px 10px;">このルートを削除</button>' +
    '</div>';
  }

  let combineOrder = [];

  function combineSelectedRoutes() {
    const statusEl = document.getElementById('routes-combine-status');
    const customRoutes = loadCustomRoutes();
    const selected = combineOrder.map((id) => customRoutes.find((r) => r.id === id)).filter(Boolean);
    if (selected.length === 0) {
      statusEl.style.color = '#C1503A';
      statusEl.textContent = '「旅程に組み込む」にチェックしたルートを1つ以上選んでください。';
      return;
    }
    statusEl.style.color = '';
    statusEl.textContent = '';

    const startDateInput = document.getElementById('routes-combine-start-date').value;
    const baseDate = startDateInput || new Date().toISOString().slice(0, 10);

    const allEvents = [];
    selected.forEach((route, i) => {
      const date = addDaysISO(baseDate, i);
      const events = TripSchedulerDynamicScheduler.buildRouteSchedule(route.from, route.to, date, route.stops || [], {
        startTime: '09:00',
        mode: route.mode,
      });
      allEvents.push(...events);
    });

    document.getElementById('routes-combine-result').innerHTML =
      '<h3 style="font-size:13px;margin:14px 0 6px;">組み合わせた旅程（' + selected.length + '日分、' + escapeHtml(baseDate) + '〜）</h3>' +
      buildDayCardsHtml(allEvents);

    safeRun(() => renderCombineMap(selected), 'routes');
  }

  function renderRoutes() {
    const customRoutes = loadCustomRoutes();
    const customHtml = customRoutes.length
      ? customRoutes.map(buildCustomRouteCardHtml).join('')
      : '<p class="hint">まだルートが登録されていません。「現地プラン作成」タブでルートを作って登録してみてください。</p>';

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

    document.getElementById('tab-routes').innerHTML =
      '<h2 style="font-size:15px;margin:0 0 4px;">作成したルート（' + customRoutes.length + '件）</h2>' +
      '<p class="hint">「旅程に組み込む」にチェックした複数のルートを、1ルート=1日として組み合わせ、複数日の旅程にできます。</p>' +
      '<div class="row" style="align-items:flex-end;">' +
        '<div class="field"><label>旅程の開始日</label><input id="routes-combine-start-date" type="date" /></div>' +
        '<div class="field" style="flex:0 0 auto;"><button class="btn" id="routes-combine-go" type="button">🧭 選択したルートを旅程にする</button></div>' +
      '</div>' +
      '<p id="routes-combine-status" class="hint"></p>' +
      '<div id="routes-combine-result"></div>' +
      '<div id="routes-combine-map-wrap" class="route-card" style="display:none;"><h3>組み合わせたルートのマップ</h3><div id="routes-combine-map" style="height:360px;border-radius:12px;"></div></div>' +
      customHtml +
      '<h2 style="font-size:15px;margin:22px 0 4px;color:var(--text-muted);">手動登録のRouteカタログ（' + DATA.routes.length + '件）</h2>' +
      curatedHtml;

    document.querySelectorAll('[data-del-custom-route-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-del-custom-route-id');
        deleteCustomRoute(id);
        combineOrder = combineOrder.filter((x) => x !== id);
        renderRoutes();
        if (leafletMap) safeRun(renderCustomRoutesOnMap, 'map');
      });
    });
    document.querySelectorAll('[data-combine-id]').forEach((cb) => {
      const id = cb.getAttribute('data-combine-id');
      if (combineOrder.includes(id)) cb.checked = true;
      cb.addEventListener('change', () => {
        if (cb.checked) { if (!combineOrder.includes(id)) combineOrder.push(id); }
        else { combineOrder = combineOrder.filter((x) => x !== id); }
      });
    });
    document.getElementById('routes-combine-go').addEventListener('click', combineSelectedRoutes);
  }

  let leafletMap = null;
  let customRoutesLayer = null;
  let combineMap = null;

  function renderCustomRoutesOnMap() {
    if (!leafletMap) return;
    if (customRoutesLayer) leafletMap.removeLayer(customRoutesLayer);
    customRoutesLayer = L.layerGroup();
    loadCustomRoutes().forEach((route) => {
      const latlngs = routeCoordsOrStraight(route).map((c) => [c[1], c[0]]);
      const line = L.polyline(latlngs, {
        color: '#5EA8E8', weight: 3, opacity: 0.8, dashArray: route.real === false ? '6,6' : null,
      });
      line.bindPopup(
        '<strong>' + escapeHtml(route.name) + '</strong>（作成したルート）<br/>' +
        '<span style="font-size:11px;color:#555;">' + escapeHtml((route.from && route.from.name) || '') + ' → ' + escapeHtml((route.to && route.to.name) || '') + '</span>'
      );
      customRoutesLayer.addLayer(line);
    });
    customRoutesLayer.addTo(leafletMap);
  }

  function renderCombineMap(routes) {
    const wrap = document.getElementById('routes-combine-map-wrap');
    wrap.style.display = 'block';
    if (!combineMap) {
      combineMap = L.map('routes-combine-map');
      L.tileLayer(GSI_TILE_URL, { attribution: GSI_ATTRIBUTION, maxZoom: 18 }).addTo(combineMap);
    } else {
      combineMap.eachLayer((layer) => { if (!(layer instanceof L.TileLayer)) combineMap.removeLayer(layer); });
    }
    setTimeout(() => combineMap.invalidateSize(), 0);

    const bounds = [];
    routes.forEach((route, idx) => {
      const color = DAY_LINE_COLORS[idx % DAY_LINE_COLORS.length];
      const latlngs = routeCoordsOrStraight(route).map((c) => [c[1], c[0]]);
      L.polyline(latlngs, { color, weight: 4, opacity: 0.8, dashArray: route.real === false ? '7,7' : null })
        .addTo(combineMap)
        .bindPopup((idx + 1) + '日目: ' + escapeHtml(route.name));
      latlngs.forEach((ll) => bounds.push(ll));
      (route.stops || []).forEach((s) => {
        L.circleMarker([s.lat, s.lng], { radius: 7, color, fillColor: color, fillOpacity: 0.85, weight: 2 })
          .addTo(combineMap)
          .bindPopup(escapeHtml(s.name));
        bounds.push([s.lat, s.lng]);
      });
    });
    if (bounds.length) combineMap.fitBounds(bounds, { padding: [40, 40] });
  }

  function renderMap() {
    const withCenter = DATA.routes.filter((r) => r.searchCenter);
    const map = L.map('map');
    leafletMap = map;
    L.tileLayer(GSI_TILE_URL, { attribution: GSI_ATTRIBUTION, maxZoom: 18 }).addTo(map);

    const customRoutes = loadCustomRoutes();
    const boundPoints = withCenter.map((r) => [r.searchCenter.lat, r.searchCenter.lng]);
    customRoutes.forEach((route) => {
      if (route.from) boundPoints.push([route.from.lat, route.from.lng]);
      if (route.to) boundPoints.push([route.to.lat, route.to.lng]);
    });

    if (boundPoints.length === 0) {
      map.setView([35.3556, 139.5309], 10);
      renderCustomRoutesOnMap();
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
    renderCustomRoutesOnMap();
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

  // ─── 現地プラン作成タブ：出発地〜目的地のルート沿いのスポットから、
  // 選んだものだけでルートを組んで名前を付けて登録する
  // （Test/travel-route-planner.html の考え方を踏襲）───
  let dpMap = null;

  function addDaysISO(dateStr, days) {
    const d = new Date(dateStr + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 10);
  }

  function initPlannerTab() {
    const statusEl = document.getElementById('dp-status');
    const fromInput = document.getElementById('dp-from');
    const toInput = document.getElementById('dp-to');
    const candidatesWrap = document.getElementById('dp-candidates-wrap');
    const candidatesEl = document.getElementById('dp-candidates');
    const previewWrap = document.getElementById('dp-preview-wrap');
    const resultEl = document.getElementById('dp-result');
    const registerWrap = document.getElementById('dp-register-wrap');
    const registerStatusEl = document.getElementById('dp-register-status');

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
          fromInput.value = '現在地';
          fromInput.dataset.lat = pos.coords.latitude;
          fromInput.dataset.lng = pos.coords.longitude;
          setStatus('現在地を取得しました（' + pos.coords.latitude.toFixed(4) + ', ' + pos.coords.longitude.toFixed(4) + '）');
        },
        () => setStatus('現在地の取得に失敗しました。地名を入力してください。', true),
        { timeout: 10000 }
      );
    });

    fromInput.addEventListener('input', () => {
      delete fromInput.dataset.lat;
      delete fromInput.dataset.lng;
    });

    const goBtn = document.getElementById('dp-go');
    const cancelBtn = document.getElementById('dp-cancel');
    let activeAbortController = null;
    let cancelledByUser = false;

    cancelBtn.addEventListener('click', () => {
      cancelledByUser = true;
      if (activeAbortController) activeAbortController.abort();
    });

    // 検索して作成中のルートの状態（「登録する」まではここだけに保持する）
    let currentFrom = null;
    let currentTo = null;
    let currentMode = 'car';
    let currentCoords = null; // [[lng,lat], ...]
    let currentReal = true;
    let currentDistanceMeters = null;
    let currentDurationSeconds = null;
    let candidates = []; // routeProgressRatio順（出発地点に近い順）にソート済み
    const selectedIds = new Set();
    const candidateMarkers = new Map(); // spotId -> leaflet marker

    async function resolvePoint(input, label) {
      if (input.dataset.lat && input.dataset.lng) {
        return { lat: parseFloat(input.dataset.lat), lng: parseFloat(input.dataset.lng), name: '現在地' };
      }
      const query = input.value.trim();
      if (!query) throw new Error(label + 'を入力するか、現在地を使ってください');
      const geo = await TripSchedulerGeocode.geocodeLocation(query, { signal: activeAbortController.signal });
      if (!geo) throw new Error('「' + query + '」が見つかりませんでした。別の表記で試してください。');
      return { lat: geo.lat, lng: geo.lng, name: geo.name };
    }

    function updatePreview() {
      const ordered = candidates.filter((s) => selectedIds.has(s.id));
      const previewDate = new Date().toISOString().slice(0, 10);
      const events = TripSchedulerDynamicScheduler.buildRouteSchedule(currentFrom, currentTo, previewDate, ordered, {
        startTime: '09:00',
        mode: currentMode,
      });
      resultEl.innerHTML = buildDayCardsHtml(events);
      previewWrap.style.display = 'block';
    }

    function updateCandidateMarkerStyle(id, selected) {
      const marker = candidateMarkers.get(id);
      if (!marker) return;
      const spot = candidates.find((s) => s.id === id);
      const color = selected ? (CATEGORY_COLOR[spot.type] || '#45B08C') : '#4A5A55';
      marker.setStyle({ radius: selected ? 9 : 5, color, fillColor: color, fillOpacity: selected ? 0.9 : 0.35, weight: selected ? 2 : 1 });
    }

    function renderCandidates() {
      candidatesEl.innerHTML = candidates.map((spot) => {
        const color = CATEGORY_COLOR[spot.type] || '#45B08C';
        return '<label class="candidate-row">' +
          '<input type="checkbox" data-spot-id="' + escapeHtml(spot.id) + '" ' + (selectedIds.has(spot.id) ? 'checked' : '') + ' />' +
          '<span style="flex:1;">' +
            '<span class="name"><span class="badge" style="background:' + color + '22;color:' + color + ';">' +
              escapeHtml(CATEGORY_LABEL[spot.type] || spot.type) + '</span> ' + escapeHtml(spot.name) + '</span>' +
            '<span class="meta">' + (spot.hours ? '営業時間: ' + escapeHtml(spot.hours) : '営業時間不明') + '</span>' +
          '</span>' +
        '</label>';
      }).join('');

      candidatesEl.querySelectorAll('[data-spot-id]').forEach((cb) => {
        cb.addEventListener('change', () => {
          const id = cb.getAttribute('data-spot-id');
          if (cb.checked) selectedIds.add(id); else selectedIds.delete(id);
          updateCandidateMarkerStyle(id, cb.checked);
          updatePreview();
        });
      });
    }

    function renderSearchMap() {
      const mapWrap = document.getElementById('dp-map-wrap');
      mapWrap.style.display = 'block';
      if (!dpMap) {
        dpMap = L.map('dp-map');
        L.tileLayer(GSI_TILE_URL, { attribution: GSI_ATTRIBUTION, maxZoom: 18 }).addTo(dpMap);
      } else {
        dpMap.eachLayer((layer) => { if (!(layer instanceof L.TileLayer)) dpMap.removeLayer(layer); });
      }
      setTimeout(() => dpMap.invalidateSize(), 0);
      candidateMarkers.clear();

      const bounds = [];
      L.marker([currentFrom.lat, currentFrom.lng]).addTo(dpMap)
        .bindPopup('<strong>' + escapeHtml(currentFrom.name || '出発地') + '</strong>（出発地）');
      bounds.push([currentFrom.lat, currentFrom.lng]);
      L.marker([currentTo.lat, currentTo.lng]).addTo(dpMap)
        .bindPopup('<strong>' + escapeHtml(currentTo.name || '目的地') + '</strong>（目的地）');
      bounds.push([currentTo.lat, currentTo.lng]);

      const latlngs = (currentCoords || []).map((c) => [c[1], c[0]]);
      if (latlngs.length >= 2) {
        L.polyline(latlngs, { color: '#45B08C', weight: 4, opacity: 0.75, dashArray: currentReal ? null : '7,7' }).addTo(dpMap);
        latlngs.forEach((ll) => bounds.push(ll));
      }

      candidates.forEach((spot) => {
        const selected = selectedIds.has(spot.id);
        const color = selected ? (CATEGORY_COLOR[spot.type] || '#45B08C') : '#4A5A55';
        const marker = L.circleMarker([spot.lat, spot.lng], {
          radius: selected ? 9 : 5, color, fillColor: color, fillOpacity: selected ? 0.9 : 0.35, weight: selected ? 2 : 1,
        }).addTo(dpMap);
        marker.bindPopup(
          '<strong>' + escapeHtml(spot.name) + '</strong><br/>' + escapeHtml(CATEGORY_LABEL[spot.type] || spot.type)
        );
        candidateMarkers.set(spot.id, marker);
        bounds.push([spot.lat, spot.lng]);
      });

      if (bounds.length) dpMap.fitBounds(bounds, { padding: [40, 40] });

      document.getElementById('dp-map-note').textContent = currentReal
        ? ''
        : '道路ルートAPI（OSRM）に接続できなかったため、直線（破線）で近似表示しています。';
    }

    goBtn.addEventListener('click', async () => {
      const corridorKm = parseFloat(document.getElementById('dp-corridor').value) || 0.3;
      const mode = document.getElementById('dp-mode').value;

      const types = [];
      if (document.getElementById('dp-cat-sightseeing').checked) types.push('sightseeing');
      if (document.getElementById('dp-cat-food').checked) types.push('food');
      if (document.getElementById('dp-cat-wifi').checked) types.push('wifi');
      if (document.getElementById('dp-cat-onsen').checked) types.push('onsen');
      if (types.length === 0) { setStatus('スポットの種類を1つ以上選んでください', true); return; }

      candidatesWrap.style.display = 'none';
      previewWrap.style.display = 'none';
      registerWrap.style.display = 'none';
      candidatesEl.innerHTML = '';
      resultEl.innerHTML = '';
      cancelledByUser = false;
      // タイムアウトはあくまで保険で、本命は「キャンセル」ボタン。
      // ユーザーがどれくらい待つかを自分で決められるようにする。
      activeAbortController = new AbortController();
      goBtn.disabled = true;
      cancelBtn.style.display = 'inline-block';

      try {
        let from;
        let to;
        try {
          setStatus('出発地・目的地を検索中…（Nominatimへ問い合わせています）');
          from = await resolvePoint(fromInput, '出発地');
          to = await resolvePoint(toInput, '目的地');
        } catch (err) {
          if (cancelledByUser) { setStatus('検索をキャンセルしました。', true); return; }
          setStatus(err.message, true);
          return;
        }

        setStatus('ルートを計算中…（OSRMへ問い合わせています）');
        let route;
        try {
          route = await TripSchedulerRouteLine.fetchRouteLine([from, to], mode, { signal: activeAbortController.signal });
        } catch (err) {
          if (cancelledByUser) { setStatus('検索をキャンセルしました。', true); return; }
          setStatus('ルートの計算に失敗しました: ' + err.message, true);
          return;
        }
        if (cancelledByUser) { setStatus('検索をキャンセルしました。', true); return; }

        setStatus('ルート沿いのスポットを検索中…（OpenStreetMap Overpass APIへ問い合わせています。混雑時は最大20秒ほどかかります。待てない場合は「キャンセル」で中断できます）');
        const lats = route.coords.map((c) => c[1]);
        const lngs = route.coords.map((c) => c[0]);
        const marginDeg = corridorKm / 111 + 0.01;
        const bbox = [
          Math.min(...lats) - marginDeg, Math.min(...lngs) - marginDeg,
          Math.max(...lats) + marginDeg, Math.max(...lngs) + marginDeg,
        ];

        let rawSpots;
        try {
          rawSpots = await TripSchedulerOverpassSpots.findSpotsInBbox(bbox, types, { signal: activeAbortController.signal });
        } catch (err) {
          if (cancelledByUser) { setStatus('検索をキャンセルしました。', true); return; }
          const isTimeout = /timed out|AbortError/i.test((err && err.name) || '') || /timed out/i.test((err && err.message) || '');
          setStatus(
            'Overpass APIへの接続に失敗しました（' + err.message + '）。' +
            (isTimeout
              ? '複数のOverpassミラーすべてが混雑等で20秒以内に応答しませんでした。' +
                '少し時間をおいて再試行するか、ルートからの許容距離を狭めてみてください。'
              : '広告ブロッカーやセキュリティ系の拡張機能（uBlock Origin等）が ' +
                'overpass-api.de 系のドメインをブロックしていないか確認してください' +
                '（一度シークレットウィンドウで試すと切り分けられます）。') +
            '詳細はブラウザの開発者ツール（F12）のConsoleタブにも出力しています。',
            true
          );
          return;
        }

        const corridorMeters = corridorKm * 1000;
        candidates = rawSpots
          .map((spot) => ({ ...spot, distanceToRouteMeters: TripSchedulerRouteLine.distanceToRouteMeters(spot.lat, spot.lng, route.coords) }))
          .filter((spot) => spot.distanceToRouteMeters <= corridorMeters)
          .map((spot) => ({ ...spot, progress: TripSchedulerRouteLine.routeProgressRatio(spot.lat, spot.lng, route.coords) }))
          .sort((a, b) => a.progress - b.progress);

        currentFrom = from;
        currentTo = to;
        currentMode = mode;
        currentCoords = route.coords;
        currentReal = route.real;
        currentDistanceMeters = route.distanceMeters;
        currentDurationSeconds = route.durationSeconds;
        selectedIds.clear();

        if (candidates.length === 0) {
          setStatus(
            'ルートから' + corridorKm + 'km以内にスポットが見つかりませんでした。' +
            '許容距離を広げるか種類を増やしてみてください（ルート自体は検索できたので、立ち寄り先無しで登録することもできます）。'
          );
        } else {
          setStatus('✅ ルート沿いに' + candidates.length + '件の候補スポットが見つかりました。下のリストから選んでください。');
          candidatesWrap.style.display = 'block';
          renderCandidates();
          updatePreview();
        }
        registerWrap.style.display = 'block';
        safeRun(renderSearchMap, 'planner');
      } finally {
        goBtn.disabled = false;
        cancelBtn.style.display = 'none';
        activeAbortController = null;
      }
    });

    document.getElementById('dp-register').addEventListener('click', () => {
      if (!currentFrom || !currentTo) {
        registerStatusEl.style.color = '#C1503A';
        registerStatusEl.textContent = '先にルートを検索してください。';
        return;
      }
      const name = document.getElementById('dp-route-name').value.trim();
      if (!name) {
        registerStatusEl.style.color = '#C1503A';
        registerStatusEl.textContent = 'ルート名を入力してください。';
        return;
      }

      const orderedStops = candidates
        .filter((s) => selectedIds.has(s.id))
        .map((s) => ({ id: s.id, name: s.name, type: s.type, lat: s.lat, lng: s.lng, hours: s.hours }));

      saveCustomRoute({
        id: 'route-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8),
        name,
        createdAt: new Date().toISOString(),
        from: currentFrom,
        to: currentTo,
        mode: currentMode,
        distanceMeters: currentDistanceMeters,
        durationSeconds: currentDurationSeconds,
        real: currentReal,
        coords: currentCoords,
        stops: orderedStops,
      });

      registerStatusEl.style.color = '';
      registerStatusEl.textContent =
        '✅「' + name + '」として登録しました（ルートカタログタブで確認できます）。' +
        '立ち寄り先の選び方を変えて、別の名前でもう一度登録することもできます。';
      document.getElementById('dp-route-name').value = '';
      safeRun(renderRoutes, 'routes');
      if (leafletMap) safeRun(renderCustomRoutesOnMap, 'map');
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
