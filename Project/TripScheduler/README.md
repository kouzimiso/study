# TripScheduler

食べログ点数だけに頼らないRestaurantFinderの評価軸と、Mapsのホテル空室
検索の仕組みを踏まえ、「食事・Wifi/電源・空いてる場所・ホテル空室」を
横断して旅程を組み、カレンダーに落とし込むための試作。

大船在住であることを前提に、大船周辺ではなく**車で日帰り圏の行き先
パターン（Route）をカタログ化**し、一度行ったRouteは記録して次回は
別の場所を優先する、という仕組みを持つ。

## ブラウザで見る（HTML GUI）

```bash
npm run build:html   # index.html を生成（デフォルトで同梱済み）
```

[`index.html`](./index.html) をブラウザで開くと、以下をタブ切り替えで見られる：

- **旅程**：`data/silver-week-2026.json` を日別タイムラインで表示
- **ルートカタログ**：`data/routes.json` のRoute一覧（混雑リスク・タグ・
  訪問履歴バッジ付き）
- **地図**：Leaflet地図（CDN読み込み）に各Routeの検索中心座標をマーカー
  表示。色は混雑リスクの目安
- **現地プラン作成**：地名（または現在地）を入力すると、その周辺の
  OpenStreetMap上の観光地・飲食店・Wifi/電源カフェ・温泉銭湯を検索し、
  カテゴリバランスを考慮して1日あたりの立ち寄り先を自動選定、時間割に
  組む（`Test/travel-route-planner.html` という既存の個人プロトタイプの
  考え方を踏襲。APIキー不要、ブラウザから直接OSMに問い合わせる）
- **楽天ホテル検索**：ブラウザから直接 `openapi.rakuten.co.jp` を呼ぶ。
  Application ID / Access Key / Affiliate ID はこの端末のlocalStorageに
  のみ保存され、サーバーには送らない（既存の `Project/Maps/index.html`
  と同じ設計）

**重要**：楽天API側は「アプリ登録」で設定したApplication URLと、実際に
このページを開いたブラウザのRefererが一致しないと
`HTTP_REFERRER_NOT_ALLOWED` で失敗する（楽天API自体のCORSは
`Access-Control-Allow-Origin: *` で許可されているため、これさえ合えば
ブラウザから直接呼べることは確認済み）。`file://` で直接開くと失敗するので、
登録したURL上（例：GitHub Pages）で配信して開くこと。

- [`SILVER_WEEK_2026_PLAN.md`](./SILVER_WEEK_2026_PLAN.md) — 2026年
  シルバーウィーク（9/21月〜9/23水、大船発）の具体的な旅程と、その
  下調べの根拠
- [`DESIGN.md`](./DESIGN.md) — 上記のような旅程を自動生成する
  「スケジュールソフト」にするための設計案（Routeデータモデル・
  訪問履歴によるローテーションを含む）
- `index.html` / `src/buildIndexHtml.js` — 上記のHTML GUI本体と、
  データから生成するビルドスクリプト
- `data/routes.json` — 大船から日帰り圏の行き先パターン（観光地・
  温泉・絶景ドライブ）のカタログ
- `data/visitHistory.json` — 訪問済みRouteの記録
- `data/silver-week-2026.json` — 今回選んだ3Routeを時間割に展開した
  イベント配列
- `src/selectRoutes.js` — 訪問履歴・混雑リスク・方角の多様性から
  N日分のRouteを選ぶロジック
- `src/buildDaySchedule.js` — 1つのRouteを、移動・観光・食事・温泉・
  Wifi電源休憩を含む1日分の時間割（イベント配列）に自動展開するロジック
- `src/planTrip.js` — `selectRoutes` → `buildDaySchedule` を繋いで、
  N日分の旅程イベント配列を一括生成するCLI
- `src/generateIcs.js` — イベント配列を `.ics`（iCalendar）形式に
  変換するスクリプト（依存ライブラリなし）
- `src/toGanttPlanList.js` — 同じイベント配列を
  [`Project/WebGantt`](../WebGantt/) の **PlanList JSON形式**に変換する
  スクリプト。1つの旅程データから、カレンダー（.ics）とガントチャート
  （WebGantt）の両方を作れる
- `src/overpassWifi.js` — OpenStreetMap Overpass APIから、座標周辺の
  Wifi/電源の目安になるカフェ等を検索するロジック（APIキー不要）
- `src/updateWifiPowerStops.js` — 各Routeの `searchCenter` を使って
  Overpass検索を行い、`wifiPowerStops` を拡充するCLI
- `src/geocode.js` — Nominatim（OSM）を使った地名→緯度経度のジオコー
  ディング（APIキー不要、Node.js/ブラウザ両対応UMD）
- `src/overpassSpots.js` — 観光地/飲食店/Wifi電源/温泉を横断して検索
  するOverpassクライアント（Node.js/ブラウザ両対応UMD）
- `src/dynamicScheduler.js` — `findSpotsAround()` が返したスポットから
  中心地点を起点に1日分の時間割を動的に組むロジック（最近傍法で巡回順を
  決め、直線距離と移動手段から所要時間を概算）。「現地プラン作成」タブの
  中身はこれら3つのUMDモジュール＋`buildDaySchedule.js`をそのまま
  `index.html` に埋め込んで動かしている

## 使い方

```bash
npm test                # ユニットテスト
npm run build:ics       # data/silver-week-2026.json → silver-week-2026.ics を生成
npm run build:gantt     # data/silver-week-2026.json → silver-week-2026.planlist.json を生成
```

### ガントチャートで見る（WebGanttと両立）

