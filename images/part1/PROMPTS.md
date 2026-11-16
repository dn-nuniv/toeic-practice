# Part 1 写真の生成プロンプト

GPT（ChatGPT の画像生成）か Gemini（nano banana）に、下の「共通の条件」と各写真のプロンプトを**続けて1つにして**貼り付けてください。

## 手順

1. 共通の条件と各写真のプロンプトを貼って生成する。1枚につき2〜3回生成して、いちばん良いものを選ぶ
2. 下の「確認すること」を見て、だめなら作り直す
3. 画像を `images/part1/incoming/p1-0004.png` のように、**ファイル名を問題 ID にして**置き、コミット・push する（形式は png / jpg / webp どれでもよい）
4. こちら（Claude）で 1600px 幅の WebP に変換し、写真を実際に見て選択肢を書く
   （プロンプトどおりに描かれないことが多いので、選択肢は写真を見てから作る）

## 共通の条件（毎回、先頭に貼る）

```
Create a realistic black-and-white documentary-style photograph, landscape 16:9.
It is for an English listening test, so the scene must be clear and easy to describe in one sentence.
- Ordinary people at work or in public places, natural poses, natural lighting, sharp focus.
- No text, letters, numbers, signs, logos, or brand names anywhere in the image.
- No famous people, no real company names, no copyrighted characters.
- Avoid unusual or artistic camera angles. Eye-level view. Avoid clutter in the background.
- Hands and faces must look natural (correct number of fingers, no distortion).
```

## 各写真のプロンプト

### p1-0004 — 人物1人の動作（オフィス）
```
A woman in business-casual clothes is standing in a small office and placing a binder on a high shelf, reaching up with one hand. She is shown from the side, full body visible. There is a desk with a computer monitor next to her. No other people.
```

### p1-0005 — 人物1人の動作（レストラン）
```
A male server wearing an apron is pouring water from a pitcher into a glass at a restaurant table set for two. No customers are seated at the table. Several other empty tables are visible in the background.
```

### p1-0006 — 複数の人物の動作（建設現場の事務所）
```
Three coworkers wearing hard hats and safety vests are standing around a table and looking at a large paper floor plan spread out on it. One of them is pointing at the plan. They are indoors in a simple site office with a window.
```

### p1-0007 — 複数の人物の動作（空港）
```
Several travelers with suitcases are standing in a line at an airport check-in counter. One airline employee behind the counter is checking a passenger's passport. The line is orderly and the counter area is bright.
```

### p1-0008 — 物の状態・人のいない写真（倉庫）
```
An empty warehouse aisle with cardboard boxes stacked neatly on wooden pallets along both sides. A forklift is parked at the end of the aisle. No people anywhere in the image.
```

### p1-0009 — 物の状態・人のいない写真（屋外）
```
A row of bicycles is parked in a metal bike rack in front of a brick office building. A few leaves are lying on the sidewalk. A bench stands next to the bike rack. No people anywhere in the image.
```

## 確認すること（生成した写真）

- **文字が入っていない**か（看板・ラベル・画面の文字。崩れた文字が出やすい）
- 手・指・顔が自然か
- 人のいない写真（p1-0008・p1-0009）に、遠くでも人が写っていないか
- プロンプトの主な動作・状態（棚に置く、水を注ぐ、図面を指さす、並ぶ、積んである、止めてある）がはっきり見えるか
- 細部がプロンプトと違っていてもかまわない（選択肢は写真に合わせて書く）
