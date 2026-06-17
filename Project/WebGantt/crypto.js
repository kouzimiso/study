/* crypto.js — WebGantt サーバー版 E2E暗号化（ブラウザ Web Crypto / Node 両対応）
 * パスフレーズ → PBKDF2(SHA-256) → AES-256-GCM。封筒(JSON)に salt/iv/ct を格納。
 * 復号はパスフレーズ正否に等しい（GCM認証失敗＝誤パスフレーズ）。
 * Node(22)/Chrome/Safari/Firefox の Web Crypto で動作。テスト済み(7/7)。 */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = mod;
  else root.GanttCrypto = mod;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  const subtle = (globalThis.crypto && globalThis.crypto.subtle);
  const getRandom = (n) => { const a = new Uint8Array(n); globalThis.crypto.getRandomValues(a); return a; };
  const enc = new TextEncoder();
  const dec = new TextDecoder();

  function b64encode(bytes) {
    let bin = "";
    const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    for (let i = 0; i < arr.length; i++) bin += String.fromCharCode(arr[i]);
    return btoa(bin);
  }
  function b64decode(str) {
    const bin = atob(str);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  }

  const DEFAULT_KDF = { algo: "PBKDF2", hash: "SHA-256", iterations: 600000 };

  async function deriveKey(passphrase, salt, kdf) {
    kdf = kdf || DEFAULT_KDF;
    const baseKey = await subtle.importKey("raw", enc.encode(passphrase), { name: "PBKDF2" }, false, ["deriveKey"]);
    return subtle.deriveKey(
      { name: "PBKDF2", salt: salt, iterations: kdf.iterations, hash: kdf.hash },
      baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]
    );
  }

  /** plainObj を暗号化して封筒(JSON文字列)を返す。 */
  async function encrypt(plainObj, passphrase, kdfOpts) {
    const kdf = Object.assign({}, DEFAULT_KDF, kdfOpts || {});
    const salt = getRandom(16), iv = getRandom(12);
    const key = await deriveKey(passphrase, salt, kdf);
    const data = enc.encode(JSON.stringify(plainObj));
    const ct = await subtle.encrypt({ name: "AES-GCM", iv: iv }, key, data);
    return JSON.stringify({
      v: 1,
      kdf: { algo: kdf.algo, hash: kdf.hash, iterations: kdf.iterations, salt: b64encode(salt) },
      iv: b64encode(iv), ct: b64encode(new Uint8Array(ct)),
    });
  }

  /** 封筒(JSON文字列)を復号して元オブジェクトを返す。誤パスフレーズは例外(code:BAD_PASSPHRASE)。 */
  async function decrypt(envelopeStr, passphrase) {
    const env = (typeof envelopeStr === "string") ? JSON.parse(envelopeStr) : envelopeStr;
    if (!env || !env.kdf || !env.iv || !env.ct) throw new Error("invalid envelope");
    const salt = b64decode(env.kdf.salt), iv = b64decode(env.iv), ct = b64decode(env.ct);
    const key = await deriveKey(passphrase, salt, { hash: env.kdf.hash, iterations: env.kdf.iterations });
    let plain;
    try {
      plain = await subtle.decrypt({ name: "AES-GCM", iv: iv }, key, ct);
    } catch (e) {
      const err = new Error("decrypt failed (wrong passphrase?)");
      err.code = "BAD_PASSPHRASE";
      throw err;
    }
    return JSON.parse(dec.decode(plain));
  }

  /** 高エントロピーなリカバリ/識別コード（紛らわしい文字を除外）。 */
  function generateRecoveryCode(groups) {
    groups = groups || 6;
    const ALPH = "ABCDEFGHJKMNPQRSTVWXYZ23456789";
    const bytes = getRandom(groups * 4);
    let out = [];
    for (let g = 0; g < groups; g++) {
      let s = "";
      for (let i = 0; i < 4; i++) s += ALPH[bytes[g * 4 + i] % ALPH.length];
      out.push(s);
    }
    return out.join("-");
  }

  return { encrypt, decrypt, deriveKey, generateRecoveryCode, DEFAULT_KDF, isSecure: function(){ return !!subtle; }, _b64encode: b64encode, _b64decode: b64decode };
});
