# SnapList AI Marketplace

写真から商品情報を整理し、メルカリ、Yahoo!オークション、ラクマ、Yahoo!フリマ向けの確認用下書きと商品台帳を作るオープンソースPWAです。

公開Web/PWA: [SnapList AIを開く](https://snaplist-ai-marketplace.pages.dev/?release=torima-mvp-v2)

> 個人向けマーケットプレイスへの自動ログイン・自動投稿は行いません。写真だけで型番、真贋、動作、傷を断定せず、出品者が必ず最終確認します。

## 主な機能

- スマートフォンのカメラ撮影、複数写真、ドラッグ＆ドロップ
- ブラウザ内画像圧縮と圧縮サムネイル保存
- API解析と、APIキーなしで使える決定論的なデモ生成
- 商品名、ブランド、状態、型番、付属品、配送、価格、仕入、手数料、送料の編集
- 早く売る・おすすめ・利益重視の参考価格
- 想定手数料、仕入、送料を含む簡易利益計算
- メルカリ、Yahoo!オークション、ラクマ、Yahoo!フリマ向け販路別下書き
- タイトル、説明文、全体のワンクリックコピー
- Yahoo!フリマ専用掲載モード
- 下書き、出品中、売却済み、保留の商品台帳
- UTF-8 BOM付きCSV、写真を含まないJSONの入出力
- PWA、オフラインキャッシュ、iPhoneのホーム画面追加

## すぐ使う

公開URLをスマートフォンで開きます。写真を追加し、商品ヒントを入力して「写真から出品案を作る」を押してください。API未設定時は写真を外部送信せず、端末内デモ生成を使います。

商品情報を確認し、販路を選択すると確認用下書きが表示されます。コピーした内容を各サービスの公式画面で確認して出品してください。

## 商品台帳とバックアップ

商品台帳はブラウザの `localStorage` に保存されます。ブラウザデータを消すと失われるため、定期的にJSONを書き出してください。JSON/CSVには商品写真を含みません。元写真は端末側で保管してください。

## APIモード

ローカル起動:

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
python -m http.server 3000 -d web
```

Webの設定画面に `http://localhost:8000` を登録し、写真送信への同意をオンにします。APIキーはブラウザに置かず、FastAPI側の環境変数または許可済みゲートウェイへ設定します。

## 開発・テスト

```bash
pip install -e '.[dev]'
ruff check app tests
pytest -q
npm test
```

GitHub ActionsはPython lint、compile、APIテスト、Webロジックテスト、PWA静的検査を実行します。

## 規約と安全性

- マーケットプレイスのID、パスワード、Cookieを収集しません。
- CAPTCHA/MFA回避、非公開API、スクレイピング、個人向けサービスへの無人出品は実装しません。
- Yahoo!フリマは他販路と同時選択できない専用掲載モードです。
- 規約は変更されるため、実際の出品前に各サービスの最新公式ルールを確認してください。
- 市場データ未取得時の価格候補は相場ではなく、入力価格からの参考計算です。

詳細:

- [Torimaを参考にした設計方針](docs/torima-inspired-design.md)
- [規約・セキュリティ方針](docs/compliance.md)
- [商品台帳データモデル](docs/data-model.md)
- [システム構成](docs/architecture.md)
- [初期設定](docs/setup.md)

## 今後のコネクタ方針

自動出品は、正式契約と公開APIが確認できる販路だけを独立コネクタとして追加します。個人向け国内C2Cは、公式の一般向け出品APIと明確な許可が確認できるまでは、下書き、CSV、JSON、公式画面での本人確認操作に限定します。

## License

MIT
