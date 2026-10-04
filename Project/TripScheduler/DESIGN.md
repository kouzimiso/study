# TripScheduler 設計案

「食事・Wifi/電源・空いてる場所・ホテル空室」を横断して、満足度の高い
旅程を自動生成する**スケジュールソフト**の設計案。

`SILVER_WEEK_2026_PLAN.md` で今回手作業で行ったこと（点数だけに頼らず
複数の観点でスポットを選び、混雑ピークを避けて時間割に組む）を、
ソフトウェアとして再現可能にするのが目的。既存の2資産を土台にする：

- [`Project/RestaurantFinder`](../RestaurantFinder/) — 食べログ点数を
  鵜呑みにせず「本当に評価できる要素」でスコアリングする仕組み
- [`Project/Maps`](../Maps/) — 楽天トラベルAPIでホテル空室を検索し
  D1に蓄積する仕組み、Overpass APIで観光地POIを取得する仕組み

## 1. 全体アーキテクチャ

```
[データ収集層]                 [ルート選定]        [日内スケジューリング]     [UI]
 food:   RestaurantFinder                ↓                 ↓            タイムライン
   /googlePlaces.js      →  Routeカタログ  →  selectRoutesForTrip() → 時間割展開 → （1日ごとの表示）
 hotel:  Maps/rakuten.js  (data/routes.json)       ↑                              ↓
 poi:    Maps/overpass.js                   訪問履歴で未訪問・久しぶりを優先      地図ビュー
 wifi:   Overpass(拡張)                     (data/visitHistory.json)          （mapExport.js拡張）
 crowd:  祝日カレンダー                       方角の多様性も考慮                    ↓
         +ヒューリスティック                                                 .ics エクスポート
```

各データソースは「アダプタ」として独立させ、POI統合データモデルに
変換して渡す構成にする（1つのAPIが死んでも他は動く）。

## 2. データモデル

「自宅（大船）からどの方向にどんな体験ができるか」というパターンは
有限個に収束するという発想から、**POI（点）ではなく Route（線＝行き先
パターン）を第一級のデータ単位**にする。1つのRouteは「観光地」「温泉」
「絶景の道」のいずれかを主目的に持ち、途中のWifi/電源・食事スポットを
内包する。これは `data/routes.json` として実装済み（下記フィールドが
実データの形）。

```jsonc
// Route（行き先パターン）共通形式 — data/routes.json
{
  "id": "manazuru-yugawara",
  "name": "真鶴・湯河原 絶景と日帰り温泉ルート",
  "category": ["scenicDrive", "onsen"], // scenicDrive | onsen | sightseeing | food | nature
  "areaDirection": "西（湯河原方面）",    // 自宅から見た方角。多様性判定に使う
  "accessFromOfuna": { "car": "約1時間", "train": "..." },
  "distanceKm": 35,
  "highlights": ["真鶴岬・三ツ石", "湯河原温泉"],
  "foodStops": [{ "name": "真鶴港周辺の海鮮店", "note": "地魚・干物" }],
  "wifiPowerStops": [{ "name": "湯河原駅周辺のカフェ", "note": "要現地確認" }],
  "onsenStops": [{ "name": "湯河原温泉の日帰り入浴施設", "note": "" }],
  "crowdRisk": "low", // low | medium | high
  "recommendedDurationHours": 7,
  "tags": ["海", "温泉", "絶景", "日の出"],
  "notes": "箱根に比べて連休中でも空いている見込み。"
}
```

個々のスポット（POI）はRouteの中の `highlights` / `foodStops` /
`wifiPowerStops` / `onsenStops` として保持する。Phase 2以降で自動収集に
切り替える際は、この内側を `RestaurantFinder` のスコアリングや
Overpass取得結果で置き換える想定（外側のRoute構造は変えない）。

