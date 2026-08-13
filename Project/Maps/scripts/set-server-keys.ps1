# （任意）サーバー側に楽天APIの共通キーを登録する。
# 登録すると、各利用者が自分でキーを持っていなくても検索できるようになる（フォールバック用）。
# wrangler secret put は値をプロンプトで聞いてくるので、聞かれたら貼り付けてEnter。
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "=== サーバー共通キーの登録（任意） ===" -ForegroundColor Green
Write-Host "楽天ウェブサービスで取得した「アプリID」「アクセスキー」を、聞かれたら貼り付けてください。"
Write-Host ""

Write-Host "-- アプリID (RAKUTEN_APP_ID) --"
npx wrangler secret put RAKUTEN_APP_ID

Write-Host ""
Write-Host "-- アクセスキー (RAKUTEN_ACCESS_KEY) --"
npx wrangler secret put RAKUTEN_ACCESS_KEY

$setAffiliate = Read-Host "アフィリエイトIDも設定しますか？ (y/N)"
if ($setAffiliate -match "^[Yy]") {
  Write-Host "-- アフィリエイトID (RAKUTEN_AFFILIATE_ID) --"
  npx wrangler secret put RAKUTEN_AFFILIATE_ID
}

Write-Host ""
Write-Host "登録完了。反映には数十秒かかることがあります。" -ForegroundColor Green
