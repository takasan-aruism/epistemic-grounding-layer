# TOKEN-GATE-01 — authority トークン門の台帳照合化（実装仕様・新フロー）

> **FLOW NOTE — 2026-07-23 ANCHOR §1-1 Taka 裁定（まずここ）:**
> 本書は `egl/docs` に置かれた**実装指示**。実装インスタンス（Monitor `b0718vzrg`）が
> `twoder/approval_registry.py` ＋ `tests/test_approval_registry.py` を **working tree に直接実装**し、§3 の不変テスト 7/7 を green にする。
> 実装契約は不変: **§2 骨格の `<<<FILL>>>` 以外は 1 バイトも変えない**（docstring・import 含む）。§3 不変テストは発注側同梱・worker は書かない。commit は人間の扉＝**Taka**。
> 起草: CC-α。TOKEN-GATE-01(paste-cache)の不変テスト7本をバイト保存し、骨格を新フロー形式（本体 `<<<FILL>>>`）へ変換。

- **status:** SPEC / 起草: CC-α 2026-07-23（TOKEN-GATE-01 を新フロー化）
- **目的:** ★3(B)。BREAKAGE_LIST 走行で確定した **DIRECT 破断 `gate1_token`（死因#4＝token が str・`validate_approval` は dict 要求）** を直す。
- **実装対象:** `twoder/approval_registry.py`。**投入:** 本書を `egl/docs` へ投下。**commit=Taka**。
- **前提（採取済）:** `docs/BREAKAGE_LIST_2026-07-23.jsonl` の唯一の DIRECT 破断が `gate1_token`：`actual=str`（`generate_via_runner.py:39-46`）／`expected=dict`（`authority.py:147-162`）。

## §1. 何を直すか

seam は `mint_token` の戻り `approval_id`（**str**）を token として渡すが、`authority.validate_approval` は **dict** を要求して弾く（死因#4）。
本仕様は **approval_id（str）のみを受け、authority 台帳の GRANT 記録を引いて照合する** `validate_approval_by_id()` を新設する。
**引数の中身から真正性を読まない**（dict を渡されたら拒否＝自己申告の排除＝族C）。CONSUMED 済みは single_use に関わらず拒否。
**既存の `authority.validate_approval` は変更しない**（新 API を追加するだけ）。台帳アクセスは骨格 import に束縛された `_AUTH` 経由。

## §2. 骨格 —— 完全ファイル（`<<<FILL>>>` 以外は bytes 一致対象）

配置: `twoder/approval_registry.py`。FILL×3（各関数本体）。シグネチャ・import・docstring は 1 バイトも変えない。

```python
"""TOKEN-GATE-01 — authority トークン門の台帳照合化。

approval_id(文字列)のみを受け、authority 台帳の GRANT 記録を引いて
action_type / task_id / operation_class を照合する。引数の中身から真正性を
読まない(dict を渡されたら拒否=自己申告の排除=族C)。CONSUMED 済みは single_use
フラグの有無に関わらず拒否する。台帳アクセスは骨格 import に束縛された authority
モジュール経由(_AUTH)で行う。既存の authority.validate_approval は変更しない。
"""
from twoder import authority as _AUTH


def _load_grant(approval_id):
    """approval_id に対応する GRANT トークンを authority 台帳から引く。無ければ None。
    台帳アクセスは _AUTH 経由(自作しない=導管)。"""
<<<FILL>>>


def validate_approval_by_id(approval_id, action_type, task_id, operation_class, ts):
    """approval_id(str)のみで検証する。dict(自己申告)は拒否。台帳 GRANT を引き、
    action_type / task_id / operation_class を台帳値と照合。CONSUMED 済みは拒否。
    戻り {"ok": bool, "reasons": list, "approval_id": str|None}。"""
<<<FILL>>>


def consume_approval_by_id(approval_id, ts):
    """approval_id で単一使用の消費を記録する(_AUTH 経由)。"""
<<<FILL>>>
```

## §3. 不変テスト（発注側同梱。worker は書かない・触らない）

配置: `tests/test_approval_registry.py`。FILL は無い。全文をそのまま同梱。

```python
import importlib

MOD = "twoder.approval_registry"
AUTH = importlib.import_module("twoder.authority")

ACTION = "USE_VLLM_INFERENCE"
OP = "DW_MACHINE_OP"
ACTOR = "2der-token-gate-test"
TS = "2026-07-11T09:00:00"


def _m():
    return importlib.import_module(MOD)


def _grant(task_id):
    return AUTH.grant_approval(ACTION, task_id, OP, ACTOR, TS)


def test_authority_binding_is_real():
    m = _m()
    assert m.__dict__["_AUTH"] is AUTH, "authority が自作定義"


def test_granted_id_passes():
    m = _m()
    tid = "TASK-TOKENGATE-PASS"
    tok = _grant(tid)
    r = m.validate_approval_by_id(tok["approval_id"], ACTION, tid, OP, TS)
    assert r["ok"] is True, r["reasons"]
    assert r["approval_id"] == tok["approval_id"]


def test_unknown_id_is_rejected():
    m = _m()
    r = m.validate_approval_by_id("APPROVAL-does-not-exist", ACTION, "TASK-X", OP, TS)
    assert r["ok"] is False


def test_dict_is_rejected():
    m = _m()
    tid = "TASK-TOKENGATE-DICT"
    tok = _grant(tid)
    r = m.validate_approval_by_id(tok, ACTION, tid, OP, TS)
    assert r["ok"] is False, "dict(自己申告)を受理している"


def test_action_type_comes_from_ledger():
    m = _m()
    tid = "TASK-TOKENGATE-ACT"
    tok = _grant(tid)
    r = m.validate_approval_by_id(tok["approval_id"], "SOME_OTHER_ACTION", tid, OP, TS)
    assert r["ok"] is False


def test_task_scope_comes_from_ledger():
    m = _m()
    tid = "TASK-TOKENGATE-SCOPE"
    tok = _grant(tid)
    r = m.validate_approval_by_id(tok["approval_id"], ACTION, "TASK-OTHER", OP, TS)
    assert r["ok"] is False


def test_consumed_id_is_rejected():
    m = _m()
    tid = "TASK-TOKENGATE-CONSUMED"
    tok = _grant(tid)
    aid = tok["approval_id"]
    assert m.validate_approval_by_id(aid, ACTION, tid, OP, TS)["ok"] is True
    m.consume_approval_by_id(aid, TS)
    assert m.validate_approval_by_id(aid, ACTION, tid, OP, TS)["ok"] is False, "消費済みが再通過"
```

## §4. 受入条件

- **7/7 green**（`test_authority_binding_is_real` / `granted_id_passes` / `unknown_id_is_rejected` / `dict_is_rejected` / `action_type_comes_from_ledger` / `task_scope_comes_from_ledger` / `consumed_id_is_rejected`）。
- `verify_skeleton_preserved` で FILL 以外の bytes 一致。**`test_dict_is_rejected` と `*_comes_from_ledger` が心臓**（自己申告を受理したら赤）。

## §5. 範囲外（別工程）

- **seam の配線**（`live_worker_runtime` / `generate_via_runner` が `validate_approval` の代わりに `validate_approval_by_id` を呼ぶ変更）は本仕様に含めない。本仕様の DONE は BUILT。
- 配線後の効果（`gate1_token` が green 化し、CONDITIONAL だった `gate1b_ts`（死因#2）ほかが確定/消滅すること）は **CONFORMANCE_PROBE 再走行**が測る。
