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

- **現地プラン作成**（メイン機能）：`Test/travel-route-planner.html`
  という既存の個人プロトタイプの考え方を踏襲した、ルートプランナー
  スタイルのルート作成機能。
  1. 出発地・目的地を入力すると、OSRM（道路ルートAPI、APIキー不要）で
     道なりのルートを計算する
  2. そのルート沿い（指定した許容距離以内）にあるOpenStreetMap上の
     観光地・飲食店・Wifi/電源カフェ・温泉銭湯を検索し、出発地からの
     順番に並べた候補リストを表示する（APIキー不要、ブラウザから直接
     OSM/OSRMに問い合わせる）
  3. 候補から好きなものだけをチェックして選ぶ（選ぶたびに地図とプレビュー
     の時間割が更新される）
  4. 名前を付けて「登録する」と、そのルート（出発地・目的地・移動手段・
     選んだ立ち寄り先の順序）が「ルートカタログ」タブに追加される。
     同じ検索結果から立ち寄り先の選び方を変えて、別名で何度でも登録できる
     （1回の検索から複数のルートバリエーションを作れる）
- **ルートカタログ**：「現地プラン作成」タブで**登録するたびに増える**
  作成済みルート一覧（出発地→目的地・移動手段・距離/時間・立ち寄り先の
  種類別件数・削除ボタン付き）に加え、`data/routes.json` の手動登録Route
  一覧（混雑リスク・タグ・訪問履歴バッジ付き）も引き続き表示する。
  作成済みルートはこの端末のブラウザのlocalStorageにのみ保存され、他の
  端末とは共有されない。
  **ルートを組み合わせる**：複数の作成済みルートに「旅程に組み込む」で
  チェックを入れ、開始日を指定して「選択したルートを旅程にする」を押すと、
  チェックした順に1ルート=1日として並べた複数日の旅程（カード表示＋
  各ルートを色分けした地図）を生成する
- **地図**：Leaflet地図（CDN読み込み）に、手動登録Routeの検索中心座標
  （色は混雑リスクの目安）と、「現地プラン作成」タブで登録した各ルートの
  経路線（青線）をまとめて表示する
- **楽天ホテル検索**：ブラウザから直接 `openapi.rakuten.co.jp` を呼ぶ。
  Application ID / Access Key / Affiliate ID はこの端末のlocalStorageに
  のみ保存され、サーバーには送らない（既存の `Project/Maps/index.html`
  と同じ設計）

旧「旅程」タブ（`data/silver-week-2026.json`という固定データを日別
タイムラインで表示するだけのタブ）は廃止した。「現地プラン作成」タブが
同じカードUIで旅程を動的に作れるようになったため。固定データ自体や
`.ics`・ガントチャート変換のCLIパイプライン（下記）はそのまま使える。

旧来の「地点＋検索半径＋日数」で自動的に周辺スポットを選んで時間割に
組む方式（単一地点を起点に巡って同じ場所へ戻る）は、ルートプランナー
スタイル（出発地〜目的地を指定し、候補から選んで名前を付けて登録する）
に置き換えた。これに伴い、検索するたびに自動で記録が増えていく「検索
履歴」機能も、ユーザーが意図的に名前を付けて登録する「作成したルート」
に置き換わっている。

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
- `start-local-server.bat` — Windowsで `index.html` を `file://` でなく
  `http://localhost:8080/` 経由で開くためのワンクリック起動バッチ
  （楽天ホテル検索・現地プラン作成タブを動かすのに必要）
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
  するOverpassクライアント（Node.js/ブラウザ両対応UMD）。中心＋半径で探す
  `findSpotsAround()` と、矩形（bbox）で探す `findSpotsInBbox()`
  （ルート沿いのスポット探索用）の2系統を持つ
- `src/routeLine.js` — 複数地点（出発地→目的地）を順番に通る経路のジオ
  メトリをOSRM（道路ルートAPI、APIキー不要）から取得するクライアント。
  OSRMが失敗・タイムアウトした場合は各地点を直線でつないだ近似に
  フォールバックする。地点がルート上のどのあたりにあるか
  （`routeProgressRatio()`）、ルートから何m離れているか
  （`distanceToRouteMeters()`）を判定する関数も持つ（ルート沿いの候補
  スポットを順番に並べたり、許容距離で絞り込むのに使う）
  （Node.js/ブラウザ両対応UMD）
- `src/dynamicScheduler.js` — 出発地〜目的地と、ルート上の順序で選んだ
  立ち寄り先（stops）から、1日分の時間割を動的に組むロジック
  （`buildRouteSchedule()`。直線距離と移動手段から所要時間を概算）。
  「現地プラン作成」タブの中身は、これら5つのUMDモジュールをそのまま
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

### 現地プラン作成タブ（出発地〜目的地のルートを作って登録する）

`index.html` の「現地プラン作成」タブで、出発地・目的地・ルートからの
許容距離・興味カテゴリ（観光地/飲食店/Wifi電源/温泉）・移動手段を指定すると：

1. `src/geocode.js`（Nominatim）で出発地・目的地をそれぞれ緯度経度に変換
2. `src/routeLine.js`（OSRM）で出発地〜目的地の道なりのルートを計算
3. そのルートのバウンディングボックス内を `src/overpassSpots.js`
   （Overpass API、`findSpotsInBbox()`）で検索し、`distanceToRouteMeters()`
   でルートから指定した許容距離以内のものだけに絞り、`routeProgressRatio()`
   で出発地からの順番に並べる
