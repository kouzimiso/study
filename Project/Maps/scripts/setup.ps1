# 初回セットアップ：依存関係インストール〜Cloudflareログイン〜D1作成〜スキーマ適用〜デプロイまでを一括実行する。
# 既に完了している手順は自動でスキップするので、途中から再実行しても安全（冪等）。
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Section($n, $total, $text) {
  Write-Host ""
  Write-Host "[$n/$total] $text" -ForegroundColor Cyan
}

Write-Host "=== rakuten-vacancy-worker セットアップ ===" -ForegroundColor Green

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Host "npm が見つかりません。Node.js (https://nodejs.org/) をインストールしてから再実行してください。" -ForegroundColor Red
  exit 1
}

$total = 6

Section 1 $total "依存関係を確認しています..."
if (-not (Test-Path "node_modules")) {
  npm install
} else {
  Write-Host "  node_modules は既に存在します。スキップします。"
}

Section 2 $total "Cloudflareへのログイン状態を確認しています..."
$whoami = npx wrangler whoami 2>&1 | Out-String
if ($whoami -notmatch "You are logged in") {
  Write-Host "  ブラウザでCloudflareへのログインを行ってください..."
  npx wrangler login
  $whoami = npx wrangler whoami 2>&1 | Out-String
} else {
  Write-Host "  既にログイン済みです。"
}
$acctMatch = [regex]::Match($whoami, "([0-9a-f]{32})")

Section 3 $total "D1データベースを確認しています..."
# 注意: このファイルには日本語コメントが含まれるBOM無しUTF-8ファイルなので、
# Get-Content/Set-Content ではなく.NETのFile APIで明示的にBOM無しUTF-8として読み書きする
# （既定エンコーディングで読み書きすると、日本語部分が文字化けすることがある）
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$tomlPath = (Resolve-Path "wrangler.toml").Path
$toml = [System.IO.File]::ReadAllText($tomlPath, $utf8NoBom)
if ($toml -match "REPLACE_WITH_YOUR_D1_DATABASE_ID") {
  Write-Host "  D1データベースを新規作成します..."
  $createOutput = npx wrangler d1 create rakuten-vacancy-db 2>&1 | Out-String
  Write-Host $createOutput
  $idMatch = [regex]::Match($createOutput, 'database_id\s*=\s*"([0-9a-f-]+)"')
  if (-not $idMatch.Success) {
    Write-Host "  database_id を自動抽出できませんでした。上の出力を見て wrangler.toml に手動で貼り付けてください。" -ForegroundColor Red
    exit 1
  }
  $dbId = $idMatch.Groups[1].Value
  $toml = $toml -replace "REPLACE_WITH_YOUR_D1_DATABASE_ID", $dbId
  [System.IO.File]::WriteAllText($tomlPath, $toml, $utf8NoBom)
  Write-Host "  wrangler.toml に database_id = $dbId を設定しました。"
} else {
  Write-Host "  既に設定済みです（database_id 設定済み）。スキップします。"
}

Section 4 $total "リモートD1にスキーマを適用しています..."
npx wrangler d1 execute rakuten-vacancy-db --remote --file=./schema.sql

Section 5 $total "Workerをデプロイしています..."
$deployOutput = npx wrangler deploy 2>&1 | Out-String
Write-Host $deployOutput

if ($deployOutput -match "register a workers\.dev subdomain") {
  Write-Host "  workers.dev サブドメインが未登録です。" -ForegroundColor Yellow
  if ($acctMatch.Success) {
    $subdomainUrl = "https://dash.cloudflare.com/$($acctMatch.Value)/workers/subdomain"
    Write-Host "  ブラウザで登録画面を開きます: $subdomainUrl"
    Start-Process $subdomainUrl
  } else {
    Write-Host "  Cloudflareダッシュボード → Workers & Pages → Settings で workers.dev サブドメインを登録してください。"
  }
  Read-Host "  好きな名前で登録して保存したら、Enterキーを押してください"
  Write-Host "  再デプロイしています..."
  $deployOutput = npx wrangler deploy 2>&1 | Out-String
  Write-Host $deployOutput
}

$urlMatch = [regex]::Match($deployOutput, 'https://[a-z0-9.\-]+\.workers\.dev')

Section 6 $total "frontend/index.html にデプロイURLを反映しています..."
if ($urlMatch.Success) {
  $workerUrl = $urlMatch.Value
  $frontendPath = (Resolve-Path "frontend/index.html").Path
  # 注意: Get-Content/Set-Content はBOM無しUTF-8ファイルをシステムのANSIコードページとして
  # 誤読・誤書込みし、日本語部分を文字化けさせることがあるため、.NETのFile APIで
  # 明示的にBOM無しUTF-8として読み書きする
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  $frontend = [System.IO.File]::ReadAllText($frontendPath, $utf8NoBom)
  $frontend = [regex]::Replace($frontend, 'API_BASE:\s*"[^"]*"', "API_BASE: `"$workerUrl`"")
  [System.IO.File]::WriteAllText($frontendPath, $frontend, $utf8NoBom)
  Write-Host "  frontend/index.html の CONFIG.API_BASE を $workerUrl に設定しました。"
} else {
  Write-Host "  デプロイURLを自動検出できませんでした。frontend/index.html の CONFIG.API_BASE を手動で設定してください。" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== セットアップ完了 ===" -ForegroundColor Green
Write-Host "残っている手動作業:"
Write-Host "  1. https://webservice.rakuten.co.jp/app/create で楽天APIキー（アプリID・アクセスキー）を取得"
Write-Host "  2. frontend/index.html を開いて「APIキー設定」から登録・テスト"
Write-Host ""
Write-Host "サーバー側に共通キーを持たせたい場合（任意）: scripts\set-server-keys.bat"
Write-Host "コード変更後の再デプロイ: scripts\deploy.bat"
Write-Host "ローカルでの動作確認: scripts\dev.bat"
