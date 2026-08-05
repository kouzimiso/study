-- ホテル一覧（楽天トラベル施設検索APIで収集した静的情報）
CREATE TABLE IF NOT EXISTS hotels (
  hotel_no INTEGER PRIMARY KEY,
  name TEXT,
  lat REAL NOT NULL,
  lng REAL NOT NULL,
  region TEXT,
  synced_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hotels_latlng ON hotels(lat, lng);

-- ホテルごとの「担当範囲」（＝空室検索をかける半径）。
-- 最近傍ホテルとの距離をもとに計算し、密集地では狭く、疎な地域では広く（最大3.0km）なる。
-- 一度計算したら使い回し、周辺ホテル構成が変わったときだけ dirty=1 を立てて再計算対象にする。
CREATE TABLE IF NOT EXISTS hotel_territory (
  hotel_no INTEGER PRIMARY KEY REFERENCES hotels(hotel_no),
  radius_km REAL NOT NULL,
  nearest_neighbor_hotel_no INTEGER,
  nearest_neighbor_km REAL,
  neighbor_set TEXT,        -- 半径内にある近隣ホテルNoのソート済みカンマ区切り（変化検知用のスナップショット）
  computed_at TEXT NOT NULL,
  checked_at TEXT,          -- 最後に「周辺ホテル構成が変わっていないか」を確認した日時
  dirty INTEGER NOT NULL DEFAULT 0  -- 1: 周辺構成が変化した可能性があり、再計算(オフラインスクリプト)が必要
);
CREATE INDEX IF NOT EXISTS idx_territory_dirty ON hotel_territory(dirty);

-- 日付×ホテル単位の空室スナップショット（ホテルの担当範囲＝そのホテル周辺の空室施設数）
CREATE TABLE IF NOT EXISTS vacancy_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hotel_no INTEGER NOT NULL REFERENCES hotels(hotel_no),
  stay_date TEXT NOT NULL,
  hotel_count INTEGER NOT NULL,
  fetched_at TEXT NOT NULL,
  UNIQUE(hotel_no, stay_date)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON vacancy_snapshots(stay_date);

-- Cronバッチ処理の進捗管理。job_type ごとに1行（'vacancy': 日々の空室巡回 / 'neighbor_check': 周辺構成の変化確認）
CREATE TABLE IF NOT EXISTS job_state (
  job_type TEXT PRIMARY KEY,
  stay_date TEXT,     -- job_type='vacancy' のときのみ使用
  cursor INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT
);
