-- Obscure Trivia accounts: a username, a password and a coin balance.
-- Paste all of this into the Supabase SQL Editor once and press Run. Running it again is safe.
--
-- How it's kept safe:
--  * The tables can't be read or changed directly by the website (row level security is on and there are no policies).
--    The site can only call the five functions below.
--  * Passwords are stored as bcrypt hashes, never as text. Session tokens are stored as SHA-256 hashes.
--  * 10 wrong passwords in a row lock that username for 15 minutes.
--  * Each coin change has an id, so a change that's sent twice (after a dropped connection) only counts once.

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
  created_at timestamptz not null default now()
);
create table if not exists public.ot_sessions (
  token_hash text primary key,
  account_id bigint not null references public.ot_accounts(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
create table if not exists public.ot_coin_ops (
  op text not null,
  account_id bigint not null references public.ot_accounts(id) on delete cascade,
  delta bigint not null,
  at timestamptz not null default now(),
  primary key (account_id, op)
);
alter table public.ot_accounts enable row level security;
alter table public.ot_sessions enable row level security;
alter table public.ot_coin_ops enable row level security;
revoke all on public.ot_accounts, public.ot_sessions, public.ot_coin_ops from anon, authenticated;

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
    values (u, lower(u), crypt(p_password, gen_salt('bf', 10)), greatest(0, least(coalesce(p_coins, 0), 10000000)))
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

-- add (or take away) coins; the same op id only ever counts once, and the balance never goes below 0
create or replace function public.ot_coins(p_token text, p_delta bigint, p_op text) returns json
language plpgsql security definer set search_path = public, extensions as $$
declare a bigint := ot_account_for(p_token); n bigint;
begin
  if p_op is null or char_length(p_op) not between 6 and 40 or abs(coalesce(p_delta, 0)) > 10000000 then raise exception 'ot:error'; end if;
  insert into ot_coin_ops (op, account_id, delta) values (p_op, a, p_delta) on conflict do nothing;
  if found then
    update ot_accounts set coins = greatest(0, coins + p_delta) where id = a returning coins into n;
  else
    select coins into n from ot_accounts where id = a;
  end if;
  delete from ot_coin_ops where account_id = a and at < now() - interval '30 days';
  return json_build_object('coins', n);
end $$;

create or replace function public.ot_logout(p_token text) returns json
language plpgsql security definer set search_path = public, extensions as $$
begin
  delete from ot_sessions where token_hash = encode(digest(coalesce(p_token, ''), 'sha256'), 'hex');
  return json_build_object('ok', true);
end $$;

-- the website may call these five, and nothing else
revoke execute on function public.ot_new_session(bigint), public.ot_account_for(text) from public, anon, authenticated;
grant execute on function public.ot_signup(text, text, bigint), public.ot_login(text, text), public.ot_me(text),
  public.ot_coins(text, bigint, text), public.ot_logout(text) to anon, authenticated;
