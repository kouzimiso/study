# WebGantt サーバー版 立案書
### ― Gitだけで完結する、公開登録型・E2E暗号化スケジュール ―

作成日: 2026-06-16　対象: `Sources/WebGantt`（JavaScript版スケジュール/ガント管理）

---

## 1. 目的

既存の JavaScript 版スケジュールソフト（`gantt.html` + `gantt_core.js`）を「Webに公開しても**他人にスケジュールの中身を見られない**」サーバー版にする。要件は次の3点。

1. アクセスすると **ユーザー登録 / ログイン** 画面になる。
2. Webに置いても**他の人に閲覧されない**（公開URLでも中身は秘匿）。
3. スケジュールは**暗号化して保存**し、**ログイン時に復号**して動作する。

加えて、利用者の希望により **「サーバーを別途立てず、Gitだけで完結」** させる方針とする（不特定多数が登録できる公開サービス）。

---

## 2. 結論（先に推奨案）

**GitHub Pages（公開・静的ホスティング）＋ GitHubアカウント認証（OAuth Device Flow）＋ 各ユーザーの「非公開 Gist」へ保存 ＋ ブラウザ内 E2E 暗号化（ゼロ知識）**

- 独自サーバー不要。GitHub の無料インフラ（Pages + Gist API）だけで成立 → **「Gitだけで完結」を満たす**。
- 誰でも GitHub アカウントでログイン＝登録できる → **「不特定多数に公開」を満たす**。
- スケジュールはブラウザ内で **AES-256-GCM** 暗号化し、鍵はユーザーのパスフレーズから **PBKDF2/Argon2id** で導出。保存先（Gist）には**暗号文しか置かない**ため、GitHub も含め誰も中身を読めない → **「他人に見られない」「ログイン時に復号」を満たす**。

> 重要な前提：**GitHub Pages 自体は秘匿化できない**（無料は公開専用、私有リポジトリで配信してもページのソースは閲覧可能）。したがって秘匿性は「ホスティングを隠すこと」ではなく **「データを暗号化して隠すこと（E2EE）」** で担保する。これが本設計の肝。

### 2.1 設置時に「案A」と「自前サーバー」を切り替え可能にする（採用方針）

本立案では、**案A（GitHub/Gist）と自前サーバー版を“設置時の設定ファイル1つで切り替えられる”プラガブル構成**を採用する。

- **共通部（変えない）**：UI（`gantt.html`）、ロジック（`gantt_core.js`）、**E2E暗号化モジュール（`crypto.js`）**。スケジュールは常にブラウザ内で暗号化され、どちらのバックエンドでも**保存先には暗号文しか渡らない**。
- **差し替え部（アダプタ）**：認証（`AuthProvider`）とデータ保存（`StorageProvider`）だけを抽象インターフェース化し、実装を2系統用意する。
  - `gist`：GitHub Device Flow 認証 ＋ 非公開 Gist 保存（案A）。
  - `selfserver`：自前サーバーの独自アカウント認証 ＋ サーバーDB保存。
- **切替方法**：`config.js`（または `config.json`）の `mode` を書き換えるだけ。コード再ビルド不要。

```js
// config.js（設置者がここだけ編集）
window.WEBGANTT_CONFIG = {
  mode: "gist",                 // "gist" | "selfserver"
  selfserver: { apiBase: "https://my-server.example.com/api" },
  gist: { clientId: "<GitHub OAuth App client_id>" },
  kdf: { algo: "PBKDF2", iterations: 600000 }   // 任意で Argon2id
};
```

これにより「まず案A（無料・サーバー不要）で公開し、後から自前サーバーへ移行」も、設定変更＋暗号データの移行だけで可能になる。

---

## 3. 前提となる技術的事実（2026年6月時点の調査）

### 3.1 GitHub / Git の公開・秘匿の実態
- **GitHub Pages（無料）は公開サイト専用**。私有リポジトリからの Pages 配信は有料プラン（Pro/Team/Enterprise）が必要で、しかも**配信されたページのソース（HTML/JS/アセット）は誰でも閲覧できる**。アクセス制御付き（閲覧者を限定できる）Pages は実質 Enterprise Cloud 限定。
- 結論：**「Webに置いて他人に見られない」をホスティング側で実現するのは無料Gitでは不可**。→ データ暗号化で対処する。

