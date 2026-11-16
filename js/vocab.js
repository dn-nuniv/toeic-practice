// 単語練習。データは data/vocab.js（window.VOCAB）から読む。
// 形式：e2j＝英→日の4択／j2e＝日→英のつづり（最初の1文字と字数のヒント）／cloze＝例文の穴埋め（和訳つき）
// 学習記録は Store の vocab_progress / vocab_attempts（単語ID と形式ごとに復習スケジュールを持つ）。
(function () {
  'use strict';
  const RAW = (window.VOCAB && window.VOCAB.words) || [];
  const WORDS = RAW.filter(w => w.status !== 'retired');
  const BY = new Map(WORDS.map(w => [w.id, w]));
  const MODES = { e2j: '英→日（4択）', j2e: '日→英（つづり）', cloze: '例文の穴埋め' };
  const POS_JA = { noun: '名詞', verb: '動詞', adjective: '形容詞', adverb: '副詞', phrase: '熟語' };
  const L = 'ABCD';
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  // ヒント：各語の最初の1文字を見せ、残りは下線（熟語は look forward to → l___ f______ t_）
  const hint = s => s.split(' ').map(t => t[0] + [...t.slice(1)].map(c => (/[\-']/.test(c) ? c : '_')).join('')).join(' ');
  const norm = s => String(s || '').trim().toLowerCase().replace(/[’]/g, "'").replace(/\s+/g, ' ');
  let run = null;   // 実行中の単語練習

  // ------------------------------------------------------------ 状態
  const prog = (w, m) => Store.getWordProgress(w.id, m);
  const known = w => { const p = prog(w, 'e2j'); return !!(p && p.reps >= 2); };   // 英→日で2回続けて正解したら「覚えた」
  function dueList(now) {
    now = now || Date.now();
    const out = [];
    for (const w of WORDS) for (const m of Object.keys(MODES)) if (SRS.isDue(prog(w, m), now)) out.push({ w, mode: m });
    return out;
  }
  /** この問題（ID の一覧）に出てくる単語 */
  function related(itemIds) {
    const s = new Set(itemIds);
    return WORDS.filter(w => (w.related_items || []).some(i => s.has(i)));
  }

  // ------------------------------------------------------------ 出題の組み立て
  // まだその形式で解いていない語 → 復習の回数が少ない語 の順に、ランダム性を持たせて選ぶ
  function pick(mode, n) {
    const fresh = shuffle(WORDS.filter(w => !prog(w, mode)));
    const seen = shuffle(WORDS.filter(w => prog(w, mode))).sort((a, b) => prog(a, mode).reps - prog(b, mode).reps);
    return fresh.concat(seen).slice(0, n || WORDS.length);
  }
  function questions(mode, words) {
    return words.map(w => {
      const m = mode === 'mix' ? (known(w) ? shuffle(['j2e', 'cloze'])[0] : 'e2j') : mode;
      return { w, mode: m, order: m === 'e2j' ? shuffle(w.choices) : null };
    });
  }

  // ------------------------------------------------------------ 実行
  /**
   * opt: { mode: 'e2j'|'j2e'|'cloze'|'mix', words: [...] または qs: [{w, mode}], title, intro,
   *        context: 'vocab'|'warmup', skipLabel（あれば途中で抜けるボタン）, doneLabel, onExit() }
   */
  function start(opt) {
    const qs = opt.qs ? opt.qs.map(q => ({ ...q, order: q.mode === 'e2j' ? shuffle(q.w.choices) : null })) : questions(opt.mode, opt.words);
    if (!qs.length) { opt.onExit(); return; }
    run = { opt, qs, idx: 0, results: [], answered: false };
    render();
  }

  function speakBtn(key, text, label) {
    return `<button class="ghost speak" data-key="${esc(key)}" data-text="${esc(text)}" title="発音を聞く">🔊${label ? ' ' + label : ''}</button>`;
  }
  function render() {
    Player.stop();
    const main = $('#main'), q = run.qs[run.idx], w = q.w, o = run.opt;
    run.answered = false;
    let body = '';
    if (q.mode === 'e2j') {
      body = `<div class="vword">${esc(w.word)} <small>${POS_JA[w.pos] || ''}</small> ${speakBtn(w.id + ':word', w.word)}</div>
        <div class="vopts">${q.order.map((c, i) => `<button class="vopt" data-id="${c}"><span class="ol">${i + 1}</span>${esc(BY.get(c) ? BY.get(c).meaning_ja : '')}</button>`).join('')}</div>`;
    } else if (q.mode === 'j2e') {
      body = `<div class="vmean">${esc(w.meaning_ja)} <small>${POS_JA[w.pos] || ''}</small></div>
        <div class="vhint">${esc(hint(w.word).split(' ').map(t => [...t].join(' ')).join('　 '))}<small>（${w.word.includes(' ') ? w.word.split(' ').map(t => t.replace(/[\-']/g, '').length).join('＋') : w.word.replace(/[\-']/g, '').length}文字）</small></div>
        <div class="vinput"><input id="vin" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="${esc(w.word[0])}…"><button id="vcheck" class="primary">答え合わせ</button></div>`;
    } else {
      const blank = `<span class="vblank">${esc(hint(w.cloze).split(' ').map(t => [...t].join(' ')).join('　 '))}</span>`;
      const i = w.example.indexOf(w.cloze);
      body = `<div class="vex">${esc(w.example.slice(0, i))}${blank}${esc(w.example.slice(i + w.cloze.length))}</div>
        <div class="vexja">${esc(w.example_ja)}</div>
        <div class="vinput"><input id="vin" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="${esc(w.cloze[0])}…"><button id="vcheck" class="primary">答え合わせ</button></div>`;
    }
    main.innerHTML = `
    <div class="progress"><div style="width:${run.idx / run.qs.length * 100}%"></div></div>
    <div class="unit-head"><span class="part">${esc(o.title || '単語')}｜${MODES[q.mode]}</span><span class="count">${run.idx + 1} / ${run.qs.length}</span></div>
    ${o.intro && run.idx === 0 ? `<p class="meta">${esc(o.intro)}</p>` : ''}
    <section class="card vcard">${body}<div class="vfb" hidden></div></section>
    <div class="actions"><button id="vnext" class="primary" hidden>${run.idx + 1 < run.qs.length ? '次へ' : '結果を見る'}</button>
      ${o.skipLabel ? `<button id="vskip" class="ghost">${esc(o.skipLabel)}</button>` : `<button id="vquit" class="ghost">やめる</button>`}</div>`;
    main.querySelectorAll('.vopt').forEach(b => b.onclick = () => answer(b.dataset.id));
    if ($('#vcheck')) { $('#vcheck').onclick = () => answer($('#vin').value); $('#vin').focus(); }
    $('#vnext').onclick = next;
    if ($('#vskip')) $('#vskip').onclick = exit;
    if ($('#vquit')) $('#vquit').onclick = () => (run.results.length ? finish() : exit());
    bindSpeak(main);
  }
  function bindSpeak(root) {
    root.querySelectorAll('.speak').forEach(b => b.onclick = () => Player.play([{ key: b.dataset.key, text: b.dataset.text, gender: 'female', pause: 200 }],
      { region: Store.getSetting('region', 'us'), rate: Store.getSetting('rate', 1) }));
  }

  function answer(v) {
    if (run.answered) return;
    const q = run.qs[run.idx], w = q.w, now = Date.now();
    let ok, chosen, alt = false;
    if (q.mode === 'e2j') {
      chosen = v; ok = v === w.id;
      $('#main').querySelectorAll('.vopt').forEach(b => { b.disabled = true; if (b.dataset.id === w.id) b.classList.add('right'); else if (b.dataset.id === v) b.classList.add('wrong'); });
    } else {
      chosen = String(v || '').trim();
      ok = norm(chosen) === norm(q.mode === 'j2e' ? w.word : w.cloze);
      // 別解（同じ意味で頭文字の同じ語、英式のつづりなど）も正解にする
      alt = !ok && (w.also_ok || []).some(x => norm(x) === norm(chosen));
      if (alt) ok = true;
      $('#vin').disabled = true; $('#vcheck').hidden = true;
    }
    run.answered = true;
    const target = q.mode === 'cloze' ? w.cloze : w.word;
    const fb = $('.vfb');
    fb.hidden = false; fb.className = 'vfb ' + (ok ? 'ok' : 'ng');
    fb.innerHTML = `<div class="verdict">${ok ? '◯ 正解' : '✕ 不正解'}　<b>${esc(target)}</b>${q.mode === 'cloze' ? `（${esc(w.word)}：${esc(w.meaning_ja)}）` : `：${esc(w.meaning_ja)}`}
        ${!ok && q.mode !== 'e2j' && chosen ? `<span class="yours">あなたの答え：${esc(chosen)}</span>` : ''}
        ${alt ? `<span class="yours">「${esc(chosen)}」も別解として正解です。この問題で覚えたい語は ${esc(target)}</span>` : ''}</div>
      <p class="vexs">${esc(w.example)} ${speakBtn(w.id + ':ex', w.example, '例文')}</p><p class="tr">${esc(w.example_ja)}</p>`;
    bindSpeak(fb);
    const prev = Store.getWordProgress(w.id, q.mode);
    const row = SRS.update(prev, w.id + ':' + q.mode, ok, now);
    Store.putWordProgress(Object.assign(row, { word_id: w.id, mode: q.mode }));
    Store.addWordAttempt({ word_id: w.id, mode: q.mode, correct: ok, chosen, first_try: !prev, context: run.opt.context || 'vocab', at: new Date(now).toISOString() });
    run.results.push({ w, mode: q.mode, ok });
    $('#vnext').hidden = false; $('#vnext').focus();
  }
  function next() { if (run.idx + 1 < run.qs.length) { run.idx++; render(); } else finish(); }

  function finish() {
    Player.stop();
    const r = run.results, ok = r.filter(x => x.ok).length, wrong = r.filter(x => !x.ok), o = run.opt;
    $('#main').innerHTML = `<section class="card"><h2>${esc(o.title || '単語')}の結果</h2><p class="big">${ok} / ${r.length} 語正解</p>
      ${wrong.length ? `<table class="tbl"><thead><tr><th>単語</th><th>意味</th><th>形式</th></tr></thead><tbody>${wrong.map(x => `<tr><td>${esc(x.w.word)}</td><td>${esc(x.w.meaning_ja)}</td><td>${MODES[x.mode]}</td></tr>`).join('')}</tbody></table>` : ''}
      <p class="meta">間違えた語は10分後から「単語の復習」に出ます。正解した語も、1日後・3日後…と間隔を空けて出し直します。</p>
      <div class="actions">${wrong.length ? '<button id="vretry" class="ghost">間違えた語をもう一度</button>' : ''}<button id="vdone" class="primary">${esc(o.doneLabel || 'ホームへ')}</button></div></section>`;
    if ($('#vretry')) $('#vretry').onclick = () => start({ ...o, qs: wrong.map(x => ({ w: x.w, mode: x.mode })), intro: '' });
    $('#vdone').onclick = exit;
  }
  function exit() { Player.stop(); const o = run.opt; run = null; o.onExit(); }

  // キーボード：1〜4で4択、Enterで答え合わせ・次へ
  document.addEventListener('keydown', e => {
    if (!run) return;
    const q = run.qs[run.idx];
    if (!run.answered && q.mode === 'e2j' && /^[1-4]$/.test(e.key)) { const b = $('#main').querySelectorAll('.vopt')[+e.key - 1]; if (b) b.click(); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (run.answered) { const n = $('#vnext'); if (n) n.click(); else { const d = $('#vdone'); if (d) d.click(); } }
      else if ($('#vcheck')) $('#vcheck').click();
    }
  });

  // ------------------------------------------------------------ ホームの「単語」カード
  function homeCard() {
    const n = WORDS.length, k = WORDS.filter(known).length, d = dueList().length;
    const count = Store.getSetting('vcount', 10), warm = Store.getSetting('warmup', true);
    return `<section class="card">
      <h2>単語</h2>
      <div class="modes">
        ${Object.entries(MODES).map(([m, label]) => `<button class="mode vmode" data-vmode="${m}"><b>${label}</b><span>${m === 'e2j' ? '単語を見て意味を選ぶ' : m === 'j2e' ? '意味を見てつづりを書く' : '例文の空欄に書く'}</span></button>`).join('')}
        <button class="mode vmode" data-vmode="review" ${d ? '' : 'disabled'}><b>単語の復習</b><span>${d ? `今日の復習 ${d}件` : '今日の復習はありません'}</span></button>
      </div>
      <div class="row"><span class="lab">語数</span><select id="vcount">${[10, 20, 30, 0].map(c => `<option value="${c}" ${c === count ? 'selected' : ''}>${c || 'すべて'}</option>`).join('')}</select>
        <small>全 ${n}語・覚えた語 ${k}語</small></div>
      <div class="row"><label class="chk"><input type="checkbox" id="warmup" ${warm ? 'checked' : ''}> Part の練習の前に「今日の単語」（これから解く問題に出てくる語）を確認する</label></div>
    </section>`;
  }
  function bindHome(onExit) {
    const main = $('#main');
    if (!$('#vcount')) return;
    $('#vcount').onchange = e => Store.setSetting('vcount', +e.target.value);
    $('#warmup').onchange = e => Store.setSetting('warmup', e.target.checked);
    main.querySelectorAll('.vmode').forEach(b => b.onclick = () => {
      const m = b.dataset.vmode, n = Store.getSetting('vcount', 10);
      if (m === 'review') {
        const qs = shuffle(dueList()).slice(0, n || undefined);
        start({ qs, title: '単語の復習', onExit });
      } else start({ mode: m, words: pick(m, n), title: '単語', onExit });
    });
  }

  /** Part の練習の前の「今日の単語」。関係する語のうち、まだ覚えていない語を最大 n 語。なければすぐ onExit */
  function warmup(itemIds, onExit, n) {
    if (!Store.getSetting('warmup', true)) { onExit(); return; }
    const words = shuffle(related(itemIds).filter(w => !known(w))).slice(0, n || 8);
    if (!words.length) { onExit(); return; }
    start({ mode: 'e2j', words, title: '今日の単語', context: 'warmup', intro: 'このあと解く問題に出てくる語です。先に意味を確認しましょう。',
      skipLabel: 'とばして問題へ', doneLabel: '問題へ進む', onExit });
  }

  function statsRow() {
    const at = Store.wordAttempts(), seen = WORDS.filter(w => Object.keys(MODES).some(m => prog(w, m))).length;
    const pct = xs => xs.length ? Math.round(xs.filter(x => x.correct).length / xs.length * 100) + '%' : '―';
    return `<h3>単語</h3><table class="tbl"><thead><tr><th>形式</th><th>練習した語</th><th>初回の正答率</th><th>全体の正答率</th></tr></thead><tbody>
      ${Object.entries(MODES).map(([m, label]) => { const a = at.filter(x => x.mode === m); return `<tr><td>${label}</td><td>${WORDS.filter(w => prog(w, m)).length} / ${WORDS.length}</td><td>${pct(a.filter(x => x.first_try))}</td><td>${pct(a)}</td></tr>`; }).join('')}
      </tbody></table><p class="meta">練習した語 ${seen}語・覚えた語 ${WORDS.filter(known).length}語・今日の単語の復習 ${dueList().length}件</p>`;
  }

  window.Vocab = { words: WORDS, related, known, start, warmup, homeCard, bindHome, statsRow, active: () => !!run };
})();
