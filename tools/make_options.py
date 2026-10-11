# morphe の options-create が書いた既定の options に、UnoTube の見た目を書き込む。
# usage: python -I tools/make_options.py <options.json>
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDING = os.path.join(ROOT, "branding")

OVERRIDES = {
    "Custom branding": {
        "customName": "UnoTube",
        "customIcon": os.path.join(BRANDING, "icon"),
        "appIcon": "custom",
    },
    "Change header": {"custom": os.path.join(BRANDING, "header")},
    # Catppuccin Mocha(Mantle) / Latte(Base)
    "Theme": {"darkThemeColor": "#181825", "lightThemeColor": "#EFF1F5"},
    "Hide Shorts components": {"hideShortsAppShortcut": True, "hideShortsWidget": True},
}


def main():
    path = sys.argv[1]
    data = json.load(open(path, encoding="utf-8"))
    patches = data[0]["patches"]
    for name, opts in OVERRIDES.items():
        if name not in patches:
            sys.exit(f"パッチ '{name}' が見つからない(本家で名前が変わった?)")
        have = patches[name].setdefault("options", {})
        for k, v in opts.items():
            if k not in have:
                sys.exit(f"パッチ '{name}' にオプション '{k}' が無い")
            have[k] = v
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    print(f"options: {sum(map(len, OVERRIDES.values()))} 件を書き込み")


if __name__ == "__main__":
    main()
