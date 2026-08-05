# rakuten-vacancy-worker

盆休みなど広範囲のホテル空室状況を、**ホテルの分布密度に応じた可変エリア**でヒートマップ表示するためのバックエンド（Cloudflare Workers + D1）。

## 設計の考え方
固定グリッドではなく、**ホテルそのものを中心にした「担当範囲（検索半径）」**を使う。
- ホテル密集地（都市部）→ 隣のホテルとの距離が近い → 担当範囲は狭く（重複を避ける）
- ホテル疎な地域（郊外・地方）→ 隣のホテルとの距離が遠い → 担当範囲は楽天APIの上限である3.0kmまで広げる

担当範囲の計算（全ホテルの最近傍距離計算）はそれなりに重い処理なので、Cloudflare Workers上ではなく**ローカルのNode.jsスクリプトで一度だけ計算**し、結果をD1に流し込む。日々のWorkerは「計算済みの担当範囲を使って空室検索するだけ」の軽い仕事に専念する。

担当範囲は基本的に使い回し、**「周辺のホテル構成が前回と変わっていないか」だけを低頻度（週1回想定）でチェック**し、変化があったホテルだけ `dirty=1` を立てる。dirtyになったホテルは、運営側が `compute-territories.mjs` を再実行して担当範囲を計算し直す（現状は自動化しておらず、`/api/admin/dirty-hotels` で対象を確認する運用）。

## 全体の流れ
```
[① scripts/sync-hotels.mjs]  （初回・地域拡大時のみ、ローカルで実行）
   楽天施設検索APIで対象地域の全ホテル座標を収集 → hotels.sql / hotels.json

[② scripts/compute-territories.mjs]  （①の後、ローカルで実行）
   hotels.json を読み、ホテルごとの担当範囲(半径)を計算 → territories.sql

[③ wrangler d1 execute --file=hotels.sql / territories.sql]
   D1に投入

[④ Cloudflare Worker（日々自動実行）]
   ・平日: 各ホテルの担当範囲で空室検索 → vacancy_snapshots に保存（1日1回、日付ごとに巡回）
   ・日曜: 周辺ホテル構成が変わっていないかの軽量チェック → 変化があれば dirty=1

[⑤ フロントエンド]
   /api/heatmap?date=YYYY-MM-DD を呼んで地図に表示
```

## セットアップ手順

### 1. 楽天ウェブサービスのアプリ登録
1. https://webservice.rakuten.co.jp/app/create でアプリ登録し、`アプリID` を取得
2. 同じ画面（[Your Apps](https://webservice.rakuten.co.jp/app/list)）で `アクセスキー` も取得（現行APIでは `applicationId` に加えて `accessKey` が必須）
3. 予約導線をアフィリエイト経由にする場合は、あわせて楽天アフィリエイトIDも取得

### 2. ホテル一覧の収集とD1への投入（初回のみ）
```bash
npm install # 依存なし。Node.js 18以上でOK（組み込みfetch使用）

export RAKUTEN_APP_ID=xxxxxxxx
export RAKUTEN_ACCESS_KEY=yyyyyyyy

# ① 対象地域（現状は関東・北海道。src/grid.js の REGIONS で調整可）の全ホテルを収集
node scripts/sync-hotels.mjs > hotels.sql
# 同時に hotels.json も出力される（②の入力に使う）

# ② ホテルごとの担当範囲(半径)を計算
node scripts/compute-territories.mjs hotels.json > territories.sql
```

### 3. Cloudflareの準備
```bash
npm install -g wrangler
wrangler login

wrangler d1 create rakuten-vacancy-db
# 出力された database_id を wrangler.toml の database_id に貼り付ける

wrangler d1 execute rakuten-vacancy-db --remote --file=./schema.sql
wrangler d1 execute rakuten-vacancy-db --remote --file=./hotels.sql
wrangler d1 execute rakuten-vacancy-db --remote --file=./territories.sql

wrangler secret put RAKUTEN_APP_ID
wrangler secret put RAKUTEN_ACCESS_KEY
wrangler secret put RAKUTEN_AFFILIATE_ID   # 任意
```

### 4. デプロイ
```bash
wrangler deploy
```
以降はCronが自動的に「日々の空室巡回」と「日曜の周辺構成チェック」を回します。

## API

| エンドポイント | 説明 |
|---|---|
| `GET /api/heatmap?date=YYYY-MM-DD` | 指定日のヒートマップ用GeoJSON（ホテルごとの担当範囲＋空室件数） |
| `GET /api/status?date=YYYY-MM-DD` | その日のデータ有無・最終取得日時・「更新確認が必要か」 |
| `POST /api/refresh?date=YYYY-MM-DD` | 手動更新をトリガー（同日中に取得済みなら何もしない） |
| `GET /api/admin/dirty-hotels` | 周辺構成が変化し、担当範囲の再計算が必要なホテル一覧 |

フロント側のイメージ：
1. 日付選択時に `/api/status` を呼ぶ
2. `needsConfirmBeforeRefresh: true` なら「◯/◯の検索結果を更新しますか？」ダイアログを表示
3. ユーザーがOKしたら `/api/refresh` を呼ぶ
4. `/api/heatmap` を呼んで地図に反映

## 既知の制約・今後詰めるべき点
- **`compute-territories.mjs` の再実行は現状手動**：`/api/admin/dirty-hotels` を定期的に確認し、対象が増えてきたら `sync-hotels.mjs` → `compute-territories.mjs` を再実行してD1に反映する運用が必要。将来的には自動化（GitHub Actionsの定期実行など）も検討候補。
- **全国展開時のスケール**：ホテル数が増えるほど日々の空室巡回リクエスト数も増える。`BATCH_SIZE_PER_RUN` やCron頻度、対象日数（`TARGET_DATE_RANGE_DAYS`）で無料枠内に収まるよう調整が必要。
- **コントリビューター方式（将来検討）**：他の人が自分の楽天APIキーを登録して特定地域の巡回に参加できるようにする案。個人情報を増やさないため、アカウント登録ではなく「自分のAPIキー入力」を本人確認代わりにする方向で検討中（詳細は仕様書参照）。
- **観光地POIの重ね合わせ**：このリポジトリはバックエンド（空室データ収集）のみ。フロントエンドでOverpass APIから観光地POIを取得し、Leafletで重ねて表示する部分は別途実装する。