### 3.2 Git の中で秘密を持つ仕組み（参考）
- **私有リポジトリ**：ソース自体を非公開にできるが、「実行中のWebアプリにログインして使う」用途には向かない（閲覧にgit権限が要る）。
- **git-crypt / SOPS**：リポジトリ内の特定ファイルを暗号化してコミットできる。git-crypt はファイル全体を透過的に暗号化（GPG鍵 or 共通鍵）、SOPS は YAML/JSON の値だけ暗号化。**単一リポジトリを少数の鍵所有者で共有する**運用には最適だが、**不特定多数の公開Webログイン**には不向き（各利用者へ鍵配布・管理が必要）。
- → 本要件（公開・多人数）には不採用。ただし「自分＋限定メンバーだけ」運用なら有力（後述・案B）。

### 3.3 クライアント側 E2E 暗号化（ブラウザ標準）
- **Web Crypto API** が全モダンブラウザで利用可。**AES-256-GCM**（認証付き暗号＝改ざん検知付き）を外部ライブラリ無しで利用できる。
- 鍵はパスフレーズから **PBKDF2-SHA256** で導出（OWASP 2025 目安：**60万回**）。より強い **Argon2id**（OWASP/NIST 推奨、RFC 9106）は WASM 実装（argon2-browser）で利用可能だが、ブラウザでは PBKDF2 より重い。→ **既定は PBKDF2(600k)、オプションで Argon2id**。
- これにより「サーバー（GitHub）は暗号文しか持たない＝ゼロ知識」を実現。

### 3.4 もし「外部サービス利用可」なら（比較用）
- **Cloudflare Pages + Cloudflare Access（Zero Trust 無料・最大50ユーザー）**：静的サイトをログインゲートで囲える。**Cloudflare Workers + D1/KV** は無料枠が最も広い（1日10万リクエスト等）。アプリ独自アカウントやサーバー保存が必要な場合の有力な土台。今回は「Gitだけで完結」方針のため**次点**。

---

## 4. 要件定義

### 4.1 機能要件
- F1. 初回アクセスで **ログイン/登録画面**を表示。
- F2. **GitHubアカウントでログイン**（＝登録。OAuth Device Flow）。
- F3. ログイン後に**パスフレーズ**を入力し、保存済み暗号データを**復号**して既存ガント画面を表示。
- F4. 編集内容は暗号化して**自分の非公開 Gist** に保存（自動保存＋手動保存）。
- F5. 既存機能（ガント表示、Plan/Todo編集、状態遷移、報告書、テンプレート等）はそのまま動作。
- F6. ログアウトで鍵・トークンをメモリ/セッションから破棄。
- F7. （任意）暗号化JSONのエクスポート/インポート（バックアップ・端末移行）。

### 4.2 非機能・セキュリティ要件
- N1. **ゼロ知識**：サーバー（GitHub）も運営者も平文スケジュールを復元できない。
- N2. パスフレーズはどこにも平文/ハッシュで送らない（鍵導出はブラウザ内のみ）。
- N3. 通信は HTTPS（GitHub API/Pages は標準でTLS）。
- N4. **XSS対策**（E2EEはXSSに弱いため最優先）：依存最小、CSP、外部スクリプト禁止、SRI。
- N5. パスフレーズ紛失＝復号不能を明示し、回復策（リカバリコード/バックアップ）を提供。
- N6. 既存JSフォーマット（PlanList JSON）を維持。

---

## 5. 推奨アーキテクチャ（案A）詳細

### 5.1 全体像
```
[ブラウザ(公開GitHub Pages配信)]
   │  1. GitHub OAuth Device Flow でログイン（client_secret不要）
   │       → access_token（gistスコープ）取得（sessionStorageに保持）
   │  2. パスフレーズ入力 → PBKDF2/Argon2id で AES鍵を導出（ブラウザ内のみ）
   │  3. 自分の非公開Gist から暗号文(JSON)を取得 → AES-256-GCMで復号
   │  4. 既存 gantt_core.js / gantt.html でスケジュール表示・編集
   │  5. 変更は暗号化して PATCH /gists/:id で保存（暗号文のみ送信）
   ▼
[GitHub]  Pages=アプリ配信(公開) / Gist=各ユーザーの暗号データ保管(非公開)
          ※ GitHub は暗号文しか保持しない（中身は読めない）
```

### 5.2 認証：GitHub OAuth **Device Flow** を使う理由
- 通常のOAuth Webフローは **client_secret** が必要 → 公開静的サイトには置けない（漏洩する）。
- **Device Flow は client_secret 不要**で、公開クライアント向けに設計されている。静的サイト単体（サーバーレス）で GitHub ログインを実現できる。
- 流れ：アプリが device code を取得 → ユーザーに「github.com/login/device でコード入力」を促す → ポーリングで access_token 取得。
- スコープは **`gist` のみ**（最小権限）。リポジトリ全体の権限は要求しない。
- 代替（さらに簡素）：ユーザーが **Fine-grained PAT（Gist権限）** を貼り付ける方式。実装は最小だがUXは劣る。MVPはPAT、正式版はDevice Flow、と段階移行可。

