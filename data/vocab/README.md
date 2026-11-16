# 単語データ（data/vocab/src）の書き方

単語練習の元データ。`python3 scripts/build_data.py` がここを読んで `data/vocab.json`（1件＝Supabase の vocab の1行）と `data/vocab.js`（アプリが読む）を作る。この2つは手で直さない。

## 置き場所

```
data/vocab/src/2026-11-16-a.json   試作の100語
data/vocab/src/<バッチ名>.json      100〜200語ずつ足していく
```

## ファイルの形

```json
{
 "batch": "2026-11-20-vocab-b",
 "source": "作成者・日付・バッチ名など",
 "note": "メモ（任意）",
 "words": [
  {
   "id": "v-0101",
   "word": "invoice",
   "pos": "noun",
   "meaning_ja": "請求書",
   "level": "B1",
   "example": "Please pay the invoice within thirty days.",
   "example_ja": "請求書は30日以内にお支払いください。",
   "cloze": "invoice"
  }
 ]
}
```

| 項目 | 必須 | 内容 |
|---|---|---|
| `id` | ○ | `v-{4桁}`。一度使った ID は変えない・使い回さない（学習記録が ID に紐づく） |
| `word` | ○ | 見出し語（原形）。日→英のつづり問題の答え |
| `pos` | ○ | `noun` / `verb` / `adjective` / `adverb` / `phrase`（熟語。日→英・穴埋めのヒントは各語の頭文字：look forward to → `l___ f______ t_`） |
| `meaning_ja` | ○ | TOEIC でよく使う意味。英→日の4択の正解と、日→英の出題に使う。同じ品詞で同じ意味の語を作らない（4択で両方が正解に見える） |
| `level` | ○ | 目安の CEFR（A1〜C1）。4択のダミーは近いレベルから選ばれる |
| `example` | ○ | オリジナルの例文。人名・会社名は架空 |
| `example_ja` | ○ | 例文の和訳（穴埋め問題で一緒に表示する） |
| `cloze` | ○ | 例文の穴埋めにする語形。**例文の中にそのまま出てくる形**（approved、Registration など）。熟語は**ひと続きで出てくる形**にする（looking forward to は可、fill it out のように間に語が入る形は不可） |
| `also_ok` | | 日→英・穴埋めで正解にする別解（頭文字と字数が同じ類義語、英式のつづり、穴埋めの語形も）。例：`["remodeling"]`、`["append", "appended"]`、`["cancelled"]` |
| `distractors` | | 4択のダミーを手で決めるときだけ（単語 ID を3つ）。省略すると build が同じ品詞・近いレベルから決まった順で選ぶ |
| `status` | | `retired` にすると出題しない。省略時は `draft`（reviewed / flagged はレビュー結果から自動） |

## build が足す項目

- `distractors`・`choices`：英→日の4択のダミーと並び（レビューで「正解が1つに決まるか」を確かめるため、データに残す）
- `related_items`：この語が出てくる問題の ID（簡単な語形変化も見る）。Part の練習の前の「今日の単語」に使う

## 作る流れ（大量に作るとき）

1. 100〜200語ずつ新しいファイルで置く（音声は後回し）
2. `build_data.py` → `validate.py`（穴埋めの語が例文にない、4択に同じ意味が並ぶ、などを検出）
3. `export_review.py` で問題と一緒に `review/packet.md` に出る（単語は英→日の4択を解いてもらい、例文・ヒントも確認してもらう）→ `import_review.py`
4. レビューを通った語から音声を作る（キーは `<単語ID>:word`・`<単語ID>:ex`。今はブラウザの読み上げで代用）
