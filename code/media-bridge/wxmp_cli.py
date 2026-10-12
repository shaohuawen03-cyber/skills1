#!/usr/bin/env python3
# wxmp_cli.py - WeChat Official Account (MP) mini-CLI (green channel:
# official API). Pure requests, no wechatpy: the published wechatpy wheel
# (1.8.18) does not expose draft/freepublish components, so this talks to
# the REST endpoints directly:
#   token    GET  /cgi-bin/token
#   material POST /cgi-bin/material/add_material   (multipart, cover image)
#   draft    POST /cgi-bin/draft/add               (JSON)
#   publish  POST /cgi-bin/freepublish/submit      (JSON)
# Calls api.weixin.qq.com DIRECTLY (domestic, fast, no proxy). Make sure
# this machine's public IP is in the MP admin IP whitelist, or token
# fetch returns errcode 40164.
# Config: conf/wxmp.txt with two lines:  appid=...  secret=...
# ASCII-only.

import os
import re
import sys

import requests

API = 'https://api.weixin.qq.com'
BASE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(BASE, 'conf')


def load_cfg():
    cfg = {}
    p = os.path.join(CONF, 'wxmp.txt')
    if not os.path.exists(p):
        return None
    try:
        for ln in open(p, encoding='utf-8'):
            ln = ln.strip()
            if '=' in ln and not ln.startswith('#'):
                k, v = ln.split('=', 1)
                cfg[k.strip()] = v.strip()
    except Exception:
        return None
    return cfg


def cfg_or_die():
    cfg = load_cfg() or {}
    if not cfg.get('appid') or not cfg.get('secret'):
        print('config missing or incomplete:')
        print('  fill conf/wxmp.txt with two lines: appid=... and secret=...')
        print('  (MP admin console -> settings & development -> developer info)')
        sys.exit(2)
    return cfg


def get_token(cfg):
    r = requests.get(API + '/cgi-bin/token', params={
        'grant_type': 'client_credential',
        'appid': cfg['appid'],
        'secret': cfg['secret'],
    }, timeout=20)
    j = r.json()
    if 'access_token' not in j:
        raise RuntimeError('token response: %s' % j)
    return j['access_token']


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def md_to_html(md):
    out = []
    for block in md.split('\n\n'):
        b = block.strip()
        if not b:
            continue
        m = re.match(r'^(#{1,3})\s+(.*)', b)
        if m:
            sizes = {1: '20px', 2: '17px', 3: '15px'}
            out.append('<p style="font-size:%s;font-weight:bold;'
                       'margin:16px 8px 8px;color:#222;">%s</p>' % (
                           sizes[len(m.group(1))], esc(m.group(2))))
        else:
            body = ''.join(('<br/>' + esc(ln) if i else esc(ln))
                           for i, ln in enumerate(b.split('\n')))
            out.append('<p style="font-size:15px;line-height:1.75;'
                       'margin:8px;color:#333;">%s</p>' % body)
    return ''.join(out)


def thumb_id():
    try:
        with open(os.path.join(CONF, 'wxmp_thumb.txt')) as f:
            return f.read().strip() or None
    except Exception:
        return None


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else 'check'
    if cmd == 'check':
        cfg = cfg_or_die()
        try:
            t = get_token(cfg)
            print('access_token OK (len %d) - appid reachable' % len(t))
            print('note: draft/publish need a CERTIFIED subscription/'
                  'service account; a test (sandbox) account only proves'
                  ' the token path.')
            return 0
        except Exception as e:
            print('token fetch FAILED: %s' % e)
            print('errcode 40164 => add this machine\'s public IP to the '
                  'MP admin IP whitelist and retry')
            return 1
    if cmd == 'upload-thumb':
        cfg = cfg_or_die()
        t = get_token(cfg)
        with open(args[1], 'rb') as f:
            r = requests.post(API + '/cgi-bin/material/add_material',
                              params={'access_token': t, 'type': 'image'},
                              files={'media': f}, timeout=60)
        j = r.json()
        if 'media_id' not in j:
            print('upload failed: %s' % j)
            return 1
        with open(os.path.join(CONF, 'wxmp_thumb.txt'), 'w') as f:
            f.write(j['media_id'])
        print('cover uploaded, media_id =', j['media_id'])
        return 0
    if cmd == 'draft':
        cfg = cfg_or_die()
        title, mdfile = args[1], args[2]
        mid = thumb_id()
        if not mid:
            print('no cover set - first run: '
                  'wxmp_cli.py upload-thumb <cover.jpg>')
            return 2
        t = get_token(cfg)
        html = md_to_html(open(mdfile, encoding='utf-8').read())
        r = requests.post(API + '/cgi-bin/draft/add',
                          params={'access_token': t},
                          json={'articles': [{
                              'title': title,
                              'content': html,
                              'thumb_media_id': mid,
                              'need_open_comment': 0,
                              'only_fans_can_comment': 0,
                          }]}, timeout=30)
        j = r.json()
        if 'media_id' not in j:
            print('draft failed: %s' % j)
            return 1
        print('draft created, media_id =', j['media_id'])
        return 0
    if cmd == 'publish':
        cfg = cfg_or_die()
        t = get_token(cfg)
        r = requests.post(API + '/cgi-bin/freepublish/submit',
                          params={'access_token': t},
                          json={'media_id': args[1]}, timeout=30)
        j = r.json()
        print('publish response:', j)
        return 0 if j.get('errcode') in (0, None) else 1
    print('usage: check | upload-thumb <img> | draft <title> <md> | '
          'publish <media_id>')
    return 2


if __name__ == '__main__':
    sys.exit(main())
