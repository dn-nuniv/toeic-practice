# 問題ファイル（data/src）の書き方

問題の元データ。`python3 scripts/build_data.py` がここを全部読んで `data/items.json`・`data/sets.json`・`data/bank.js` を作る（この3つは手で直さない）。

## 置き場所

```
data/src/part1/pilot-v0.json      試作の49問（Part ごとに1ファイル）
data/src/part5/2026-11-20-a.json  生成バッチごとに1ファイル足していく
```

- フォルダ名 `part1`〜`part7` で Part が決まる。1ファイルに入れるのは1つの Part だけ。
- ファイル名は自由（生成日とバッチ名にするとよい）。読み込みはファイル名順だが、出力は ID 順に並べ直される。
- 問題を消すときはファイルから削除せず、`"status": "retired"` にする（学習記録が ID に紐づくため）。

## ファイルの形

```json
{
 "batch": "2026-11-20-a",
 "source": "作成者・日付・バッチ名など（items.source に入る）",
 "note": "メモ（任意）",
 "sets": [ ... ],
 "items": [ ... ]
}
```

- `sets`：Part 1・3・4・6・7。設問はセットの `questions` に入れる（`set_id` と `question_ids` は自動で入る）。
- `items`：Part 2・5 の単独の問題。
- 書ける項目は下の表のものだけ。知らない項目（書き間違い）があるとエラーになり、出力は更新されない。

### 問題（items / questions の中身）

| 項目 | 必須 | 内容 |
|---|---|---|
| `id` | ○ | `p{Part}-{4桁}`（例 `p5-0013`）。一度使った ID は変えない・使い回さない |
| `type` | ○ | 出題タイプ（`data/blueprint.json` の types） |
| `scene` | ○ | 場面（`data/blueprint.json` の scenes） |
| `level` | ○ | 目安の CEFR（`A2` / `B1` / `B2` など） |
| `prompt` | ○ | 設問文。Part 5 の空欄は `-------`、Part 6 は `[1]` など空欄番号 |
| `options` | ○ | 選択肢の文字列の配列。先頭から a, b, c, d の ID になる（Part 2 は3つ、他は4つ） |
| `answer` | ○ | 正解の選択肢ID（`a`〜`d`）。表示位置ではない |
| `explanation_ja` | ○ | 解説。根拠の英文を短く引用し、他が違う理由を1文で |
| `translation_ja` | ○ | 設問文の和訳（Part 1 など不要なら空文字 `""`） |
| `translation_options_ja` | | 選択肢の和訳（選択肢と同じ数） |
| `option_notes_ja` | ○（新しい問題） | 選択肢ごとのコメント（選択肢と同じ順・同じ数）。正解には「なぜ正解か」、誤答には「どこが違うか」。表示順は変わるので (A) などの記号は使わない |
| `point_ja` | ○（新しい問題） | TOEIC のポイント。ほかの問題にも使える知識を1〜2文（例：than を見たら比較級。much・far・even は比較級を強める） |
| `shuffle` | | 選択肢の並びを固定するときだけ `false`（金額の昇順、[1]〜[4] の位置など） |
| `status` | | `retired` にすると出題されなくなる。省略時は `draft`（reviewed / flagged はレビュー結果から自動） |
| `voices` | | Part 1・2 の話者の性別を指定するとき（例 `{"stem": "female", "options": "male"}`）。省略すると ID の番号で男女が交互に決まる |
| `part` / `source` | | 省略時はフォルダとファイルの値。書く場合はそれと一致させる |

`options` は `{"id": "a", "text": "..."}` の形でも書ける。

### セット（sets の中身）

| 項目 | 必須 | 内容 |
|---|---|---|
| `id` | ○ | `p{Part}-s{3桁}`（例 `p3-s007`）。Part 1 の試作3件だけは `p1-s0001` の4桁 |
| `kind` | ○ | `photo` / `conversation` / `announcement` / `voicemail` / `email` / `single` / `double` / `triple` / `chat` など |
| `scene` | ○ | 場面 |
| `translation_ja` | ○ | 本文・スクリプトの和訳 |
| `questions` | ○ | 設問の配列（Part 3・4 は3問、Part 6 は4問） |
| `image` | | Part 1 の写真（`images/part1/<item id>.webp`） |
| `speakers` | | Part 3・4 の話者 `[{"id": "W", "gender": "female", "name": "..."}]` |
| `segments` | | Part 3・4 のスクリプト `[{"speaker": "W", "text": "..."}]`（1要素＝1音声ファイル） |
| `graphic` | | 図表問題の図 `{"title": "...", "columns": [...], "rows": [[...]]}` |
| `passages` | | Part 6・7 の本文 `[{"type": "email", "header": {...}, "title": "...", "table": {...}, "text": "..."}]` |
| `status` | | `retired` にするとセットごと出題されなくなる |

## 最小の例（Part 5）

```json
{
 "batch": "2026-11-20-a",
 "source": "2026-11-20 / batch a",
 "items": [
  {
   "id": "p5-0013",
   "type": "grammar.part_of_speech",
   "scene": "office",
   "level": "B1",
   "prompt": "Please read the safety guidelines ------- before using the new equipment.",
   "options": ["careful", "carefully", "care", "caring"],
   "answer": "b",
   "explanation_ja": "動詞 read を修飾するので副詞 carefully。careful は形容詞、care・caring は名詞・動名詞で文が成り立たない。",
   "translation_ja": "新しい機器を使う前に、安全の手引きをよく読んでください。",
   "translation_options_ja": ["注意深い", "注意深く", "注意", "世話をすること"]
  }
 ]
}
```

ファイルを足したら `build_data.py` → `validate.py` の順に実行する。build のエラーは書き方の誤り、validate のエラー・警告は問題の中身（選択肢の数、空欄の数、正解だけ長い など）の確認。
