# CLAUDE.md — TOEIC L&R 練習アプリ

このリポジトリで作業するときの前提と手順。作業を始める前に必ず読むこと。

## 目的と段階
- AI で作った TOEIC L&R 形式の**オリジナル問題**を、シャッフル・復習スケジュール・音声つきで練習する授業補助アプリ。
- **段階1（今）**：サーバーなしの静的サイト。学習記録はブラウザ（localStorage）。リポジトリは private のまま進める（GitHub Pages は後で）。
- **段階2（予定）**：Next.js＋Supabase のログイン付きアプリ（先生の既存の JLPT アプリと同じ構成）。段階1のデータ形式と `js/store.js` の関数の形は、そのまま移せるように保つこと。
- 正確さの基準：市販教材ほどの厳密さは求めない。機械チェック＋別AI（Orca）との相互レビューで十分。

## 構成
- `index.html`, `css/`, `js/`：アプリ本体。`js/store.js` は保存先の差し替え口（段階2で Supabase 版にする）。
- `data/src/part{N}/*.json`：**問題の元データ**（生成バッチごとに1ファイル）。書き方は `data/src/README.md`。
- `data/items.json`, `data/sets.json`：問題データ（1件＝Supabase の1行）。`data/bank.js` はアプリが読むまとめ版。この3つは `build_data.py` が `data/src` から作る（手で編集しない）。
- `data/vocab/src/*.json`：**単語の元データ**（書き方は `data/vocab/README.md`）。`build_data.py` が `data/vocab.json`・`data/vocab.js` を作る。アプリの単語練習は `js/vocab.js`（英→日の4択・日→英のつづり・例文の穴埋め・単語の復習、Part の練習の前の「今日の単語」）。
- `data/blueprint.json`：大量生成の設計表（Part × 出題タイプ × 場面）。
- `data/reviews.json`：相互レビューの結果（`import_review.py` が作る）。`data/explain_reviews.json`：解説の確認の結果（`import_review.py --explain` が作る）。
- `scripts/`：`build_data.py`（データ作成）、`validate.py`（機械チェック）、`export_review.py` / `import_review.py`（相互レビュー。単語も同じ流れ）、`gen_audio.py`（音声）、`vocab_lib.py`（単語の共通処理）。
- `supabase/schema.sql`：段階2のテーブル案。`images/part1/`：Part 1 の写真。`audio/`：生成した音声と manifest。

## 作業の流れ（問題を増やすとき）
1. `data/blueprint.json` の升目を指定して問題を作り、`data/src/part{N}/<バッチ名>.json` として新しいファイルで置く（既存ファイルの問題は書き換えない。形は `data/src/README.md`）
2. `python3 scripts/build_data.py` — 書き方の誤り（知らない項目・必須項目の欠け・ID の形・重複）があるとエラーで止まる
3. `python3 scripts/validate.py` — **エラー0件になるまで直す**。警告も目を通す
4. `python3 scripts/export_review.py` → `review/PROMPT.md` と `review/packet.md` を先生が Orca に渡す → 返ってきた JSON を `python3 scripts/import_review.py <file> --reviewer orca` → もう一度 `build_data.py`
   - flagged の問題は、直すなら `data/src` の問題を書き換える（ID はそのまま）。古いレビューは効かなくなり draft に戻るので、次の export で再レビューに回る
   - 検討して直さないなら `python3 scripts/import_review.py --resolve <ID> --note "理由"` で解決済みにする
   - **解説の確認**（上とは別。正解と解説を見せて、解説・和訳の誤りを探してもらう）：`python3 scripts/export_review.py --explain [--part N] [--limit 40]` → `review/EXPLAIN_PROMPT.md` と `review/explain_packet.md` を渡す → `python3 scripts/import_review.py <file> --reviewer orca --explain` → `build_data.py`。結果は `data/explain_reviews.json`、問題ごとの状態は `explain_status`（unchecked / checked / flagged）。解説・和訳を直すと unchecked に戻る。直さないなら `--resolve <ID> --explain --note "理由"`
5. `python3 scripts/gen_audio.py --dry-run` で件数と文字数を確認 → `python3 scripts/gen_audio.py`
6. ブラウザで `index.html` を開いて確認 → コミット・push（コミットメッセージは日本語）

## 問題を作るときのルール
- **オリジナルのみ**。TOEIC 公式問題・市販教材・他のAI教材の英文や設定を流用しない。人名・会社名は架空、メールアドレスや URL は `.example` ドメイン。
- 正解は**ただ1つに決まる**こと。言い換え（paraphrase）で正解を作り、誤答は「本文の語をそのまま使ったひっかけ」「部分的に合っている」「本文にない」などで作る。正解の選択肢だけが長い・詳しい、を避ける。
- 正解は表示位置ではなく**選択肢ID**（a/b/c/d）で持つ。金額・日付の昇順や [1]〜[4] の位置など、並びに意味がある問題は `shuffle: false`。
- Part 1：選択肢は写真と照合して1つだけ正しいこと。人のいない写真で being（進行中の動作）は誤答。写真を作ったら必ず目で確認する。
- Part 2：選択肢3つ。同じ語・似た音のひっかけを入れる。間接的な応答が正解の問題も一定数入れる。
- Part 3・4：1セット3問。図表問題・発言の意図を問う問題・3人の会話も含める。
- Part 6：1セット4問、うち1問は文挿入。空欄は本文中に `[1]`〜`[4]`。
- Part 7：単一文書・チャット・ダブル／トリプルパッセージ。照合問題（cross.reference）を入れる。位置を問う問題の本文は `— [1] —` の形。
- 解説は3つに分ける：`explanation_ja`（正解の理由。根拠の英文を短く引用）、`option_notes_ja`（選択肢ごとのコメント。options と同じ順の配列。表示順が変わるので (A) などの記号は使わず中身で書く）、`point_ja`（TOEIC のポイント。ほかの問題にも使える知識を1〜2文）。和訳（`translation_ja`、`translation_options_ja`）もつける。
- ID は `p{Part}-{4桁}`、セットは `p{Part}-s{3桁}`（試作の Part 1 の3セットだけ `p1-s0001` の4桁）。既存の ID は変えない（学習記録が ID に紐づくため）。不要になった問題は削除せず `status: "retired"`。
- `status` は draft → reviewed / flagged（レビュー結果から build_data が自動で設定）。各レビューは問題の版（`content_hash`、`scripts/review_hash.py`）を記録し、今の版へのレビューだけが状態に効く。