4. 候補スポットをチェックリストで表示し、チェックしたものだけが
   ルートに入る（チェックのたびに、`src/dynamicScheduler.js` の
   `buildRouteSchedule()` でプレビューの時間割を再生成し、地図上の
   マーカーの見た目も更新する）
5. 地図には出発地・目的地・ルート線（OSRMが応答しない場合は直線（破線）で
   近似表示）・候補スポット（採用済みは種類別の色、未採用は薄いグレー）を
   プロットする（`Test/travel-route-planner.html` のルート表示を踏襲）
6. 「ルート名」を入力して「登録する」を押すと、出発地・目的地・移動手段・
   選んだ立ち寄り先の順序・ルートのジオメトリをまとめて「ルートカタログ」
   タブに追加する（ブラウザのlocalStorageに保存）。同じ検索結果から
   立ち寄り先の選び方を変えて、別名で何度でも登録できる

「ルートカタログ」タブでは、登録したルートに「旅程に組み込む」で
チェックを入れ、開始日を指定して「選択したルートを旅程にする」を押すと、
チェックした順に1ルート=1日として並べた複数日の旅程を生成できる
（`buildRouteSchedule()` を日ごとに呼び、結果をカードと地図で表示）。

**検証状況**：ロジック自体（`test/geocode.test.js` / `test/overpassSpots.test.js`
/ `test/dynamicScheduler.test.js` / `test/routeLine.test.js`）はモックfetch
で検証済みで、ブラウザでのUI動作（ルート検索→候補選択→プレビュー更新→
登録→ルートカタログへの反映→複数ルートの組み合わせ→地図描画）も
Playwrightで一連のシナリオとして確認済み。ただし実際のOverpass/OSRM/
Nominatimへのライブ接続は、このセッションの実行環境ではプロキシの接続
不安定により確認できていない。安定したネットワーク・通常のブラウザから
試すこと。

**`index.html` を `file://` で直接開くと検索に失敗する**：ブラウザは
`file://` で開いたページからのリクエストを `Origin: null` として送るが、
`overpass-api.de` 等のサーバーはこの場合CORSヘッダーを返さないため、
「Overpass APIへの接続に失敗しました」というエラーになる（Nominatim側は
`Origin: null` でも許可されるため、ジオコーディング自体は`file://`でも
動くことがある）。ページ内にも同様の警告が自動表示される。

**`http://localhost` 経由でも、Overpassミラー全てが混雑等で応答しない
ことがある**：コンソールに `signal timed out` と出る場合は、CORS拒否
ではなくクライアント側のタイムアウト（複数ミラーへ並行して問い合わせ、
一番早く返ってきたものを使う方式）が先に切れたことを示す。Overpass APIは
混雑時は数秒〜十数秒かかることがあるため、タイムアウトは20秒に設定して
いる。それでも全ミラーが20秒以内に応答しない場合は、少し時間をおく・
ルートからの許容距離を狭める・時間帯を変える、のいずれかで再試行すること。

**20秒も待てない／もっと待ちたい場合は「キャンセル」ボタンで判断を
ユーザーに委ねられる**：固定タイムアウトを短くしすぎると気づいた時には
もう諦めてしまっている一方、長くしすぎると本当に詰まった時に延々と
待たされる。そこで「ルート沿いのスポットを探す」ボタンを押すと隣に
「✕ キャンセル」ボタンが現れるようにし、20秒のタイムアウトは
「それでも応答が無ければ諦める」という保険として残しつつ、待つか
やめるかはユーザー自身がいつでも決められるようにした
（`src/geocode.js` / `src/overpassSpots.js` の `combineSignals()` が、
タイムアウト用のAbortSignalとキャンセルボタン用のAbortSignalを1つに
合成し、どちらが先に発火しても即座に中断する。地点検索・ルート計算・
スポット検索のどの段階でキャンセルしても即座に中断する）。

**OSRM（ルート計算・ルート線描画）が失敗した場合**：
`src/routeLine.js` はOSRM（`router.project-osrm.org`、公開デモサーバーで
ミラーは無い）が応答しない場合、出発地〜目的地を直線でつないだ近似に
自動的にフォールバックする。この場合は地図上の線が破線になり、地図の下に
「直線（破線）で近似表示しています」という注記が出る。直線近似でも
ルートの計算自体は失敗しないので、候補スポットの検索・登録は続けられる
（ただし直線近似の場合、ルート沿いのスポット検索の精度は道なりの経路より
落ちる）。

回避策：フォルダ内で簡単なローカルサーバーを起動し、`http://localhost:...`
経由で開く。

```bash
npx serve .
# または
python -m http.server 8000
```

Windowsの場合は [`start-local-server.bat`](./start-local-server.bat) を
ダブルクリックするだけでよい。Python（`python`/`py`）またはNode.js（`npx`）
のどちらかが入っていれば自動検出してサーバーを起動し、
`http://localhost:8080/index.html` をブラウザで自動的に開く（ポート番号は
バッチファイル先頭の `PORT` を書き換えれば変更できる）。終了する場合は、
起動と同時に開く別ウィンドウ（サーバー用コンソール）を閉じればよい。

あるいはGitHub Pages等で公開して、そのURL上で開く（楽天ホテル検索タブの
`HTTP_REFERRER_NOT_ALLOWED`対策と同じ理由で、いずれにせよ`file://`は
避けたほうがよい）。
