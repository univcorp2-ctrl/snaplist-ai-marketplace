# Existing Solutions and API Research

調査日: 2026-07-16

## 再利用候補
- `jjshay/ebay-listing-automation` (MIT): AI画像解析、説明生成、eBay Inventory API連携の参考になる。ただしeBay中心で、日本の複数フリマ、自社ストア、PWAは不足。
- `jennyvothreads/acculister`: 複数サイト名を掲げる小規模Python実装。更新・構成・公開API適合性を精査する必要があり、直接クローンするよりコネクタ設計だけ参考にする方針。
- eBay自身のモバイルアプリにも写真からAIで商品情報を作る機能があるが、他社横断や自社ストア連携は別途必要。

## 公式APIの整理
- eBay: Browse APIで商品検索、Inventory APIで在庫商品・Offer・公開が可能。
- Yahoo!ショッピング: 商品登録APIとCSVアップロード形式が公開されている。
- メルカリ、ラクマ、個人向けYahoo!オークション: 一般開発者向けの公式出品APIを確認できなかったため、初版は下書き生成とエクスポート。

## Build vs clone
既存OSSは部分的には利用可能ですが、国内規約対応、自社ストア、複数AIゲートウェイ、iPhone PWA、公式/アシストの安全な切替を一体化したものは確認できませんでした。そのため、MIT実装を参考資料としつつ、ライセンス混入を避けて新規実装しています。

## References
- eBay Inventory API: https://developer.ebay.com/develop/api/sell/inventory_api
- eBay Browse API: https://developer.ebay.com/api-docs/buy/browse/overview.html
- Yahoo!ショッピング 商品登録API: https://developer.yahoo.co.jp/webapi/shopping/editItem.html
- Yahoo!ショッピング CSV: https://developer.yahoo.co.jp/webapi/shopping/upload_format.html
- https://github.com/jjshay/ebay-listing-automation
- https://github.com/jennyvothreads/acculister
