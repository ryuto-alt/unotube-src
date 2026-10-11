# preset.txt の初期値を Morphe の Settings.java に書き込む。
# 本家の Settings.java は build.sh が毎回 git checkout で戻してから呼ぶ。
# usage: python -I tools/apply_preset.py <preset.txt> <Settings.java>
import re
import sys


def load(path):
    out = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.split("#", 1)[0].strip() if not re.search(r'"#', line) else line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            sys.exit(f"{path}:{n}: '=' がない: {line}")
        k, v = (s.strip() for s in line.split("=", 1))
        out[k] = v
    return out


def main():
    preset, target = sys.argv[1], sys.argv[2]
    src = open(target, encoding="utf-8").read()
    missing = []
    for key, value in load(preset).items():
        # 例: new BooleanSetting("morphe_hide_ads", TRUE, ...)  ※移行用の DEPRECATED_ 行は "morphe_" 無しなので当たらない
        pat = re.compile(r'(Setting<?[\w.<>]*>?\(\s*"morphe_' + re.escape(key) + r'",\s*)([^,)]+)')
        hits = pat.findall(src)
        if len(hits) != 1:
            missing.append(f"{key} ({len(hits)} 件)")
            continue
        src = pat.sub(lambda m: m.group(1) + value, src)
    if missing:
        sys.exit("Settings.java に見つからないキー(本家で変わった?):\n  " + "\n  ".join(missing))
    open(target, "w", encoding="utf-8", newline="\n").write(src)
    print(f"preset: {len(load(preset))} 件を書き込み")


if __name__ == "__main__":
    main()
