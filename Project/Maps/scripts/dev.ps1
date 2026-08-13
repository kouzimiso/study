# ローカル開発サーバーを起動する（実際のCloudflareにはデプロイしない。ローカルD1はwrangler dev用に自動生成される）。
# 楽天APIへの呼び出しは本物なので、実際に検索すればRakuten側の応答が返る。
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "=== ローカル開発サーバー ===" -ForegroundColor Green
Write-Host "[1/2] ローカルD1にスキーマを適用しています..."
npx wrangler d1 execute rakuten-vacancy-db --local --file=./schema.sql

Write-Host "[2/2] wrangler dev を起動しています（http://127.0.0.1:8787）..."
Write-Host "  index.html の CONFIG.API_BASE を一時的に http://127.0.0.1:8787 に変更してからブラウザで開くとテストできます。"
npx wrangler dev
