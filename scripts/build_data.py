# -*- coding: utf-8 -*-
"""試作問題バンク（v0）を data/items.json と data/sets.json に書き出す。
問題文はすべて教材用のオリジナル。公式問題・市販教材の英文は使っていない。
行の形は supabase/schema.sql の items / sets テーブルと一致させている。"""
import json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = "claude-opus-5.5 / 2026-11-16 / pilot-v0"
items, sets = [], []

def opts(*texts):
    return [{"id": chr(97 + i), "text": t} for i, t in enumerate(texts)]

def item(id, part, prompt, options, answer, exp, tr, type_, scene, set_id=None, shuffle=True, level="B1", translation_options=None):
    items.append(dict(id=id, part=part, set_id=set_id, type=type_, scene=scene, prompt=prompt,
                      options=options, answer=answer, shuffle=shuffle, explanation_ja=exp,
                      translation_ja=tr, translation_options_ja=translation_options,
                      level=level, status="draft", source=SRC, review=[]))

def aset(id, part, kind, scene, question_ids, translation_ja, speakers=None, segments=None,
         passages=None, graphic=None, image=None):
    sets.append(dict(id=id, part=part, kind=kind, scene=scene, speakers=speakers or [],
                     segments=segments or [], passages=passages or [], graphic=graphic,
                     image=image, question_ids=question_ids, translation_ja=translation_ja,
                     status="draft", source=SRC))

# ============================================================ Part 1（写真描写）
# 写真は sets.image に置き、設問は1問ずつ。選択肢は音声のみ（採点まで伏せる）
p1 = [
 ("p1-0001", "images/part1/p1-0001.webp", "office",
  opts("She's arranging chairs in a row.", "She's watering some plants.", "She's opening a window.", "She's putting on a jacket."),
  "b", "女性がじょうろで窓辺の植物に水をやっている。窓は閉まっているので (C) は誤り。",
  ["彼女は椅子を一列に並べている。", "彼女は植物に水をやっている。", "彼女は窓を開けている。", "彼女は上着を着ているところだ。"]),
 ("p1-0002", "images/part1/p1-0002.webp", "warehouse",
  opts("A man is moving some boxes with a hand truck.", "A man is climbing a ladder.", "Some shelves are being painted.", "A truck is parked in a garage."),
  "a", "男性が台車（hand truck）で箱を運んでいる。はしご・ペンキ塗り・トラックは写真にない。写っていない物を含む選択肢は消去できる。",
  ["男性が台車で箱を運んでいる。", "男性がはしごを登っている。", "棚にペンキが塗られているところだ。", "トラックが車庫に止めてある。"]),
 ("p1-0003", "images/part1/p1-0003.webp", "meeting",
  opts("People are seated around a table.", "A presentation is being given.", "Some chairs have been arranged around a table.", "A screen is being installed."),
  "c", "人が写っていない写真。being（進行中の動作）を含む選択肢は、動作をしている人がいないので誤り。have been arranged（並べられた状態）が正解。",
  ["人々がテーブルを囲んで座っている。", "発表が行われているところだ。", "椅子がテーブルの周りに並べられている。", "スクリーンが取り付けられているところだ。"]),
]
for iid, img, scene, o, ans, exp, tro in p1:
    sid = iid.replace("p1-", "p1-s")
    item(iid, 1, "写真に最も合う描写を選んでください。", o, ans, exp, "", "photo.description", scene,
         set_id=sid, translation_options=tro, level="A2")
    aset(sid, 1, "photo", scene, [iid], "", image=img)

