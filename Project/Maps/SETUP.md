# セットアップ手順書

このドキュメントは「バックエンド（Cloudflare Worker + D1）を立ち上げて、フロントから実際に楽天トラベルAPIへ検索が飛ぶようにする」までの手順と、今のセットアップ状態をまとめたものです。

## 今の状態（このリポジトリで完了済みのこと）

| 項目 | 状態 |
|---|---|
| `npm install`（wrangler等のインストール） | 済み |
| Cloudflareアカウントへのログイン (`wrangler login`) | 済み（`kouzim3@gmail.com`） |
| D1データベース作成 (`rakuten-vacancy-db`) | 済み。`wrangler.toml` に `database_id` 設定済み |
| D1へのスキーマ適用（リモート） | 済み |
| Workerのデプロイ | 済み：`https://rakuten-vacancy-worker.travelmaps.workers.dev` |
| workers.dev サブドメイン登録 | 済み（`travelmaps`） |
| `frontend/index.html` の `CONFIG.API_BASE` | 上記URLに設定済み |
| 楽天ウェブサービスのAPIキー登録 | **未完了（利用者ごとに必要）** |

つまり、バックエンドの立ち上げは完了しています。残っているのは「楽天のAPIキーを取得して、画面の『APIキー設定』から登録する」ことだけです。

## 必要なもの（前提環境）

- Node.js 18以降（`npm`/`npx` が使えること）
- Cloudflareアカウント（無料枠でOK。D1・Workersとも無料枠内で足りる想定）
- 楽天ウェブサービスのアカウント（APIキー取得用）

## バッチファイル一覧（`scripts/`）

ダブルクリックするだけで実行できます。実体は同名の `.ps1`（PowerShell）で、`.bat` はその起動ラッパーです。

| ファイル | 用途 | いつ使うか |
|---|---|---|
| `scripts/setup.bat` | 初回セットアップ一式（依存関係インストール→ログイン→D1作成→スキーマ適用→デプロイ→フロントURL反映） | 最初の1回。既に完了している手順は自動でスキップされるので、途中で失敗しても再実行すれば続きから進みます |
| `scripts/deploy.bat` | スキーマ再適用＋Workerの再デプロイ | `src/`配下のコードや`schema.sql`を変更した後 |
| `scripts/dev.bat` | ローカルでWorkerを起動（`http://127.0.0.1:8787`） | コードの動作確認をデプロイ前にしたいとき |
| `scripts/set-server-keys.bat` | 楽天APIキーをサーバー側の共通キーとして登録（任意） | 利用者が各自キーを持たなくても検索できるようにしたい場合 |

## 手順

### 1. 初回セットアップ

```bash
scripts\setup.bat
```

これだけで以下が自動的に行われます（既に済んでいる項目は自動スキップ）。

1. `npm install`
2. Cloudflareへのログイン確認（未ログインならブラウザが開くのでログイン）
3. D1データベース作成 → `wrangler.toml` に `database_id` を自動反映
4. リモートD1へのスキーマ適用
5. Workerのデプロイ
   - このとき「workers.dev サブドメイン未登録」と出た場合は、登録画面をブラウザで自動的に開きます。**画面で好きな名前を選んで保存し**、コンソールに戻って Enter を押すと自動で再デプロイされます（この「名前を選ぶ」作業だけはCLIから自動化できません）
6. デプロイされたURLを `frontend/index.html` の `CONFIG.API_BASE` に自動反映

### 2. 楽天APIキーの取得・登録（利用者ごとに必要）

1. https://webservice.rakuten.co.jp/app/create でアプリ登録し、`アプリID` を取得
2. 同じ画面（[Your Apps](https://webservice.rakuten.co.jp/app/list)）で `アクセスキー` も取得
3. `frontend/index.html` をブラウザで開き、「APIキー設定」→ アプリID・アクセスキーを入力 →「キーをテスト」で検証 →「保存」

キーはブラウザの `localStorage` にのみ保存され、サーバーには送られません（検索時のAPI呼び出しにその都度使われるだけです）。

### 3.（任意）サーバー側に共通キーを持たせる

利用者全員が自分のキーを持っている必要をなくしたい場合、サーバー側にフォールバック用のキーを登録できます。

```bash
scripts\set-server-keys.bat
```

聞かれたら楽天の `アプリID` / `アクセスキー` を貼り付けてください（アフィリエイトIDは任意）。

## 今後の運用

### コードを変更した後の再デプロイ

```bash
scripts\deploy.bat
```

`schema.sql` を変更した場合もこれで（`CREATE TABLE IF NOT EXISTS` なので）安全に反映されます。

### ローカルでの動作確認

```bash
scripts\dev.bat
```

`http://127.0.0.1:8787` でWorkerが起動します。フロントから試すには `frontend/index.html` の `CONFIG.API_BASE` を一時的に `http://127.0.0.1:8787` に変更し、確認後は本番URLに戻してください（コミット時にローカルURLが残らないよう注意）。ローカルの楽天API呼び出しは本物のAPIに実際に飛びます（モックではありません）。

## トラブルシューティング（実際に発生した事例）

- **「Failed to fetch」がAPIキー設定画面で出る**
  → `CONFIG.API_BASE` が空、またはWorkerが未デプロイの状態。ブラウザから直接見えているのはCORSエラーやDNS未解決であり、楽天側の問題ではない。`scripts\setup.bat` を実行してデプロイを完了させる
- **デプロイ直後にWorkerのURLへアクセスするとSSLエラーになる**
  → `workers.dev` サブドメイン未登録、またはDNS/TLS反映待ち（数分かかることがある）。`setup.bat` が自動で登録画面を開くので、名前を決めて保存後、数分待って再アクセス
- **`.ps1`/`wrangler.toml`/`frontend/index.html` を PowerShell の `Get-Content`/`Set-Content` で書き換えると日本語が文字化けする**
  → BOM無しUTF-8ファイルをWindows PowerShell 5.1がシステムのANSIコードページとして誤読するため。このリポジトリのスクリプトは `.NET` の `File.ReadAllText`/`WriteAllText` にBOM無しUTF-8を明示して回避済み。今後同様のファイル書き換えを追加する場合も同じ方法を使うこと

## なぜCloudflareが必要なのか

- 楽天トラベルAPIはブラウザから直接呼ぶとCORSでブロックされる（`Access-Control-Allow-Origin` が返らないため）。サーバー側でプロキシする必要がある
- このアプリの核心機能は「みんなの検索結果を共有・蓄積する」ことなので、ブラウザのlocalStorageだけでは完結せず、共有データベース（D1）が必要
- Cloudflare Workers/D1は無料枠でこの用途に十分で、現状のコードもこれを前提に書かれている（他のサーバーレス環境への移行も原理的には可能）