Wifi/電源については専用の公開APIが乏しいため、**OpenStreetMap Overpass
APIの `internet_access` / `internet_access:fee` タグ**を第一候補にする
（`src/overpassWifi.js` で実装済み。既存の `Project/Maps/src/overpass.js`
と同じ「複数パブリックインスタンスへのフォールバック」の考え方を踏襲）。
飲食店の評価は `RestaurantFinder/src/scoring.js` の
`scoreRestaurant()` をそのまま `foodStops` のスコアに流用する。

**検証状況の注記**：このセッションの実行環境からOverpass系の各インスタンス
（`overpass-api.de`、`lz4.overpass-api.de`、`overpass.kumi.systems`、
`overpass.nchc.org.tw`）への接続を試したところ、トンネル中断・タイムアウト・
502などで軒並み失敗した。`overpass.osm.ch` のみ接続できたが、返るデータが
空だった（日本のデータを持たないレプリカの可能性）。`src/overpassWifi.js`
のロジック自体はモックfetchによるユニットテストで検証済みだが、実データでの
動作確認は別の安定したネットワークから行う必要がある。

### 訪問履歴とローテーション

「一度行ったルートは記録し、次は別の場所を提案してほしい」という要求に
応えるため、訪問履歴を独立したデータとして持つ（`data/visitHistory.json`）。

```jsonc
[{ "routeId": "manazuru-yugawara", "visitedOn": "2026-09-21" }]
```

選定ロジック `src/selectRoutes.js` の `selectRoutesForTrip()` は：

1. `crowdRisk` が指定した上限（デフォルト `medium`）を超えるルートを除外
2. 各ルートの「最終訪問日からの経過日数」を計算し、**未訪問（`Infinity`）
   を最優先**、訪問済みは経過日数が長いものから優先
3. 同点の場合は、その旅程内で**まだ使っていない `areaDirection`（方角）
   を優先**し、3日間が同じ方向に偏らないようにする

これはテスト付きで実装済み（`test/selectRoutes.test.js`）。旅行後は
`visitHistory.json` に訪問日を追記するだけで、次回の提案が自動的に
別のルートへシフトする。

## 3. 混雑度（crowdIndex）の推定方法

Google Popular Times等の公式APIは提供されていないため、まずは
ヒューリスティックで代替する：

1. 祝日カレンダー（内閣府の祝日API等）から連休の位置づけ（初日／中日／
   最終日）を判定
2. NEXCO・JR等が公開する**交通機関の混雑予測発表**（今回のリサーチで
   使ったようなニュース記事・公式発表）を手動 or 定期クロールで
   `crowdIndex` の全国係数として反映
3. スポット単位の敷地の広さ・知名度（例：鎌倉大仏＝激混み確定、
   北鎌倉の寺社群＝広く分散）は初期値をキュレーションで持たせ、
   将来的にはユーザーの実測フィードバック（「行ってみたら混んでた／
   空いてた」の投稿）を `Project/Maps` と同じ「みんなで蓄積」方式で
   D1に貯めて精度を上げる

## 4. スケジューリングエンジン

入力：自宅（大船）、日程（開始日・終了日）、興味カテゴリの重み
（観光地・温泉・絶景ドライブ など）、移動手段（車／電車）、許容する
`crowdRisk` の上限

処理：
1. **Route選定**（実装済み）：`selectRoutesForTrip()` で日数分のRouteを
   訪問履歴・混雑リスク・方角の多様性から選ぶ
2. **日内スケジューリング**（実装済み）：`buildDaySchedule()` が、選ばれた
   Routeの `highlights` / `foodStops` / `onsenStops` / `wifiPowerStops` を
   「往路移動→観光→（中間で昼食）→温泉→Wifi電源休憩→帰路移動」の順に、
   `recommendedDurationHours` を総枠として均等割りで展開する。厳密な
   最適化ではなく実用十分な近似解（`accessFromOfuna.car` の文字列から
   `parseTravelMinutes()` で移動時間を推定し、往復分を確保する）
