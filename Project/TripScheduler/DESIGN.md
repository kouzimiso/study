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
[データ収集層]                [スケジューリングエンジン]        [UI]
 food:   RestaurantFinder            ↓                   タイムライン
   /googlePlaces.js      →   POI統合データモデル    →     （1日ごとの時間割）
 hotel:  Maps/rakuten.js          ↓          ↑                ↓
 poi:    Maps/overpass.js    制約付きスケジューリング     地図ビュー
 wifi:   Overpass(拡張)          （移動時間・開場時間・       （mapExport.js拡張）
 crowd:  祝日カレンダー           混雑ピーク回避）              ↓
         +ヒューリスティック                              .ics エクスポート
```

各データソースは「アダプタ」として独立させ、POI統合データモデルに
変換して渡す構成にする（1つのAPIが死んでも他は動く）。

## 2. データモデル

```jsonc
// POI（Point of Interest）共通形式
{
  "id": "kitakamakura-engakuji",
  "name": "円覚寺",
  "category": "temple", // temple | restaurant | cafe_workspace | nature | hotel
  "lat": 35.337, "lng": 139.549,
  "avgStayMinutes": 60,
  "openingHours": "08:00-16:30",
  "nearestStation": "北鎌倉",
  "walkMinutesFromStation": 1,
  "scores": {
    "satisfaction": 78,      // RestaurantFinder型のスコアリング（飲食以外にも応用）
    "wifi": null,             // Overpassのinternet_accessタグから
    "power": null,
    "crowdIndex": 0.3         // 0(空いている)〜1(激混み)。祝日パターン推定
  },
  "source": { "provider": "overpass", "refId": "way/12345" }
}
```

Wifi/電源については専用の公開APIが乏しいため、**OpenStreetMap Overpass
APIの `internet_access` / `internet_access:fee` タグ**を第一候補にする
（既存の `Project/Maps/src/overpass.js` を拡張して取得できる）。
飲食店の評価は `RestaurantFinder/src/scoring.js` の
`scoreRestaurant()` をそのまま `scores.satisfaction` に流用する。

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

入力：出発駅、日程（開始日・終了日）、1日の活動時間枠、興味カテゴリの
重み（食事・自然・寺社・作業時間 など）、宿泊要否

処理：
1. 出発駅から一定の移動時間（例：電車30分・徒歩20分以内）で到達できる
   POIを候補として抽出
2. `crowdIndex` が高い連休最終日午後などの時間帯には、移動系（帰路）の
   予定を優先的に割り当てる制約を入れる
3. 各日について、開場時間・滞在時間・移動時間を考慮しながら貪欲法で
   訪問順を決定（厳密な最適化ではなく、実用十分な近似解でよい）
4. 食事の時間帯には `scores.satisfaction` が高い候補を優先
5. 生成した候補を複数パターン提示し、ユーザーが入れ替え可能にする

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
| 2 | RestaurantFinderのスコアリングをPOI選定に接続 | 未着手 |
| 3 | Overpass APIでWifi/電源スポットを自動収集 | 未着手 |
| 4 | 楽天トラベルAPI（Maps/rakuten.js）でホテル空室を自動反映 | 未着手 |
| 5 | 混雑度ヒューリスティック＋貪欲法スケジューリングの自動生成 | 未着手 |
| 6 | Webタイムライン UI（既存Maps同様、Cloudflare Workers + D1想定） | 未着手 |

Phase 2以降は既存の `RestaurantFinder` と `Maps` のコードをライブラリ
として共通化する（例：`Project/shared/` に切り出す）のが自然な流れ。

## 未解決の論点

- Wifi/電源の情報はOverpassのタグ網羅性に依存するため、抜けが多い
  エリアでは手動キュレーションとのハイブリッドが必要になりそう
- 混雑度は公式データが乏しく、当面は経験則＋ユーザー投稿蓄積に頼らざるを
  得ない。精度を求めるなら、実際に「行った人の体感」をUIから軽く
  投稿してもらう仕組み（`Project/Maps` の検索結果共有と同じ発想）が
  現実的
