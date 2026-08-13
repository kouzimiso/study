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
-- 楽天空室検索APIのレスポンス（ホテル名・料金・アフィリエイトURL）に加え、満室ホテルの
-- 名前一覧もJSONで保存し、同じ日付・セルは当日中は再利用する。
CREATE TABLE IF NOT EXISTS hotel_details (
  date TEXT NOT NULL,            -- 宿泊日 YYYY-MM-DD
  lat INTEGER NOT NULL,          -- セル中心 (度 × 1e6)
  lng INTEGER NOT NULL,
  payload TEXT NOT NULL,         -- {vacant:[...], full:[...]} のJSON
  fetched_at TEXT NOT NULL,      -- 最後に取得した日時(JST基準ISO)
  PRIMARY KEY (date, lat, lng)
);

-- セル単位（日付に依存しない）で「施設検索（ホテルの実在確認）を済ませたか」を記憶する
-- 進捗マーカー。範囲検索は「①実在するホテルを発見する」→「②発見済みホテルのある場所だけ
-- 空室確認する」の2段構成で、①の対象はランダムに一様サンプリングするのではなく無駄なく
-- 進めるため、既に調べたセルを恒久的に記録して二度と調べ直さないようにする。
-- 一度調べれば結果は変わらない（ホテルが海に湧いたり消えたりはしない）ため日付を持たない。
CREATE TABLE IF NOT EXISTS cell_facilities (
  lat INTEGER NOT NULL,              -- セル中心 (度 × 1e6)
  lng INTEGER NOT NULL,
  total_hotel_count INTEGER NOT NULL, -- このセル周辺で発見したホテル数（0なら以後スキップ対象）
  checked_at TEXT NOT NULL,          -- 確認日時(JST基準ISO)
  PRIMARY KEY (lat, lng)
);

-- 楽天の施設検索(SimpleHotelSearch)で発見した実在ホテルの一覧（日付に依存しない、恒久データ）。
-- 「①発見フェーズ」で見つかったホテルをここに蓄積し、「②空室確認フェーズ」ではランダムな
-- 座標ではなく、ここに載っている実在ホテルの場所だけを狙って空室確認することで、
-- 海や山中など存在しないホテルへの無駄な検索を原理的に無くす。
CREATE TABLE IF NOT EXISTS hotels (
  hotel_no INTEGER PRIMARY KEY,      -- 楽天のホテル番号
  name TEXT NOT NULL,
  lat INTEGER NOT NULL,              -- ホテルの実座標 (度 × 1e6)
  lng INTEGER NOT NULL,
  cell_lat INTEGER NOT NULL,         -- 所属するグローバル格子セルの中心座標
  cell_lng INTEGER NOT NULL,         -- （vacancy_cellsと突き合わせるために保持）
  discovered_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hotels_bbox ON hotels(lat, lng);
CREATE INDEX IF NOT EXISTS idx_hotels_cell ON hotels(cell_lat, cell_lng);
