# TOEIC L&R 練習アプリ（試作）

AIで作ったTOEIC L&R形式のオリジナル問題を、シャッフル・復習スケジュール・音声つきで練習するWebアプリの試作です。
今はサーバーなしの静的サイト（段階1）ですが、ログイン付きアプリ（段階2：Next.js＋Supabase）にそのまま移せるよう、データと学習記録の形をそろえてあります。

> 問題はすべて教材用に新しく作ったもので、TOEIC公式問題や市販教材の英文は使っていません。スコアの予測にはなりません。TOEICはETSの登録商標で、本教材はETS・IIBCとは関係ありません。

## 開き方

- `index.html` をブラウザで開くだけで動きます（ファイルを直接開いても、GitHub Pages に置いても動作）。
- 学習記録はブラウザ（localStorage）に保存されます。「成績」画面から書き出し・読み込みができます。

## できること

- **3つの出題方法**：練習（まだ解いていない問題から）／復習（今日が期日の問題）／ミニ模試（Part 1〜7を本番の順に）
- **シャッフル**：出題順と選択肢の並びを毎回入れ替え（図表・位置の選択肢など順番に意味がある問題は固定）
- **復習スケジュール**：SM-2方式。正解すると1日後→3日後→…と間隔が延び、間違えると10分後から出し直し
- **音声**：`audio/` に生成済みの音声があればそれを再生し、なければブラウザの読み上げで代用。米国・英国・オーストラリア・ランダムを選択（カナダは米国英語に近く、Google の音声もないので外した）
- **Part 1・2** は選択肢の英文を採点まで伏せる。採点後に解説・和訳・スクリプトを表示
- キーボード：1〜4で選択、Enterで採点・次へ
- **単語**：英→日（4択）・日→英（最初の1文字と字数のヒントでつづりを書く）・例文の穴埋め・単語の復習。Part の練習の前に、これから解く問題に出てくる語を「今日の単語」として先に確認できる（設定で切れる）

## フォルダ構成

```
index.html, css/, js/          アプリ本体（js/store.js だけ差し替えれば保存先を Supabase にできる）
data/src/part{N}/*.json        問題の元データ（生成バッチごとに1ファイル。書き方は data/src/README.md）
data/items.json, sets.json     問題データ（1件＝Supabase の1行。build_data.py が data/src から作る）
data/bank.js                   上の2つをまとめたもの（アプリはこれを読む）
data/vocab/src/*.json          単語の元データ（書き方は data/vocab/README.md）。build で data/vocab.json・vocab.js を作る
data/blueprint.json            大量生成の設計表（Part × 出題タイプ × 場面）
data/reviews.json              相互レビューの結果（import_review.py が作る）
images/part1/                  Part 1 の写真
audio/                         生成した音声と manifest
scripts/                       生成・検証・レビュー・音声のスクリプト
supabase/schema.sql            段階2のテーブル案（行単位のアクセス制御つき）
```

## 問題を増やすときの流れ

1. **生成**：`data/blueprint.json` の升目（Part × 出題タイプ × 場面）を指定してAIに問題を作らせ、`data/src/part{N}/<バッチ名>.json` として置く（形は `data/src/README.md`）
2. **データ作成**：`python3 scripts/build_data.py`
3. **機械チェック**：`python3 scripts/validate.py`（形式の誤り、正解が選択肢にない、似すぎた問題、正解だけが長い選択肢などを検出）
4. **相互レビュー**：`python3 scripts/export_review.py` で正解を伏せた問題集（`review/packet.md`）と指示文（`review/PROMPT.md`）を作り、Orca などで別のAIに解かせる
5. **照合**：返ってきたJSONを `python3 scripts/import_review.py <ファイル> --reviewer orca` で取り込み、もう一度 `build_data.py` を実行。一致すれば「レビュー済み」、食い違いや指摘があれば「要確認」になる
6. **音声**：下記

## 音声の作り方（Google Cloud Text-to-Speech）

Mac のターミナルで、このフォルダに移動してから実行します。API キーは環境変数 `GOOGLE_TTS_API_KEY`（なければ `GOOGLE_API_KEY`）から読みます（どこにも書き出しません）。Cloud Text-to-Speech 用の `AIza` で始まるキーが必要で、Gemini API のキーでは動きません。追加のライブラリは不要です。

```sh
python3 scripts/gen_audio.py --dry-run     # 作る件数と文字数の確認だけ（APIは呼ばない）
python3 scripts/gen_audio.py               # 米国・英国・オーストラリアの音声を作る
```

- 同じ文・同じ声の音声は作り直さないので、問題を追加したら同じコマンドを実行するだけです。
- 声は Neural2 → WaveNet → Standard の順に、使えるものを自動で選びます（`--tier` で指定も可）。
- 試作の49問では、3地域で約9,500文字です（Neural2 の無料枠は毎月100万文字）。
- API キーに「Cloud Text-to-Speech API」の利用が許可されている必要があります。

## Part 1 の写真

試作の3枚は Gamma の画像生成で作りました。1枚あたり70クレジットを使い、残りは150クレジットなので、数を増やすときは Google Cloud の画像生成（Imagen）など別の手段に切り替えます。写真と選択肢が食い違っていないかは、人の目で確認してください。

## 段階2（ログイン付きアプリ）への移行

- `supabase/schema.sql` のテーブルを作り、`data/items.json`・`sets.json` をそのまま投入する
- `js/store.js` の中身を Supabase の読み書きに差し替える（関数の形はそのまま）
- 学生が段階1で貯めた記録は「成績」→「記録を書き出す」のJSONから `user_progress`・`attempts` に移せる
- 音声と写真は Supabase Storage に置き、`audio/manifest.json` のパスを差し替える

## 試作の範囲と注意

- 問題は49問（Part 1:3 / 2:8 / 3:6 / 4:6 / 5:12 / 6:4 / 7:10）。すべて「未レビュー」
- 難易度は本番に合わせて調整していません。語彙レベルの判定（NGSL/TSL）は、リストを取り込んだあとに追加予定
- ライセンス：アプリのコードは自由に改変可。問題文はこのリポジトリの所有者に帰属