# ============================================================ Part 2（応答問題）
p2 = [
 ("When is the budget meeting?", ("In conference room B.", "Tomorrow at ten.", "About the new budget."), "b",
  "When（いつ）に時を答えている (B) が正解。(C) は質問と同じ budget を使ったひっかけ。",
  "予算会議はいつですか。", ["会議室Bです。", "明日の10時です。", "新しい予算についてです。"], "wh.when", "meeting"),
 ("Who's in charge of the new hiring process?", ("Ms. Park in human resources.", "Higher than last year.", "Yes, it's in process."), "a",
  "Who（誰）に人物で答えている (A) が正解。疑問詞で始まる質問に Yes/No で答える (C) は誤り。",
  "新しい採用手続きの担当は誰ですか。", ["人事部のパクさんです。", "去年より高いです。", "はい、手続き中です。"], "wh.who", "hr"),
 ("Why was the delivery delayed?", ("Because of the snowstorm.", "Two boxes, please.", "It was delivered to the lobby."), "a",
  "Why（なぜ）に理由で答えている (A) が正解。(C) は delivery と似た delivered を使ったひっかけ。",
  "配達はなぜ遅れたのですか。", ["吹雪のせいです。", "2箱お願いします。", "ロビーに届けられました。"], "wh.why", "logistics"),
 ("Would you like me to print the agenda?", ("Thanks, that would be helpful.", "It's on the second floor.", "The printer is new."), "a",
  "Would you like me to ～?（～しましょうか）という申し出に、お礼を言って受けている (A) が正解。",
  "議題を印刷しましょうか。", ["ありがとう、助かります。", "2階にあります。", "そのプリンターは新しいです。"], "offer", "office"),
 ("Haven't you finished the sales report yet?", ("I'm still waiting for the final figures.", "The sale ends on Sunday.", "Yes, he reported it."), "a",
  "まだ終わっていない理由を述べる (A) が自然な応答。(B) は sales に似た sale、(C) は report を使ったひっかけで、主語も he でずれている。",
  "売上報告書はまだ終わっていないのですか。", ["最終的な数字をまだ待っているところです。", "セールは日曜日に終わります。", "はい、彼が報告しました。"], "negative.question", "sales"),
 ("Should we take a taxi or the train to the airport?", ("The train is faster at this hour.", "Yes, I trained them.", "At gate twelve."), "a",
  "A or B の選択疑問文には Yes/No で答えない。理由を添えて電車を選んでいる (A) が正解。",
  "空港へはタクシーと電車のどちらで行きましょうか。", ["この時間は電車のほうが速いです。", "はい、私が彼らを訓練しました。", "12番ゲートです。"], "choice", "travel"),
 ("Where can I find the updated price list?", ("It's posted on the company intranet.", "The prices went up.", "I found it interesting."), "a",
  "Where（どこ）に場所で答えている (A) が正解。(C) は find を使ったひっかけ。",
  "最新の価格表はどこにありますか。", ["社内のイントラネットに掲載されています。", "値段が上がりました。", "おもしろいと思いました。"], "wh.where", "sales"),
 ("The new software is much easier to use, isn't it?", ("Yes, it saves me a lot of time.", "Use the side entrance.", "It's on sale now."), "a",
  "付加疑問文（～ですよね）に同意して具体的に答えている (A) が正解。",
  "新しいソフトはずっと使いやすいですよね。", ["ええ、ずいぶん時間の節約になります。", "横の入口を使ってください。", "今セール中です。"], "tag.question", "it"),
]
for i, (q, o, ans, exp, tr, tro, typ, scene) in enumerate(p2, 1):
    item(f"p2-{i:04d}", 2, q, opts(*o), ans, exp, tr, typ, scene, translation_options=tro, level="A2")

# ============================================================ Part 3（会話問題）
aset("p3-s001", 3, "conversation", "meeting", ["p3-0001", "p3-0002", "p3-0003"],
 "女性：ダニエル、ハーロウ・フーズのお客さまから電話があったわ。飛行機が欠航して、火曜日に来られなくなったそうよ。\n"
 "男性：それは残念だ。大会議室を予約して、12人分の昼食も注文してあるのに。\n"
 "女性：そうよね。代わりに木曜日の午後に発表を移せないかと聞かれたの。\n"
 "男性：木曜日？その日はシカゴの見本市に行くことになっているんだ。\n"
 "女性：でも、マリアはあなたと一緒に提案書を作ったでしょう。隅から隅まで分かっているわ。\n"
 "男性：確かに。今朝のうちに彼女に頼んでみるよ。それから、仕出し業者に電話して昼食の注文を変更しておく。",
 speakers=[{"id": "W", "gender": "female"}, {"id": "M", "gender": "male", "name": "Daniel"}],
 segments=[
  {"speaker": "W", "text": "Hi, Daniel. The clients from Harlow Foods just called. Their flight was canceled, so they can't come in on Tuesday."},
  {"speaker": "M", "text": "That's a shame. We've already reserved the large meeting room and ordered lunch for twelve people."},
  {"speaker": "W", "text": "I know. They asked if we could move the presentation to Thursday afternoon instead."},
  {"speaker": "M", "text": "Thursday? I'm supposed to be at the trade fair in Chicago that day."},
  {"speaker": "W", "text": "Well, Maria worked on the proposal with you. She knows it inside out."},
  {"speaker": "M", "text": "True. I'll ask her this morning, and I'll call the caterer to change the lunch order."}])
item("p3-0001", 3, "Why can't the clients come on Tuesday?",
 opts("Their flight was canceled.", "They are attending a trade fair.", "The meeting room is not available.", "They want to change the proposal."), "a",
 "女性の最初の発言に Their flight was canceled とある。見本市に行くのは男性なので (B) は誤り。",
 "顧客はなぜ火曜日に来られないのか。", "detail", "meeting", set_id="p3-s001",
 translation_options=["飛行機が欠航した。", "見本市に参加する。", "会議室が使えない。", "提案内容を変えたい。"])
