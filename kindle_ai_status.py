#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI コーディング状況の取得 (Claude クォータ / Claude Code セッション)

設計方針: 正確性より安定性
- すべての関数は例外を投げない（失敗時は state を持つ dict を返す）
- クォータ API は「最善努力」: キャッシュ + バックオフ。トークンのリフレッシュはしない
- API が使えなくても、ローカル JSONL から 5h のトークン量を集計して表示できる
- ファイル走査は件数・サイズに上限を設ける（cron の実行時間を伸ばさない）
"""

import json
import time
import logging
import datetime
from pathlib import Path

import requests

CREDENTIALS_PATH = Path.home() / '.claude' / '.credentials.json'
PROJECTS_DIR = Path.home() / '.claude' / 'projects'
CACHE_PATH = Path.home() / '.kindle_monitor_claude_cache.json'

USAGE_URL = 'https://api.anthropic.com/api/oauth/usage'
HTTP_TIMEOUT = 5
REFRESH_INTERVAL_S = 20 * 60      # 成功後に再取得するまでの最短間隔
MIN_BACKOFF_S = 30 * 60           # 429 等の失敗後に待つ最短時間
AUTH_BACKOFF_S = 60 * 60          # トークン無効時の再確認間隔
STALE_LIMIT_S = 12 * 3600         # これより古いキャッシュ値は表示しない

MAX_FILES = 60                    # 走査する JSONL の上限
TAIL_BYTES = 256 * 1024           # 各ファイルの末尾から読む量
WINDOW_5H_S = 5 * 3600


# ---------------------------------------------------------------- cache
def _load_cache():
    try:
        with open(CACHE_PATH, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache):
    try:
        tmp = CACHE_PATH.with_suffix('.tmp')
        with open(tmp, 'w') as f:
            json.dump(cache, f)
        tmp.replace(CACHE_PATH)
    except Exception as e:
        logging.warning("Claude cache save error: " + str(e))


# ---------------------------------------------------------------- quota
def _read_token():
    """(token, state)。期限切れ・欠落時は token=None。リフレッシュはしない。"""
    try:
        if not CREDENTIALS_PATH.exists():
            return None, 'auth'
        with open(CREDENTIALS_PATH, 'r') as f:
            oauth = json.load(f).get('claudeAiOauth', {})
        token = oauth.get('accessToken')
        exp_ms = oauth.get('expiresAt', 0)
        if not token:
            return None, 'auth'
        if exp_ms and time.time() * 1000 >= exp_ms:
            return None, 'auth'
        return token, 'ok'
    except Exception as e:
        logging.warning("Claude credentials read error: " + str(e))
        return None, 'auth'


def _parse_reset(value):
    """resets_at (ISO8601) → ローカル時刻の 'HH:MM' / 'M/D'。失敗時は ''。"""
    try:
        dt = datetime.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        local = dt.astimezone()
        return local
    except Exception:
        return None


def _pct(block):
    try:
        return int(round(float(block.get('utilization'))))
    except Exception:
        return None


def get_claude_quota(enabled=True):
    """
    戻り値: {
      'five_hour': int|None, 'seven_day': int|None,
      'five_reset': 'HH:MM'|'', 'seven_reset': 'M/D'|'',
      'state': 'live' | 'cached' | 'auth' | 'limited' | 'error' | 'off',
      'age_min': キャッシュ値の経過分 (live は 0)
    }
    """
    empty = {'five_hour': None, 'seven_day': None, 'five_reset': '',
             'seven_reset': '', 'state': 'off', 'age_min': 0}
    if not enabled:
        return empty
    try:
        now = time.time()
        cache = _load_cache()
        good = cache.get('last_good') or {}
        good_age = now - good.get('ts', 0) if good else None

        def from_cache(state):
            if good and good_age is not None and good_age < STALE_LIMIT_S:
                out = dict(good.get('data', empty))
                out['state'] = 'cached' if state in ('live', 'cached') else state
                out['age_min'] = int(good_age // 60)
                return out
            out = dict(empty)
            out['state'] = state
            return out

        # まだ再取得する時刻でなければキャッシュを返す
        if now < cache.get('next_try', 0):
            return from_cache(cache.get('last_state', 'cached'))

        token, tstate = _read_token()
        if not token:
            cache['next_try'] = now + AUTH_BACKOFF_S
            cache['last_state'] = 'auth'
            _save_cache(cache)
            return from_cache('auth')

        headers = {
            'Authorization': 'Bearer ' + token,
            'anthropic-version': '2023-06-01',
            'anthropic-beta': 'oauth-2025-04-20',
            'Accept': 'application/json',
        }
        resp = requests.get(USAGE_URL, headers=headers, timeout=HTTP_TIMEOUT)
        logging.info("Claude usage API: HTTP " + str(resp.status_code))

        if resp.status_code == 200:
            data = resp.json()
            fh, sd = data.get('five_hour') or {}, data.get('seven_day') or {}
            fr, sr = _parse_reset(fh.get('resets_at')), _parse_reset(sd.get('resets_at'))
            result = {
                'five_hour': _pct(fh), 'seven_day': _pct(sd),
                'five_reset': fr.strftime('%H:%M') if fr else '',
                'seven_reset': (str(sr.month) + '/' + str(sr.day)) if sr else '',
                'state': 'live', 'age_min': 0,
            }
            cache['last_good'] = {'ts': now, 'data': result}
            cache['next_try'] = now + REFRESH_INTERVAL_S
            cache['last_state'] = 'cached'
            _save_cache(cache)
            return result

        # 失敗: 状態に応じてバックオフ
        if resp.status_code == 429:
            try:
                retry_after = int(resp.headers.get('Retry-After', 0))
            except Exception:
                retry_after = 0
            wait, state = max(retry_after, MIN_BACKOFF_S), 'limited'
        elif resp.status_code in (401, 403):
            wait, state = AUTH_BACKOFF_S, 'auth'
        else:
            wait, state = MIN_BACKOFF_S, 'error'
        cache['next_try'] = now + wait
        cache['last_state'] = state
        _save_cache(cache)
        return from_cache(state)
    except Exception as e:
        logging.warning("Claude quota error: " + str(e))
        try:
            cache = _load_cache()
            cache['next_try'] = time.time() + MIN_BACKOFF_S
            cache['last_state'] = 'error'
            _save_cache(cache)
        except Exception:
            pass
        return dict(empty, state='error')


# ---------------------------------------------------------------- local logs
def _recent_jsonl(max_age_s):
    """mtime が新しい順に JSONL を返す（上限あり）。"""
    files = []
    try:
        cutoff = time.time() - max_age_s
        for p in PROJECTS_DIR.glob('*/*.jsonl'):
            try:
                m = p.stat().st_mtime
                if m >= cutoff:
                    files.append((m, p))
            except Exception:
                continue
    except Exception:
        return []
    files.sort(key=lambda x: x[0], reverse=True)
    return files[:MAX_FILES]


def _tail_lines(path):
    """ファイル末尾 TAIL_BYTES を行リストで返す（先頭の欠けた行は捨てる）。"""
    with open(path, 'rb') as f:
        f.seek(0, 2)
        size = f.tell()
        start = max(0, size - TAIL_BYTES)
        f.seek(start)
        data = f.read()
    lines = data.split(b'\n')
    if start > 0 and lines:
        lines = lines[1:]
    return lines


def _parse_ts(value):
    try:
        return datetime.datetime.fromisoformat(str(value).replace('Z', '+00:00')).timestamp()
    except Exception:
        return None


def _short_model(model):
    m = str(model or '')
    if m.startswith('claude-'):
        m = m[len('claude-'):]
    return m or '?'


def get_local_tokens_5h():
    """直近5時間の assistant 出力+入力(新規)+キャッシュ作成トークン概算。失敗時 None。
    ※末尾 TAIL_BYTES のみ走査するため下限値（目安）。
    """
    try:
        now = time.time()
        total = 0
        seen = set()
        for _, path in _recent_jsonl(WINDOW_5H_S):
            for raw in _tail_lines(path):
                if b'"usage"' not in raw:
                    continue
                try:
                    j = json.loads(raw)
                except Exception:
                    continue
                if j.get('type') != 'assistant':
                    continue
                ts = _parse_ts(j.get('timestamp'))
                if ts is None or now - ts > WINDOW_5H_S:
                    continue
                msg = j.get('message') or {}
                key = msg.get('id') or (path.name, j.get('timestamp'))
                if key in seen:
                    continue
                seen.add(key)
                u = msg.get('usage') or {}
                total += int(u.get('input_tokens') or 0) \
                    + int(u.get('output_tokens') or 0) \
                    + int(u.get('cache_creation_input_tokens') or 0)
        return total
    except Exception as e:
        logging.warning("Local token scan error: " + str(e))
        return None


def get_ai_sessions(limit=4):
    """直近の Claude Code セッション。
    各要素: {'project', 'model', 'ctx', 'age_min', 'status'}
      ctx = 最後の assistant ターンの文脈量（input+cache）トークン
      status = 'active'(<10分) / 'idle'(<60分) / 'done'
    会話本文は読み取らない。失敗時は空リスト。
    """
    sessions = []
    try:
        now = time.time()
        for mtime, path in _recent_jsonl(24 * 3600):
            if len(sessions) >= limit:
                break
            try:
                project, model, ctx = '', '', 0
                for raw in reversed(_tail_lines(path)):
                    if not raw.strip():
                        continue
                    try:
                        j = json.loads(raw)
                    except Exception:
                        continue
                    if not project and j.get('cwd'):
                        project = Path(str(j['cwd'])).name
                    if not model and j.get('type') == 'assistant':
                        msg = j.get('message') or {}
                        if msg.get('model'):
                            model = msg['model']
                            u = msg.get('usage') or {}
                            ctx = int(u.get('input_tokens') or 0) \
                                + int(u.get('cache_read_input_tokens') or 0) \
                                + int(u.get('cache_creation_input_tokens') or 0)
                    if project and model:
                        break
                if not project:
                    project = path.parent.name.split('-')[-1] or '?'
                age = now - mtime
                status = 'active' if age < 600 else ('idle' if age < 3600 else 'done')
                sessions.append({
                    'project': project, 'model': _short_model(model),
                    'ctx': ctx, 'age_min': int(age // 60), 'status': status,
                })
            except Exception as e:
                logging.warning("Session parse error: " + str(e))
                continue
    except Exception as e:
        logging.warning("AI sessions error: " + str(e))
    return sessions


def fmt_tokens(n):
    """1234 → '1k', 1234567 → '1.2M'。None は '--'。"""
    if n is None:
        return '--'
    if n >= 1_000_000:
        return '%.1fM' % (n / 1_000_000)
    if n >= 1000:
        return str(int(n / 1000)) + 'k'
    return str(int(n))
