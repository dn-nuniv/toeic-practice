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
    getSetting(k, d) { const v = load().settings[k]; return v === undefined ? d : v; },
    setSetting(k, v) { load().settings[k] = v; save(); },
    exportAll() { return JSON.stringify({ format: 'toeic-practice-progress', version: 1, exported_at: new Date().toISOString(), ...load() }, null, 1); },
    importAll(text) {
      const d = JSON.parse(text);
      if (d.format !== 'toeic-practice-progress') throw new Error('このアプリの記録ファイルではありません');
      mem = { progress: d.progress || {}, attempts: d.attempts || [], settings: d.settings || {} }; save();
    },
    reset() { mem = { progress: {}, attempts: [], settings: load().settings }; save(); }
  };
})();
