# SPEC: RTHREAD stage 1 v0.2 — 被覆テスト完成(T15/T25/T36/T37/T38/T40)

> **FLOW NOTE(新フロー・2インスタンス):** 本 v0.2 は **テスト追加のみ**。`request_thread.py` は **1 バイトも変更しない**
> （v0.1a 実測で6本すべて現行コードに green=production 変更不要）。実装インスタンスは新規テストファイルを配置し
> 全テスト green + 骨格 byte 不変 を確認する。commit=Taka。

- **status:** SPEC / 起草: CC-α 2026-07-24 / 正本: `RRI_IMPL_SPEC_v0.1.md` + `RRI_SPEC_MACHINE_v1_1.json`
- **位置づけ:** 初版 rollout stage 1(totals, no accounts)の**残り被覆**。初版 §1 deliverable-3「T14–T18, T25, T36–T40(第1段に要る分)」のうち v0.1a で未達だった分。
- **前提:** v0.1a(`request_thread.py` sha 現行 / commit `02bb767`)が配備・5/5 green・監査 CONSISTENT。
- **スコープ外(初版どおり別段):** I2 load-bearing化=stage②(accounts) / merge・split T16/T17=stage④(transactions) / T39 re-raise=挙動追加。**本 v0.2 に混ぜない。**

## §1. 追加するもの
既存 stage-1 関数の契約を封印する被覆テスト6本。**production code 変更なし**（実測 6/6 green を確認済み）。

| test | 封印する契約 | 対象関数 |
|---|---|---|
| T15 | disposal は4種のみ。REJECTED→reason_code 必須 / MERGED_INTO→target_id 必須 | `dispose_question` |
| T25 | 1接触=1RTHREAD、別接触は別 `RTHREAD-<8hex>` | `open_thread` |
| T36 | projection は決定論(byte一致)で再構成・格納されない(DERIVED) | `project` |
| T37 | 違法遷移は `RThreadIllegalTransition` で reject | `advance_state` |
| T38 | 未提示 OPEN_GAP が残ると RESOLVED を reject | `advance_state` |
| T40 | THREAD_ACCEPTED は全 OPEN_GAP を網羅しないと `RThreadResidualIncomplete` | `accept_thread` |

## §2. テスト(発注側同梱・実装は触らない)
配置: `rri/rri/test_request_thread_stage1_cov.py`（新規・既存 `test_request_thread_stage1.py` は無改変）。

```python
import importlib
import json

import pytest


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("RTHREAD_EVENTS", str(tmp_path / "ev.jsonl"))
    import rri.request_thread as m
    importlib.reload(m)
    return m


@pytest.fixture()
def rt(tmp_path, monkeypatch):
    return _fresh(tmp_path, monkeypatch)


# ── T15 disposal は4種+必須 reason/target ──────────────────────────────────
def test_t15_disposal_types_and_required_fields(rt):
    tid = rt.open_thread("D", "T")
    q = rt.raise_question(tid, "q", "T")
    with pytest.raises(ValueError):
        rt.dispose_question(tid, q, "BOGUS", "T")
    q2 = rt.raise_question(tid, "q2", "T")
    with pytest.raises(ValueError):
        rt.dispose_question(tid, q2, "REJECTED", "T")            # reason_code 欠
    q3 = rt.raise_question(tid, "q3", "T")
    with pytest.raises(ValueError):
        rt.dispose_question(tid, q3, "MERGED_INTO", "T")         # target_id 欠
    rt.dispose_question(tid, q2, "REJECTED", "T", reason_code="dup")
    rt.dispose_question(tid, q3, "MERGED_INTO", "T", target_id="Q-x")


# ── T25 1接触=1RTHREAD ─────────────────────────────────────────────────────
def test_t25_one_contact_one_rthread(rt):
    a = rt.open_thread("DS-A", "T")
    b = rt.open_thread("DS-B", "T")
    assert a != b and a.startswith("RTHREAD-")


# ── T36 projection は決定論・格納されない ───────────────────────────────────
def test_t36_projection_deterministic_derived(rt):
    tid = rt.open_thread("D", "T")
    rt.raise_question(tid, "q", "T")
    assert json.dumps(rt.project(tid), sort_keys=True) == json.dumps(rt.project(tid), sort_keys=True)


# ── T37 違法遷移は reject ───────────────────────────────────────────────────
def test_t37_illegal_transition_rejected(rt):
    tid = rt.open_thread("D", "T")
    with pytest.raises(rt.RThreadIllegalTransition):
        rt.advance_state(tid, "RESOLVED", {}, "T")               # SOFT->RESOLVED は無い


# ── T38 未提示 OPEN_GAP があると RESOLVED reject ────────────────────────────
def test_t38_unpresented_gap_blocks_resolved(rt):
    tid = rt.open_thread("D", "T")
    q = rt.raise_question(tid, "q", "T")
    rt.advance_state(tid, "NARROWING", {"request_type_ok": True, "bind_context_ok": True}, "T")
    rt.dispose_question(tid, q, "OPEN_GAP", "T")                 # in_flight=0 だが未 present
    with pytest.raises(rt.RThreadIllegalTransition):
        rt.advance_state(tid, "RESOLVED",
                         {"all_disposed": True, "suspense_settled": True,
                          "all_gaps_presented": True, "thread_accepted": True}, "T")


# ── T40 THREAD_ACCEPTED は residual 網羅必須 ────────────────────────────────
def test_t40_thread_accepted_exhaustive_residual(rt):
    tid = rt.open_thread("D", "T")
    q = rt.raise_question(tid, "q", "T")
    rt.dispose_question(tid, q, "OPEN_GAP", "T")
    with pytest.raises(rt.RThreadResidualIncomplete):
        rt.accept_thread(tid, [], "human", "T")                 # OPEN_GAP q を列挙せず
    rt.accept_thread(tid, [{"question_id": q, "disposal": "DECLINED"}], "human", "T")
```

## §3. 受入
- `test_request_thread_stage1.py`(5) + `test_request_thread_stage1_cov.py`(6) = **11/11 green**。
- `request_thread.py` は **byte 不変**（production 変更ゼロ。git diff で本体 0 行）。
- 監査ハーネス `audit_rthread_stage1.py` は引き続き **CONSISTENT**（v0.2 で本体無改変のため A/B/C 不変）。

## §4. 完了後
- `CC_IMPL_2026-07-24_RTHREAD_STAGE1_v0.2_BUILT.md` を置く → 設計側が再監査(11/11 + 本体 byte 不変) → CONSISTENT → commit=Taka。
- DE 起票は commit 後 live submit 経由。
