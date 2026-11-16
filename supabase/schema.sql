-- ログイン付きアプリ（段階2）に移すときの Supabase のテーブル案。
-- data/items.json・data/sets.json の1件がそのまま1行になるように列をそろえてある。
-- 学習記録は js/store.js が localStorage に保存している形（user_progress・attempts）と同じ。

create table if not exists sets (
  id            text primary key,          -- 例 p3-s001
  part          smallint not null check (part between 1 and 7),
  kind          text not null,             -- photo / conversation / announcement / email / single / double など
  scene         text,                      -- 職場の場面（meeting, logistics など）
  speakers      jsonb not null default '[]',
  segments      jsonb not null default '[]',   -- Part 3・4 のスクリプト
  passages      jsonb not null default '[]',   -- Part 6・7 の本文
  graphic       jsonb,                     -- Part 3・4 の図
  image         text,                      -- Part 1 の写真（Storage のパス）
  question_ids  text[] not null default '{}',
  translation_ja text,
  status        text not null default 'draft',
  source        text
);

create table if not exists items (
  id            text primary key,          -- 例 p5-0003
  part          smallint not null check (part between 1 and 7),
  set_id        text references sets(id),
  type          text not null,             -- 出題タイプ（grammar.passive, inference など）
  scene         text,
  prompt        text not null,
  options       jsonb not null,            -- [{"id":"a","text":"..."}]
  answer        text not null,             -- 正解の選択肢ID（表示位置ではない）
  shuffle       boolean not null default true,
  explanation_ja text,
  translation_ja text,
  translation_options_ja jsonb,
  option_notes_ja jsonb,                    -- 選択肢ごとのコメント（options と同じ順）
  point_ja      text,                     -- TOEIC のポイント
  voices        jsonb,                     -- Part 1・2 の話者の性別
  level         text,
  status        text not null default 'draft' check (status in ('draft','reviewed','flagged','retired')),
  source        text,
  review        jsonb not null default '[]',
  explain_status text not null default 'unchecked' check (explain_status in ('unchecked','checked','flagged'))  -- 解説の確認
);

-- 学生ごとの復習の状態（SM-2）
create table if not exists user_progress (
  user_id       uuid not null references auth.users(id) on delete cascade,
  item_id       text not null references items(id),
  reps          int not null default 0,
  ease          real not null default 2.5,
  interval_days int not null default 0,
  due_at        timestamptz,
  lapses        int not null default 0,
  seen          int not null default 0,
  correct       int not null default 0,
  last_seen_at  timestamptz,
  primary key (user_id, item_id)
);
create index if not exists user_progress_due on user_progress (user_id, due_at);

-- 解答の記録（誤答分析・授業での集計用）
create table if not exists attempts (
  id            bigint generated always as identity primary key,
  user_id       uuid not null references auth.users(id) on delete cascade,
  item_id       text not null references items(id),
  part          smallint,
  correct       boolean not null,
  chosen        text,                      -- 選んだ選択肢ID（未解答は null）
  first_try     boolean not null default false,
  mode          text,                      -- practice / review / mock / retry
  at            timestamptz not null default now()
);
create index if not exists attempts_item on attempts (item_id);

-- 単語（data/vocab.json の1件が1行）
create table if not exists vocab (
  id            text primary key,            -- v-0001
  word          text not null,
  pos           text not null check (pos in ('noun','verb','adjective','adverb','phrase')),
  meaning_ja    text not null,
  level         text,
  example       text not null,
  example_ja    text not null,
  cloze         text not null,               -- 例文の穴埋めにする語形（例文中にそのまま出てくる）
  also_ok       text[] not null default '{}', -- 記述問題で正解にする別解（同じ意味で頭文字の同じ語、英式のつづりなど）
  distractors   text[] not null default '{}', -- 英→日の4択のダミー（vocab.id）
  choices       text[] not null default '{}', -- 4択の並び（レビュー用。アプリでは毎回シャッフル）
  related_items text[] not null default '{}', -- この語が出てくる問題（items.id）。「今日の単語」に使う
  status        text not null default 'draft' check (status in ('draft','reviewed','flagged','retired')),
  source        text,
  review        jsonb not null default '[]'
);

-- 単語の復習の状態（単語ID と形式ごと。形式は e2j＝英→日 / j2e＝日→英 / cloze＝例文の穴埋め）
create table if not exists vocab_progress (
  user_id       uuid not null references auth.users(id) on delete cascade,
  word_id       text not null references vocab(id),
  mode          text not null check (mode in ('e2j','j2e','cloze')),
  reps          int not null default 0,
  ease          real not null default 2.5,
  interval_days int not null default 0,
  due_at        timestamptz,
  lapses        int not null default 0,
  seen          int not null default 0,
  correct       int not null default 0,
  last_seen_at  timestamptz,
  primary key (user_id, word_id, mode)
);
create index if not exists vocab_progress_due on vocab_progress (user_id, due_at);

-- 単語の解答の記録
create table if not exists vocab_attempts (
  id            bigint generated always as identity primary key,
  user_id       uuid not null references auth.users(id) on delete cascade,
  word_id       text not null references vocab(id),
  mode          text not null,
  correct       boolean not null,
  chosen        text,                        -- 選んだ単語ID、または書いた答え
  first_try     boolean not null default false,
  context       text,                        -- vocab（単語練習）/ warmup（今日の単語）
  at            timestamptz not null default now()
);

-- 行単位のアクセス制御：問題はログインした人が読めるだけ、記録は本人のものだけ
alter table sets enable row level security;
alter table items enable row level security;
alter table user_progress enable row level security;
alter table attempts enable row level security;
alter table vocab enable row level security;
alter table vocab_progress enable row level security;
alter table vocab_attempts enable row level security;
create policy "read sets"  on sets  for select to authenticated using (status <> 'retired');
create policy "read items" on items for select to authenticated using (status <> 'retired');
create policy "own progress" on user_progress for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own attempts" on attempts for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "read vocab" on vocab for select to authenticated using (status <> 'retired');
create policy "own vocab progress" on vocab_progress for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own vocab attempts" on vocab_attempts for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
-- 教員が全員の記録を見る用のビュー・関数は、JLPTアプリの教員ロールの仕組みに合わせて追加する
