# TripScheduler

食べログ点数だけに頼らないRestaurantFinderの評価軸と、Mapsのホテル空室
検索の仕組みを踏まえ、「食事・Wifi/電源・空いてる場所・ホテル空室」を
横断して旅程を組み、カレンダーに落とし込むための試作。

大船在住であることを前提に、大船周辺ではなく**車で日帰り圏の行き先
パターン（Route）をカタログ化**し、一度行ったRouteは記録して次回は
別の場所を優先する、という仕組みを持つ。

- [`SILVER_WEEK_2026_PLAN.md`](./SILVER_WEEK_2026_PLAN.md) — 2026年
  シルバーウィーク（9/21月〜9/23水、大船発）の具体的な旅程と、その
  下調べの根拠
- [`DESIGN.md`](./DESIGN.md) — 上記のような旅程を自動生成する
  「スケジュールソフト」にするための設計案（Routeデータモデル・
  訪問履歴によるローテーションを含む）
- `data/routes.json` — 大船から日帰り圏の行き先パターン（観光地・
  温泉・絶景ドライブ）のカタログ
- `data/visitHistory.json` — 訪問済みRouteの記録
- `data/silver-week-2026.json` — 今回選んだ3Routeを時間割に展開した
  イベント配列
- `src/selectRoutes.js` — 訪問履歴・混雑リスク・方角の多様性から
  N日分のRouteを選ぶロジック
- `src/generateIcs.js` — イベント配列を `.ics`（iCalendar）形式に
  変換するスクリプト（依存ライブラリなし）
- `src/toGanttPlanList.js` — 同じイベント配列を
  [`Project/WebGantt`](../WebGantt/) の **PlanList JSON形式**に変換する
  スクリプト。1つの旅程データから、カレンダー（.ics）とガントチャート
  （WebGantt）の両方を作れる

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

生成された `.ics` ファイルはGoogleカレンダー・Appleカレンダー等に
インポートできる。任意の旅程を組みたい場合は `data/*.json` と同じ形式
（`date`, `start`, `end`, `title`, `location`, `description`）で
JSONを作り、`node src/generateIcs.js <入力.json> <出力.ics>` を実行する。
