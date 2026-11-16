// 学習記録の保存。今はブラウザ（localStorage）に保存する。
// ログイン付きアプリに移すときは、このファイルだけを Supabase 版に差し替える。
// 行の形は supabase/schema.sql の user_progress / attempts テーブルと同じ。
(function () {
  'use strict';
  const KEY = 'toeic-practice.v1';
  let mem = null;
  function load() {
    if (mem) return mem;
    try { mem = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { mem = null; }
    if (!mem || typeof mem !== 'object') mem = {};
    mem.progress = mem.progress || {};   // item_id -> 復習の状態
    mem.attempts = mem.attempts || [];   // 解答の記録（新しいものを後ろに追加）
    mem.settings = mem.settings || {};
    mem.vocab_progress = mem.vocab_progress || {};  // "<単語ID>:<形式>" -> 復習の状態（形式は e2j / j2e / cloze）
    mem.vocab_attempts = mem.vocab_attempts || [];  // 単語の解答の記録
    mem.daily = mem.daily || [];                    // 今日の学習を終えた記録 { date, part, correct, total, at }
    return mem;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch (e) { /* 保存できない環境では、このページを開いている間だけ保持 */ } }
  const MAX_ATTEMPTS = 5000;

  window.Store = {
    getProgress(id) { return load().progress[id] || null; },
    allProgress() { return Object.values(load().progress); },
    putProgress(row) { load().progress[row.item_id] = row; save(); },
    addAttempt(row) { const m = load(); m.attempts.push(row); if (m.attempts.length > MAX_ATTEMPTS) m.attempts.splice(0, m.attempts.length - MAX_ATTEMPTS); save(); },
    attempts() { return load().attempts; },
    // 単語：行の形は supabase/schema.sql の vocab_progress / vocab_attempts と同じ（word_id と mode で1行）
    getWordProgress(wordId, mode) { return load().vocab_progress[wordId + ':' + mode] || null; },
    putWordProgress(row) { load().vocab_progress[row.word_id + ':' + row.mode] = row; save(); },
    addWordAttempt(row) { const m = load(); m.vocab_attempts.push(row); if (m.vocab_attempts.length > MAX_ATTEMPTS) m.vocab_attempts.splice(0, m.vocab_attempts.length - MAX_ATTEMPTS); save(); },
    wordAttempts() { return load().vocab_attempts; },
    // 今日の学習（1日1 Part）：終えたときに1行足す
    addDaily(row) { load().daily.push(row); save(); },
    dailyLog() { return load().daily; },
    getSetting(k, d) { const v = load().settings[k]; return v === undefined ? d : v; },
    setSetting(k, v) { load().settings[k] = v; save(); },
    exportAll() { return JSON.stringify({ format: 'toeic-practice-progress', version: 1, exported_at: new Date().toISOString(), ...load() }, null, 1); },
    importAll(text) {
      const d = JSON.parse(text);
      if (d.format !== 'toeic-practice-progress') throw new Error('このアプリの記録ファイルではありません');
      mem = { progress: d.progress || {}, attempts: d.attempts || [], settings: d.settings || {}, vocab_progress: d.vocab_progress || {}, vocab_attempts: d.vocab_attempts || [], daily: d.daily || [] }; save();
    },
    reset() { mem = { progress: {}, attempts: [], settings: load().settings, vocab_progress: {}, vocab_attempts: [], daily: [] }; save(); }
  };
})();
