# TripScheduler

食べログ点数だけに頼らないRestaurantFinderの評価軸と、Mapsのホテル空室
検索の仕組みを踏まえ、「食事・Wifi/電源・空いてる場所・ホテル空室」を
横断して旅程を組み、カレンダーに落とし込むための試作。

- [`SILVER_WEEK_2026_PLAN.md`](./SILVER_WEEK_2026_PLAN.md) — 2026年
  シルバーウィーク（9/21月〜9/23水、大船発）の具体的な旅程と、その
  下調べの根拠
- [`DESIGN.md`](./DESIGN.md) — 上記のような旅程を自動生成する
  「スケジュールソフト」にするための設計案
- `data/silver-week-2026.json` — 上記旅程をイベント配列として
  構造化したデータ
- `src/generateIcs.js` — イベント配列を `.ics`（iCalendar）形式に
  変換するスクリプト（依存ライブラリなし）

## 使い方

```bash
npm test                # ユニットテスト
npm run build:ics       # data/silver-week-2026.json → silver-week-2026.ics を生成
```

生成された `.ics` ファイルはGoogleカレンダー・Appleカレンダー等に
インポートできる。任意の旅程を組みたい場合は `data/*.json` と同じ形式
（`date`, `start`, `end`, `title`, `location`, `description`）で
JSONを作り、`node src/generateIcs.js <入力.json> <出力.ics>` を実行する。
