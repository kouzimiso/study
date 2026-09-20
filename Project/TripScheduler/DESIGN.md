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
（既存の `Project/Maps/src/overpass.js` を拡張して取得できる）。
飲食店の評価は `RestaurantFinder/src/scoring.js` の
`scoreRestaurant()` をそのまま `foodStops` のスコアに流用する。

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
2. **日内スケジューリング**（未実装）：選ばれた各Routeの `highlights` /
   `foodStops` / `wifiPowerStops` / `onsenStops` を、滞在時間・移動時間・
   食事の時間帯（昼食は11:30-13:30等）を考慮して1日の時間割に展開する。
   今回は手作業でMarkdownの表に組んだが、ロジック化するなら
   `recommendedDurationHours` を軸に貪欲法で十分（厳密な最適化は不要）
3. 連休最終日など `crowdIndex` が高い時間帯には、移動系（帰路）の予定を
   優先的に割り当てる制約を入れる
4. 生成した候補を複数パターン提示し、ユーザーが入れ替え可能にする

## 5. UI／出力

- **タイムラインビュー**：1日ごとにカード形式で時間割を表示（今回の
  Markdownの表と同じ構造をWebUIにする）
- **地図ビュー**：`Project/RestaurantFinder/src/mapExport.js` を拡張し、
  1日の訪問順を線でつないで地図上に描画（スコアに応じた色分けは流用）
- **.ics エクスポート**：Googleカレンダー等に取り込めるiCalendar形式で
  出力（`Project/TripScheduler/src/generateIcs.js` として今回試作した）

## 6. 段階的な実装ロードマップ

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | 手動でPOIを選定し、Markdown＋.icsで旅程を作る | ✅ 今回実施 |
| 1 | 旅程データをJSON化し、.icsを自動生成するスクリプト | ✅ 今回実施 |
| 1.5 | Routeカタログ化（`data/routes.json`）＋訪問履歴ベースの選定ロジック（`selectRoutesForTrip()`） | ✅ 今回実施 |
| 2 | RestaurantFinderのスコアリングを `foodStops` 選定に接続 | 未着手 |
| 3 | Overpass APIでWifi/電源スポットを自動収集し `wifiPowerStops` に反映 | 未着手 |
| 4 | 楽天トラベルAPI（Maps/rakuten.js）でホテル空室を自動反映 | 未着手 |
| 5 | Route選定後の「日内スケジューリング」を自動化（現状は手作業でMarkdown化） | 未着手 |
| 6 | Webタイムライン UI（既存Maps同様、Cloudflare Workers + D1想定）＋訪問履歴をD1で管理 | 未着手 |

Phase 2以降は既存の `RestaurantFinder` と `Maps` のコードをライブラリ
として共通化する（例：`Project/shared/` に切り出す）のが自然な流れ。

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
