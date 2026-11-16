// TOEIC L&R 練習アプリ（試作）本体。データは data/bank.js（window.BANK）から読む。
(function () {
  'use strict';
  const RAW = window.BANK || { items: [], sets: [] };
  // retired（使わなくなった問題）は出題しない。データには学習記録のために残してある
  const BANK = { ...RAW, items: RAW.items.filter(i => i.status !== 'retired'), sets: RAW.sets.filter(s => s.status !== 'retired') };
  const ITEMS = new Map(BANK.items.map(i => [i.id, i]));
  const SETS = new Map(BANK.sets.map(s => [s.id, s]));
  const PART_NAME = { 1: '写真描写問題', 2: '応答問題', 3: '会話問題', 4: '説明文問題', 5: '短文穴埋め問題', 6: '長文穴埋め問題', 7: '読解問題' };
  const LISTENING = new Set([1, 2, 3, 4]);
  const L = 'ABCD';
  // 今日の学習：1日1 Part、読解とリスニングを交互に回す（Part 5 は問題が多いので1周に2回）。1日の目安は約10問
  const DAILY_ROTATION = [5, 2, 6, 3, 7, 4, 5, 1], DAILY_COUNT = 10;
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const main = $('#main');
  let session = null;

  // ------------------------------------------------------------ 出題の単位
  // Part 1・3・4・6・7 はセット（写真・会話・本文）ごと、Part 2・5 は1問ごとに出す
  function allUnits() {
    const units = [];
    for (const s of BANK.sets) { const its = s.question_ids.map(id => ITEMS.get(id)).filter(Boolean); if (its.length) units.push({ part: s.part, set: s, items: its }); }
    for (const it of BANK.items) if (!it.set_id) units.push({ part: it.part, set: null, items: [it] });
    return units;
  }
  function takeUntil(units, n) { const out = []; let c = 0; for (const u of units) { if (n && c >= n) break; out.push(u); c += u.items.length; } return out; }

  function buildSession(mode, parts, count) {
    const pool = allUnits().filter(u => parts.includes(u.part));
    let units;
    if (mode === 'review') {
      const now = Date.now();
      units = pool.filter(u => u.items.some(it => SRS.isDue(Store.getProgress(it.id), now)))
        .sort((a, b) => due(a) - due(b));
      units = takeUntil(units, count);
    } else if (mode === 'mock') {
      const plan = { 1: 1, 2: 3, 3: 1, 4: 1, 5: 4, 6: 1, 7: 2 };
      units = [];
      for (const p of [1, 2, 3, 4, 5, 6, 7]) if (parts.includes(p)) units.push(...shuffle(pool.filter(u => u.part === p)).slice(0, plan[p]));
    } else if (mode === 'daily') {
      // 今日の学習：復習の期日が来た問題 → まだ解いていない問題 → 解いたことのある問題 の順
      const now = Date.now();
      const isDue = u => u.items.some(it => SRS.isDue(Store.getProgress(it.id), now));
      const dueU = pool.filter(isDue).sort((a, b) => due(a) - due(b));
      const fresh = shuffle(pool.filter(u => !isDue(u) && u.items.some(it => !Store.getProgress(it.id))));
      const seen = shuffle(pool.filter(u => !dueU.includes(u) && !fresh.includes(u)));
      units = takeUntil(dueU.concat(fresh, seen), count);
    } else if (mode === 'retry') {
      const wrong = new Set(session.results.filter(r => !r.correct).map(r => r.item_id));
      units = session.units.filter(u => u.items.some(it => wrong.has(it.id))).map(u => ({ part: u.part, set: u.set, items: u.items }));
      units = shuffle(units);
    } else {
      // 練習：まだ解いていない問題を先に、あとはランダム
      const fresh = shuffle(pool.filter(u => u.items.some(it => !Store.getProgress(it.id))));
      const seen = shuffle(pool.filter(u => !fresh.includes(u)));
      units = takeUntil(fresh.concat(seen), count);
    }
    // 選択肢の並びを決める（shuffle:false の問題は元の順のまま）
    for (const u of units) u.order = Object.fromEntries(u.items.map(it => [it.id, it.shuffle === false ? it.options.map(o => o.id) : shuffle(it.options.map(o => o.id))]));
    return { mode, units, idx: 0, results: [], graded: false };
  }
  function due(u) { return Math.min(...u.items.map(it => { const s = Store.getProgress(it.id); return s && s.due_at ? Date.parse(s.due_at) : Infinity; })); }
  function dueCount() { const now = Date.now(); return BANK.items.filter(it => SRS.isDue(Store.getProgress(it.id), now)).length; }

  // ------------------------------------------------------------ ホーム
  function home() {
    Player.stop(); session = null;
    const parts = Store.getSetting('parts', [1, 2, 3, 4, 5, 6, 7]);
    const region = Store.getSetting('region', 'us'), rate = Store.getSetting('rate', 1), count = Store.getSetting('count', 10), qread = Store.getSetting('qread', 'exam');
    const n = BANK.items.length, seen = BANK.items.filter(it => Store.getProgress(it.id)).length, d = dueCount();
    const reviewed = BANK.items.filter(it => it.status === 'reviewed').length;
    main.innerHTML = `
    ${dailyCard()}
    <section class="card">
      <h2>練習のしかた</h2>
      <div class="modes">
        <button class="mode" data-mode="practice"><b>練習</b><span>まだ解いていない問題から順に出題</span></button>
        <button class="mode" data-mode="review" ${d ? '' : 'disabled'}><b>復習</b><span>${d ? `今日の復習 ${d}問` : '今日の復習はありません'}</span></button>
        <button class="mode" data-mode="mock"><b>ミニ模試</b><span>Part 1〜7を本番の順に</span></button>
      </div>
    </section>
    ${window.Vocab && Vocab.words.length ? Vocab.homeCard() : ''}
    <section class="card">
      <h2>設定</h2>
      <div class="row"><span class="lab">Part</span><div class="chips">${[1, 2, 3, 4, 5, 6, 7].map(p => `<label class="chip"><input type="checkbox" name="part" value="${p}" ${parts.includes(p) ? 'checked' : ''}><span>${p}</span></label>`).join('')}</div></div>
      <div class="row"><span class="lab">問題数</span><select id="count">${[10, 20, 30, 0].map(c => `<option value="${c}" ${c === count ? 'selected' : ''}>${c || 'すべて'}</option>`).join('')}</select><small>（練習・復習のとき）</small></div>
      <div class="row"><span class="lab">英語の種類</span><select id="region">${[['us', '米国'], ['gb', '英国'], ['au', 'オーストラリア'], ['ca', 'カナダ']].map(([k, v]) => `<option value="${k}" ${k === region ? 'selected' : ''}>${v}</option>`).join('')}</select>
        <span class="lab">速さ</span><select id="rate">${[0.8, 0.9, 1, 1.1, 1.25].map(r => `<option value="${r}" ${r === rate ? 'selected' : ''}>${r}×</option>`).join('')}</select></div>
      <div class="row"><span class="lab">設問の読み上げ</span><select id="qread">${[['exam', '本番形式（解答時間 8秒・図表12秒）'], ['short', '読む（間を短く）'], ['off', '読まない']].map(([k, v]) => `<option value="${k}" ${k === qread ? 'selected' : ''}>${v}</option>`).join('')}</select><small>（Part 3・4）</small></div>
    </section>
    <p class="meta">問題 ${n}問（${esc(BANK.version || '')}）・解いた問題 ${seen}問・レビュー済み ${reviewed}問<br>
    この問題はAIが作成した練習用のオリジナル問題です。TOEIC公式問題ではなく、スコアの予測にはなりません。</p>`;
    main.querySelectorAll('input[name=part]').forEach(c => c.onchange = () => Store.setSetting('parts', [...main.querySelectorAll('input[name=part]:checked')].map(x => +x.value)));
    $('#count').onchange = e => Store.setSetting('count', +e.target.value);
    $('#region').onchange = e => Store.setSetting('region', e.target.value);
    $('#rate').onchange = e => Store.setSetting('rate', +e.target.value);
    $('#qread').onchange = e => Store.setSetting('qread', e.target.value);
    main.querySelectorAll('.mode[data-mode]').forEach(b => b.onclick = () => start(b.dataset.mode));
    $('#daily').onclick = () => start('daily');
    if (window.Vocab) Vocab.bindHome(home);
  }

  // ------------------------------------------------------------ 今日の学習
  const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  function nextDailyPart() {
    const has = p => BANK.items.some(i => i.part === p);
    const n = Store.dailyLog().length;
    for (let k = 0; k < DAILY_ROTATION.length; k++) { const p = DAILY_ROTATION[(n + k) % DAILY_ROTATION.length]; if (has(p)) return p; }
    return 5;
  }
  function dailyCard() {
    const log = Store.dailyLog(), t = today(), done = log.filter(r => r.date === t), p = nextDailyPart();
    const head = done.length
      ? `<p class="done">✓ 今日の学習は終わりました（${done.map(r => `Part ${r.part}：${r.correct} / ${r.total}問正解`).join('、')}）</p>`
      : `<p>今日は <b>Part ${p}｜${PART_NAME[p]}</b> を約${DAILY_COUNT}問。${window.Vocab && Store.getSetting('warmup', true) ? '先に関係する単語を確認します。' : ''}</p>`;
    return `<section class="card daily"><h2>今日の学習</h2>${head}
      <div class="actions"><button id="daily" class="${done.length ? 'ghost' : 'primary'}">${done.length ? `次の Part も解く（Part ${p}）` : '今日の学習を始める'}</button></div>
      <p class="meta">1日1 Part、読解とリスニングを交互に進めます（これまでに ${log.length}回）。</p></section>`;
  }

  function start(mode) {
    if (mode === 'daily') {
      const p = nextDailyPart(), s = buildSession('daily', [p], DAILY_COUNT);
      if (!s.units.length) { alertBox('出題できる問題がありません。'); return; }
      s.dailyPart = p;
      const go = () => { session = s; renderUnit(); };
      if (window.Vocab) Vocab.warmup(s.units.flatMap(u => u.items.map(it => it.id)), go); else go();
      return;
    }
    const parts = Store.getSetting('parts', [1, 2, 3, 4, 5, 6, 7]);
    if (!parts.length) { alertBox('Partを1つ以上選んでください。'); return; }
    const s = buildSession(mode, parts, mode === 'mock' ? 0 : Store.getSetting('count', 10));
    if (!s.units.length) { alertBox('出題できる問題がありません。'); return; }
    // 今日の単語：これから解く問題に出てくる語を先に確認する（設定で切れる。覚えた語は出さない）
    const go = () => { session = s; renderUnit(); };
    if (window.Vocab) Vocab.warmup(s.units.flatMap(u => u.items.map(it => it.id)), go); else go();
  }
  function alertBox(msg) { const p = document.createElement('p'); p.className = 'warn'; p.textContent = msg; main.prepend(p); setTimeout(() => p.remove(), 3000); }

  // ------------------------------------------------------------ 1単位の表示
  function renderUnit() {
    Player.stop();
    const u = session.units[session.idx]; session.graded = false;
    const nQ = session.units.reduce((a, x) => a + x.items.length, 0);
    const done = session.units.slice(0, session.idx).reduce((a, x) => a + x.items.length, 0);
    const wide = u.part >= 6 || (u.part === 3 && u.set && u.set.graphic);
    main.innerHTML = `
    <div class="progress"><div style="width:${(done / nQ) * 100}%"></div></div>
    <div class="unit-head"><span class="part">Part ${u.part}｜${PART_NAME[u.part]}</span><span class="count">${done + 1}${u.items.length > 1 ? '–' + (done + u.items.length) : ''} / ${nQ}</span></div>
    ${LISTENING.has(u.part) ? audioBar() : ''}
    <div class="unit ${wide ? 'two' : ''}">
      ${stimulus(u)}
      <div class="questions">${u.items.map(it => question(u, it)).join('')}</div>
    </div>
    ${u.set && u.set.translation_ja ? `<details class="trans hidden-until-graded"><summary>スクリプト・本文の訳</summary><div>${nl(esc(u.set.translation_ja))}</div></details>` : ''}
    <div class="actions"><button id="grade" class="primary">採点する</button><button id="next" class="primary" hidden>${session.idx + 1 < session.units.length ? '次へ' : '結果を見る'}</button><button id="quit" class="ghost">やめる</button></div>`;
    $('#grade').onclick = grade; $('#next').onclick = next; $('#quit').onclick = () => (session.results.length ? finish() : home());
    if (LISTENING.has(u.part)) bindAudio(u);
    window.scrollTo(0, 0);
  }

  function audioBar() {
    return `<div class="audio"><button id="play" class="play">▶ 再生</button><button id="stop" class="ghost">■ 停止</button><span id="astate" class="astate"></span></div>`;
  }
  function utterances(u) {
    const out = [];
    if (u.part === 1 || u.part === 2) {
      const it = u.items[0], g = it.voices || {};
      if (u.part === 2) out.push({ key: `${it.id}:stem`, text: it.prompt, gender: g.stem || 'female', pause: 900 });
      u.order[it.id].forEach((oid, i) => {
        out.push({ key: `label:${L[i]}:${g.options || 'male'}`, text: L[i] + '.', gender: g.options || 'male', pause: 250 });
        out.push({ key: `${it.id}:opt:${oid}`, text: it.options.find(o => o.id === oid).text, gender: g.options || 'male', pause: 800 });
      });
    } else {
      const spk = Object.fromEntries((u.set.speakers || []).map(s => [s.id, s]));
      u.set.segments.forEach((sg, i) => out.push({ key: `${u.set.id}:seg:${i}`, text: sg.text, gender: (spk[sg.speaker] || {}).gender || 'female', pause: 500 }));
      // 設問の読み上げ（本番では会話・説明文の後にナレーターが1問ずつ読み、解答時間が続く）
      const qr = Store.getSetting('qread', 'exam');
      if (qr !== 'off' && out.length) {
        out[out.length - 1].pause = 1200;
        u.items.forEach(it => out.push({ key: `${it.id}:q`, text: it.prompt, gender: Player.NARRATOR, qid: it.id, fixed: true,
          pause: qr === 'exam' ? (it.type === 'graphic' ? 12000 : 8000) : 2500 }));
      }
    }
    return out;
  }
  function bindAudio(u) {
    const st = $('#astate');
    $('#play').onclick = () => Player.play(utterances(u), {
      region: Store.getSetting('region', 'us'), rate: Store.getSetting('rate', 1),
      onState: (s, how) => { st.textContent = s === 'playing' ? (how === 'file' ? '再生中' : '再生中（ブラウザの読み上げ）') : ''; },
      // 読み上げ中の設問に枠を付ける
      onItem: x => main.querySelectorAll('.q').forEach(q => q.classList.toggle('reading', !!(x && x.qid === q.dataset.id)))
    });
    $('#stop').onclick = () => Player.stop();
  }

  function nl(s) { return s.replace(/\n/g, '<br>'); }
  function paras(text, part) {
    let h = esc(text);
    if (part === 6) h = h.replace(/\[(\d)\]/g, '<span class="blank">[$1]</span>');
    if (part === 7) h = h.replace(/— \[(\d)\] —/g, '<span class="pos">[$1]</span>');
    return h.split(/\n\n+/).map(p => `<p>${nl(p)}</p>`).join('');
  }
  function table(t) { return `<table class="tbl"><thead><tr>${t.columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${t.rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`; }
  function stimulus(u) {
    if (!u.set) return '';
    const s = u.set;
    if (u.part === 1) return `<figure class="photo"><img src="${esc(s.image)}" alt="Part 1の写真"></figure>`;
    if (u.part === 3 || u.part === 4) {
      const g = s.graphic ? `<div class="graphic"><div class="gt">${esc(s.graphic.title)}</div>${table(s.graphic)}</div>` : '';
      const sc = `<details class="script hidden-until-graded"><summary>スクリプト</summary>${s.segments.map(x => `<p><b>${esc(x.speaker)}:</b> ${esc(x.text)}</p>`).join('')}</details>`;
      return g || sc ? `<div class="stim">${g}${sc}</div>` : '';
    }
    return `<div class="stim passages">${s.passages.map(p => `<article class="doc ${esc(p.type)}">
      ${p.header ? `<dl class="hdr">${Object.entries(p.header).map(([k, v]) => `<dt>${esc(k)}:</dt><dd>${esc(v)}</dd>`).join('')}</dl>` : ''}
      ${p.title ? `<h3>${esc(p.title)}</h3>` : ''}${p.table ? table(p.table) : ''}${paras(p.text || '', u.part)}</article>`).join('')}</div>`;
  }
  function question(u, it) {
    const hideText = u.part === 1 || u.part === 2;
    const head = u.part === 6 ? `空欄 ${esc(it.prompt)}` : u.part === 1 ? '' : u.part === 2 ? 'Mark your answer.' : nl(esc(it.prompt));
    return `<div class="q" data-id="${it.id}">
      ${head ? `<div class="qt">${head}</div>` : ''}
      <div class="opts">${u.order[it.id].map((oid, i) => {
        const o = it.options.find(x => x.id === oid);
        return `<label class="opt" data-oid="${oid}"><input type="radio" name="q-${it.id}" value="${oid}"><span class="ol">(${L[i]})</span><span class="ot ${hideText ? 'hidden-until-graded' : ''}">${esc(o.text)}</span></label>`;
      }).join('')}</div>
      <div class="exp" hidden></div>
      <div class="qid">${it.id}${it.status !== 'reviewed' ? '・未レビュー' : ''}</div>
    </div>`;
  }

  // 解説の (A)〜(D) はデータ上の並び順で書いてあるので、画面に出した並び順の記号に置き換える
  function relabel(text, it, ord) {
    return String(text || '').replace(/\(([A-D])\)/g, (m, a) => {
      const o = it.options[a.charCodeAt(0) - 65];
      return o ? `(${L[ord.indexOf(o.id)]})` : m;
    });
  }

  // ------------------------------------------------------------ 採点
  function grade() {
    if (session.graded) return;
    const u = session.units[session.idx], now = Date.now();
    session.graded = true; Player.stop();
    for (const it of u.items) {
      const box = main.querySelector(`.q[data-id="${it.id}"]`);
      const ch = box.querySelector('input:checked'), chosen = ch ? ch.value : null, ok = chosen === it.answer;
      box.querySelectorAll('input').forEach(x => x.disabled = true);
      box.querySelectorAll('.opt').forEach(l => { if (l.dataset.oid === it.answer) l.classList.add('right'); else if (l.dataset.oid === chosen) l.classList.add('wrong'); });
      box.classList.add(ok ? 'ok' : 'ng');
      const ord = u.order[it.id], letter = L[ord.indexOf(it.answer)];
      // 選択肢ごとの和訳とコメント（表示した並び順で）、TOEIC のポイント
      const tr = it.translation_options_ja, on = it.option_notes_ja;
      const tro = tr || on ? `<ul class="tro">${ord.map((oid, i) => { const k = it.options.findIndex(o => o.id === oid);
          return `<li class="${oid === it.answer ? 'ans' : ''}"><b>(${L[i]})</b> ${tr ? esc(tr[k]) : ''}${on ? `<span class="note">${esc(on[k])}</span>` : ''}</li>`; }).join('')}</ul>` : '';
      const pt = it.point_ja ? `<p class="point"><b>TOEIC のポイント</b>${esc(it.point_ja)}</p>` : '';
      const e = box.querySelector('.exp'); e.hidden = false;
      e.innerHTML = `<div class="verdict">${ok ? '◯ 正解' : chosen ? '✕ 不正解' : '― 未解答'}　正解は (${letter})</div><p>${esc(relabel(it.explanation_ja, it, ord))}</p>${it.translation_ja && it.part !== 6 ? `<p class="tr">訳：${esc(it.translation_ja)}</p>` : ''}${tro}${pt}`;
      const prev = Store.getProgress(it.id);
      Store.putProgress(SRS.update(prev, it.id, ok, now));
      Store.addAttempt({ item_id: it.id, part: it.part, correct: ok, chosen, first_try: !prev, mode: session.mode, at: new Date(now).toISOString() });
      session.results.push({ item_id: it.id, part: it.part, correct: ok });
    }
    main.querySelectorAll('.hidden-until-graded').forEach(x => x.classList.remove('hidden-until-graded'));
    $('#grade').hidden = true; $('#next').hidden = false; $('#next').focus();
  }
  function next() { if (session.idx + 1 < session.units.length) { session.idx++; renderUnit(); } else finish(); }

  function finish() {
    Player.stop();
    const r = session.results, ok = r.filter(x => x.correct).length;
    // 今日の学習は、最後まで解いたときだけ記録する
    const nQ = session.units.reduce((a, x) => a + x.items.length, 0);
    let dailyMsg = '';
    if (session.mode === 'daily' && !session.recorded) {
      if (r.length === nQ) { Store.addDaily({ date: today(), part: session.dailyPart, correct: ok, total: r.length, at: new Date().toISOString() }); session.recorded = true; dailyMsg = '<p class="done">✓ 今日の学習を記録しました。</p>'; }
      else dailyMsg = '<p class="meta">途中でやめたので、今日の学習には記録していません。</p>';
    }
    const byPart = {}; r.forEach(x => { (byPart[x.part] = byPart[x.part] || [0, 0])[1]++; if (x.correct) byPart[x.part][0]++; });
    main.innerHTML = `<section class="card"><h2>${session.mode === 'daily' ? '今日の学習の結果' : '結果'}</h2>${dailyMsg}<p class="big">${ok} / ${r.length} 問正解</p>
      <table class="tbl"><thead><tr><th>Part</th><th>正解</th><th>正答率</th></tr></thead><tbody>${Object.entries(byPart).map(([p, [a, b]]) => `<tr><td>Part ${p}</td><td>${a} / ${b}</td><td>${Math.round(a / b * 100)}%</td></tr>`).join('')}</tbody></table>
      <p class="meta">間違えた問題は10分後から「復習」に出ます。正解した問題も、1日後・3日後…と間隔を空けて出し直します。</p>
      <div class="actions">${ok < r.length ? '<button id="retry" class="primary">間違えた問題をもう一度</button>' : ''}<button id="home" class="ghost">ホームへ</button></div></section>`;
    if ($('#retry')) $('#retry').onclick = () => { const s = buildSession('retry'); session = s; renderUnit(); };
    $('#home').onclick = home;
  }

  // ------------------------------------------------------------ 成績
  function stats() {
    Player.stop(); session = null;
    const at = Store.attempts(), now = Date.now();
    const rows = [1, 2, 3, 4, 5, 6, 7].map(p => {
      const a = at.filter(x => x.part === p), f = a.filter(x => x.first_try);
      const total = BANK.items.filter(i => i.part === p).length, seen = BANK.items.filter(i => i.part === p && Store.getProgress(i.id)).length;
      const pct = (xs) => xs.length ? Math.round(xs.filter(x => x.correct).length / xs.length * 100) + '%' : '―';
      return `<tr><td>Part ${p}</td><td>${seen} / ${total}</td><td>${pct(f)}</td><td>${pct(a)}</td></tr>`;
    }).join('');
    main.innerHTML = `<section class="card"><h2>成績</h2>
      <table class="tbl"><thead><tr><th>Part</th><th>解いた問題</th><th>初回の正答率</th><th>全体の正答率</th></tr></thead><tbody>${rows}</tbody></table>
      <p class="meta">今日の復習 ${dueCount()}問・解答の記録 ${at.length}件。記録はこのブラウザに保存されています。</p>
      ${window.Vocab && Vocab.words.length ? Vocab.statsRow() : ''}
      <div class="actions"><button id="exp" class="ghost">記録を書き出す</button><label class="ghost file">記録を読み込む<input type="file" id="imp" accept="application/json" hidden></label><button id="rst" class="ghost danger">記録を消去</button></div></section>`;
    $('#exp').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([Store.exportAll()], { type: 'application/json' })); a.download = 'toeic-practice-progress.json'; a.click(); };
    $('#imp').onchange = e => { const f = e.target.files[0]; if (!f) return; f.text().then(t => { try { Store.importAll(t); stats(); } catch (err) { alertBox(err.message); } }); };
    $('#rst').onclick = () => { if (confirm('このブラウザの学習記録をすべて消去します。よろしいですか。')) { Store.reset(); stats(); } };
  }

  document.querySelectorAll('[data-nav]').forEach(a => a.onclick = e => { e.preventDefault(); a.dataset.nav === 'stats' ? stats() : home(); });
  document.addEventListener('keydown', e => {
    if (!session || /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName) && e.target.type !== 'radio') return;
    const u = session.units[session.idx];
    if (!session.graded && u.items.length === 1 && /^[1-4]$/.test(e.key)) { const r = main.querySelectorAll('.q input')[+e.key - 1]; if (r) r.checked = true; }
    if (e.key === 'Enter') { e.preventDefault(); session.graded ? next() : grade(); }
  });
  home();
})();