3. **統合パイプライン**（実装済み）：`src/planTrip.js` が1と2を連結し、
   N日分の旅程イベント配列を1コマンドで生成する（`npm run plan`）
4. 連休最終日など `crowdIndex` が高い時間帯には、移動系（帰路）の予定を
   優先的に割り当てる制約を入れる（現状は未実装。`planTrip.js` は
   開始時刻を固定で展開するのみ）
5. 生成した候補を複数パターン提示し、ユーザーが入れ替え可能にする

## 5. UI／出力

- **タイムラインビュー**（実装済み）：`index.html`（`src/buildIndexHtml.js`
  で生成）が日ごとにカード形式で時間割を表示する。データはビルド時に
  HTMLへ埋め込むため、`file://` で開いても（ホテル検索タブ・「現地プラン
  作成」タブを除いて）動く。この2タブは外部API（楽天／Overpass）に
  `fetch()` するため、`file://` だと `Origin: null` になり
  `HTTP_REFERRER_NOT_ALLOWED`やCORS拒否で失敗する（詳細は後述）
- **ルートカタログビュー**（実装済み）：`index.html` の2つ目のタブ。
  訪問履歴から「未訪問」「前回訪問からN日」を計算してバッジ表示する
- **地図ビュー**（実装済み）：`index.html` の3つ目のタブ。Leaflet
  （CDN読み込み）で各Routeの `searchCenter` をマーカー表示。色は
  `crowdRisk`。`RestaurantFinder/src/mapExport.js` と同じ発想（スコア/
  リスクに応じた色分け）だが、1日の訪問順を線で結ぶところまでは未実装
- **楽天ホテル検索**（実装済み、ライブ検証済み）：`index.html` の4つ目の
  タブ。ブラウザから直接 `openapi.rakuten.co.jp` を叩く。APIキーは
  localStorageにのみ保存しサーバーには送らない（`Project/Maps/index.html`
  と同じ設計）。楽天API側のCORSは `Access-Control-Allow-Origin: *` で
  許可されているため直接呼べるが、「アプリ登録」のApplication URLと
  実際のRefererが一致しないと `HTTP_REFERRER_NOT_ALLOWED` になる
  （詳細はREADME参照）
- **.ics エクスポート**：Googleカレンダー等に取り込めるiCalendar形式で
  出力（`Project/TripScheduler/src/generateIcs.js` として今回試作した）
- **ガントチャート（WebGantt）エクスポート**：`Project/WebGantt` が持つ
  PlanList JSON仕様に変換して出力（`src/toGanttPlanList.js`、後述）

### WebGantt（PlanList形式）との両立

`Project/WebGantt`（既存の私物スケジュール／Todo管理アプリ）は
「PlanList」という独自のJSON仕様を持っている（`Project/WebGantt/README.md`
参照）。TripSchedulerの旅程イベント配列（`date`/`start`/`end`/`title`/
`location`/`description`）に **`category`**（`move`/`sightseeing`/
`food`/`onsen`/`work`）と **`routeId`**（`data/routes.json` のID）の
2フィールドを足すだけで、同じ配列から

1. `src/generateIcs.js` → `.ics`（カレンダーアプリ用）
2. `src/toGanttPlanList.js` → PlanList JSON（`Project/WebGantt/gantt.html`
   でガントチャート表示用）

の両方を生成できる（下図）。イベントの正本は1つのまま、出力先ごとに
アダプタを分ける構成にしたので、旅程を編集しても片方だけ更新漏れが
起きない。

```
data/silver-week-2026.json（イベント配列 + category + routeId）
        ├─ src/generateIcs.js        → .ics（カレンダー）
        └─ src/toGanttPlanList.js    → PlanList JSON（WebGanttのガント表示）
```

変換の対応関係：

