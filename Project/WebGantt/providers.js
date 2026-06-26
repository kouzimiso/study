/* providers.js — 認証/保存アダプタ（mode で切替）。保存先は暗号文(string)のみ扱う＝ゼロ知識。
 * mode: "gist" | "selfserver" | "local"
 *  - gist: GitHub の Fine-grained PAT(gist権限) を貼ってログイン。各ユーザーの非公開Gistに保存。
 *          ※api.github.com はCORS対応のため静的サイト単体で動作。OAuth Device Flow は
 *            トークン交換がCORS非対応のため小さなプロキシが必要（将来拡張）。
 *  - selfserver: 自前サーバーAPI(register/login/schedule)。
 *  - local: ログイン無し・localStorageに暗号文を保存（オフライン/開発用）。
 * fetch / storage は config._fetch 等で差し替え可能（テスト用）。テスト済み(15/15)。
 */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = mod;
  else root.GanttProviders = mod;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const GIST_DESC = "webgantt-data";
  const GIST_FILE = "schedule.enc.json";

  function makeLocal(config) {
    const KEY = "webgantt_enc_v1";
    const ls = config._localStorage || (typeof localStorage !== "undefined" ? localStorage : null);
    let user = null;
    return {
      mode: "local",
      needsPassphrase: true,
      async register() { return this.login(); },
      async login() { user = { name: "local" }; return user; },
      logout() { user = null; },
      currentUser() { return user; },
      async load() { return ls ? ls.getItem(KEY) : null; },
      async save(ciphertext) { if (ls) ls.setItem(KEY, ciphertext); },
    };
  }

  function makeGist(config) {
    const fetchFn = config._fetch || function(){ return globalThis.fetch.apply(globalThis, arguments); };
    const API = "https://api.github.com";
    let token = null, user = null, gistId = null;
    async function gh(path, opts) {
      opts = opts || {};
      const headers = Object.assign({
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
      }, opts.headers || {});
      // cache:"no-store" 必須: GitHub認証APIは Cache-Control: private, max-age=60 を返すため、
      // 付けないとブラウザが最大60秒間 gist 内容をキャッシュし、保存直後の再読込で
      // 古い暗号データを返す（＝スケジュール変更が反映されない）原因になる。
      const res = await fetchFn(API + path, Object.assign({ cache: "no-store" }, opts, { headers }));
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        const e = new Error("GitHub API " + res.status + ": " + txt);
        e.status = res.status; throw e;
      }
      return res.status === 204 ? null : res.json();
    }
    return {
      mode: "gist",
      needsPassphrase: true,
      // creds: { token }  (Fine-grained PAT, gist権限)
      async login(creds) {
        token = (creds && creds.token || "").trim();
        if (!token) throw new Error("PATが必要です");
        user = await gh("/user");
        return { name: user.login, avatar: user.avatar_url };
      },
      async register(creds) { return this.login(creds); },
      logout() { token = null; user = null; gistId = null; },
      currentUser() { return user ? { name: user.login } : null; },
      async _findGist() {
        if (gistId) return gistId;
        const list = await gh("/gists?per_page=100");
        for (const g of (list || [])) {
          if (g.description === GIST_DESC && g.files && g.files[GIST_FILE]) { gistId = g.id; return gistId; }
        }
        return null;
      },
      async load() {
        const id = await this._findGist();
        if (!id) return null;
        const g = await gh("/gists/" + id);
        const f = g.files && g.files[GIST_FILE];
        if (!f) return null;
        if (f.truncated && f.raw_url) {
          const r = await fetchFn(f.raw_url, { cache: "no-store" }); return await r.text();
        }
        return f.content || null;
      },
      async save(ciphertext) {
        const body = JSON.stringify({ description: GIST_DESC, files: { [GIST_FILE]: { content: ciphertext } } });
        const id = await this._findGist();
        if (id) { await gh("/gists/" + id, { method: "PATCH", body }); }
        else {
          const created = await gh("/gists", { method: "POST", body: JSON.stringify({
            description: GIST_DESC, public: false, files: { [GIST_FILE]: { content: ciphertext } } }) });
          gistId = created.id;
        }
      },
    };
  }

  function makeSelfServer(config) {
    const fetchFn = config._fetch || function(){ return globalThis.fetch.apply(globalThis, arguments); };
    const base = (config.selfserver && config.selfserver.apiBase || "").replace(/\/$/, "");
    let token = null, user = null;
    const _ss = config._sessionStorage || (typeof sessionStorage !== "undefined" ? sessionStorage : null);
    const ss = (_ss && typeof _ss.getItem === "function") ? _ss : null;
    if (ss) { token = ss.getItem("webgantt_token") || null; }
    async function api(path, opts) {
      opts = opts || {};
      const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
      if (token) headers["Authorization"] = "Bearer " + token;
      const res = await fetchFn(base + path, Object.assign({ cache: "no-store" }, opts, { headers }));
      if (res.status === 404) return { _notfound: true };
      if (!res.ok) { const t = await res.text().catch(() => ""); const e = new Error("API " + res.status + ": " + t); e.status = res.status; throw e; }
      const ct = res.headers && res.headers.get && res.headers.get("content-type") || "";
      return ct.indexOf("application/json") >= 0 ? res.json() : res.text();
    }
    return {
      mode: "selfserver",
      needsPassphrase: true,
      async register(creds) {
        await api("/register", { method: "POST", body: JSON.stringify({ username: creds.username, password: creds.password }) });
        return this.login(creds);
      },
      async login(creds) {
        const r = await api("/login", { method: "POST", body: JSON.stringify({ username: creds.username, password: creds.password }) });
        token = r.token; user = { name: creds.username };
        if (ss) ss.setItem("webgantt_token", token);
        return user;
      },
      logout() { token = null; user = null; if (ss) ss.removeItem("webgantt_token"); },
      currentUser() { return user; },
      async load() {
        const r = await api("/schedule", { method: "GET" });
        if (r && r._notfound) return null;
        return (r && r.ciphertext) || null;
      },
      async save(ciphertext) {
        await api("/schedule", { method: "PUT", body: JSON.stringify({ ciphertext: ciphertext }) });
      },
    };
  }

  function create(config) {
    config = config || {};
    const mode = config.mode || "local";
    if (mode === "gist") return makeGist(config);
    if (mode === "selfserver") return makeSelfServer(config);
    return makeLocal(config);
  }
  return { create, GIST_DESC, GIST_FILE };
});
