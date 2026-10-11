#!/usr/bin/env bash
# UnoTube を作る: 実機の YouTube を吸い出し → Morphe パッチに初期値(preset.txt)を書き込んで
# ソースからビルド → 見た目の options を付けてパッチ → 実機へインストール。
# 重い処理は低優先度で走らせる。
#
# usage: bash build.sh                 吸い出しから全部
#        bash build.sh --no-install    APK を作るところまで
#        bash build.sh --no-pull       吸い出し済みの yt-<版>.apk を使う
# 本家の更新を取り込む: git -C morphe-patches pull && bash build.sh
set -euo pipefail
cd "$(dirname "$0")"

NO_INSTALL=0 NO_PULL=0
for a in "$@"; do
  case $a in
    --no-install) NO_INSTALL=1 ;;
    --no-pull) NO_PULL=1 ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done

CLI=tools/morphe-desktop-1.18.1-all.jar
APKEDITOR=tools/APKEditor-1.4.9.jar
SETTINGS=extensions/youtube/src/main/java/app/morphe/extension/youtube/settings/Settings.java
STRINGS=patches/src/main/resources/addresources
low() { cmd //c "start /low /wait /b $*"; }
py() { python -X utf8 -I "$@"; }
mkdir -p logs out

if [[ $NO_PULL == 0 ]]; then
  ver=$(adb shell dumpsys package com.google.android.youtube | grep -m1 versionName | cut -d= -f2 | tr -d '\r')
  echo "== 実機の YouTube $ver を吸い出し"
  rm -rf src merge_in && mkdir -p src
  for p in $(adb shell pm path com.google.android.youtube | tr -d '\r' | cut -d: -f2); do
    adb pull "$p" src/ >/dev/null
  done
  echo "== 分割 APK を結合"
  cp -r src merge_in
  low java -jar "${APKEDITOR//\//\\}" m -f -i merge_in -o "yt-$ver.apk" > logs/merge.log 2>&1
  rm -rf merge_in
else
  ver=$(ls yt-*.apk | sed -E 's/yt-(.*)\.apk/\1/' | sort -V | tail -1)
fi
test -f "yt-$ver.apk"

echo "== 本家に UnoTube を被せる (overlay / ロゴ / preset.txt / strings.txt)"
# morphe-patches の中の書き換えは毎回ここで捨てて作り直す。直接いじった変更も消えるので、
# 残したい変更は overlay/*.patch にする(git -C morphe-patches diff > overlay/xxx.patch)
git -C morphe-patches reset -q
git -C morphe-patches checkout -- .
git -C morphe-patches clean -fdq  # overlay で足したファイルも消す(ビルド結果は .gitignore 済みなので残る)
for p in overlay/*.patch; do
  git -C morphe-patches apply "../$p" || { echo "!! $p が当たらない(本家で該当箇所が変わった)"; exit 1; }
done
py tools/make_branding.py > /dev/null
py tools/make_splash.py > /dev/null
cp -r branding/res-overrides/. morphe-patches/patches/src/main/resources/
py tools/apply_preset.py preset.txt "morphe-patches/$SETTINGS"
py tools/apply_strings.py strings.txt "morphe-patches/$STRINGS"

echo "== Morphe パッチをビルド"
export GITHUB_ACTOR=${GITHUB_ACTOR:-$(gh api user -q .login)} GITHUB_TOKEN=${GITHUB_TOKEN:-$(gh auth token)}
export ANDROID_HOME=${ANDROID_HOME:-$LOCALAPPDATA/Android/Sdk}
(cd morphe-patches && low gradlew.bat :patches:buildAndroid --no-daemon --max-workers=4 --console=plain) > logs/gradle.log 2>&1 \
  || { tail -30 logs/gradle.log; exit 1; }
mpp=$(ls morphe-patches/patches/build/libs/patches-*.mpp | grep -v sources | tail -1)
pver=$(basename "$mpp" .mpp | sed 's/^patches-//')
echo "   $mpp"
# 書き換えた本家は戻しておく(overlay を作り直すときは git -C morphe-patches apply ../overlay/unotube.patch から)
git -C morphe-patches reset -q && git -C morphe-patches checkout -- . && git -C morphe-patches clean -fdq

echo "== 見た目の options を作成"
rm -f options.json
java -jar "$CLI" options-create -p "$mpp" -o options.json > logs/options.log 2>&1
py tools/make_options.py options.json

echo "== YouTube $ver にパッチ (patches $pver)"
apk="out/UnoTube-$ver.apk"
low java -jar "${CLI//\//\\}" patch -p "${mpp//\//\\}" --options-file options.json \
  --keystore keystore\\yt-mod.keystore -o "${apk//\//\\}" -t tmp "yt-$ver.apk" > logs/patch.log 2>&1 \
  || { sed 's/\x1b\[[0-9;]*m//g' logs/patch.log | grep -vE 'localizations' | tail -30; exit 1; }
if sed 's/\x1b\[[0-9;]*m//g' logs/patch.log | grep -qiE 'failed|重大|SEVERE'; then
  sed 's/\x1b\[[0-9;]*m//g' logs/patch.log | grep -iE -B2 -A5 'failed|重大|SEVERE' | head -40
  exit 1
fi
echo "== できた: $apk"

[[ $NO_INSTALL == 1 ]] && exit 0
if ! adb shell pm list packages 2>/dev/null | tr -d '\r' | grep -qx package:app.revanced.android.gms; then
  echo "== MicroG-RE (Google ログイン用) をインストール"
  adb install tools/microg-7.2.1-icon-arm64-v8a.apk
fi
# 署名が同じ(keystore/yt-mod.keystore)なら上書きでログイン状態と設定が残る
adb install -r "$apk"
echo "== インストール完了"
