# 商品台帳データモデル

商品台帳はブラウザの `localStorage` に `snaplist:inventory:v2` として保存されます。

```json
{
  "id": "uuid",
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601",
  "status": "draft | listed | sold | hold",
  "source": "demo | api",
  "photos": [{ "id": "uuid", "name": "photo.jpg", "thumbnail": "data:image/jpeg;base64,..." }],
  "name": "商品名",
  "brand": "ブランド",
  "category": "カテゴリ",
  "condition": "状態",
  "color": "色",
  "size": "サイズ",
  "model": "型番または要確認",
  "accessories": "付属品",
  "flaws": "傷・注意点",
  "shippingMethod": "配送方法",
  "shippingDays": "発送日数",
  "price": 5000,
  "cost": 1000,
  "feeRate": 10,
  "shippingCost": 750,
  "notes": "出品文に含めないメモ",
  "platforms": ["mercari"],
  "drafts": {}
}
```

## バックアップ

商品台帳画面のJSON出力を利用します。JSON/CSVには写真を含めないため、元写真は端末側で別途保管してください。JSON読込は同じIDの商品を更新し、新しいIDの商品を追加します。

## 正規化

読込時に未知の状態値、未知の販路、画像以外のdata URLを除外します。同じIDが複数ある場合は最後のデータを採用します。
