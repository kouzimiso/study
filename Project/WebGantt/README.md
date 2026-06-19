# WebGantt — スケジュール/Todo 管理（JavaScript版）

`kivy_ui_parts.py` の `GanttChart`（ガント＝スケジュール管理機能）を、スマホのブラウザ上でも
開発・動作できる JavaScript 版として作り直したものです。**PlanList の JSON フォーマット仕様は
そのまま**。外部プログラム起動（`今すぐ実行`）は無効化しています（押すと通知のみ）。

## ファイル

| ファイル | 役割 |
|----------|------|
| `gantt.html` | アプリ本体（UI）。これをブラウザで開く。 |
| `gantt_core.js` | 純粋ロジック（ブラウザ非依存）。Python版の移植。`gantt.html` と同じフォルダに置く。 |

この2つを同じフォルダに置けば動きます（オフライン可）。サーバー不要。

## 使い方

1. `gantt.html` をブラウザ（PC / スマホ）で開く。初回はサンプルが表示されます。
2. `📂 読込` で PlanList の JSON ファイルを開く（複数可）。
3. 編集・打刻すると **この端末のブラウザに自動保存**（localStorage）されます。
4. `💾 保存` で現在の編集対象ファイルを JSON としてダウンロード（元ファイルへ反映する場合は上書き保存）。

> ブラウザは任意の場所へ直接書き込めないため、保存は「ダウンロード」方式です。
> 編集途中の状態は localStorage に自動保持されるので、閉じても続きから再開できます。

## 機能（Python版からの移植範囲）

- ガント表示：日 / 週 / 月、前後移動（◀ ▶）、今日、現在時刻ライン
- Plan バー（状態色：作業中 / 未着手 / 停止中 / 完了 / 遅延）と進捗表示
- 子 Todo の子バー展開（`Todo展開` トグル、階層対応）と折りたたみ（＋ / −）
- 繰り返し（weekly / daily(N日毎) / monthly(last可) / cron、time・until・skip_dates）
- Todo 状態遷移：未作業 / 作業中 / 停止中 / 完了、進捗率、`work_sessions`（作業期間）手動編集
- リスク警告バナー（期限超過・見積超過・実績超過・未解決トラブル・スケジュールリスク高）
- 「スケジュールなし」一覧（リスク/実行中バッジ付き）
- Plan の新規 / 編集 / 複製 / 削除 / 完了にする
- テンプレート保存・作成、PlanList インポート（重複検出）、作業報告書生成、バー色設定

## PlanList JSON 仕様（変更なし）

トップレベルは `{ "<name>": plan }` または `{ "<name>": [plan, ...] }` の混在を許容。

```json
{
  "装置立上げ": {
    "name": "装置立上げ", "type": "todo", "task_kind": "human",
    "priority": "high", "pin": true, "estimate_min": 480,
    "text": "作業内容",
    "schedule": { "start": "2026-06-15 09:00", "end": "2026-06-18 18:00", "completion": "" },
    "todo": [
      { "name": "開梱・設置", "type": "setup", "complete": true,
        "start": "2026-06-15 09:00", "end": "2026-06-15 11:00" },
      { "name": "配線", "complete": false, "estimate_min": 120,
        "children": [ { "name": "AC配線", "complete": true } ],
        "work_sessions": [ { "start": "2026-06-15 13:00", "end": "2026-06-15 14:30", "note": "" } ] }
    ]
  },
  "日次バックアップ": {
    "name": "日次バックアップ", "type": "todo",
    "schedule": { "start": "2026-06-15 19:00", "end": "2026-06-15 19:30",
      "recurrence": { "daily": true } }
  }
}
```

繰り返し例：`{"weekly":["Mon","Wed"]}` / `{"daily":2}` / `{"monthly":[1,15]}` / `{"monthly":"last"}` /
`{"cron":"30 9 * * *"}`。`recurrence.time.{start,end}`、`recurrence.until`、`recurrence.skip_dates` も対応。

## 検証

- `gantt_core.js`：Node でロジック単体テスト 54 件合格（parse/occurrence/recurrence/build_models/
  状態遷移/リスク/JSON CRUD 往復/報告書）。
- `gantt.html`：jsdom による結合スモークテスト 15 件合格（描画・範囲切替・各ポップアップ・保存）。

外部プログラム起動と Redmine 連携は本版では非対応です。

---

# サーバー版（公開・ログイン・E2E暗号化）

ローカル版に加え、**Webに公開してログインで使う暗号化版**を同梱しています。スケジュールは
ブラウザ内で AES-256-GCM 暗号化され、保存先には暗号文しか渡りません（ゼロ知識）。設置時に
`config.js` の `mode` を書き換えるだけで保存先（GitHub / 自前サーバー / ローカル）を切り替えられます。
詳細設計は `立案書_WebGanttサーバー版.md` を参照。

