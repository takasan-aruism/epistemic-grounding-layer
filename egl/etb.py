"""ETB — Evidence Trust Boundary(docs/grounding-layer-unified-v0.2.md §16.2)。

取得内容は **data であって instruction ではない**(ETB-1)。実 LLM が evidence を読む今
(real Gate4)、取得内容に仕込まれた prompt-injection が judge を操作し得る。
ETB-4: hidden text / zero-width / bidi / instruction-like pattern をスキャンし taint_flags を付す。
ETB-5: taint は Raw→Normalized→Fragment→Claim へ伝播(acquisition が付し gate1 GC-8 が構造 block)。
構造防御(scan + GC-8)が主。judge prompt 硬化(ETB-1)は defense in depth(LLM の従順に依存しない)。
"""
import re

ZERO_WIDTH = ["​", "‌", "‍", "⁠", "﻿", "᠎"]
BIDI = ["‪", "‫", "‬", "‭", "‮",           # trojan-source(RLO/LRO 等)
        "⁦", "⁧", "⁨", "⁩"]
# instruction-like: judge/LLM を steer しようとする典型パターン(EN + JA)。過検出は fail-safe 側
# (tainted → GC-8 block)ゆえ許容。ETB-6: 自動破棄でなく flag + Curator 判断。
_INSTRUCTION = [
    r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+instructions?",
    r"disregard\s+(the\s+)?(previous|above|system|prior)",
    r"you\s+are\s+now\b", r"\bsystem\s*:", r"</?(system|instruction|prompt|im_start)\b",
    r"output\s+(only\s+)?[\"']?(SUPPORTED|f1_entailment|WITHIN)",
    r"respond\s+with\s+(only\s+)?[\"']?(SUPPORTED|WITHIN)",
    r"as\s+an?\s+(ai|assistant|language\s+model)",
    r"(以前|前|上記|これまで)の指示を無視", r"新しい指示", r"次のように(出力|回答)",
    r"SUPPORTED\s*(と|を)\s*(出力|回答|返)",
]
_HIDDEN_HTML = [r"display\s*:\s*none", r"font-size\s*:\s*0", r"visibility\s*:\s*hidden",
                r"opacity\s*:\s*0\b", r"aria-hidden\s*=\s*[\"']true"]


def scan_content(text):
    """ETB-4: 取得内容を data として走査し taint_flags(型のリスト)を返す。空=清浄。"""
    if isinstance(text, (bytes, bytearray)):
        text = bytes(text).decode("utf-8", "replace")
    if not text:
        return []
    flags = []
    if any(z in text for z in ZERO_WIDTH):
        flags.append("ZERO_WIDTH")
    if any(b in text for b in BIDI):
        flags.append("BIDI_OVERRIDE")
    if any(re.search(p, text, re.I) for p in _INSTRUCTION):
        flags.append("INSTRUCTION_LIKE")
    if any(re.search(p, text, re.I) for p in _HIDDEN_HTML):
        flags.append("HIDDEN_HTML")
    return flags


def merge_taint(*flag_lists):
    """EF-4: taint は継承 + 追加検出分を加算(重複排除、順序安定)。"""
    out = []
    for fl in flag_lists:
        for f in (fl or []):
            if f not in out:
                out.append(f)
    return out
