# RestaurantFinder

食べログ・Google マップの「点数」だけに頼らず、**本当に評価できる要素**
（一次情報性・リピート言及・レビューの偏り・投稿の不自然な集中など）を
加味して店舗をスコアリング・ランキングするツール。

評価基準の考え方・リサーチの根拠は [`EVALUATION_CRITERIA.md`](./EVALUATION_CRITERIA.md) を参照。

## 構成

```
src/
  scoring.js       評価基準をロジック化したスコアリング関数（依存なし）
  googlePlaces.js  Google Places API (New) 連携（検索・詳細取得）
  cli.js           CLIエントリポイント
test/
  scoring.test.js  スコアリングロジックのユニットテスト
  fixtures/        APIキーなしでも動作確認できるデモ用データ
```

## 使い方

### デモ実行（APIキー不要）

```bash
npm install    # 依存パッケージなし。念のためengines確認用
npm start
# または
node src/cli.js --demo
```

「Google 点数は 4.6 点だが二極化・短期集中投稿が疑われる話題の店」より、
「点数は 4.3 点でもリピート言及・具体的なレビューが多い地元の店」の方が
総合スコアで上位に来ることを確認できる。

### 実データで検索（Google Places API キーが必要）

```bash
export GOOGLE_PLACES_API_KEY=xxxxx
node src/cli.js "渋谷 定食"
```

Google Places API (New) の `places:searchText` で候補を検索し、各店舗の
`Place Details`（レビュー最大5件を含む）を取得してスコアリングする。

**制約**：Places API (New) はレビューを最大5件までしか返さない仕様の
ため、二極化検知・バースト検知は限られたサンプルに基づく参考値になる。
精度を上げたい場合は、他のレビューソース（自前クローラなど、対象サイトの
利用規約の範囲内で）と組み合わせることを想定している。

## テスト

```bash
npm test
```