## 単語を作るときのルール
- 意味と例文は**オリジナル**。市販の単語帳の訳語・例文を写さない。見出し語のリストとして TSL（TOEIC Service List）を使う場合は CC BY-SA 4.0 の出典表示をアプリに入れる。
- 同じ品詞で同じ意味（例：estimate と quote の「見積もり」）の語を作らない。英→日の4択で両方が正解に見えるため。どうしても要るときは `distractors` を手で決める。
- `cloze` は例文の中にそのまま出てくる語形。ヒント（最初の1文字と字数）と和訳で答えが1つに決まる例文にする。
- 大量に作るときは音声を後回しにし、100〜200語ずつ「作成 → validate → 相互レビュー」を回してから音声を作る。
- 単語の学習記録は問題とは別（`vocab_progress` / `vocab_attempts`、単語ID×形式ごと）。形を変えるときは `supabase/schema.sql` も直す。

## 音声（Google Cloud Text-to-Speech）
- `scripts/gen_audio.py` は環境変数 `GOOGLE_TTS_API_KEY`（なければ `GOOGLE_API_KEY`）を使う。Cloud Text-to-Speech 用の `AIza` で始まるキーが必要（Gemini API のキーは使えない）。**キーを表示・ログ出力・ファイル保存・コミットしない**。
- 同じ文・同じ声は作り直さない（manifest の hash で判定）。Neural2 → WaveNet → Standard の順に声を選ぶ。
- 音声のキーは `js/audio.js` と共通の規則（`<item>:opt:<id>`, `<item>:stem`, `<set>:seg:<n>`, `<item>:q`, `label:A:female`）。変えるときは両方を直す。
- Part 3・4 の設問（`<item>:q`）はナレーターが読む（男性の声の一覧の最後。`gen_audio.py` と `js/audio.js` の `NARRATOR`）。アプリでは会話の後に1問ずつ読み、解答時間（8秒・図表12秒、再生速度で縮まない）を空ける。設定で「間を短く」「読まない」も選べる。
- Part 1・2 の話者の性別は `build_data.py` が `voices` に設定する。

## Part 1 の写真
- 試作の3枚は Gamma の画像生成。これからは、先生が Orca 経由で GPT と Gemini（nano banana）の両方に `images/part1/PROMPTS.md` の指示文を渡して作る。白黒・16:9・文字なし。
- 先生が `images/part1/incoming/<item id>-gpt.png`・`<item id>-gemini.png` を push → Claude が両方を見比べて良い方を選ぶ（文字なし・手や顔が自然・動作がはっきり・人のいない写真に人がいない）→ `python3 scripts/prep_photo.py p1-0004=gemini …` で 1600px 幅の WebP（`images/part1/<item id>.webp`）にする → **写真を見てから**選択肢を書く（プロンプトどおりに描かれないことが多いため）。

## 次にやること（TODO）
1. ~~問題データの置き場所を変える~~ → 済み（`data/src/part{N}/*.json` を読む形。試作49問は `pilot-v0.json` に移した。出力は移行前と同一）
2. `data/blueprint.json` に沿って Part ごとに生成（例：Part 5 を30問ずつ）。生成のたびに validate とレビュー用の書き出し。
3. 語彙レベルの判定：NGSL / TSL（CC BY-SA 4.0、出典表示が必要）を取り込み、各問題の語彙をプロファイルする。TSL は単語練習の見出し語のリストにも使う（配布元のサイトをネットワークで許可する必要がある）。
4. ~~Part 3・4 の設問の読み上げ~~ → 済み（`<item>:q`。解答時間つき）
5. 段階2：JLPT アプリの構成に合わせて Supabase へ移行（`supabase/schema.sql`）。
8. 厚い解説（`option_notes_ja`・`point_ja`）：既存の184問すべてに追加済み。解説の確認のしくみ（`--explain`）も済み。次は実際に184問の解説を確認してもらう（Part 1・2／3・4／5・6／7 くらいに分けて）。※問題を作ったときの生成スクリプトを流し直すと解説が消えるので、今後の修正は `data/src` の JSON を直接直す。
6. 単語の音声（`<単語ID>:word`・`<単語ID>:ex`）：レビューを通った語から `gen_audio.py` に足す。今はブラウザの読み上げで代用。
7. ~~Part 1〜7 の学習のさせ方~~ → 「今日の学習」（1日1 Part、5→2→6→3→7→4→5→1 の順で読解とリスニングを交互、約10問、今日の単語→問題）。記録は Store の daily。

## 確認のしかた
- `python3 scripts/validate.py` がエラー0件であること。
- ブラウザで index.html を開き、各 Part を1問ずつ解いて、表示・採点・解説・音声を確認する。
- 学習記録の形（`user_progress` / `attempts`、単語は `vocab_progress` / `vocab_attempts`）を変えるときは `supabase/schema.sql` も合わせて直す。
