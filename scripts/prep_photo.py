# -*- coding: utf-8 -*-
"""images/part1/incoming/ に置いた生成画像を、アプリで使う形（幅1600px の WebP）にして images/part1/ に置く。
Pillow が必要（pip install pillow）。

  python3 scripts/prep_photo.py --list                     # 届いている候補の一覧
  python3 scripts/prep_photo.py p1-0004=gemini p1-0005=gpt # 写真ごとに採用する候補を指定して変換
  python3 scripts/prep_photo.py                            # 候補が1つしかない写真（p1-0004.png など）をすべて変換

ファイル名は「問題ID-モデル名」（例 p1-0004-gpt.png / p1-0004-gemini.png）か「問題ID」だけ（p1-0004.png）。
変換した写真の候補は、採用しなかった方も含めて incoming から削除する。"""
import pathlib, re, sys
from collections import defaultdict

from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "images/part1/incoming", ROOT / "images/part1"
EXT = (".png", ".jpg", ".jpeg", ".webp")

cands = defaultdict(dict)  # item id -> {label: path}
for p in sorted(SRC.glob("*")):
    m = re.fullmatch(r"(p1-\d{4})(?:-([a-z0-9]+))?", p.stem)
    if p.suffix.lower() in EXT and m: cands[m.group(1)][m.group(2) or ""] = p
    elif p.is_file() and p.name != ".gitkeep": print(f"飛ばします（ファイル名が p1-0000 か p1-0000-モデル名 の形でない）: {p.name}")

args = sys.argv[1:]
if not cands: sys.exit(f"{SRC.relative_to(ROOT)} に画像がありません")
if args == ["--list"]:
    for k, v in sorted(cands.items()):
        print(k, ", ".join(f"{lab or '（名前なし）'}: {p.name} {Image.open(p).size}" for lab, p in v.items()))
    sys.exit()

picks = {}
if args:
    for a in args:
        iid, _, lab = a.partition("=")
        if iid not in cands or lab not in cands[iid]: sys.exit(f"候補が見つかりません: {a}（--list で確認）")
        picks[iid] = lab
else:
    for iid, v in cands.items():
        if len(v) == 1: picks[iid] = next(iter(v))
        else: print(f"{iid}: 候補が {len(v)} つあるので飛ばします（{iid}=モデル名 で指定）")

for iid, lab in sorted(picks.items()):
    im = ImageOps.exif_transpose(Image.open(cands[iid][lab])).convert("RGB")
    if im.width != 1600: im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    out = DST / f"{iid}.webp"
    im.save(out, "WEBP", quality=82, method=6)
    for p in cands[iid].values(): p.unlink()
    print(f"{iid}: {lab or '（名前なし）'} を採用 → {out.relative_to(ROOT)}（{im.width}×{im.height}、{out.stat().st_size // 1024} KB）")
