# UnoTube (ソース)

自分好みに改造した Android 用 YouTube「UnoTube」を作るためのリポジトリです。
ダウンロードは https://ryuto-alt.github.io/unotube-releases/ から。

UnoTube は [Morphe Patches](https://github.com/MorpheApp/morphe-patches)(GPLv3) をもとにした**非公式の改造版**で、
Morphe 公式とは関係ありません。YouTube は Google LLC の商標で、UnoTube は Google とも関係ありません。

## 仕組み

Morphe Patches をフォークせず、本家の上に UnoTube の変更を「被せて」からビルドします。
本家を更新しても、被せる部分はそのまま残ります。

| ファイル | 中身 |
|---|---|
| `overlay/unotube.patch` | 本家のソースへの変更(起動アニメーション、「について」画面、検索バーの大きさなど) |
| `preset.txt` | 設定の初期値(広告・ショート・AI ボタンを消す、画質、SponsorBlock、配色など) |
| `strings.txt` | 表示する文字の差し替え(Morphe → UnoTube、設定の項目名、抜けている日本語訳) |
| `tools/make_branding.py` | アイコン・ヘッダーロゴを描く(Catppuccin Mocha) |
| `tools/make_splash.py` | 起動画面の Lottie |
| `tools/make_options.py` | パッチのオプション(アプリ名・アイコン・テーマ色) |
| `MORPHE_COMMIT` | 最後にビルドした Morphe Patches のコミット |
| `build.sh` | 全部まとめて流す |

## ビルド

Windows の Git Bash で動かす前提です。

必要なもの: Java 21 以上 / Android SDK(platform 36, build-tools 36。`ANDROID_HOME`)/ Python 3 + Pillow /
`gh`(`gh auth refresh -s read:packages` で GitHub Packages を読めるようにする)/ adb とつないだ Android 端末(arm64)

```bash
bash build.sh               # 端末の YouTube を吸い出し → ビルド → パッチ → 端末へインストール
bash build.sh --no-install  # APK を out/ に作るところまで
bash build.sh --no-pull     # 吸い出し済みの yt-<版>.apk を使う
```

初回は Morphe Patches(`MORPHE_COMMIT` のコミット)と道具(morphe-cli、APKEditor、MicroG-RE)を自動で取ってきます。
署名鍵は `keystore/yt-mod.keystore` に作られます。これを無くすと、上書きでアップデートできなくなります。

本家を新しくするとき:

```bash
git -C morphe-patches pull && bash build.sh
```

本家の変更で `overlay/unotube.patch` が当たらなくなったら、`build.sh` がそこで止まります。

## ライセンス

GPLv3(`LICENSE`)。Morphe Patches の追加条件は `NOTICE` にあります。
