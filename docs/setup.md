# Setup Guide

## 1. APIなしで試す
Cloudflare Pages公開URLをiPhoneのSafariで開き、写真を選びます。商品ヒントを入れて「AIで商品を解析する」を押すと、ブラウザ内デモが動きます。共有メニューから「ホーム画面に追加」でPWA化できます。

## 2. FastAPIを接続
```bash
cp .env.example .env
pip install -e '.[dev]'
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Webの「API設定」にバックエンドURLを保存します。

## 3. AIを接続
必要なSecret名:
- `AI_GATEWAY_API_KEY`
- `AI_GATEWAY_URL`
- `AI_MODEL`

OpenAI互換ではないプロバイダーは `ai_draft` をアダプター化してください。ブラウザへAPIキーを置かないでください。

## 4. eBay自動出品
必要なSecret名:
- `EBAY_ACCESS_TOKEN`
- `EBAY_MERCHANT_LOCATION_KEY`
- `EBAY_FULFILLMENT_POLICY_ID`
- `EBAY_PAYMENT_POLICY_ID`
- `EBAY_RETURN_POLICY_ID`
- `PUBLIC_IMAGE_BASE_URL`

本番では商品カテゴリ推定、通貨換算、配送条件をストア設定に合わせて必ず調整します。

## 5. Yahoo!ショッピング
必要なSecret名:
- `YAHOO_SHOPPING_SELLER_ID`
- `YAHOO_SHOPPING_ACCESS_TOKEN`

中古品カテゴリ、商品状態、ストア固有カテゴリ、画像アップロードを確認してから送信します。

## 6. メルカリ・ラクマ・Yahoo!オークション
一般公開の出品APIが利用できる契約を取得できるまではアシストモードです。非公開APIやブラウザログインの自動化は、規約違反・アカウント停止・認証情報漏えいのリスクがあるため入れていません。

## 7. App Store配布
`mobile/` で `npm install`、`npm run sync:ios` を行う構成です。実際の配布にはApple Developer Program、Bundle ID、署名、プライバシー表示、App Store審査が必要です。
