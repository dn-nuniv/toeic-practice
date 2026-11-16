# -*- coding: utf-8 -*-
"""レビューがどの版の問題に対するものかを示すハッシュ。
問題文・選択肢・正解、セットの本文（スクリプト・文書・図・写真）のどれかが変わると値が変わる。
import_review.py が各レビューに content_hash として記録し、build_data.py が今の問題と照合する。"""
import hashlib, json


def content_hash(item, aset=None):
    body = {"prompt": item["prompt"], "options": item["options"], "answer": item["answer"],
            "set": {k: aset.get(k) for k in ("segments", "passages", "graphic", "image")} if aset else None}
    return hashlib.sha1(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


EXPLAIN_FIELDS = ("explanation_ja", "option_notes_ja", "point_ja", "translation_ja", "translation_options_ja")


def explain_hash(item, aset=None):
    """解説の確認（export_review.py --explain）がどの版の解説に対するものか。
    問題そのもの（content_hash の中身）に加えて、解説・和訳・本文の訳のどれかが変わると値が変わる。"""
    body = {"content": content_hash(item, aset), "explain": {k: item.get(k) for k in EXPLAIN_FIELDS},
            "set_translation": aset.get("translation_ja") if aset else None}
    return hashlib.sha1(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
