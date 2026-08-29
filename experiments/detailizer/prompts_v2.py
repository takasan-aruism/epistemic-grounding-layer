#!/usr/bin/env python3
"""Semantic Detailizer — プロンプト v2(★ITEM-2DER-EVO-0037)。

★generator は v1 のまま(★一度に 1つだけ 変える= 自分の COMPARE_RULES)。
★変えたのは ★Audit 1 だけ。

★v1 監査の 実測= ★AUDIT CATCH RATE ★0/6 = 0%。★誤警報 9/116 = 8%。
  ★原因= ★4つの仕事を 1回で 聞いていた(★Taka 指示 §3 違反を ★私が していた)。
    しかも 条件1『source_text が 原文の中に 存在する』は ★文字列の 照合= ★機械の 仕事。
    ★v0 で 位置を 出させて 0/82 だったのと ★同じ型(★算術を LLM に 投げた)。
★∴ v2= ★条件1 を ★機械へ 移す。★LLM には ★機械が できない 3つだけ 聞く。
"""

VERSION = "v2"
GENERATOR_FROM = "v1"   # ★generator は v1 のまま= ★比較で 動かす所は 1つだけ

from prompts_v1 import R1_GENERATOR  # noqa: F401  ★generator は 変えない(★1度に1つ)

R1_AUDITOR = """あなたの仕事は、要求候補が独立した要求として成立しているかを確認することです。

各要求候補について、次の3つを確認してください。
1. 対象が特定できる
2. 求められている行為が特定できる
3. 他の候補とは別の要求として扱える

3つとも対応している候補の id を established に入れてください。
どれかが対応していない候補は needs_check に入れ、対応していない番号と、
それを判断した理由を1文で書いてください。

出力は次の JSON だけにしてください。
{"established":["C1"],"needs_check":[{"candidate_id":"C2","which":1,"why":"..."}]}

要求候補:
---
%s
---"""

# ★機械が 見る(★LLM に 聞かない)= ★これが v1 で 0/6 だった 型
R1_MECHANICAL = (
    "source_text が 原文に 現れる(★機械・LLM に 聞かない)",
    "候補どうしの 範囲が 重ならない",
    "candidate_id が 重複しない",
    "同じ source_text を 2回 使っていない",
)