## 追加ファイル
| ファイル | 役割 |
|----------|------|
| `index.html` | サーバー版の入口（ログイン/登録/パスフレーズ画面 → 復号して `gantt.html` を内包表示） |
| `config.js`  | **設置者が編集**。`mode` と接続先を設定 |
| `crypto.js`  | E2E暗号（PBKDF2 + AES-256-GCM）。Node/ブラウザ両対応 |
| `providers.js` | 保存先アダプタ（`gist` / `selfserver` / `local`） |
| `deploy_github.bat` | GitHubへ公開する Windows バッチ（リポジトリ作成→push→Pages有効化） |

`gantt.html` / `gantt_core.js` はローカル版と共有（`index.html` が `?host=1` で内包し、暗号化/復号は親で実施）。

## モード切替（`config.js` の `mode`）
- **`gist`（既定・推奨）**：GitHub の **classic** PAT（**gist** スコープ）でログイン。
  ※ Fine-grained token は Gist API で 403（Resource not accessible）になるため classic を使う。
  各ユーザーの**非公開Gist**に暗号データを保存。サーバー不要・無料。
- **`selfserver`**：自前サーバーAPIに保存（`selfserver.apiBase` を設定）。後述のAPIを実装すれば移行可能。
- **`local`**：ログイン無し・この端末の localStorage に暗号保存（お試し/オフライン）。

## かんたん公開：`deploy_github.bat`（Windows）
WebGantt フォルダで `deploy_github.bat` をダブルクリック。リポジトリ名とモードを聞かれ、
選んだ `mode` で `config.js` を生成し、公開用フォルダ `_deploy` を作って GitHub へ push します。
- **GitHub CLI（`gh`）がある場合**：リポジトリ作成・push・Pages有効化まで全自動。事前に `gh auth login` を実行。
- **`gh` が無い場合**：空のPublicリポジトリを作ってURLを貼ると push。最後にPagesを手動で有効化（手順を表示）。
- 必要ツール：`git`（必須）、`gh`（任意・推奨）。`_deploy` は親リポジトリの `.gitignore` に入れておくと安全。

## 設置手順（手動・gistモードで公開する例）
1. このフォルダ（`index.html`, `config.js`, `crypto.js`, `providers.js`, `gantt.html`, `gantt_core.js`）を
   **公開GitHubリポジトリ**に置き、**GitHub Pages** を有効化（無料でHTTPS公開）。
   ※ Pagesのソースは公開されるが、データはE2EEなので閲覧されても中身は読めない。
2. 利用者は GitHub で **classic の personal access token** を作成
   （Settings → Developer settings → Tokens (classic)、スコープは **gist** のみ。
   近道: https://github.com/settings/tokens/new?scopes=gist ）。Fine-grained は Gist API で 403 になる。
3. 公開URLにアクセス → PATを貼ってログイン → パスフレーズを作成 → 利用開始。

> 注意：GitHub の OAuth **Device Flow** はトークン交換がCORS非対応のため、静的サイト単体では使えません。
> 本MVPは PAT 貼り付け方式です。ボタン1つのGitHubログインにしたい場合は、トークン交換用の極小プロキシ
> （例：Cloudflare Workers）が別途必要です。

## 自前サーバー（`selfserver`）へ移行する場合のAPI契約
`apiBase` 配下に以下を実装（**暗号文文字列をそのまま保存**するだけ。サーバーは平文を見ない）：

| メソッド/パス | 役割 | リクエスト | レスポンス |
|---|---|---|---|
| `POST /register` | 登録 | `{username,password}` | 200/4xx |
| `POST /login` | ログイン | `{username,password}` | `{token}` |
| `GET /schedule` | 取得 | (Bearer token) | `{ciphertext}` / 404=未保存 |
| `PUT /schedule` | 保存 | `{ciphertext}` (Bearer token) | 200 |

- ログインパスワードは **Argon2id 等でハッシュ保存**。暗号鍵を導出する**パスフレーズはログインパスワードと分離**（サーバーに鍵が渡らない設計）。
- HTTPS（リバースプロキシ等）は設置者が用意。

## セキュリティ上の注意（必読）
- **パスフレーズ紛失＝復号不能**（サーバーにも鍵はない）。控えを安全に保管。
- 静的サイトE2EEは**ホスティング元への信頼が残る**（配信JSが改ざんされると平文が漏れ得る）。
  リリースのタグ管理・SRI・CSP・依存最小化で軽減。
- XSSが致命傷になり得るため、外部スクリプト読み込みは避け、CSPを設定すること。

## 検証
- `crypto.js`：Node 暗号往復テスト **7件**合格（往復一致・誤パスフレーズ拒否・改ざん検知・リカバリコード形式・salt一意）。
- `providers.js`：Node 契約テスト **15件**合格（local/gist/selfserver の login/load/save/重複/401）。
- `index.html`：jsdom 結合テスト **14件**合格（local 新規→暗号化保存→アプリ表示、既存→誤/正パスフレーズ、gist/selfserver ログイン画面表示）。
- `gantt.html`：ホストモード追加後も非ホストのスモーク **15件**合格（回帰なし）。
