#!/usr/bin/env python3
"""★Monitor が 島津で 使った 肯定版の 設問を ★10テーマで 回す(★ITEM-2DER-EVO-0054)。
★設定は Monitor と 同じ= Qwen3.6-35B-A3B / temperature=0 / thinking off / ★max_tokens は 送らない。
"""
import json, os, re, sys, time, urllib.request
MY = "/tmp/claude-1000/-home-takasan/b2930a6c-e4f7-42f6-82da-6d48a6998fb7/scratchpad"
D = MY + "/fact"
PRE = open(D + "/preamble.txt", encoding="utf-8").read()
INSTR = open(D + "/instr_pos.txt", encoding="utf-8").read()


def run(cid, src, tag=""):
    prompt = PRE + "【SOURCE】\n" + src + "\n\n" + INSTR
    body = {"model": "Qwen3.6-35B-A3B",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True, "stream_options": {"include_usage": True},
            "temperature": 0, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request("http://127.0.0.1:8005/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    out, finish, usage, t0 = [], None, None, time.time()
    try:
        for raw in urllib.request.urlopen(req, timeout=3600):
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            p = line[5:].strip()
            if p == "[DONE]":
                break
            try:
                ev = json.loads(p)
            except Exception:
                continue
            if ev.get("usage"):
                usage = ev["usage"]
            for ch in ev.get("choices") or []:
                piece = (ch.get("delta") or {}).get("content")
                if piece:
                    out.append(piece)
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
    except Exception as e:
        finish = "EXCEPTION:%s" % type(e).__name__
    txt = "".join(out)
    open("%s/out/%s%s.txt" % (D, cid, tag), "w", encoding="utf-8").write(txt)
    return {"finish": finish, "usage": usage, "chars": len(txt),
            "sec": round(time.time() - t0, 1), "prompt_chars": len(prompt)}


if __name__ == "__main__":
    os.makedirs(D + "/out", exist_ok=True)
    cases = json.load(open(D + "/cases.json"))
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 16464   # ★島津と 同じ 長さに 揃える
    res = {}
    for c in cases:
        src = open("%s/src/%s.txt" % (D, c["id"]), encoding="utf-8", errors="replace").read()[:lim]
        r = run(c["id"], src)
        r["theme"] = c["theme"]; r["type"] = c["type"]; r["src_chars"] = len(src)
        res[c["id"]] = r
        print("  %-4s %-22s %-10s %6d字 %5.0f秒 出力%6d字" % (
            c["id"], c["theme"][:22], r["finish"], r["src_chars"], r["sec"], r["chars"]))
    json.dump(res, open(D + "/run10.json", "w"), ensure_ascii=False)