item("p3-0002", 3, "What does the woman imply when she says, \"She knows it inside out\"?",
 opts("Maria can give the presentation.", "Maria should revise the proposal.", "Maria has visited Harlow Foods.", "Maria will order lunch."), "a",
 "男性が木曜日に不在だと言ったのを受けて、提案書をよく知るマリアなら代わりに発表できる、とほのめかしている。発言の意図を問う問題は前後の流れで判断する。",
 "女性が「隅から隅まで分かっている」と言うとき、何を示唆しているか。", "intention", "meeting", set_id="p3-s001",
 translation_options=["マリアが発表できる。", "マリアは提案書を直すべきだ。", "マリアはハーロウ・フーズを訪れたことがある。", "マリアが昼食を注文する。"])
item("p3-0003", 3, "What does the man say he will do?",
 opts("Book a flight to Chicago", "Contact a catering company", "Reserve a different room", "Call the clients"), "b",
 "最後に I'll call the caterer と言っている。caterer（仕出し業者）が catering company に言い換えられている。",
 "男性は何をすると言っているか。", "next.action", "meeting", set_id="p3-s001",
 translation_options=["シカゴ行きの飛行機を予約する", "仕出し業者に連絡する", "別の部屋を予約する", "顧客に電話する"])

aset("p3-s002", 3, "conversation", "customer.service", ["p3-0004", "p3-0005", "p3-0006"],
 "男性：もしもし、先週注文したプリンター用紙の件でお電話しました。まだ届かなくて、もうすぐなくなりそうなんです。\n"
 "女性：申し訳ございません。通常配送で発送されていますので、金曜日までには届くはずです。\n"
 "男性：水曜日に大事な郵送物があるんです。それまでに用紙を手に入れる方法はありませんか。\n"
 "女性：本日、もう1箱お送りできます。お客さまは当社の地域外ですので、最も早いのは翌日配送になります。配送料は無料にいたします。\n"
 "男性：それは助かります。ありがとうございます。",
 speakers=[{"id": "M", "gender": "male"}, {"id": "W", "gender": "female"}],
 segments=[
  {"speaker": "M", "text": "Hello, I'm calling about the order of printer paper we placed last week. It hasn't arrived yet, and we're running out."},
  {"speaker": "W", "text": "I'm sorry about that. I see that it was sent by standard delivery, so it should arrive by Friday."},
  {"speaker": "M", "text": "We have an important mailing on Wednesday. Is there any way to get more paper before then?"},
  {"speaker": "W", "text": "I can send a second box today. Since you're outside our local area, the fastest option would be next-day delivery, and I'll waive the fee."},
  {"speaker": "M", "text": "That would be great. Thank you."}],
 graphic={"title": "Delivery Options", "columns": ["Option", "Time", "Fee"],
          "rows": [["Standard", "5–7 days", "$8"], ["Express", "2–3 days", "$15"], ["Next Day", "1 day", "$25"], ["Same Day (local only)", "Same day", "$40"]]})
item("p3-0004", 3, "What problem does the man mention?",
 opts("An order has not arrived.", "A printer is broken.", "A bill is incorrect.", "A mailing was lost."), "a",
 "男性の最初の発言 It hasn't arrived yet から、注文品が届いていないことが分かる。",
 "男性はどんな問題を述べているか。", "problem", "customer.service", set_id="p3-s002",
 translation_options=["注文品が届いていない。", "プリンターが壊れている。", "請求書が間違っている。", "郵送物がなくなった。"])
item("p3-0005", 3, "Look at the graphic. How much would the man normally pay for the second delivery?",
 opts("$8", "$15", "$25", "$40"), "c",
 "女性は翌日配送（next-day delivery）で送ると言っている。表で Next Day の料金を見ると $25。当日配送は地域内（local only）のみなので対象外。",
 "図を見てください。2回目の配送に男性は通常いくら払うことになるか。", "graphic", "customer.service", set_id="p3-s002", shuffle=False)
item("p3-0006", 3, "What does the woman offer to do?",
 opts("Send a free sample", "Waive a fee", "Cancel the first order", "Refund the original order"), "b",
 "I'll waive the fee（料金を免除します）と言っている。",
 "女性は何をすると申し出ているか。", "offer", "customer.service", set_id="p3-s002",
 translation_options=["無料サンプルを送る", "料金を免除する", "最初の注文を取り消す", "元の注文代金を返金する"])

