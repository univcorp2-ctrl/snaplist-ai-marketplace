# iPhone wrapper

Web/PWA完成後に同じUIをApp Store向けiOSコンテナへ格納するCapacitor設定です。

```bash
cd mobile
npm install
npm run add:ios
npm run sync:ios
npm run open:ios
```

Xcode側でBundle IDを自社ドメインへ変更し、Camera/Photo Libraryの用途説明、署名Team、プライバシーマニフェストを設定します。Appleの署名情報はGitHubへ保存しません。
