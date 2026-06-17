/* config.js — 設置者がここだけ編集する。サーバー版の動作モードを切り替える。
 *
 *  mode:
 *    "gist"       … GitHub の Fine-grained PAT(gist権限) でログインし、各ユーザーの
 *                   非公開Gistに暗号データを保存（無料・サーバー不要。案A）。
 *    "selfserver" … 自前サーバーAPI(register/login/schedule)に保存（案D）。
 *                   selfserver.apiBase を自分のサーバーURLにする。
 *    "local"      … ログイン無し・この端末のlocalStorageに暗号保存（オフライン/お試し）。
 *
 *  どのモードでもスケジュールはブラウザ内で AES-256-GCM 暗号化され、保存先には
 *  暗号文しか渡らない（ゼロ知識）。パスフレーズはどこにも送信されない。
 */
window.WEBGANTT_CONFIG = {
  mode: "gist",                         // "gist" | "selfserver" | "local"
  gist: {
    // 任意。Device Flow を将来使う場合の GitHub OAuth App client_id。
    // PAT 方式では未使用。
    clientId: ""
  },
  selfserver: {
    apiBase: "https://your-server.example.com/api"   // 自前サーバーのAPIベースURL
  },
  kdf: {
    iterations: 600000                  // PBKDF2 反復回数（OWASP目安）。大きいほど安全だが遅い。
  },
  sampleIfEmpty: false                  // 初回ログインでサンプルを入れるか
};
