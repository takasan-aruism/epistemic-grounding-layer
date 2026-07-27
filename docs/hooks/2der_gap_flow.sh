#!/usr/bin/env bash
# 「文書に書いた Gap が、機械が読む資料に入っているか」を1行で出す。
# 理由: 2026-07-28、CC-α が9件の Gap を CC_*.md に書きながら、資料(JSON)に1件も入れなかった。
#       原因は「手で写す」設計であり、写し忘れを鳴らす計器が無かった。
# ★方針: 忘れないようにするのではなく、忘れたら見えるようにする。
# ★注意: 資料の id は G-01(0詰め)と G-20(0詰めなし)が混在している。数値で正規化して比べる。
#         初版は 0 詰めの違いで 5 件を誤検出した(運用方針 §4-15: 0 でない値はまず自分を疑う)。
set -uo pipefail
cd /home/takasan/egl 2>/dev/null || { echo "Gap の流れ: 判定不能(egl に入れない)"; exit 0; }
timeout 20 python3 - <<'PY' 2>/dev/null || echo "Gap の流れ: 判定不能"
import json, re, glob, os

try:
    d = json.load(open("docs/2DER_EXECUTION_ARCHITECTURE.json"))
except Exception:
    print("Gap の流れ: 判定不能(資料を読めない)"); raise SystemExit

def norm(s):
    m = re.match(r"G-0*(\d+)$", str(s).strip())
    return "G-%d" % int(m.group(1)) if m else None

in_json = {n for g in d.get("gaps", []) if isinstance(g, dict) and (n := norm(g.get("id")))}

in_docs = {}
for p in glob.glob("docs/CC_*.md"):
    try:
        s = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in set(re.findall(r"\bG-\d+\b", s)):
        # G-9999 は自己試験用の予約 id。文書がそれを引用しても数えない
        # (2026-07-28: 自分が試験の様子を文書に書いたら、計器が自分を数えた。本日5回目の自己一致)
        if (n := norm(m)) and n != "G-9999":
            in_docs.setdefault(n, []).append(os.path.basename(p))

missing = sorted(set(in_docs) - in_json, key=lambda x: int(x.split("-")[1]))
if not missing:
    print(f"Gap の流れ: 文書の Gap は全て資料に在る（資料 {len(in_json)} 件）")
else:
    head = ", ".join(missing[:6]) + (" ほか" if len(missing) > 6 else "")
    first = sorted(in_docs[missing[0]])[0]
    print(f"Gap の流れ: ★資料に無い Gap {len(missing)} 件 — {head}（{missing[0]} の初出: {first}）")
PY