### 5.3 暗号設計（ゼロ知識）
- **登録時**：パスフレーズ入力 → ランダム salt 生成 → KDFで鍵導出 → 空スケジュールを暗号化 → 検証用に小さな「マジック値」も暗号化（パスフレーズ正否判定用）→ Gist保存。
- **ログイン時**：Gistから取得 → 同じ salt と入力パスフレーズで鍵導出 → 復号成功すればログイン成立（パスフレーズ照合＝復号可否で判定。サーバー照合なし）。
- **保存フォーマット（Gist内 `schedule.enc.json`）例**：
```json
{
  "v": 1,
  "kdf": { "algo": "PBKDF2", "hash": "SHA-256", "iterations": 600000, "salt": "<base64>" },
  "cipher": { "algo": "AES-GCM", "iv": "<base64>", "ct": "<base64(暗号文=PlanList JSON)>" },
  "check": { "iv": "<base64>", "ct": "<base64(既知マジック値)>" }
}
```
- 平文は**復号後のメモリ上のみ**。`localStorage` には平文を置かない（暗号文キャッシュは可）。

### 5.4 データモデル
- 1ユーザー = 1つの非公開Gist（`description: "webgantt-data"` で識別）。
- Gist内ファイル：`schedule.enc.json`（本体）。将来 `meta.json`（更新日時・KDFパラメータ履歴）を追加可。
- スケジュール本体の平文構造は**既存 PlanList JSON 仕様のまま**（`gantt_core.js` がそのまま処理）。

### 5.5 既存資産の再利用
- `gantt_core.js`：**そのまま流用**（純粋ロジック、変更不要）。
- `gantt.html`：UIは流用。データ入出力部だけ「ローカルファイル/localStorage」から「Gist取得・保存＋暗号化」に差し替え。
- 追加実装：`auth.js`（Device Flow）、`crypto.js`（KDF＋AES-GCM）、`store_gist.js`（Gist読書）、ログイン/登録画面。

### 5.6 切替の核：共通インターフェース（プラガブル設計）

UI は下記の2インターフェースだけに依存させ、実装を `config.mode` で選ぶ。**暗号化は呼び出し側（共通）で行い、Provider は暗号文(string)だけを扱う**＝どちらのバックエンドもゼロ知識。

```js
// 認証プロバイダ
interface AuthProvider {
  login(): Promise<Session>;     // 案A=GitHub Device Flow / 自前=ID・パスワード
  logout(): void;
  currentUser(): User | null;
}
// データ保存プロバイダ（暗号文のみ授受）
interface StorageProvider {
  load(): Promise<string|null>;  // 暗号化済みJSON文字列を取得（無ければnull）
  save(ciphertext: string): Promise<void>;
}
```

| 機能 | `gist` 実装（案A） | `selfserver` 実装 |
|---|---|---|
| AuthProvider.login | GitHub OAuth Device Flow（client_secret不要） | `POST /api/login`（独自アカウント） |
| 登録 | GitHubアカウント＝登録 | `POST /api/register`（メール+パスワード） |
| StorageProvider.load | `GET /gists/:id` の暗号ファイル | `GET /api/schedule`（暗号文を返す） |
| StorageProvider.save | `PATCH /gists/:id` | `PUT /api/schedule`（暗号文を受け取り保存） |
| サーバーが見えるもの | 暗号文のみ | 暗号文のみ（＋アカウント情報） |

**起動フロー（共通）**：`config.mode` でProvider生成 → `AuthProvider.login()` → パスフレーズ入力 → `StorageProvider.load()` → `crypto.decrypt()` → 既存ガント表示 → 変更時 `crypto.encrypt()` → `StorageProvider.save()`。

### 5.7 自前サーバー版（`selfserver`）の最小仕様
- 形態：任意（Node/Express、Python/FastAPI、PHP 等）。要件は下記APIを満たすことのみ。
- API：`register` / `login`（セッションorトークン発行）/ `GET schedule` / `PUT schedule`。保存は**暗号文文字列をそのまま**1ユーザー1レコードで持つ（DBは SQLite/JSON でも可）。
- パスワード（ログイン用）はサーバーで Argon2id ハッシュ保存。**スケジュール暗号鍵を導出するパスフレーズはログインパスワードと分離**（サーバーに鍵が渡らないようにする）。
- 自前サーバーなら HTTPS（リバースプロキシ等）を設置者が用意する。

