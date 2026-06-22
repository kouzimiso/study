/* zip.js — 依存なしの最小 ZIP 書出/読込（store方式・CRC32付き）。
   画像付き作業メモのバンドル(DL/UPLOAD)用。window.GZ.zip(files) / window.GZ.unzip(buf)。
   files: [{name:string, data:Uint8Array}]  -> Blob(application/zip)
   unzip: ArrayBuffer -> [{name, data:Uint8Array}]（store・データ記述子なし前提＝本実装が出す形）。 */
(function () {
  "use strict";
  var T = (function () {
    var t = [], c, n, k;
    for (n = 0; n < 256; n++) { c = n; for (k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1); t[n] = c >>> 0; }
    return t;
  })();
  function crc32(u8) { var c = 0xFFFFFFFF; for (var i = 0; i < u8.length; i++) c = T[(c ^ u8[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function enc(s) { return new TextEncoder().encode(s); }
  function u16(n) { return [n & 0xFF, (n >>> 8) & 0xFF]; }
  function u32(n) { return [n & 0xFF, (n >>> 8) & 0xFF, (n >>> 16) & 0xFF, (n >>> 24) & 0xFF]; }

  function zip(files) {
    var chunks = [], central = [], offset = 0;
    files.forEach(function (f) {
      var name = enc(f.name), data = f.data || new Uint8Array(0), crc = crc32(data), sz = data.length;
      var lh = [].concat([0x50, 0x4b, 0x03, 0x04], u16(20), u16(0x0800), u16(0), u16(0), u16(0),
        u32(crc), u32(sz), u32(sz), u16(name.length), u16(0));
      var lhu = new Uint8Array(lh.length + name.length); lhu.set(lh, 0); lhu.set(name, lh.length);
      chunks.push(lhu); chunks.push(data);
      var ch = [].concat([0x50, 0x4b, 0x01, 0x02], u16(20), u16(20), u16(0x0800), u16(0), u16(0), u16(0),
        u32(crc), u32(sz), u32(sz), u16(name.length), u16(0), u16(0), u16(0), u16(0), u32(0), u32(offset));
      var chu = new Uint8Array(ch.length + name.length); chu.set(ch, 0); chu.set(name, ch.length);
      central.push(chu);
      offset += lhu.length + sz;
    });
    var cdSize = central.reduce(function (a, c) { return a + c.length; }, 0), cdOff = offset;
    var eocd = [].concat([0x50, 0x4b, 0x05, 0x06], u16(0), u16(0), u16(files.length), u16(files.length),
      u32(cdSize), u32(cdOff), u16(0));
    return new Blob(chunks.concat(central, [new Uint8Array(eocd)]), { type: "application/zip" });
  }

  function unzip(buf) {
    var dv = new DataView(buf), u8 = new Uint8Array(buf), out = [], i = 0, n = u8.length, dec = new TextDecoder();
    while (i + 4 <= n && dv.getUint32(i, true) === 0x04034b50) {
      var nameLen = dv.getUint16(i + 26, true), exLen = dv.getUint16(i + 28, true), sz = dv.getUint32(i + 22, true);
      var nameStart = i + 30, dataStart = nameStart + nameLen + exLen;
      var name = dec.decode(u8.subarray(nameStart, nameStart + nameLen));
      out.push({ name: name, data: u8.subarray(dataStart, dataStart + sz) });
      i = dataStart + sz;
    }
    return out;
  }

  window.GZ = { zip: zip, unzip: unzip, crc32: crc32 };
})();
