-- Obscure Trivia accounts: a username, a password, a coin balance, and a blackjack table that runs here on the server.
-- Paste all of this into the Supabase SQL Editor and press Run. Running it again (after an update) is safe.
--
-- How it's kept safe:
--  * The tables can't be read or changed directly by the website (row level security is on and there are no policies).
--    The site can only call the functions granted at the bottom.
--  * Passwords are stored as bcrypt hashes, never as text. Session tokens are stored as SHA-256 hashes.
--  * 10 wrong passwords in a row lock that username for 15 minutes.
--  * There is no way for the website to set or add any amount of coins. Coins only come from:
--     - a right quiz answer: 1 coin, once per question of each game, and no faster than a quick human could answer;
--     - blackjack, which is played entirely here: the server shuffles, keeps the shoe and the dealer's face-down card
--       secret, checks every move against the real hand, and pays out itself;
--     - at sign-up, the coins already in that browser, up to 500.

create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.ot_accounts (
  id bigint generated always as identity primary key,
  username text not null,
  uname text not null unique,                       -- lower case, so "Sam" and "sam" are the same account
  pass_hash text not null,
  coins bigint not null default 0 check (coins >= 0),
  failed int not null default 0,
  locked_until timestamptz,
  earn_tokens real not null default 25,           -- quiz coins: a bucket of 25 that refills 1 every 4 seconds
  earn_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
alter table public.ot_accounts add column if not exists earn_tokens real not null default 25;
alter table public.ot_accounts add column if not exists earn_at timestamptz not null default now();
create table if not exists public.ot_sessions (
  token_hash text primary key,
  account_id bigint not null references public.ot_accounts(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
-- the old "add any amount" function and its table are gone for good
drop function if exists public.ot_coins(text, bigint, text);
drop table if exists public.ot_coin_ops;
-- each question of each quiz game pays once per account
create table if not exists public.ot_earned (
  account_id bigint not null references public.ot_accounts(id) on delete cascade,
  code text not null,
  q smallint not null,
  at timestamptz not null default now(),
  primary key (account_id, code, q)
);
-- one blackjack round per account; the shoe and the dealer's face-down card never leave the server until they're dealt
create table if not exists public.ot_bj (
  account_id bigint primary key references public.ot_accounts(id) on delete cascade,
  phase text not null default 'none',                -- none, insurance, play, over
  shoe smallint[] not null default '{}',             -- cards still to come (0-51: rank = card % 13 + 1, suit = card / 13), drawn from the end
  dealer smallint[] not null default '{}',
  active int not null default 0,
  insurance bigint not null default 0,
  insurance_paid bigint not null default 0,
  staked bigint not null default 0,
  returned bigint not null default 0,
  round bigint not null default 0,
  updated_at timestamptz not null default now()
);
create table if not exists public.ot_bj_hands (
  account_id bigint not null references public.ot_accounts(id) on delete cascade,
  idx int not null,
  cards smallint[] not null,
  bet bigint not null,
  doubled boolean not null default false,
  from_split boolean not null default false,
  split_aces boolean not null default false,
  done boolean not null default false,
  result text not null default '',
  paid bigint not null default 0,
  primary key (account_id, idx)
);
alter table public.ot_accounts enable row level security;
alter table public.ot_sessions enable row level security;
alter table public.ot_earned enable row level security;
alter table public.ot_bj enable row level security;
alter table public.ot_bj_hands enable row level security;
revoke all on public.ot_accounts, public.ot_sessions, public.ot_earned, public.ot_bj, public.ot_bj_hands from anon, authenticated;

-- a new session for an account: the token goes back to the browser, only its hash is kept
create or replace function public.ot_new_session(p_account bigint) returns text
language plpgsql security definer set search_path = public, extensions as $$
declare t text := encode(gen_random_bytes(32), 'hex');
begin
  insert into ot_sessions (token_hash, account_id, expires_at) values (encode(digest(t, 'sha256'), 'hex'), p_account, now() + interval '1 year');
  delete from ot_sessions where account_id = p_account and expires_at < now();
  return t;
end $$;

create or replace function public.ot_account_for(p_token text) returns bigint
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint;
begin
  select account_id into a from ot_sessions where token_hash = encode(digest(coalesce(p_token, ''), 'sha256'), 'hex') and expires_at > now();
  if a is null then raise exception 'ot:session'; end if;
  return a;
end $$;

create or replace function public.ot_signup(p_username text, p_password text, p_coins bigint default 0) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint; u text := btrim(coalesce(p_username, ''));
begin
  if u !~ '^[A-Za-z0-9_]{3,20}$' then raise exception 'ot:bad_username'; end if;
  if char_length(coalesce(p_password, '')) < 8 or octet_length(p_password) > 72 then raise exception 'ot:bad_password'; end if;
  if exists (select 1 from ot_accounts where uname = lower(u)) then raise exception 'ot:taken'; end if;
  insert into ot_accounts (username, uname, pass_hash, coins)
    values (u, lower(u), crypt(p_password, gen_salt('bf', 10)), greatest(0, least(coalesce(p_coins, 0), 500)))
    returning id into a;
  return json_build_object('token', ot_new_session(a), 'username', u, 'coins', (select coins from ot_accounts where id = a));
exception when unique_violation then raise exception 'ot:taken';
end $$;

create or replace function public.ot_login(p_username text, p_password text) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare r ot_accounts%rowtype;
begin
  select * into r from ot_accounts where uname = lower(btrim(coalesce(p_username, ''))) for update;
  if not found then
    perform crypt(coalesce(p_password, ''), gen_salt('bf', 10));     -- take the same time as a real check
    raise exception 'ot:wrong';
  end if;
  if r.locked_until is not null and r.locked_until > now() then raise exception 'ot:locked'; end if;
  if r.pass_hash <> crypt(coalesce(p_password, ''), r.pass_hash) then
    update ot_accounts set failed = case when failed + 1 >= 10 then 0 else failed + 1 end,
      locked_until = case when failed + 1 >= 10 then now() + interval '15 minutes' else locked_until end where id = r.id;
    return json_build_object('error', 'ot:wrong');                  -- returned, not raised, so the failed count is kept
  end if;
  update ot_accounts set failed = 0, locked_until = null where id = r.id;
  return json_build_object('token', ot_new_session(r.id), 'username', r.username, 'coins', r.coins);
end $$;

create or replace function public.ot_me(p_token text) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint := ot_account_for(p_token);
begin
  return (select json_build_object('username', username, 'coins', coins) from ot_accounts where id = a);
end $$;

create or replace function public.ot_logout(p_token text) returns json
language plpgsql security definer set search_path = public, extensions as $$
begin
  delete from ot_sessions where token_hash = encode(digest(coalesce(p_token, ''), 'sha256'), 'hex');
  return json_build_object('ok', true);
end $$;

-- ================================================================ quiz coins: 1 per right answer, once per question of a game
-- The browser can't add coins any other way. Claims are limited to a bucket of 25 that refills 1 every 4 seconds,
-- about as fast as a quick player can read and answer, so a script can't pile up coins either.
create or replace function public.ot_earn(p_token text, p_code text, p_q int) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint := ot_account_for(p_token); r ot_accounts%rowtype; t real;
begin
  if p_code is null or p_code !~ '^[A-Z0-9]{5}$' or p_q is null or p_q < 0 or p_q > 19 then raise exception 'ot:error'; end if;
  select * into r from ot_accounts where id = a for update;
  if exists (select 1 from ot_earned where account_id = a and code = p_code and q = p_q) then
    return json_build_object('coins', r.coins, 'dup', true);
  end if;
  t := least(25, r.earn_tokens + extract(epoch from now() - r.earn_at) / 4);
  if t < 1 then raise exception 'ot:slow'; end if;
  insert into ot_earned (account_id, code, q) values (a, p_code, p_q);
  update ot_accounts set coins = coins + 1, earn_tokens = t - 1, earn_at = now() where id = a returning coins into r.coins;
  delete from ot_earned where account_id = a and at < now() - interval '90 days';
  return json_build_object('coins', r.coins);
end $$;

-- ================================================================ blackjack, played here on the server
-- Rules: a fresh 6-deck shoe shuffled for every hand (so cards can't be counted), dealer peeks for blackjack with an Ace or
-- 10 showing and stands on all 17s, blackjack pays 3 to 2 (rounded down), other wins 1 to 1, double on any first two cards
-- (also after splitting), split equal values up to 4 hands (split Aces get one card each), insurance pays 2 to 1.

-- a fair whole number from 0 to n-1 from the server's cryptographic random bytes
create or replace function public.ot_bj_rand(n int) returns int
language plpgsql security definer set search_path = public, extensions as $$
declare lim bigint := (4294967296 / n) * n; b bytea; x bigint;
begin
  loop
    b := gen_random_bytes(4);
    x := get_byte(b, 0)::bigint * 16777216 + get_byte(b, 1) * 65536 + get_byte(b, 2) * 256 + get_byte(b, 3);
    if x < lim then return (x % n)::int; end if;
  end loop;
end $$;

create or replace function public.ot_bj_shoe() returns smallint[]
language plpgsql security definer set search_path = public, extensions as $$
declare s smallint[] := '{}'; j int; t smallint;
begin
  for d in 1..6 loop for c in 0..51 loop s := s || c::smallint; end loop; end loop;
  for i in reverse 312..2 loop
    j := ot_bj_rand(i) + 1;
    t := s[i]; s[i] := s[j]; s[j] := t;
  end loop;
  return s;
end $$;

create or replace function public.ot_bj_val(c smallint) returns int language sql immutable set search_path = public as $$ select least(c % 13 + 1, 10) $$;
create or replace function public.ot_bj_total(cs smallint[]) returns int language sql immutable set search_path = public as $$
  select (case when bool_or(c % 13 = 0) and sum(least(c % 13 + 1, 10)) + 10 <= 21 then sum(least(c % 13 + 1, 10)) + 10
               else coalesce(sum(least(c % 13 + 1, 10)), 0) end)::int from unnest(cs) c $$;
create or replace function public.ot_bj_soft(cs smallint[]) returns boolean language sql immutable set search_path = public as $$
  select coalesce(bool_or(c % 13 = 0) and sum(least(c % 13 + 1, 10)) + 10 <= 21, false) from unnest(cs) c $$;
create or replace function public.ot_bj_isbj(cs smallint[]) returns boolean language sql immutable set search_path = public as $$
  select coalesce(array_length(cs, 1), 0) = 2 and public.ot_bj_total(cs) = 21 $$;

create or replace function public.ot_bj_draw(p_a bigint) returns smallint
language plpgsql security definer set search_path = public, extensions as $$
declare c smallint; n int;
begin
  select shoe[array_length(shoe, 1)], array_length(shoe, 1) into c, n from ot_bj where account_id = p_a;
  if c is null then raise exception 'ot:error'; end if;
  update ot_bj set shoe = shoe[1:n - 1] where account_id = p_a;
  return c;
end $$;

-- results and payouts; the coins go straight onto the account
create or replace function public.ot_bj_settle(p_a bigint) returns void
language plpgsql security definer set search_path = public, extensions as $$
declare b ot_bj%rowtype; h ot_bj_hands%rowtype; d int; dbj boolean; p int; pbj boolean; v_res text; v_paid bigint; back bigint := 0; ins bigint := 0;
begin
  select * into b from ot_bj where account_id = p_a;
  d := ot_bj_total(b.dealer); dbj := ot_bj_isbj(b.dealer);
  for h in select * from ot_bj_hands where account_id = p_a order by idx loop
    p := ot_bj_total(h.cards); pbj := ot_bj_isbj(h.cards) and not h.from_split;
    if pbj and dbj then v_res := 'push'; v_paid := h.bet;
    elsif pbj then v_res := 'blackjack'; v_paid := h.bet + (h.bet * 3) / 2;
    elsif dbj then v_res := 'lose'; v_paid := 0;
    elsif p > 21 then v_res := 'bust'; v_paid := 0;
    elsif d > 21 or p > d then v_res := 'win'; v_paid := h.bet * 2;
    elsif p = d then v_res := 'push'; v_paid := h.bet;
    else v_res := 'lose'; v_paid := 0;
    end if;
    update ot_bj_hands set result = v_res, paid = v_paid where account_id = p_a and idx = h.idx;
    back := back + v_paid;
  end loop;
  if b.insurance > 0 and dbj then ins := b.insurance * 3; end if;
  update ot_bj set phase = 'over', insurance_paid = ins, returned = back + ins, updated_at = now() where account_id = p_a;
  update ot_accounts set coins = coins + back + ins where id = p_a;
end $$;

create or replace function public.ot_bj_dealer(p_a bigint) returns void
language plpgsql security definer set search_path = public, extensions as $$
declare dl smallint[];
begin
  select dealer into dl from ot_bj where account_id = p_a;
  while ot_bj_total(dl) < 17 loop dl := dl || ot_bj_draw(p_a); end loop;
  update ot_bj set dealer = dl where account_id = p_a;
  perform ot_bj_settle(p_a);
end $$;

-- the current hand is finished: move to the next one (dealing a split hand its second card), or let the dealer play
create or replace function public.ot_bj_next(p_a bigint) returns void
language plpgsql security definer set search_path = public, extensions as $$
declare b ot_bj%rowtype; h ot_bj_hands%rowtype; n int; c smallint;
begin
  select * into b from ot_bj where account_id = p_a;
  update ot_bj_hands set done = true where account_id = p_a and idx = b.active;
  select * into h from ot_bj_hands where account_id = p_a and idx > b.active and not done order by idx limit 1;
  if found then
    update ot_bj set active = h.idx where account_id = p_a;
    if array_length(h.cards, 1) = 1 then
      c := ot_bj_draw(p_a);
      update ot_bj_hands set cards = cards || c where account_id = p_a and idx = h.idx returning * into h;
      if h.split_aces or ot_bj_total(h.cards) = 21 then perform ot_bj_next(p_a); end if;
    end if;
    return;
  end if;
  select count(*) into n from ot_bj_hands where account_id = p_a;
  update ot_bj set active = n - 1 where account_id = p_a;
  if exists (select 1 from ot_bj_hands where account_id = p_a and ot_bj_total(cards) <= 21) then perform ot_bj_dealer(p_a);
  else perform ot_bj_settle(p_a);
  end if;
end $$;

-- what the player is allowed to see: never the shoe, and never the dealer's face-down card before the round is over
create or replace function public.ot_bj_view(p_a bigint) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare b ot_bj%rowtype; v_coins bigint; shown boolean; hs json; h ot_bj_hands%rowtype; n int;
begin
  select coins into v_coins from ot_accounts where id = p_a;
  select * into b from ot_bj where account_id = p_a;
  if not found or b.phase = 'none' then return json_build_object('phase', 'none', 'coins', v_coins, 'hands', '[]'::json, 'dealer', '[]'::json); end if;
  shown := b.phase = 'over';
  select coalesce(json_agg(json_build_object('cards', x.cards, 'bet', x.bet, 'doubled', x.doubled, 'splitAces', x.split_aces,
           'total', ot_bj_total(x.cards), 'soft', ot_bj_soft(x.cards), 'result', case when shown then x.result else '' end,
           'paid', case when shown then x.paid else 0 end) order by x.idx), '[]'::json), count(*)
    into hs, n from ot_bj_hands x where x.account_id = p_a;
  select * into h from ot_bj_hands where account_id = p_a and idx = b.active;
  return json_build_object(
    'phase', b.phase, 'round', b.round, 'coins', v_coins, 'active', b.active, 'hands', hs,
    'dealer', case when shown then to_json(b.dealer) else json_build_array(b.dealer[1], null) end,
    'dealerTotal', ot_bj_total(case when shown then b.dealer else array[b.dealer[1]] end),
    'dealerBJ', shown and ot_bj_isbj(b.dealer),
    'insurance', b.insurance, 'insuranceCost', case when b.phase = 'insurance' then h.bet / 2 else 0 end,
    'insurancePaid', case when shown then b.insurance_paid else 0 end,
    'staked', b.staked, 'returned', case when shown then b.returned else 0 end,
    'couldDouble', b.phase = 'play' and array_length(h.cards, 1) = 2 and not h.split_aces,
    'couldSplit', b.phase = 'play' and array_length(h.cards, 1) = 2 and not h.split_aces and n < 4 and ot_bj_val(h.cards[1]) = ot_bj_val(h.cards[2]),
    'betLeft', v_coins >= h.bet);
end $$;

create or replace function public.ot_bj_state(p_token text) returns json
language plpgsql security definer set search_path = public, extensions as $$
begin
  return ot_bj_view(ot_account_for(p_token));
end $$;

create or replace function public.ot_bj_deal(p_token text, p_bet bigint) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint := ot_account_for(p_token); v_coins bigint; b ot_bj%rowtype; p1 smallint; d1 smallint; p2 smallint; d2 smallint;
begin
  select coins into v_coins from ot_accounts where id = a for update;      -- one move at a time per account, even from two tabs
  insert into ot_bj (account_id) values (a) on conflict do nothing;
  select * into b from ot_bj where account_id = a for update;
  if b.phase in ('insurance', 'play') then raise exception 'ot:bj_busy'; end if;
  if p_bet is null or p_bet < 1 or p_bet > v_coins then raise exception 'ot:bj_bet'; end if;
  update ot_accounts set coins = coins - p_bet where id = a;
  delete from ot_bj_hands where account_id = a;
  update ot_bj set shoe = ot_bj_shoe(), dealer = '{}', active = 0, insurance = 0, insurance_paid = 0, staked = p_bet, returned = 0,
    round = round + 1, phase = 'deal', updated_at = now() where account_id = a;
  p1 := ot_bj_draw(a); d1 := ot_bj_draw(a); p2 := ot_bj_draw(a); d2 := ot_bj_draw(a);
  insert into ot_bj_hands (account_id, idx, cards, bet) values (a, 0, array[p1, p2], p_bet);
  update ot_bj set dealer = array[d1, d2] where account_id = a;
  if d1 % 13 = 0 and p_bet >= 2 then update ot_bj set phase = 'insurance' where account_id = a;     -- offer insurance first
  elsif ot_bj_isbj(array[d1, d2]) and (d1 % 13 = 0 or ot_bj_val(d1) = 10) then perform ot_bj_settle(a);   -- dealer peeks
  elsif ot_bj_isbj(array[p1, p2]) then perform ot_bj_settle(a);
  else update ot_bj set phase = 'play' where account_id = a;
  end if;
  return ot_bj_view(a);
end $$;

-- a move: insure, noinsure, hit, stand, double or split. Anything the rules or the coins don't allow is refused.
create or replace function public.ot_bj_act(p_token text, p_action text) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint := ot_account_for(p_token); v_coins bigint; b ot_bj%rowtype; h ot_bj_hands%rowtype; n int; c smallint; ins bigint; aces boolean;
begin
  select coins into v_coins from ot_accounts where id = a for update;
  select * into b from ot_bj where account_id = a for update;
  if not found then raise exception 'ot:bj_state'; end if;
  if b.phase = 'insurance' then
    if p_action not in ('insure', 'noinsure') then raise exception 'ot:bj_state'; end if;
    select * into h from ot_bj_hands where account_id = a and idx = 0;
    if p_action = 'insure' then
      ins := h.bet / 2;
      if ins < 1 or ins > v_coins then raise exception 'ot:bj_coins'; end if;
      update ot_accounts set coins = coins - ins where id = a;
      update ot_bj set insurance = ins, staked = staked + ins where account_id = a;
    end if;
    if ot_bj_isbj(b.dealer) or ot_bj_isbj(h.cards) then perform ot_bj_settle(a);
    else update ot_bj set phase = 'play' where account_id = a;
    end if;
    return ot_bj_view(a);
  end if;
  if b.phase <> 'play' then raise exception 'ot:bj_state'; end if;
  select * into h from ot_bj_hands where account_id = a and idx = b.active;
  select count(*) into n from ot_bj_hands where account_id = a;
  if p_action = 'hit' then
    c := ot_bj_draw(a);
    update ot_bj_hands set cards = cards || c where account_id = a and idx = h.idx returning * into h;
    if ot_bj_total(h.cards) >= 21 then perform ot_bj_next(a); end if;
  elsif p_action = 'stand' then
    perform ot_bj_next(a);
  elsif p_action = 'double' then
    if array_length(h.cards, 1) <> 2 or h.split_aces then raise exception 'ot:bj_state'; end if;
    if h.bet > v_coins then raise exception 'ot:bj_coins'; end if;
    update ot_accounts set coins = coins - h.bet where id = a;
    update ot_bj set staked = staked + h.bet where account_id = a;
    c := ot_bj_draw(a);
    update ot_bj_hands set bet = bet * 2, doubled = true, cards = cards || c where account_id = a and idx = h.idx;
    perform ot_bj_next(a);
  elsif p_action = 'split' then
    if array_length(h.cards, 1) <> 2 or h.split_aces or n >= 4 or ot_bj_val(h.cards[1]) <> ot_bj_val(h.cards[2]) then raise exception 'ot:bj_state'; end if;
    if h.bet > v_coins then raise exception 'ot:bj_coins'; end if;
    update ot_accounts set coins = coins - h.bet where id = a;
    update ot_bj set staked = staked + h.bet where account_id = a;
    aces := h.cards[1] % 13 = 0;
    update ot_bj_hands set idx = -idx - 1000 where account_id = a and idx > h.idx;        -- make room after this hand
    update ot_bj_hands set idx = -idx - 999 where account_id = a and idx < 0;
    insert into ot_bj_hands (account_id, idx, cards, bet, from_split, split_aces) values (a, h.idx + 1, array[h.cards[2]], h.bet, true, aces);
    c := ot_bj_draw(a);
    update ot_bj_hands set cards = array[h.cards[1], c], from_split = true, split_aces = aces where account_id = a and idx = h.idx returning * into h;
    if aces or ot_bj_total(h.cards) = 21 then perform ot_bj_next(a); end if;
  else
    raise exception 'ot:bj_state';
  end if;
  return ot_bj_view(a);
end $$;

-- the website may call these, and nothing else
revoke execute on function public.ot_new_session(bigint), public.ot_account_for(text), public.ot_bj_rand(int), public.ot_bj_shoe(),
  public.ot_bj_val(smallint), public.ot_bj_total(smallint[]), public.ot_bj_soft(smallint[]), public.ot_bj_isbj(smallint[]),
  public.ot_bj_draw(bigint), public.ot_bj_settle(bigint), public.ot_bj_dealer(bigint), public.ot_bj_next(bigint), public.ot_bj_view(bigint)
  from public, anon, authenticated;
grant execute on function public.ot_signup(text, text, bigint), public.ot_login(text, text), public.ot_me(text), public.ot_logout(text),
  public.ot_earn(text, text, int), public.ot_bj_state(text), public.ot_bj_deal(text, bigint), public.ot_bj_act(text, text) to anon, authenticated;
