# Part 1 写真の生成（Orca 経由で GPT と Gemini に作らせる）

## 流れ

1. 下の「Orca に貼る指示文」（いちばん新しい弾）を **GPT（画像生成）と Gemini（nano banana）の両方**に送る。同じ指示文で6枚ずつ作らせる
2. できた画像を、**問題 ID とモデル名をファイル名にして** `images/part1/incoming/` に置き、コミット・push する
   - 例：`p1-0010-gpt.png`、`p1-0010-gemini.png`（形式は png / jpg / webp どれでもよい）
   - 片方しかうまくできなかった写真は、その1枚だけでよい
3. Claude が両方を見比べて良い方を選び（理由も伝える）、1600px 幅の WebP にして、写真を見ながら選択肢を書く
   - 選ぶ基準：文字が入っていない／手や顔が自然／主な動作・状態がはっきり見える／人のいない写真に人が写っていない
   - 選ばれなかった方を使いたいときは、そう言えば差し替える

## 第2弾 p1-0010〜p1-0015：Orca に貼る指示文（ここから下を、そのまま全部コピー）

```
Please generate 6 photographs, one at a time, for an English listening test (TOEIC Part 1 style: "Look at the picture and choose the best description").
Label each image with its ID (p1-0010 to p1-0015) so I can tell them apart.

Requirements for ALL 6 images:
- Realistic black-and-white documentary-style photograph, landscape 16:9.
- The main action or state must be clear and easy to describe in one sentence.
- Ordinary people at work or in public places, natural poses, natural lighting, sharp focus, eye-level camera.
- NO text, letters, numbers, signs, logos, labels, screens with writing, or brand names anywhere in the image.
- No famous people, no real company names, no copyrighted characters.
- Simple, uncluttered background.
- Hands and faces must look natural (correct number of fingers, no distortion).

p1-0010 (one person, office):
A woman is watering a row of potted plants on a windowsill in an office, holding a small watering can. She is shown from the side, upper body and the plants clearly visible. No other people.

p1-0011 (one person, workshop):
A man wearing safety glasses is measuring a long wooden board with a tape measure at a workbench in a carpentry workshop. Some hand tools are hanging on the wall behind him. No other people.

p1-0012 (two people, office lobby):
Two businesspeople, a man and a woman, are shaking hands in a bright office lobby. Both are smiling and facing each other. A sofa and a potted plant are in the background. No other people.

p1-0013 (group, outdoor cafe):
Four friends are sitting around a round table on an outdoor cafe terrace, eating lunch. There are plates, glasses, and an umbrella over the table. No waiter is in the image. Other tables nearby are empty.

p1-0014 (objects only, NO people):
An empty meeting room. Several chairs are neatly arranged around a long rectangular table. A closed laptop and a water pitcher with glasses are on the table. The window blinds are open. There are no people anywhere in the image.

p1-0015 (objects only, NO people):
An outdoor market stall with apples, oranges, and pears displayed in wooden crates and baskets on a table under a canvas awning. No price tags, signs, or writing. There are no people anywhere in the image.
```

## 第1弾 p1-0004〜p1-0009（済み）

```
Please generate 6 photographs, one at a time, for an English listening test (TOEIC Part 1 style: "Look at the picture and choose the best description").
Label each image with its ID (p1-0004 to p1-0009) so I can tell them apart.

Requirements for ALL 6 images:
- Realistic black-and-white documentary-style photograph, landscape 16:9.
- The main action or state must be clear and easy to describe in one sentence.
- Ordinary people at work or in public places, natural poses, natural lighting, sharp focus, eye-level camera.
- NO text, letters, numbers, signs, logos, labels, screens with writing, or brand names anywhere in the image.
- No famous people, no real company names, no copyrighted characters.
- Simple, uncluttered background.
- Hands and faces must look natural (correct number of fingers, no distortion).

p1-0004 (one person, office):
A woman in business-casual clothes is standing in a small office and placing a binder on a high shelf, reaching up with one hand. She is shown from the side, full body visible. There is a desk with a computer monitor next to her (the screen is dark or blank). No other people.

p1-0005 (one person, restaurant):
A male server wearing an apron is pouring water from a pitcher into a glass at a restaurant table set for two. No customers are seated at the table. Several other empty tables are visible in the background.

p1-0006 (group, site office):
Three coworkers wearing hard hats and safety vests are standing around a table and looking at a large paper floor plan spread out on it. One of them is pointing at the plan. They are indoors in a simple site office with a window. The plan has only lines, no writing.

p1-0007 (group, airport):
Several travelers with suitcases are standing in a line at an airport check-in counter. One airline employee behind the counter is checking a passenger's passport. The line is orderly and the counter area is bright. No signs or screens with writing.

p1-0008 (objects only, NO people):
An empty warehouse aisle with cardboard boxes stacked neatly on wooden pallets along both sides. A forklift is parked at the end of the aisle. The boxes have no labels or writing. There are no people anywhere in the image.

p1-0009 (objects only, NO people):
A row of bicycles is parked in a metal bike rack in front of a brick office building. A few leaves are lying on the sidewalk. A bench stands next to the bike rack. There are no people anywhere in the image.
```

## 1枚ずつ作り直すとき

うまくいかなかった写真だけ作り直すときは、上の「Requirements for ALL 6 images」の部分と、その写真の段落（例：`p1-0007 ...`）だけを貼って、「Generate only this image」と書き添える。
