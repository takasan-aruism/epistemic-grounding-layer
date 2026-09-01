#!/usr/bin/env python3
"""★SOURCE から FACT カードを 作る(★段③後段 ／ ★ITEM-2DER-EVO-0059 の LLM 分)。

★★私の 受入(★RRI が 出し ★MGR が 割った・逐語)=
  (a)★FACT は ★台帳へ 書かない
  (b)★CONTENT 由来と INDEX 由来を ★同じ棚に 置かない
  (c)★`F001` は ★projection 内の ローカル識別子(★恒久IDに しない)
  (d)★索引・目次・リンク集に 当たった時に ★★作らずに 返す(★私が EVO-0058 で 自分で 名指しした 範囲)

★★作らない もの= ★新台帳 0 ／ 新ID族 0 ／ 新state 0 ／ 新語彙 0 ／ ★★判別器 0。
  ★CONTENT か INDEX かは ★ACQUISITION の 返りに 在る(★受入 (a)『OBS- の id と CONTENT/INDEX の 別 2つ』)
  ∴ ★私は ★受け取るだけ= ★自分で 判別しない。

★★設問の 正本= `egl/experiments/fact10/prompt/`(★ATOMIC-FACT ／ EVO-0058 で 保存済)。
★★呼び方の 実測値= temperature 0 ／ thinking off ／ ★max_tokens は 送らない ／ 並列8。
"""
import json, os, time, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
PROMPT_DIR = os.path.join(D, "..", "fact10", "prompt")
ENDPOINT = "http://127.0.0.1:8005/v1/chat/completions"
MODEL = "Qwen3.6-35B-A3B"

# ★ACQUISITION が 返す 語。★私は 増やさない(★新語彙 0)。
CONTENT, INDEX = "CONTENT", "INDEX"

# ★作らずに 返す 理由(★EVO-0058 の 実測から。★私が 決め直して いない)
WHY_INDEX = ("★索引は ATOMIC-FACT の 成立範囲の 外(EVO-0058 実測)= "
             "★プロトコルは 守られる(完走 3/3・引用 31/31)が ★出るのは 所在カードだけ"
             "(★21件中 16件= 76% が has_url/title/publisher)")


def _prompt(text):
    pre = open(os.path.join(PROMPT_DIR, "preamble.txt"), encoding="utf-8").read()
    ins = open(os.path.join(PROMPT_DIR, "instr_pos.txt"), encoding="utf-8").read()
    return pre + "【SOURCE】\n" + text + "\n\n" + ins


def _call(text, timeout=1800):
    body = {"model": MODEL, "messages": [{"role": "user", "content": _prompt(text)}],
            "temperature": 0, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason")


def _parse(raw):
    """★返りを 開く。-> (カードの list, 作らなかった分の list) ／ 取れなければ (None, None)。

    ★★2026-09-01 の 実測で 直した= ★ATOMIC-FACT の 返りは
      `{"facts":[...], "residual":[...]}` の ★2つの 配列を 持つ
      ∴ ★『最初の [ から 最後の ] まで』で 切ると ★2つを 跨いで 壊れる(★実測 9,815字で 発火)。
    ∴ ★★まず 丸ごと JSON として 開く。★切り出しは 最後の 手段。
    ★★`residual` は 捨てない= ★『作らなかった分』は ★私の 受入(作らずに返す)の 証拠。
    """
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    obj = None
    try:
        obj = json.loads(s)
    except Exception:
        for a, b in (("{", "}"), ("[", "]")):
            i, j = s.find(a), s.rfind(b)
            if i >= 0 and j > i:
                try:
                    obj = json.loads(s[i:j + 1]); break
                except Exception:
                    continue
    if obj is None:
        return None, None
    if isinstance(obj, list):
        return obj, []
    if isinstance(obj, dict):
        for k in ("facts", "cards", "FACT", "items"):
            if isinstance(obj.get(k), list):
                return obj[k], (obj.get("residual") if isinstance(obj.get("residual"), list) else [])
    return None, None


def project(source, call=None):
    """★1つの SOURCE を FACT カードへ 落とす。-> dict

    source= {"obs_id": "OBS-…", "source_kind": "CONTENT"|"INDEX", "text": "…"}
    ★★INDEX は ★呼ばずに 返す= ★GPU も 使わない。
    """
    obs = source.get("obs_id")
    kind = source.get("source_kind")
    base = {"obs_id": obs, "source_kind": kind, "cards": [], "called_llm": False}

    if kind == INDEX:
        base.update({"made": False, "why": WHY_INDEX})
        return base
    if kind != CONTENT:
        base.update({"made": False, "why": "★source_kind が %r= ★私の 知る 語では ない"
                                           "(★受け取る 語は CONTENT / INDEX の 2つ)" % (kind,)})
        return base

    t0 = time.perf_counter()
    raw, finish = (call or _call)(source.get("text") or "")
    base["called_llm"] = True
    base["finish_reason"] = finish
    base["秒"] = round(time.perf_counter() - t0, 1)
    got, residual = _parse(raw)
    base["作らなかった分"] = residual or []
    if got is None:
        base.update({"made": False, "why": "★JSON が 取れなかった(finish=%s)= ★作らない" % finish})
        return base

    cards = []
    for n, c in enumerate(got, 1):
        if not isinstance(c, dict):
            continue
        d = dict(c)
        # ★(c) ローカル識別子= ★この projection の 中でだけ 通る。★恒久IDに しない
        d["local_id"] = "F%03d" % n
        d["obs_id"] = obs                      # ★引く鍵は (obs_id, local_id) の 対
        cards.append(d)
    base.update({"made": bool(cards), "cards": cards})
    if not cards:
        base["why"] = "★カードが 0件= ★作らない"
    return base


class Shelf:
    """★(b) CONTENT 由来と INDEX 由来を ★同じ棚に 置かない。

    ★棚は source_kind で 分ける= ★混ざる 道が 構造として 無い。
    ★★台帳へは 書かない= ★この器は ★記憶の 上にしか 存在しない(★保存の 口を 持たない)。
    """

    def __init__(self):
        self.shelves = {CONTENT: [], INDEX: []}
        self.refused = []

    def add(self, result):
        k = result.get("source_kind")
        if k not in self.shelves:
            self.refused.append(result); return "REFUSED_UNKNOWN_KIND"
        if not result.get("made"):
            self.refused.append(result); return "REFUSED_NOT_MADE"
        self.shelves[k].extend(result["cards"])
        return "SHELVED"

    def summary(self):
        return {"CONTENT のカード": len(self.shelves[CONTENT]),
                "INDEX のカード": len(self.shelves[INDEX]),
                "作らずに返した": len(self.refused),
                "★棚が混ざっていない": all(
                    c.get("obs_id") is not None for c in self.shelves[CONTENT])}