---

## 6. 方式比較

| 観点 | **案A（推奨）GitHub Pages + Gist + E2EE** | 案B 私有リポ + git-crypt/SOPS | 案C Cloudflare Pages + Access + Workers/D1 | 案D 自前サーバ(Node等) |
|---|---|---|---|---|
| Gitだけで完結 | ◎（GitHubのみ） | ◎（Gitのみ） | △（Cloudflare併用） | ✕ |
| 不特定多数に公開登録 | ◎（GitHubアカウント） | ✕（鍵配布が必要） | ○（独自/IdP認証可） | ○ |
| 他人に見られない | ◎（E2EE＋非公開Gist） | ◎（ファイル暗号化） | ○（ゲート＋任意E2EE） | ○ |
| ログイン時復号 | ◎ | △（git操作で復号） | ◎ | ◎ |
| サーバー運用 | 不要 | 不要 | ほぼ不要（無料枠） | 必要（保守・可用性） |
| 費用 | 無料 | 無料 | 無料枠 | サーバー費 |
| 主な弱点 | GitHub依存・要GitHubアカウント・静的E2EEの限界 | 多人数公開に不向き | 外部依存・50人無料枠 | 運用コスト・攻撃面 |

**結論**：本立案は **案A と 案D（自前サーバー）を共通コア＋アダプタで両対応**し、**設置時に `config.mode` で切替**できる構成を採用する（§2.1・§5.6）。
- まず **`gist`（案A）** で無料・サーバー不要に公開し、必要になったら **`selfserver`（案D）** へ設定変更＋暗号データ移行で乗り換えられる。
- どちらも E2EE 共通のため、サーバー側は常に暗号文しか持たない。
- 「**自分＋限定メンバー**だけ」で良いなら **案B（git-crypt）** も最小構成として併記（公開用途には非推奨）。
- 案C（Cloudflare）は `selfserver` の API を Workers/D1 で実装する一形態として流用可能。

---

## 7. セキュリティ上の限界と注意（必読）

1. **静的サイトE2EEの根本的限界**：アプリのJS自体はホスティング元（GitHub）が配信する。配信元が悪意を持てば「復号後に平文を盗むJS」を仕込み得る。＝**ホスティング元への信頼は残る**（これは全ての静的E2EEに共通）。対策：依存を最小化、SRI、CSP、リリースをタグ管理し改ざん検知。
2. **XSSが致命傷**：E2EEはXSSに弱い。innerHTML多用を避ける（既存コードは `textContent`/DOM生成中心で良好）、外部スクリプト読み込み禁止、厳格なCSP。
3. **パスフレーズ紛失＝復号不能**：サーバーに鍵が無いため**リセット不可**。対策：登録時に**リカバリコード**（高エントロピー）を発行し、それでも復号できる second-wrap を用意、または暗号化バックアップのエクスポートを必須化。
4. **トークンの扱い**：GitHubトークンは `sessionStorage`（タブを閉じれば消える）に限定保持。スコープは `gist` のみ。
5. **公開＝濫用対策**：不特定多数公開では GitHub API レート制限・スパム登録の考慮が必要（各ユーザーは自分のGistを使うため負荷は分散されるが、Device Flow のポーリング等に注意）。
6. **GitHub依存リスク**：仕様変更・障害・規約。重要データは暗号化エクスポートで多重バックアップ。

---

## 8. 開発フェーズ計画

| Phase | 内容 | 完了条件 |
|---|---|---|
| P0 設計確定 | 本立案書レビュー、初期 `mode` 既定値の決定 | 方針承認 |
| P1 共通コア | `crypto.js`（PBKDF2/Argon2id+AES-GCM、check値、リカバリコード）＋ Provider インターフェース＋`config.js` 読込 | 暗号化↔復号の往復テスト合格 |
| P2 結合(UI) | 既存`gantt.html`のI/Oを `StorageProvider`/`AuthProvider` 経由に差し替え（ダミーProviderで疎通） | ログイン→復号→編集→暗号保存が一周（ダミー） |
| P3 gistアダプタ | `auth_gist.js`(Device Flow)＋`store_gist.js`(Gist) | `mode:"gist"` で実GitHubに保存/復元成功 |
| P4 selfserverアダプタ | `auth_server.js`＋`store_server.js`＋最小サーバー雛形(register/login/schedule API) | `mode:"selfserver"` で同一動作 |
| P5 セキュリティ強化 | CSP/SRI、XSS点検、リカバリ導線、ログアウト破棄、両modeのE2EE検証 | 簡易セキュリティレビュー合格 |
| P6 公開 | 既定modeで配信、READMEと設置手順/利用規約/免責 | 第三者が登録・利用可能。modeの切替手順を文書化 |

