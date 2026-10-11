# strings.txt の文字列を Morphe の strings.xml に書き込む。
# 本家の addresources は build.sh が毎回 git checkout で戻してから呼ぶ。
# usage: python -I tools/apply_strings.py <strings.txt> <addresources ディレクトリ>
import glob
import os
import re
import sys
from xml.sax.saxutils import escape

JA = "values-ja-rJP"


def load(path):
    out = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            sys.exit(f"{path}:{n}: '=' がない: {line}")
        k, v = (s.strip() for s in line.split("=", 1))
        out[k] = v
    return out


def android_text(s):
    # strings.xml の書式: XML のエスケープに加えて ' と " はバックスラッシュ
    return escape(s).replace("'", "\\'").replace('"', '\\"')


def find(files, name):
    pat = re.compile(r'(<string name="' + re.escape(name) + r'"[^>]*>)(.*?)(</string>)', re.S)
    for f in files:
        src = open(f, encoding="utf-8").read()
        if pat.search(src):
            return f, src, pat
    return None, None, pat


def main():
    strings, res = load(sys.argv[1]), sys.argv[2]
    ja_files = sorted(glob.glob(os.path.join(res, JA, "*", "strings.xml")))
    en_files = sorted(glob.glob(os.path.join(res, "values", "*", "strings.xml")))
    for name, text in strings.items():
        value = android_text(text)
        f, src, pat = find(ja_files, name)
        how = "日本語訳を差し替え"
        if f is None:
            f, src, pat = find(en_files, name)
            if f is None:
                sys.exit(f"文字列 '{name}' が見つからない(本家で名前が変わった?)")
            if 'translatable="false"' in pat.search(src).group(1):
                how = "固定文字を差し替え"
            else:
                # 日本語訳が抜けている: 同じモジュールの日本語ファイルに足す
                module = os.path.basename(os.path.dirname(f))
                f = os.path.join(res, JA, module, "strings.xml")
                src = open(f, encoding="utf-8").read()
                src = src.replace("</resources>", f'  <string name="{name}">{value}</string>\n</resources>')
                open(f, "w", encoding="utf-8", newline="\n").write(src)
                print(f"strings: {name} … 日本語訳を追加")
                continue
        src = pat.sub(lambda m: m.group(1) + value + m.group(3), src)
        open(f, "w", encoding="utf-8", newline="\n").write(src)
        print(f"strings: {name} … {how}")


if __name__ == "__main__":
    main()