# ============================================================ Part 4（説明文問題）
aset("p4-s001", 4, "announcement", "facilities", ["p4-0001", "p4-0002", "p4-0003"],
 "従業員の皆さまにお知らせします。東側エレベーターの保守作業が、今週土曜日の午前8時に始まり、月曜日の午後まで続く予定です。"
 "この間は、西側のエレベーターか階段をご利用ください。重い機材を運ぶ必要がある方は、業務用エレベーターを予約できるよう、事前に施設管理室へご連絡ください。"
 "ご不便をおかけしますが、ご理解とご協力をお願いいたします。",
 speakers=[{"id": "N", "gender": "female"}],
 segments=[
  {"speaker": "N", "text": "Attention, all employees. This is a reminder that maintenance work on the east elevators will begin this Saturday at 8 A.M. and is expected to continue through Monday afternoon."},
  {"speaker": "N", "text": "During this time, please use the west elevators or the stairs. Employees who need to move heavy equipment should contact the facilities office in advance so that a service elevator can be reserved."},
  {"speaker": "N", "text": "We apologize for any inconvenience and thank you for your patience."}])
item("p4-0001", 4, "What is the announcement mainly about?",
 opts("An office relocation", "Elevator maintenance", "A fire drill", "New security procedures"), "b",
 "冒頭の maintenance work on the east elevators から、エレベーターの保守作業についての案内と分かる。",
 "お知らせは主に何についてか。", "main.topic", "facilities", set_id="p4-s001",
 translation_options=["事務所の移転", "エレベーターの保守", "避難訓練", "新しい保安手順"])
item("p4-0002", 4, "When will the work end?",
 opts("On Saturday morning", "On Saturday evening", "On Monday afternoon", "On Tuesday morning"), "c",
 "continue through Monday afternoon（月曜日の午後まで続く）とある。土曜日の午前8時は開始時刻。",
 "作業はいつ終わるか。", "detail", "facilities", set_id="p4-s001", shuffle=False,
 translation_options=["土曜日の朝", "土曜日の夕方", "月曜日の午後", "火曜日の朝"])
item("p4-0003", 4, "Why should some employees contact the facilities office?",
 opts("To report a problem", "To reserve a service elevator", "To request a parking space", "To receive a new badge"), "b",
 "重い機材を運ぶ人は so that a service elevator can be reserved（業務用エレベーターを予約するために）連絡するよう求められている。",
 "一部の従業員はなぜ施設管理室に連絡すべきなのか。", "reason", "facilities", set_id="p4-s001",
 translation_options=["問題を報告するため", "業務用エレベーターを予約するため", "駐車スペースを申し込むため", "新しい社員証を受け取るため"])

aset("p4-s002", 4, "voicemail", "printing", ["p4-0004", "p4-0005", "p4-0006"],
 "もしもし、ブライトライン印刷のカレン・リーです。御社の創立記念行事用にご注文いただいたパンフレットの件でお電話しました。"
 "デザインの校正刷りはできあがったのですが、表紙の写真について確認があります。お送りいただいた画像ファイルが少し小さいため、印刷するとぼやけて見えるかもしれません。"
 "解像度の高いものがあれば、明日の正午までにメールでお送りいただけますか。そうすれば、予定どおり来週の水曜日にパンフレットをお届けできます。よろしくお願いします。",
 speakers=[{"id": "N", "gender": "female", "name": "Karen Lee"}],
 segments=[
  {"speaker": "N", "text": "Hi, this is Karen Lee from Brightline Printing. I'm calling about the brochures you ordered for your company's anniversary event."},
  {"speaker": "N", "text": "We've finished the design proofs, but there's a question about the cover photo. The image file you sent is a little too small, so it may look blurry when it's printed."},
  {"speaker": "N", "text": "If you have a higher-resolution version, could you e-mail it to me by noon tomorrow? That way, we can still deliver the brochures on schedule next Wednesday. Thanks."}])
item("p4-0004", 4, "Who most likely is the speaker?",
 opts("An event planner", "A printing company employee", "A photographer", "A delivery driver"), "b",
 "this is Karen Lee from Brightline Printing と名乗り、パンフレットの校正の話をしているので印刷会社の社員。",
 "話し手は誰だと考えられるか。", "speaker.identity", "printing", set_id="p4-s002",
 translation_options=["イベントの企画者", "印刷会社の社員", "写真家", "配達ドライバー"])
item("p4-0005", 4, "What problem does the speaker mention?",
 opts("An image file is too small.", "A delivery date has changed.", "A payment is overdue.", "Some text is misspelled."), "a",
 "The image file you sent is a little too small とある。納品日は予定どおりなので (B) は誤り。",
 "話し手はどんな問題を述べているか。", "problem", "printing", set_id="p4-s002",
 translation_options=["画像ファイルが小さすぎる。", "配達日が変わった。", "支払いが遅れている。", "文字につづりの誤りがある。"])
item("p4-0006", 4, "What does the speaker ask the listener to do by tomorrow?",
 opts("Approve a price", "Send a file", "Pick up some brochures", "Choose a new photographer"), "b",
 "could you e-mail it to me by noon tomorrow と、高解像度の画像を送るよう頼んでいる。",
 "話し手は聞き手に明日までに何をするよう頼んでいるか。", "request", "printing", set_id="p4-s002",
 translation_options=["価格を承認する", "ファイルを送る", "パンフレットを受け取りに来る", "新しい写真家を選ぶ"])