`npm run build:gantt` で生成される `silver-week-2026.planlist.json` は
[`Project/WebGantt`](../WebGantt/) の `gantt.html` にそのまま読み込める
PlanList形式。1日＝1つのPlan、その日の各予定（移動・観光・食事・温泉・
Wifi電源休憩）が子Todoになり、種類ごとに `type`
（`move` / `sightseeing` / `food` / `onsen` / `work`）が付く。

```bash
npm run build:gantt
# WebGantt/gantt.html をブラウザで開き、「📂 読込」で
# TripScheduler/silver-week-2026.planlist.json を選択するとガント表示できる
```

`data/silver-week-2026.json` の各イベントに `category`（move/sightseeing/
food/onsen/work）と `routeId`（`data/routes.json` のRoute ID）を持たせて
いるのはこの変換のため。イベントの元データを1つ増やすだけで、カレンダー
とガントチャートの両方が最新化される。

### Routeを選ぶ（一度行った場所は次から後回しになる）

```bash
node -e "
const { selectRoutesForTrip } = require('./src/selectRoutes');
const routes = require('./data/routes.json');
const visitHistory = require('./data/visitHistory.json');
console.log(selectRoutesForTrip(routes, visitHistory, 3, { today: new Date() }));
"
```

旅行後は `data/visitHistory.json` に `{ "routeId": "...", "visitedOn": "YYYY-MM-DD" }`
を追記するだけで、次回の選定では今回行ったRouteの優先度が下がり、
自動的に別の行き先が提案されるようになる。

### 旅程を1コマンドで自動生成する（Route選定＋日内スケジューリング）

```bash
npm run plan 3 -- --start-date=2026-09-21 --out=data/my-trip.json
# 出力先を省略すると標準出力にJSONを吐く。選ばれたRouteと選定理由はstderrに出る。
```

`src/planTrip.js` は `selectRoutesForTrip()` でN日分のRouteを選び、
各Routeを `buildDaySchedule()` で1日分の時間割（移動→観光→昼食→温泉→
Wifi電源休憩→帰路、という順の近似スケジュール）に展開する。出力は
そのまま `generateIcs.js` / `toGanttPlanList.js` に渡せる。

```bash
node src/planTrip.js 3 --start-date=2026-09-21 --out=/tmp/trip.json
node src/generateIcs.js /tmp/trip.json /tmp/trip.ics
node src/toGanttPlanList.js /tmp/trip.json /tmp/trip.planlist.json data/routes.json
```

`--max-crowd-risk=low` で混雑リスクの上限を絞ったり、`--exclude=id1,id2`
で特定Routeを除外したりできる（`data/silver-week-2026.json` は、この
自動生成結果に地名の表記調整などを手作業で加えたもの）。

生成された `.ics` ファイルはGoogleカレンダー・Appleカレンダー等に
インポートできる。任意の旅程を組みたい場合は `data/*.json` と同じ形式
（`date`, `start`, `end`, `title`, `location`, `description`）で
JSONを作り、`node src/generateIcs.js <入力.json> <出力.ics>` を実行する。

### Wifi/電源スポットの自動収集（Overpass API・APIキー不要）

```bash
node src/updateWifiPowerStops.js              # dry-run：見つかった候補を表示するだけ
node src/updateWifiPowerStops.js --write       # data/routes.json のwifiPowerStopsを実際に更新
```

各Routeの `searchCenter`（検索中心の緯度経度）周辺で、`internet_access`
タグを持つカフェ・レストラン等をOverpass APIから検索し、確認済みの候補を
`wifiPowerStops` に追加する。1つのRouteの検索が失敗しても他のRouteの処理は
続行する。

**注意**：このセッションの実行環境からはOverpass系の主要インスタンス
（`overpass-api.de` 等）への接続が不安定で、ライブデータでの動作確認が
できていない。`src/overpassWifi.js` のロジックはモックfetchによるユニット
テストで検証済みだが、実際にWifi/電源情報を収集する際は、安定したネット
ワークから一度 dry-run で結果を確認してから `--write` を使うこと。

### 現地プラン作成タブ（地点を指定して動的にスケジュールを組む）

`index.html` の「現地プラン作成」タブで、地名（または現在地）・検索半径・
日数・興味カテゴリ（観光地/飲食店/Wifi電源/温泉）・移動手段を指定すると：

1. `src/geocode.js`（Nominatim）で地点を緯度経度に変換
2. `src/overpassSpots.js`（Overpass API）でその周辺のスポットを検索
3. `src/dynamicScheduler.js` が、カテゴリごとの上限件数を守りつつ中心から
   近い順にスポットを選び（`selectSpotsForDay()`）、最近傍法で巡回順を
   決めて（`orderSpotsGreedy()`）、移動時間を直線距離と移動手段の速度から
   概算しながら1日分の時間割を組む（`buildDynamicDaySchedule()`）。
   複数日を指定した場合は、使用済みスポットを除外しながら日ごとに
   選定し直す
4. 結果を旅程タブと同じカードUIで表示し、専用の地図（選ばれなかった
   候補は薄いグレー、採用されたスポットは種類別の色）にプロットする

**検証状況**：ロジック自体（`test/geocode.test.js` / `test/overpassSpots.test.js`
/ `test/dynamicScheduler.test.js`）はモックfetchで検証済みで、ブラウザでの
UI動作（タブ表示・フォーム・地図初期化・エラーハンドリング）もPlaywrightで
確認済み。ただし実際のOverpass APIへのライブ接続は、このセッションの
実行環境ではプロキシの接続不安定（Nominatim側は問題なし）により確認
できていない。安定したネットワーク・通常のブラウザから試すこと。