各Phaseで `gantt_core.js` のテスト（既存54件）と暗号往復テストを CI 的に回す。アダプタは共通インターフェースに対する契約テストで `gist`/`selfserver` を同一観点で検証する。

---

## 9. コスト・運用
- 費用：**無料**（GitHub Pages + Gist、無料アカウント枠内）。
- 運用：サーバー保守不要。アプリ更新は Git push のみ。障害対応は GitHub 側に依存。
- バックアップ：ユーザー各自の暗号エクスポート＋（任意）リポジトリにリリースタグ。

---

## 10. リスクと対策（要約）

| リスク | 影響 | 対策 |
|---|---|---|
| パスフレーズ紛失 | データ復旧不可 | リカバリコード＋暗号バックアップ必須化 |
| ホスティング改ざん | 平文漏洩 | SRI/CSP、タグ運用、依存最小化 |
| XSS | 鍵・平文漏洩 | DOM生成中心、CSP、外部JS禁止 |
| GitHub障害/規約変更 | 利用不可 | エクスポートで多重バックアップ、移行容易な設計 |
| GitHubアカウント前提 | 一部ユーザー登録不可 | 案Cへ拡張（独自アカウント＝要バックエンド） |

---

## 11. 要確認事項（次の判断ポイント）

1. **初期の既定 `mode`**：最初の公開を `gist`（無料・サーバー不要）で始めるか、最初から `selfserver` も並行整備するか。※両対応は確定（設置時に切替可能）。
2. **自前サーバーの実装言語/基盤**：`selfserver` を作る場合の土台（Node/Express・Python・PHP・Cloudflare Workers 等）。
3. **鍵回復**：パスフレーズ紛失時、復旧不能を許容するか／リカバリコードを導入するか。
4. **KDF**：既定 PBKDF2(60万回) で良いか、Argon2id(WASM) を採用するか。
5. **gist保存先**：Gist（手軽）か、専用の私有リポジトリ（履歴管理が強い）か。

承認後、Phase 1（共通コア：暗号モジュール＋Providerインターフェース＋config）から実装に着手します。

---

## 実装状況（2026-06-16）

方針「gistで開始 → 必要時にselfserverへ設定切替」で着手。プラガブル構成で実装済み。

- ✅ P1 共通コア：`crypto.js`（PBKDF2+AES-256-GCM 封筒形式）、`config.js`（mode切替）、`providers.js`（`gist`/`selfserver`/`local`）。
- ✅ P2 UI結合：`gantt.html` を `?host=1` のホストモードに対応（暗号化/復号は親、子は平文をメモリのみ・postMessage連携。非ホスト動作は後方互換）。
- ✅ P3 gistアダプタ：GitHub Fine-grained PAT 方式（`api.github.com`／非公開Gist）。
- ✅ P4 selfserverアダプタ：REST契約（register/login/schedule）実装済み。**サーバー本体（雛形）は未実装**＝移行時に用意。
- ⏳ P5 セキュリティ強化（CSP/SRI、リカバリコードUI）・⏳ P6 公開（Pages設置・規約）。

検証：crypto 7件 / providers 15件 / index(jsdom) 14件 / gantt回帰 15件 / core 54件 すべて合格。

> 補足：`gist` のワンクリックGitHubログイン（OAuth Device Flow）は CORS の都合で静的単体では不可のため、
> MVPは PAT 貼り付け。将来ボタンログインにする場合のみトークン交換用の極小プロキシが必要。

## 参考（調査ソース）

- GitHub Pages と私有リポジトリ/公開可否: https://github.com/orgs/community/discussions/22817 , https://docs.github.com/articles/setting-repository-visibility
- Cloudflare Access（Zero Trust 無料枠）: https://www.cloudflare.com/sase/products/access/ , https://developers.cloudflare.com/cloudflare-one/
- 無料サーバーレス比較（Workers/D1 等）: https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026 , https://developers.cloudflare.com/workers/platform/pricing/
- Web Crypto による E2E 暗号化（PBKDF2/AES-GCM）: https://bradyjoslin.com/posts/webcrypto-encryption/ , https://github.com/bradyjoslin/webcrypto-example
- git-crypt / SOPS: https://blog.gitguardian.com/a-comprehensive-guide-to-sops/ , https://en.thedavestack.com/git-crypt/
- パスワードハッシュ/KDF（Argon2id・OWASP 2025/2026）: https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/