# ============================================================ Part 5（短文穴埋め）
p5 = [
 ("The quarterly report must be ------- to the finance department by Friday.", ("submit", "submitting", "submitted", "submission"), "c",
  "must be の後で「提出される」という受け身にするので過去分詞 submitted。", "四半期報告書は金曜日までに経理部に提出されなければならない。", "grammar.passive", "finance"),
 ("Ms. Tanaka has worked at Corvex Industries ------- 2019.", ("since", "for", "during", "until"), "a",
  "現在完了（has worked）と、起点を表す年（2019）を結ぶのは since。for の後には期間（five years など）が来る。", "タナカさんは2019年からコーベックス工業で働いている。", "grammar.preposition", "hr"),
 ("All visitors are required to sign in at the front desk ------- entering the building.", ("before", "although", "because", "unless"), "a",
  "動名詞 entering の前に置けるのは前置詞の before。although・because・unless は接続詞で、ここでは使えない。", "来訪者は全員、建物に入る前に受付で記帳しなければならない。", "grammar.preposition_vs_conjunction", "office"),
 ("The new marketing campaign was ------- successful than the company had expected.", ("much", "more", "most", "very"), "b",
  "than があるので比較級を作る more。much は比較級を強める語なので、much more successful の形なら使える。", "新しい販促キャンペーンは、会社が予想していた以上に成功した。", "grammar.comparative", "marketing"),
 ("Please let us know if you have ------- questions about the contract.", ("any", "every", "much", "each"), "a",
  "疑問・条件の文で複数形の名詞 questions を修飾できるのは any。every と each は単数名詞、much は数えられない名詞に付く。", "契約について何か質問があればお知らせください。", "grammar.quantifier", "legal"),
 ("The training session has been postponed ------- the instructor is ill.", ("because", "because of", "despite", "so that"), "a",
  "後ろに主語と動詞（the instructor is ill）が続くので接続詞の because。because of と despite の後には名詞が来る。", "講師が病気のため、研修は延期された。", "grammar.conjunction", "hr"),
 ("Employees who wish to take time off in August should submit ------- requests by June 30.", ("they", "them", "their", "themselves"), "c",
  "名詞 requests の前なので所有格 their。", "8月に休暇を取りたい従業員は、6月30日までに申請書を提出すること。", "grammar.pronoun", "hr"),
 ("The hotel offers a shuttle service to the airport, which is ------- to all guests free of charge.", ("available", "capable", "eligible", "responsible"), "a",
  "be available to ～ で「～が利用できる」。eligible は for を伴って「資格がある」の意味で、主語が人になる。", "そのホテルは空港への送迎バスを運行しており、宿泊客は全員無料で利用できる。", "vocab.adjective", "travel"),
 ("Mr. Ortiz ------- the shipment schedule when the client called.", ("reviews", "was reviewing", "has reviewed", "will review"), "b",
  "when the client called（過去のある時点）にしていた最中の動作なので過去進行形。", "顧客から電話があったとき、オルティスさんは出荷予定を確認していた。", "grammar.tense", "logistics"),
 ("The company decided to ------- its customer service hours to better serve international clients.", ("extend", "expire", "exceed", "explain"), "a",
  "「受付時間を延長する」の extend。expire（期限が切れる）は目的語をとらない。", "その会社は海外の顧客により良く対応するため、顧客サービスの受付時間を延長することにした。", "vocab.verb", "customer.service"),
 ("Neither the manager ------- her assistant was able to attend the conference.", ("or", "nor", "and", "but"), "b",
  "neither A nor B（AもBも～ない）の組み合わせ。either なら or を使う。", "部長もそのアシスタントも、会議に出席できなかった。", "grammar.correlative", "meeting"),
 ("Applications will be reviewed -------, and qualified candidates will be contacted within two weeks.", ("careful", "carefully", "carefulness", "more careful"), "b",
  "動詞 reviewed を修飾するので副詞 carefully。", "応募書類は慎重に審査され、条件を満たす候補者には2週間以内に連絡がある。", "grammar.part_of_speech", "hr"),
]
for i, (q, o, ans, exp, tr, typ, scene) in enumerate(p5, 1):
    item(f"p5-{i:04d}", 5, q, opts(*o), ans, exp, tr, typ, scene)

