# -*- coding: utf-8 -*-
"""images/part1/incoming/ に置いた生成画像を、アプリで使う形（幅1600px の WebP）にして images/part1/ に置く。
  python3 scripts/prep_photo.py            # incoming の画像をすべて変換
ファイル名は問題 ID（例 p1-0004.png）にしておく。変換後、incoming の元画像は削除する。
Pillow が必要（pip install pillow）。"""
import pathlib, re, sys

from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "images/part1/incoming", ROOT / "images/part1"
files = sorted(p for p in SRC.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
if not files: sys.exit(f"{SRC.relative_to(ROOT)} に画像がありません")
for p in files:
    if not re.fullmatch(r"p1-\d{4}", p.stem): print(f"飛ばします（ファイル名が p1-0000 の形でない）: {p.name}"); continue
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    if im.width != 1600: im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    out = DST / f"{p.stem}.webp"
    im.save(out, "WEBP", quality=82, method=6)
    p.unlink()
    print(f"{p.name} → {out.relative_to(ROOT)}（{im.width}×{im.height}、{out.stat().st_size // 1024} KB）")