| TripScheduler（イベント） | WebGantt（PlanList） |
|---|---|
| 同じ `date` を持つイベント群 | 1つの Plan（`todo: [...]` を持つ親） |
| `title` | 子 Todo の `name` |
| `category` | 子 Todo の `type`（move/sightseeing/food/onsen/work） |
| `start`/`end`（`date`と結合） | 子 Todo の `start`/`end`（`"YYYY-MM-DD HH:MM"`） |
| `location` + `description` | 子 Todo の `text` |
| `routeId` で引いた Route の `name`/`notes` | Plan の `name`/`text` |
| `routeId` で引いた Route の `tags` | Plan の `settings.tags`（+固定タグ `旅行`/`TripScheduler`） |

`priority`/`tags`/`status` は実運用のPlanList（例：ユーザー私物の
`Shibaura_SC` リポジトリの `RunTodo.json`）に合わせて `settings` 配下に
置く形にした。`gantt_core.js` の `meta(plan, key, default)` はPlanの
トップレベル→`settings`の順に見るため、どちらに置いても動作上は同じだが、
実運用ファイルとの一貫性を優先した。

実データで `Project/WebGantt/gantt_core.js` の `loadPlansFlat()` +
`buildModels()` に通して検証済み（3 Plan・19バーが正しく構築され、
`meta()` 経由で `priority`/`tags` も正しく読めることを確認）。

## 6. 段階的な実装ロードマップ

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | 手動でPOIを選定し、Markdown＋.icsで旅程を作る | ✅ 今回実施 |
| 1 | 旅程データをJSON化し、.icsを自動生成するスクリプト | ✅ 今回実施 |
| 1.5 | Routeカタログ化（`data/routes.json`）＋訪問履歴ベースの選定ロジック（`selectRoutesForTrip()`） | ✅ 今回実施 |
| 1.6 | WebGantt PlanList形式への変換（`src/toGanttPlanList.js`）でガントチャート表示と両立 | ✅ 今回実施 |
| 1.7 | Route選定後の「日内スケジューリング」を自動化（`buildDaySchedule()`）＋選定からの統合パイプライン（`planTrip.js`） | ✅ 今回実施 |
| 2 | RestaurantFinderのスコアリングを `foodStops` 選定に接続 | 未着手 |
| 3 | Overpass APIでWifi/電源スポットを自動収集し `wifiPowerStops` に反映 | 🟡 ロジック実装・モックテスト済み。ライブ検証はこのセッションのネットワーク制約で未実施（`src/overpassWifi.js`/`src/updateWifiPowerStops.js`） |
| 4 | 楽天トラベルAPIでホテル空室を反映 | ✅ ブラウザから直接呼ぶ形で今回実施（`index.html` 「楽天ホテル検索」タブ）。キー検証・Referer要件まで実機確認済み。空室検索の自動組み込み（`foodStops`同様にRouteへ反映）は未着手 |
| 5 | 混雑ピーク時間帯を避ける制約の `planTrip.js` への組み込み（現状は開始時刻固定） | 未着手 |
| 6 | Webタイムライン UI | ✅ `index.html`（`src/buildIndexHtml.js`）として今回実施。ただし訪問履歴の保存先は今もローカルのJSONファイルで、Cloudflare Workers + D1でのオンライン化は未着手 |
| 7 | 地点を指定して動的にRoute相当のプランを生成（`data/routes.json`の事前定義に頼らない） | ✅ `index.html` 「現地プラン作成」タブとして今回実施。`src/geocode.js`（Nominatim）・`src/overpassSpots.js`（Overpass、観光/飲食/Wifi電源/温泉を横断検索）・`src/dynamicScheduler.js`（最近傍法での巡回順決定＋直線距離からの移動時間概算）。UIと各ロジックはモックテスト・Playwrightで検証済みだが、Overpass APIへのライブ接続はこのセッションの実行環境では未確認（Nominatim側は確認済み） |