# ============================================================ Part 6（長文穴埋め）
aset("p6-s001", 6, "email", "office", ["p6-0001", "p6-0002", "p6-0003", "p6-0004"],
 "宛先：全従業員／差出人：ポール・グリーン（総務課長）／件名：給湯室の改装\n"
 "従業員の皆さま\n来週の月曜日から、2階の給湯室は改装のため閉鎖されます。工事は約2週間かかる見込みです。この間は3階の給湯室をご利用ください。\n"
 "なお、古い冷蔵庫は土曜日に撤去されます。マグカップや食品容器など私物は、金曜日の夕方までに冷蔵庫から出しておいてください。残されたものは処分されます。\n"
 "再開後の給湯室には、より大きな冷蔵庫、2台目の電子レンジ、座席の追加が予定されています。工事期間中のご理解に感謝いたします。",
 passages=[{"type": "email", "header": {"To": "All Staff", "From": "Paul Greene, Office Manager", "Subject": "Kitchen renovation", "Date": "May 2"},
            "text": "Dear staff,\n\nBeginning next Monday, the second-floor kitchen will be closed for renovation. The work is expected to [1] about two weeks. During this period, please use the kitchen on the third floor.\n\n[2] We ask that you take any personal items, such as mugs and food containers, out of the refrigerator by Friday evening. Anything left behind will be [3].\n\nWhen the kitchen reopens, it will have a larger refrigerator, a second microwave, and more seating. We appreciate your [4] while the work is being completed.\n\nPaul Greene"}])
item("p6-0001", 6, "[1]", opts("take", "make", "hold", "keep"), "a",
 "take ＋時間 で「（時間が）かかる」。The work is expected to take about two weeks.", "（空欄1）工事は約2週間かかる見込みだ。", "vocab.collocation", "office", set_id="p6-s001")
item("p6-0002", 6, "[2]",
 opts("Please note that the old refrigerator will be removed on Saturday.", "The new menu will be posted in the cafeteria.",
      "Thank you for attending the safety training last week.", "The third-floor kitchen will also be closed during this time."), "a",
 "直後に「私物を金曜日の夕方までに冷蔵庫から出して」と続くので、古い冷蔵庫が土曜日に撤去されるという文が自然。(D) は3階を使うよう求める前の段落と矛盾する。",
 "（空欄2）文挿入問題", "text.insertion", "office", set_id="p6-s001",
 translation_options=["なお、古い冷蔵庫は土曜日に撤去されます。", "新しいメニューは食堂に掲示されます。", "先週の安全研修へのご参加ありがとうございました。", "3階の給湯室もこの間閉鎖されます。"])
item("p6-0003", 6, "[3]", opts("discard", "discarded", "discarding", "discards"), "b",
 "will be の後で「処分される」という受け身にするので過去分詞 discarded。", "（空欄3）残されたものは処分される。", "grammar.passive", "office", set_id="p6-s001")
item("p6-0004", 6, "[4]", opts("patience", "patient", "patiently", "patients"), "a",
 "所有格 your の後には名詞が来る。「忍耐・辛抱」の patience。patients は「患者たち」で意味が合わない。", "（空欄4）ご辛抱（ご理解）に感謝します。", "grammar.part_of_speech", "office", set_id="p6-s001")

# ============================================================ Part 7（読解）
aset("p7-s001", 7, "single", "fitness", ["p7-0001", "p7-0002"],
 "グリーンウェイ・フィットネスセンター　夏の入会キャンペーン\n6月1日から30日までにご入会の方は、入会金（通常50ドル）が無料。12か月プランにお申し込みの新会員には、パーソナルトレーナーのセッションを2回無料でご提供します。"
 "施設には25メートルプール、サウナがあり、毎週30以上のグループレッスンを行っています。なお、プールは清掃のため7月10日から14日まで閉鎖します。ご入会は受付またはウェブサイトから。",
 passages=[{"type": "advertisement", "title": "Greenway Fitness Center — Summer Membership Offer",
            "text": "Join between June 1 and June 30 and pay no registration fee (normally $50). New members who sign up for a 12-month plan will also receive two free sessions with a personal trainer.\n\nOur facilities include a 25-meter pool, a sauna, and more than 30 group classes each week. Please note that the pool will be closed for cleaning from July 10 to July 14.\n\nTo join, visit our front desk or register online at www.greenwayfit.example."}])
item("p7-0001", 7, "What is being offered to people who join in June?",
 opts("A free month of membership", "No registration fee", "A discount on swimming lessons", "A free towel"), "b",
 "pay no registration fee（入会金なし）とある。トレーナーのセッション無料は12か月プランの人だけ。",
 "6月に入会する人には何が提供されるか。", "detail", "fitness", set_id="p7-s001",
 translation_options=["1か月分の会費無料", "入会金の免除", "水泳レッスンの割引", "無料のタオル"])
item("p7-0002", 7, "What is indicated about the pool?",
 opts("It was recently built.", "It is 50 meters long.", "It will be temporarily unavailable in July.", "It is open only to 12-month members."), "c",
 "the pool will be closed for cleaning from July 10 to July 14 とある。temporarily unavailable（一時的に使えない）への言い換え。",
 "プールについて何が示されているか。", "indicated", "fitness", set_id="p7-s001",
 translation_options=["最近造られた。", "長さが50メートルある。", "7月に一時的に使えなくなる。", "12か月会員しか使えない。"])

