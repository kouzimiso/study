-- ユーザーが検索した「日付 × 地点(グリッドセル)」の空室結果キャッシュ。
-- 誰かが検索した結果がそのまま共有データベースにたまり、別の人が同じ日付・場所を
-- 見たときに再利用される（「数人で好きな場所・日付を検索して結果をためる」モデル）。
--
-- セル中心は全国共通のグローバル格子（src/grid.js）で量子化するため、
-- 近い場所を検索した人は同じセルを共有できる。
-- 鮮度：同じセルを「今日」誰かが検索済みなら再利用し、日付が変われば再検索する。
CREATE TABLE IF NOT EXISTS vacancy_cells (
  date TEXT NOT NULL,            -- 宿泊日 YYYY-MM-DD
  lat INTEGER NOT NULL,          -- セル中心 (度 × 1e6、グローバル格子で量子化)
  lng INTEGER NOT NULL,
  radius_km REAL NOT NULL,       -- このセルに使った検索半径(楽天API上限3.0km以下)
  hotel_count INTEGER NOT NULL,  -- 空室のある施設数
  fetched_at TEXT NOT NULL,      -- 最後に検索した日時(ISO8601)
  PRIMARY KEY (date, lat, lng)
);
CREATE INDEX IF NOT EXISTS idx_cells_date ON vacancy_cells(date);

-- 空室ホテル一覧のキャッシュ（ヒートマップのセルをクリックしたときに表示する詳細）。
-- 楽天空室検索APIのレスポンス（ホテル名・料金・アフィリエイトURL）をJSONで保存し、
-- 同じ日付・セルは当日中は再利用する。
CREATE TABLE IF NOT EXISTS hotel_details (
  date TEXT NOT NULL,            -- 宿泊日 YYYY-MM-DD
  lat INTEGER NOT NULL,          -- セル中心 (度 × 1e6)
  lng INTEGER NOT NULL,
  payload TEXT NOT NULL,         -- ホテル一覧のJSON配列
  fetched_at TEXT NOT NULL,      -- 最後に取得した日時(JST基準ISO)
  PRIMARY KEY (date, lat, lng)
);
