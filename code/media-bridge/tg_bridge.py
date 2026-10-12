#!/usr/bin/env python3
# tg_bridge.py - stdlib-only Telegram remote-control bridge (green channel).
# Long-polls getUpdates through the local proxy and answers a fixed set of
# commands. No third-party dependency on purpose: any Python 3.8+ runs it.
#   token : conf/tg_token.txt   (one line, from @BotFather)
#   owner : conf/tg_owner.txt   (written by the first /start - anti-hijack)
#   proxy : env TG_PROXY, default http://127.0.0.1:10808
# The token file is re-read every loop, so dropping the token in starts the
# bridge without any restart. ASCII-only.

import json
import os
import subprocess
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(BASE, 'conf')
LOGS = os.path.join(BASE, 'logs')
for _d in (CONF, LOGS):
    os.makedirs(_d, exist_ok=True)
LOG = os.path.join(LOGS, 'tg_bridge.log')
PROXY = os.environ.get('TG_PROXY', 'http://127.0.0.1:10808')
API = 'https://api.telegram.org'

HELP = ('media-bridge commands:\n'
        '/ping - alive check\n'
        '/status - git-sync watcher heartbeats on this laptop\n'
        '/help - this text\n'
        '(more commands land as the other channels get configured)')


def log(msg):
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + str(msg)
    try:
        with open(LOG, 'a', encoding='utf-8', errors='replace') as f:
            f.write(line + '\n')
    except Exception:
        pass


def api(token, method, payload=None, timeout=65):
    url = API + '/bot' + token + '/' + method
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data,
                                 headers={'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def send(token, chat_id, text):
    try:
        api(token, 'sendMessage', {'chat_id': chat_id, 'text': text[:3900]})
    except Exception as e:
        log('sendMessage failed: %r' % (e,))


def read_token():
    try:
        with open(os.path.join(CONF, 'tg_token.txt'), 'r',
                  encoding='utf-8') as f:
            parts = f.read().strip().split()
            return parts[0] if parts else None
    except Exception:
        return None


def owner():
    try:
        with open(os.path.join(CONF, 'tg_owner.txt'), 'r',
                  encoding='utf-8') as f:
            v = f.read().strip()
            return int(v) if v else None
    except Exception:
        return None


def watcher_status():
    lines = []
    sd = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'git-sync')
    try:
        for name in sorted(os.listdir(sd)):
            if name.startswith('watch-') and name.endswith('.json'):
                try:
                    with open(os.path.join(sd, name), encoding='utf-8') as f:
                        h = json.load(f)
                    lines.append('%s: %s @ %s (pid %s)' % (
                        name[6:-5], h.get('last_action'),
                        h.get('last_run'), h.get('pid')))
                except Exception:
                    pass
    except Exception:
        pass
    if not lines:
        return 'no watcher state files found'
    return '\n'.join(lines[-14:])


def handle(token, chat, text):
    o = owner()
    if o is None:
        if text.startswith('/start'):
            try:
                with open(os.path.join(CONF, 'tg_owner.txt'), 'w',
                          encoding='utf-8') as f:
                    f.write(str(chat))
                send(token, chat, 'owner claimed. ' + HELP)
                log('owner claimed: %s' % chat)
            except Exception as e:
                log('owner claim failed: %r' % (e,))
        else:
            send(token, chat, 'send /start to claim this bridge')
        return
    if chat != o:
        send(token, chat, 'not authorized')
        return
    t = text.strip().lower()
    if t == '/ping':
        send(token, chat, 'pong from %s at %s' % (
            os.environ.get('COMPUTERNAME', '?'),
            time.strftime('%Y-%m-%d %H:%M:%S')))
    elif t == '/status':
        send(token, chat, 'watchers on %s:\n%s' % (
            os.environ.get('COMPUTERNAME', '?'), watcher_status()))
    elif t.startswith('/help') or t == '/start':
        send(token, chat, HELP)
    else:
        send(token, chat, 'unknown command. ' + HELP)


def main():
    log('tg_bridge start, pid %s, proxy %s' % (os.getpid(), PROXY))
    offset = 0
    off_file = os.path.join(CONF, 'tg_offset.txt')
    try:
        with open(off_file, 'r') as f:
            offset = int(f.read().strip() or 0)
    except Exception:
        offset = 0
    while True:
        token = read_token()
        if not token:
            log('waiting for conf/tg_token.txt ...')
            time.sleep(60)
            continue
        try:
            res = api(token, 'getUpdates',
                      {'offset': offset + 1, 'timeout': 50,
                       'allowed_updates': ['message']}, timeout=65)
            for u in res.get('result', []):
                offset = max(offset, u.get('update_id', 0))
                try:
                    with open(off_file, 'w') as f:
                        f.write(str(offset))
                except Exception:
                    pass
                m = u.get('message') or {}
                chat = (m.get('chat') or {}).get('id')
                text = m.get('text') or ''
                if chat and text:
                    log('msg from %s: %s' % (chat, text[:80]))
                    handle(token, chat, text)
        except Exception as e:
            log('poll failed: %r' % (e,))
            time.sleep(10)


if __name__ == '__main__':
    main()
