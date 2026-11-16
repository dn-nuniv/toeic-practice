// 復習のタイミング（忘却曲線に合わせた出し直し）。SM-2 方式を簡略化したもの。
// 正解：間隔を 1日 → 3日 → 前回の間隔×容易度 と広げる
// 不正解：10分後に出し直し、間隔を最初からやり直す（容易度を下げる）
(function () {
  'use strict';
  const DAY = 86400000;
  function initial(id) {
    return { item_id: id, reps: 0, ease: 2.5, interval_days: 0, due_at: null, lapses: 0, seen: 0, correct: 0, last_seen_at: null };
  }
  function update(prev, id, correct, now) {
    now = now || Date.now();
    const s = Object.assign(initial(id), prev || {});
    const q = correct ? 4 : 1; // SM-2 の評価（0〜5）
    s.ease = Math.max(1.3, s.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)));
    if (correct) {
      s.reps += 1;
      s.interval_days = s.reps === 1 ? 1 : s.reps === 2 ? 3 : Math.round(s.interval_days * s.ease);
      s.due_at = new Date(now + s.interval_days * DAY).toISOString();
      s.correct += 1;
    } else {
      s.reps = 0; s.lapses += 1; s.interval_days = 0;
      s.due_at = new Date(now + 10 * 60000).toISOString();
    }
    s.seen += 1; s.last_seen_at = new Date(now).toISOString();
    return s;
  }
  function isDue(s, now) { return !!(s && s.due_at && Date.parse(s.due_at) <= (now || Date.now())); }
  window.SRS = { initial, update, isDue };
})();