aset("p7-s002", 7, "single", "business.news", ["p7-0003", "p7-0004", "p7-0005"],
 "金沢（4月3日）――シアトルに本社を置くカフェチェーンのソルバーグ・コーヒーが、来月、日本で初めての店舗を開く。120席のカフェは、金沢駅近くに新しく完成したヒカリビルの1階に入る。\n"
 "同社の地域担当ディレクター、アンナ・ソルバーグ氏によると、金沢を選んだのは、海外からの訪問客が増えていることと、長い茶の文化があるためだという。カフェでは地元で焙煎した豆を使い、石川県の農場の食材を使った季節のメニューも提供する。\n"
 "同社は約40人のスタッフを採用する予定だ。［英語を話せる応募者は特に歓迎する。］営業時間は午前7時から午後9時まで。",
 passages=[{"type": "article", "title": "Local Business",
            "text": "KANAZAWA (April 3) — Solberg Coffee, a Seattle-based café chain, will open its first store in Japan next month. — [1] — The 120-seat café will be located on the ground floor of the newly completed Hikari Building near Kanazawa Station.\n\nAccording to the company's regional director, Anna Solberg, Kanazawa was chosen because of its growing number of international visitors and its long tradition of tea culture. — [2] — The café will serve locally roasted beans and will offer a seasonal menu featuring ingredients from farms in Ishikawa Prefecture.\n\nThe company plans to hire about 40 staff members. — [3] — Opening hours will be from 7 A.M. to 9 P.M. — [4] —"}])
item("p7-0003", 7, "What is the article mainly about?",
 opts("A new café opening", "The history of tea in Kanazawa", "The renovation of a train station", "A change in company leadership"), "a",
 "第1文で日本初の店舗を開くと述べ、全体がその出店の話。茶の文化は選んだ理由の一つにすぎない。",
 "記事は主に何についてか。", "main.topic", "business.news", set_id="p7-s002",
 translation_options=["新しいカフェの開店", "金沢の茶の歴史", "駅の改修", "経営陣の交代"])
item("p7-0004", 7, "According to the article, why was Kanazawa chosen?",
 opts("Its rent is lower than in other cities.", "It has a growing number of international visitors.", "The company's director was born there.", "It has a large coffee factory."), "b",
 "because of its growing number of international visitors とある。",
 "記事によると、なぜ金沢が選ばれたのか。", "reason", "business.news", set_id="p7-s002",
 translation_options=["他の都市より家賃が安い。", "海外からの訪問客が増えている。", "ディレクターの出身地である。", "大きなコーヒー工場がある。"])
item("p7-0005", 7, "In which of the positions marked [1], [2], [3], and [4] does the following sentence best belong?\n\"Applicants who speak English are especially encouraged to apply.\"",
 opts("[1]", "[2]", "[3]", "[4]"), "c",
 "「応募者（Applicants）」は、直前の「約40人を採用する予定」を受けている。[3] に入れると採用の話がつながる。",
 "次の文は [1]〜[4] のどこに入るのが最も適切か。「英語を話せる応募者は特に歓迎する。」", "sentence.position", "business.news",
 set_id="p7-s002", shuffle=False)

aset("p7-s003", 7, "double", "events", ["p7-0006", "p7-0007", "p7-0008", "p7-0009", "p7-0010"],
 "【文書1】レイクビュー会議センター　会議室料金（1日あたり）\nメープル室：20人・300ドル／シダー室：50人・550ドル／オーク・ホール：120人・1,200ドル／パイン・ホール：200人・1,800ドル\n"
 "※全室にプロジェクターとマイクが含まれます。※ケータリングは30人以上の団体で利用できます。※60日前までのご予約は10%割引。\n"
 "【文書2】宛先：レイクビュー会議センター／差出人：ローサ・マルティネス（デルタライン物流）／日付：3月3日／件名：予約のお願い\n"
 "5月15日に当社の年次営業研修のための部屋を予約したいと思います。参加者は約45人の見込みです。全員分の昼食も必要で、ベジタリアン向けのメニューも用意していただきたいです。"
 "2か月以上前の予約なので割引の対象になると理解しています。合計金額をご確認いただけますか。",
 passages=[
  {"type": "table", "title": "Lakeview Conference Center — Room Rates (per day)",
   "table": {"columns": ["Room", "Capacity", "Rate"],
             "rows": [["Maple Room", "20", "$300"], ["Cedar Room", "50", "$550"], ["Oak Hall", "120", "$1,200"], ["Pine Hall", "200", "$1,800"]]},
   "text": "• A projector and microphones are included in all rooms.\n• Catering is available for groups of 30 or more.\n• Bookings made at least 60 days in advance receive a 10% discount on the room rate."},
  {"type": "email", "header": {"To": "events@lakeviewcc.example", "From": "Rosa Martinez <rmartinez@deltaline.example>", "Date": "March 3", "Subject": "Booking request"},
   "text": "Hello,\n\nI would like to reserve a room for our company's annual sales training on May 15. We expect about 45 participants. We will also need lunch for everyone, and we would like a vegetarian option to be available.\n\nSince we are booking more than two months in advance, I understand that we are eligible for a discount. Could you please confirm the total price?\n\nRegards,\nRosa Martinez\nDeltaline Logistics"}])
