# コード変更後の再デプロイ用。スキーマ適用（IF NOT EXISTSなので何度実行しても安全）→デプロイの順で実行する。
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "=== 再デプロイ ===" -ForegroundColor Green

$toml = Get-Content "wrangler.toml" -Raw
if ($toml -match "REPLACE_WITH_YOUR_D1_DATABASE_ID") {
  Write-Host "wrangler.toml の database_id が未設定です。先に scripts\setup.bat を実行してください。" -ForegroundColor Red
  exit 1
}

Write-Host "[1/2] リモートD1にスキーマを適用しています..."
npx wrangler d1 execute rakuten-vacancy-db --remote --file=./schema.sql

Write-Host "[2/2] Workerをデプロイしています..."
npx wrangler deploy

Write-Host ""
Write-Host "デプロイ完了。" -ForegroundColor Green
