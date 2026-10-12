#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""split_cards.py - cut a narration script into N subtitle CARDS (one TTS clip each).

  python3 split_cards.py script.txt --cards 9 --out-dir work/
    writes work/cards.json   [card text for TTS, one per card]
           work/lines.json   [card text as subtitle rows, rows joined by newline]

Cuts happen only at clause punctuation, card sizes are balanced (minimum of the
largest card), and each card is shown as at most 4 rows of 18 characters.
"""
import argparse, json, os, re, sys
PUN = r'[\s，。！？、；：,.!?;:]'
def n(s): return len(re.sub(PUN, '', s))
def clauses_of(text):
    out, cur = [], ''
    for ch in text:
        if ch in '"“”「」' or ch.isspace():
            continue
        cur += ch
        if ch in '，。！？；：,.!?;:':
            out.append(cur); cur = ''
    if cur.strip(): out.append(cur)
    return out
def partition(cl, k):
    """split clauses into k contiguous cards minimising the largest card (chars)."""
    N = len(cl); w = [n(c) for c in cl]
    pre = [0]
    for x in w: pre.append(pre[-1] + x)
    INF = 10**9
    dp = [[INF]*(N+1) for _ in range(k+1)]; bk = [[0]*(N+1) for _ in range(k+1)]
    dp[0][0] = 0
    for j in range(1, k+1):
        for i in range(1, N+1):
            for p in range(j-1, i):
                if dp[j-1][p] >= INF: continue
                v = max(dp[j-1][p], pre[i]-pre[p])
                if v < dp[j][i]: dp[j][i] = v; bk[j][i] = p
    cuts = []; i = N
    for j in range(k, 0, -1):
        p = bk[j][i]; cuts.append((p, i)); i = p
    return [''.join(cl[a:b]) for a, b in reversed(cuts)]
def rows_of(card, maxrow=18):
    rows, cur = [], ''
    for c in clauses_of(card):
        if cur and n(cur) + n(c) > maxrow:
            rows.append(cur); cur = ''
        cur += c
    if cur: rows.append(cur)
    return rows
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script')
    ap.add_argument('--cards', type=int, required=True)
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    raw = open(a.script, encoding='utf-8').read()
    t = raw.split('\n\n', 1)[1] if ('\n\n' in raw and raw.index('\n\n') < 200) else raw
    cards = partition(clauses_of(t), a.cards)
    rows = ['\n'.join(rows_of(c)) for c in cards]
    for c, r in zip(cards, rows):
        if len(r.split('\n')) > 4:
            raise SystemExit('a card needs more than 4 rows - use more cards: ' + c[:20])
    os.makedirs(a.out_dir, exist_ok=True)
    json.dump(cards, open(os.path.join(a.out_dir, 'cards.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(rows, open(os.path.join(a.out_dir, 'lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%d cards, %d characters' % (len(cards), sum(n(c) for c in cards)))
    for c, r in zip(cards, rows):
        print(n(c), '|'.join(r.split('\n')))


if __name__ == '__main__':
    main()