item("p7-0006", 7, "What is indicated about all the rooms at the conference center?",
 opts("They have a view of the lake.", "They include audio-visual equipment.", "They can be booked by the hour.", "They are available on weekends only."), "b",
 "文書1に A projector and microphones are included in all rooms とある。プロジェクターとマイクを audio-visual equipment（視聴覚機器）と言い換えている。",
 "会議センターの全室について何が示されているか。", "indicated", "events", set_id="p7-s003",
 translation_options=["湖が見える。", "視聴覚機器が含まれている。", "1時間単位で予約できる。", "週末しか使えない。"])
item("p7-0007", 7, "Why did Ms. Martinez write the e-mail?",
 opts("To cancel a booking", "To make a reservation", "To complain about a service", "To ask about job openings"), "b",
 "文書2の I would like to reserve a room から、予約のためのメール。",
 "マルティネスさんはなぜメールを書いたのか。", "purpose", "events", set_id="p7-s003",
 translation_options=["予約を取り消すため", "予約をするため", "サービスに苦情を言うため", "求人について尋ねるため"])
item("p7-0008", 7, "Which room will most likely be reserved for Ms. Martinez's group?",
 opts("Maple Room", "Cedar Room", "Oak Hall", "Pine Hall"), "b",
 "【2文書の照合】参加者は約45人（文書2）。定員50人のシダー室なら収まる（文書1）。メープル室は20人で足りず、オーク・ホール以上は大きすぎる。",
 "マルティネスさんの団体にはどの部屋が予約されると考えられるか。", "cross.reference", "events", set_id="p7-s003", shuffle=False)
item("p7-0009", 7, "What is suggested about Ms. Martinez's group?",
 opts("It can use the catering service.", "It needs two rooms.", "It will stay overnight.", "It booked the center last year."), "a",
 "【2文書の照合】ケータリングは30人以上の団体が対象（文書1）で、この団体は約45人（文書2）なので利用できる。",
 "マルティネスさんの団体について何が示唆されているか。", "cross.reference", "events", set_id="p7-s003",
 translation_options=["ケータリングを利用できる。", "部屋が2つ必要だ。", "宿泊する。", "昨年もこのセンターを予約した。"])
item("p7-0010", 7, "If the discount is applied, how much will the group pay for the room?",
 opts("$270", "$495", "$550", "$1,080"), "b",
 "【2文書の照合】3月3日の時点で5月15日は60日以上先なので10%割引が適用される。シダー室 $550 × 0.9 ＝ $495。",
 "割引が適用されると、団体は部屋代にいくら払うか。", "cross.reference", "events", set_id="p7-s003", shuffle=False)

# ------------------------------------------------------------ 音声の話者（性別）を決める
# 音声生成スクリプトとアプリの読み上げは、どちらもこの指定に従う
for n, it in enumerate([i for i in items if i["part"] in (1, 2)]):
    g1, g2 = ("female", "male") if n % 2 == 0 else ("male", "female")
    it["voices"] = {"options": g1} if it["part"] == 1 else {"stem": g1, "options": g2}

# ------------------------------------------------------------ レビュー結果を反映（scripts/import_review.py が作る）
rpath = ROOT / "data" / "reviews.json"
if rpath.exists():
    reviews = json.loads(rpath.read_text(encoding="utf-8"))
    for it in items:
        rs = reviews.get(it["id"])
        if not rs: continue
        it["review"] = rs
        bad = any((not r["agree"]) or r.get("ambiguous") or r.get("issues") for r in rs)
        it["status"] = "flagged" if bad else "reviewed"

# ------------------------------------------------------------ 書き出し
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "data" / "sets.json").write_text(json.dumps(sets, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
VERSION = datetime.date.today().isoformat() + "-pilot-v0"
(ROOT / "data" / "bank.js").write_text(
    "// 自動生成（scripts/build_data.py）。file:// でも読めるように JSON を JS として置いている\n"
    "window.BANK = " + json.dumps({"version": VERSION, "items": items, "sets": sets}, ensure_ascii=False) + ";\n", encoding="utf-8")
print(len(items), "items", dict(sorted(Counter(i["part"] for i in items).items())), "|", len(sets), "sets")
