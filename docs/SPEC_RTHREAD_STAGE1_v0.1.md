# SPEC: RTHREAD stage 1 v0.1 — 骨格＋不変テスト(T14/T18・保存則核)

> **FLOW NOTE — 新フロー(ANCHOR §1-1・Taka裁定 2026-07-24: RRI も実装インスタンス):**
> 実装インスタンス(Monitor `b0718vzrg`)が **`rri/rri/request_thread.py`** を working tree に直接実装し、
> **`rri/rri/test_request_thread_stage1.py`**(§3 発注側同梱)を green にする。**別 repo=rri(twoderでない)**。
> 実装契約: §2 骨格の `<<<FILL>>>` 以外は 1 バイトも変えない(定数 TRANSITIONS/EVENT_TYPES・例外・_mint 含む)。§3 テストは触らない。
> event stream 置き場 `rri/rri/rthread_events.jsonl` は **追跡下**(裁定21 達成前提)。commit=Taka。
> 起草: CC-α。正本=`RRI_IMPL_SPEC_v0.1.md` + `RRI_SPEC_MACHINE_v1_1.json`(複式保存則 I1/I2 は Taka 訂正 2026-07-24)。

- **status:** SPEC / 起草: CC-α 2026-07-24 / 正本: `RRI_IMPL_SPEC_v0.1.md`
- **★3 クローズ証跡(precondition):** commit `38d1988`(death#2/#4/#6/#7 closed)
- **スコープ:** 成果物3 v0.1 = **保存則の核**(`check_conservation`/`project`)＋ T14/T18。他の関数は骨格に署名を固定するが本体 FILL。残テスト(T15-17/25/36-40)は v0.2。

## §1. 直す/作るもの

複式保存則(**Taka 訂正 2026-07-24**)を machine で成立させる:
- **I1(処分次元):** `raised_total == resolved + open_gap + rejected + merged + in_flight_count`
- **I2(科目次元):** `sum(per_account_balances.values()) == raised_total`(全問い1 account)
両方が毎遷移で成立。**account_id default=`DEFAULT`(RESOLVED可) / `UNCLASSIFIED`=分類保留(RESOLVED不可・出口 OPEN_GAP/REJECTED/MERGED)** — `ADJUDICATION_SENSITIVE: 16` ＋ account_id の stage1 適用(CC-α 設計判断・Taka レビュー対象)。

## §2. 骨格 —— 完全ファイル(`<<<FILL>>>` 以外は bytes 一致対象)

配置: `rri/rri/request_thread.py`。FILL は各関数本体(11箇所)。定数・例外・`_mint`・docstring は不変。

```python
"""RTHREAD stage 1 — 依頼ID(1接触=1スレッド)の帳簿。複式保存則(I1 処分次元 / I2 科目次元)+状態+projection。

sole writer of rthread_events.jsonl。first-class store は event stream のみ(architecture)。
RTHREAD は projection(fat record を作らない=裁定#25)。信頼フィールドは呼出側封印(G-1)。
本モジュールは stdlib 以外を import しない。
"""
from __future__ import annotations

import hashlib
import json
import os

# event stream 置き場(テストは環境変数 RTHREAD_EVENTS で throwaway 隔離)。sole writer。
_EVENTS = os.environ.get("RTHREAD_EVENTS",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "rthread_events.jsonl"))

EVENT_TYPES = ("THREAD_OPENED", "QUESTION_RAISED", "QUESTION_DISPOSED", "NARROWED",
               "EXPANDED", "GAP_PRESENTED", "HUMAN_REPLIED", "STATE_ADVANCED", "THREAD_ACCEPTED")
STATES = ("SOFT", "NARROWING", "AWAITING_HUMAN", "RESOLVED", "DISPATCHABLE", "CLOSED")
DISPOSALS = ("RESOLVED", "OPEN_GAP", "REJECTED", "MERGED_INTO")
UNCLASSIFIED = "UNCLASSIFIED"
# UNCLASSIFIED の問いが取れない処分(出口規則 ADJUDICATION_SENSITIVE:16)。
UNCLASSIFIED_FORBIDDEN_DISPOSAL = ("RESOLVED",)

# 遷移テーブル (from,to) -> 必須 guard_evidence キー。stage 1(validator 除外)。
TRANSITIONS = {
    (None, "SOFT"): (),
    ("SOFT", "NARROWING"): ("request_type_ok", "bind_context_ok"),
    ("NARROWING", "NARROWING"): (),
    ("NARROWING", "AWAITING_HUMAN"): (),
    ("AWAITING_HUMAN", "NARROWING"): ("human_replied",),
    ("NARROWING", "RESOLVED"): ("all_disposed", "suspense_settled", "all_gaps_presented", "thread_accepted"),
    ("RESOLVED", "DISPATCHABLE"): ("__DEFERRED__",),
}


class RThreadError(RuntimeError):
    pass


class RThreadIllegalTransition(RThreadError):
    pass


class RThreadConservationError(RThreadError):
    pass


class RThreadResidualIncomplete(RThreadError):
    pass


def _mint(prefix, *parts):
    """決定論 id。prefix-<8hex>。"""
    return "%s-%s" % (prefix, hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:8])


# ── 実装インスタンスが FILL を実装する(署名・docstring・定数・例外・_mint は 1 バイト不変) ──

def _append(event):
    """event(dict) を _EVENTS へ 1 行 JSON append(sole writer)。sealed_by 等は呼び手が既に刻んだ前提。"""
<<<FILL>>>


def _read(thread_id):
    """_EVENTS を順に読み thread_id の event を list で返す(thread_id=None なら全件)。無ければ []。"""
<<<FILL>>>


def open_thread(ds_thread_ref, ts):
    """THREAD_OPENED を append し thread_id 'RTHREAD-<8hex>' を返す。sealed_by を registry から刻む(G-1)。"""
<<<FILL>>>


def raise_question(thread_id, memo, ts, account_id="DEFAULT"):
    """QUESTION_RAISED を append し question_id 'Q-<8hex>' を返す。account_id は1問い1つ(I2)。
    default='DEFAULT'(RESOLVED 可)。'UNCLASSIFIED' は分類保留の特殊値。"""
<<<FILL>>>


def dispose_question(thread_id, question_id, disposal, ts, reason_code=None, target_id=None):
    """QUESTION_DISPOSED を append。disposal in DISPOSALS。REJECTED→reason_code必須、MERGED_INTO→target_id必須。
    **UNCLASSIFIED account の問いを RESOLVED 処分するのは不可(出口規則・ValueError)**。不正/欠落は ValueError(fail-closed)。"""
<<<FILL>>>


def present_gaps(thread_id, question_ids, ds_delivery_receipt, ts):
    """GAP_PRESENTED を append(OPEN_GAP を DS 経由で人へ提示した受領)。"""
<<<FILL>>>


def human_replied(thread_id, answer_refs, ts):
    """HUMAN_REPLIED を append(DS 経由のみ・G-7)。"""
<<<FILL>>>


def advance_state(thread_id, to_state, guard_evidence, ts):
    """TRANSITIONS に (project(thread_id)['status'], to_state) が在り guard_evidence がキーを満たす時のみ
    STATE_ADVANCED を append。違法遷移は RThreadIllegalTransition。**append 前に check_conservation(project) で I1/I2 両方を通す**。
    to_state=='RESOLVED' の guard: in_flight_count==0 かつ UNCLASSIFIED を RESOLVED 処分した問い 0 件 かつ 全 OPEN_GAP presented かつ THREAD_ACCEPTED。
    to_state=='DISPATCHABLE' は stage 1 では '__DEFERRED__' により RThreadError(後段)。"""
<<<FILL>>>


def accept_thread(thread_id, residual_gaps, human_ref, ts):
    """THREAD_ACCEPTED(人間の扉)。residual_gaps は全 OPEN_GAP を exhaustive 列挙
    (各 {question_id, disposal in {DECLINED,TRANSFERRED}, target_id?})。非網羅は RThreadResidualIncomplete。"""
<<<FILL>>>


def project(thread_id):
    """events を先頭から畳んで projection を deterministic 再構成(byte-identical・DERIVED・#25)。
    返り {status, turn_count, open_gaps, raised_total, resolved, open_gap, rejected, merged,
          in_flight_count, per_account_balances, suspense_balance}。
    raised_total=QUESTION_RAISED数 / resolved..merged=各 disposal 数 / in_flight_count=処分イベントを持たない raised 問いの数(残差でなく独立導出=I1 load-bearing) /
    per_account_balances={account_id: その account に raise された問い数}(I2, Σ==raised) /
    suspense_balance=per_account_balances.get('UNCLASSIFIED',0)。非決定要素(時刻/乱数)を入れない。"""
<<<FILL>>>


def check_conservation(projection):
    """複式保存則。不成立は RThreadConservationError(halt・fail-closed)。
    I1(処分次元): raised_total == resolved + open_gap + rejected + merged + in_flight_count。
    I2(科目次元): sum(per_account_balances.values()) == raised_total。"""
<<<FILL>>>
```

## §3. 不変テスト(発注側同梱・実装インスタンスは触らない)

配置: `rri/rri/test_request_thread_stage1.py`。FILL 無し・全文同梱。
**T14 は次元ごとに mutation を1つずつ**(I1破り=処分握り潰し / I2破り=account二重計上)。片方だけだと他方が空振り(Taka 指示)。

```python
import importlib
import os

import pytest


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("RTHREAD_EVENTS", str(tmp_path / "ev.jsonl"))
    import rri.request_thread as m
    importlib.reload(m)
    return m


@pytest.fixture()
def rt(tmp_path, monkeypatch):
    return _fresh(tmp_path, monkeypatch)


# ── T14 (I1 処分次元) 保存則が成立し、処分記録を握り潰すと halt ──────────────
def test_t14_i1_disposal_dimension(rt):
    tid = rt.open_thread("DS-1", "T")
    q1 = rt.raise_question(tid, "q1", "T")
    rt.raise_question(tid, "q2", "T")
    rt.dispose_question(tid, q1, "RESOLVED", "T")
    p = rt.project(tid)
    rt.check_conservation(p)                 # 正常: raised2 == resolved1 + in_flight1
    assert p["raised_total"] == 2 and p["resolved"] == 1 and p["in_flight_count"] == 1
    # mutation(I1破り): 処分記録を1件握り潰す → raised != 4種+in_flight → halt
    bad = dict(p); bad["resolved"] = 0
    with pytest.raises(rt.RThreadConservationError):
        rt.check_conservation(bad)


# ── T14 (I2 科目次元) 保存則が成立し、account を二重計上すると halt ───────────
def test_t14_i2_account_dimension(rt):
    tid = rt.open_thread("DS-2", "T")
    rt.raise_question(tid, "q1", "T", account_id="DEFAULT")
    p = rt.project(tid)
    rt.check_conservation(p)                 # 正常: Σ per_account == raised
    assert sum(p["per_account_balances"].values()) == p["raised_total"]
    # mutation(I2破り): account balance を二重計上 → Σ != raised → halt
    bad = dict(p); bad["per_account_balances"] = dict(p["per_account_balances"])
    k = next(iter(bad["per_account_balances"]))
    bad["per_account_balances"][k] += 1
    with pytest.raises(rt.RThreadConservationError):
        rt.check_conservation(bad)


# ── T18a RESOLVED は in_flight==0 を要求(未処分ありで RESOLVED 遷移は reject) ──
def test_t18_resolved_requires_in_flight_zero(rt):
    tid = rt.open_thread("DS-3", "T")
    rt.raise_question(tid, "q1", "T", account_id="DEFAULT")   # 未処分=in_flight 1
    rt.advance_state(tid, "NARROWING", {"request_type_ok": True, "bind_context_ok": True}, "T")
    with pytest.raises(rt.RThreadError):
        rt.advance_state(tid, "RESOLVED",
                         {"all_disposed": True, "suspense_settled": True,
                          "all_gaps_presented": True, "thread_accepted": True}, "T")


# ── T18b UNCLASSIFIED の問いは RESOLVED 処分できない(出口規則) ─────────────
def test_t18_unclassified_cannot_be_resolved(rt):
    tid = rt.open_thread("DS-4", "T")
    q1 = rt.raise_question(tid, "q1", "T", account_id="UNCLASSIFIED")
    with pytest.raises(ValueError):
        rt.dispose_question(tid, q1, "RESOLVED", "T")
    # OPEN_GAP なら可(出口)
    rt.dispose_question(tid, q1, "OPEN_GAP", "T")
    p = rt.project(tid)
    assert p["open_gap"] == 1 and p["in_flight_count"] == 0
```

## §4. 受入条件

- `test_request_thread_stage1.py` **4/4 green**(T14 I1・T14 I2・T18a・T18b)。
- `verify_skeleton_preserved` 相当で骨格 FILL 以外 bytes 一致(定数/例外/_mint 不変)。
- **mutation check(G-T1):** T14 の各 mutation(resolved 握り潰し / account 二重計上)で `check_conservation` が確かに halt する(テスト内で実証済み)。
- 残(v0.2): T15-17(disposal種別/merge/split), T25(1接触1スレッド), T36(projection byte-identical), T37-40(状態機械)。
