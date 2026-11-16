// 音声の再生。audio/manifest.js に生成済みの音声ファイルがあればそれを使い、
// なければブラウザの読み上げ機能（speechSynthesis）で代わりに読む。
// 音声のキー（key）は scripts/gen_audio.py と同じ規則：
//   Part 1 選択肢 <item>:opt:<option> / Part 2 質問 <item>:stem / Part 3・4 <set>:seg:<n> / 記号 label:A:female
(function () {
  'use strict';
  const LANG = { us: 'en-US', gb: 'en-GB', au: 'en-AU', ca: 'en-CA' };
  const FEMALE = /female|samantha|victoria|karen|moira|tessa|serena|zira|aria|jenny|libby|sonia|natasha|catherine|susan|hazel|kate|allison|ava|joanna|salli|kendra|kimberly|emma|amy|nicole|olivia|linda|heather/i;
  const MALE = /(^|\W)male|daniel|alex|fred|david|guy|ryan|william|oliver|george|thomas|james|lee|gordon|aaron|arthur|mark|matthew|joey|justin|brian|russell|liam|eric|tom/i;
  let queue = [], token = 0, cur = null, onState = () => {};

  function manifestFile(region, key) {
    const m = window.AUDIO_MANIFEST || {};
    return m[region] && m[region][key] && m[region][key].file;
  }
  function hasFiles(region, keys) { return keys.length > 0 && keys.every(k => manifestFile(region, k)); }

  function pickVoice(region, gender) {
    if (!('speechSynthesis' in window)) return null;
    const lang = LANG[region] || 'en-US';
    let vs = speechSynthesis.getVoices().filter(v => v.lang && v.lang.replace('_', '-').startsWith(lang));
    if (!vs.length) vs = speechSynthesis.getVoices().filter(v => v.lang && v.lang.startsWith('en'));
    if (!vs.length) return null;
    const re = gender === 'male' ? MALE : FEMALE, other = gender === 'male' ? FEMALE : MALE;
    return vs.find(v => re.test(v.name) && !other.test(v.name)) || vs.find(v => re.test(v.name)) || vs[gender === 'male' ? Math.min(1, vs.length - 1) : 0];
  }

  function speak(u, region, rate, done) {
    if (!('speechSynthesis' in window)) { done(); return; }
    const ut = new SpeechSynthesisUtterance(u.text);
    ut.lang = LANG[region] || 'en-US'; ut.rate = rate;
    const v = pickVoice(region, u.gender); if (v) ut.voice = v;
    ut.onend = done; ut.onerror = done;
    speechSynthesis.speak(ut);
  }

  function playFile(src, rate, done, fail) {
    const a = new Audio(src); cur = a; a.playbackRate = rate;
    a.onended = done; a.onerror = fail;
    a.play().catch(fail);
  }

  function stop() {
    token++; queue = [];
    if (cur) { try { cur.pause(); } catch (e) {} cur = null; }
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    onState('stopped');
  }

  function play(utts, opt) {
    stop();
    const my = ++token, region = opt.region || 'us', rate = opt.rate || 1;
    onState = opt.onState || (() => {});
    queue = utts.slice();
    onState('playing', hasFiles(region, utts.map(u => u.key)) ? 'file' : 'tts');
    const next = () => {
      if (my !== token) return;
      const u = queue.shift();
      if (!u) { cur = null; onState('stopped'); if (opt.onEnd) opt.onEnd(); return; }
      const after = () => { if (my === token) setTimeout(next, (u.pause || 450) / rate); };
      const src = manifestFile(region, u.key);
      if (src) playFile(src, rate, after, () => speak(u, region, rate, after));
      else speak(u, region, rate, after);
    };
    next();
  }

  // ブラウザによっては声の一覧が後から読み込まれる
  if ('speechSynthesis' in window) { speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices(); }
  window.Player = { play, stop, hasFiles, regions: Object.keys(LANG) };
})();