Phase 2・4（自動反映の残り）は既存の `RestaurantFinder` と `Maps` の
コードをライブラリとして共通化する（例：`Project/shared/` に切り出す）
のが自然な流れ。Phase 7は `data/routes.json` の手動カタログを代替する
ものではなく、「今回の旅行のために知らない土地で即興プランを組みたい」
という別のユースケースを満たす。ユーザー私物の
`Test/travel-route-planner.html`（出発地→目的地のルート沿いにOSMで
スポットを検索し、経路に追加していくプロトタイプ）の考え方を参考にした。

## 未解決の論点

- Wifi/電源の情報はOverpassのタグ網羅性に依存するため、抜けが多い
  エリアでは手動キュレーションとのハイブリッドが必要になりそう
- 混雑度は公式データが乏しく、当面は経験則＋ユーザー投稿蓄積に頼らざるを
  得ない。精度を求めるなら、実際に「行った人の体感」をUIから軽く
  投稿してもらう仕組み（`Project/Maps` の検索結果共有と同じ発想）が
  現実的
- 現状の `areaDirection` は「北」「北西」のような大まかな方角の文字列
  一致でしか多様性を判定していないため、隣接する方角（北と北西など）
  が2日連続で選ばれることがある。緯度経度から実際の距離・方位角を
  計算する方式に置き換えれば精度が上がる
- Routeカタログは現状 `data/routes.json` に手動で8件登録しているのみ。
  「無数に登録」していくには、既存の観光メディア記事（るるぶ・じゃらん
  等）からのルート抽出を半自動化するか、地域ごとにユーザー自身が
  追記していく運用が現実的
- 日帰りではなく1泊以上のRoute（今回は扱っていない）を組み込む場合、
  ホテル空室（Maps/rakuten.js）との接続が必須になる
- 「現地プラン作成」タブの巡回順決定（`orderSpotsGreedy()`）は最近傍法の
  近似解で、スポット数が増えると遠回りが生じやすい。カテゴリごとの上限
  件数（`DEFAULT_MAX_BY_TYPE`）も固定値で、ユーザーが調整できない
- 動的検索したスポットは営業時間判定（`travel-route-planner.html` にある
  曜日・時刻ベースの開店チェック）を今回は実装していない。Overpassの
  `opening_hours` タグは取得しているが表示のみで、スケジュール生成には
  未反映
- Overpass APIはこのセッションの実行環境では接続できなかったため、
  実データでの検索結果の精度（ヒット件数・分類の妥当性）は未検証。
  安定したネットワークでの実地検証が必要
- ユーザーの実機検証で「Overpass APIへの接続に失敗しました」が再現し、
  ブラウザのコンソールログから根本原因は `index.html` を `file://` で
  直接開いていたことと判明（`file://`はOrigin:nullとして送られ、
  `overpass-api.de`等がCORSヘッダーを返さずブロックされる）。対応として
  `file://`検出時にページ内へ警告（ローカルサーバー起動を促す）を表示する
  ようにした（`src/buildIndexHtml.js`の`#dp-file-warning`）他、Windowsで
  ワンクリックでローカルサーバーを起動できる`start-local-server.bat`を
  追加した
- `http://localhost`経由に直しても、今度は4つのOverpassミラー全てで
  `signal timed out`が発生。これはCORS拒否ではなく、クライアント側の
  `AbortSignal.timeout()`がサーバーより先に切れていたことが原因
  （一度`timeoutMs`を15000→10000に短縮したのが逆効果だった。Overpass
  クエリは`[timeout:25]`でサーバーに25秒の処理猶予を伝えているため、
  クライアント側がそれより短いと、サーバーが処理中でも先に失敗扱いに
  なる）。対応として `src/overpassSpots.js` の `fetchOverpassRaw()` を
  直列リトライから `Promise.any()` による並列問い合わせに変更し
  （4ミラーを同時に試し、最初に成功したものを使う）、1ミラーあたりの
  タイムアウトを20000msに戻した。これにより合計の最悪待ち時間が
  「ミラー数×タイムアウト」から「タイムアウト1回分」に短縮される
