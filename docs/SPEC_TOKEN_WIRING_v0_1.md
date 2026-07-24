# TOKEN 配線 SPEC v0.1 — validate/consume を台帳照合(approval_registry)に統一（B: §9 全経路）

> **FLOW NOTE — 2026-07-23 ANCHOR §1-1 Taka 裁定（まずここ）:**
> 本書は `egl/docs` の**実装指示**。実装インスタンス（Monitor `b0718vzrg`）が working tree を直接修正し、受入(§5)を green にする。
> 実装対象: (A) `twoder/approval_registry.py` にアダプタ3関数を**追加**（§2 骨格 FILL×3・既存関数は不変）＋ `tests/test_token_wiring.py`（§2 不変テスト同梱・worker は触らない）。
> (B) 6ファイルの `validate_approval`/`consume_approval` を `validate_by_token`/`consume_by_token` に置換（§3 表）。(C) `probe/conformance_probe.py` の gate1/gate7 を新経路向けに更新（§4）。commit=Taka。

- **status:** SPEC / 起草: CC-α 2026-07-23
- **目的:** ★3(B) の配線。BREAKAGE_LIST の唯一 DIRECT 破断 `gate1_token`（死因#4＝seam が str を渡し `validate_approval` は dict 要求）を**配線で消す**。Taka 裁定=B（§9 全経路統一）。
- **恒久原則（§9・DE 化は Taka 承認待ち）:** 境界を跨ぐ token は両側が同じ識別子（台帳 approval_id）で扱う。真正性は**台帳のみ**が持ち、引数 dict の中身は信じない（族C）。

## §1. 何を直すか / なぜアダプタか

`validate_approval` を呼ぶ6経路は **dict token を運搬しているだけで中身(action_type 等)を業務に使っていない**（調査済）。よって全経路を、**approval_id を台帳照合する新API**（`validate_approval_by_id`＝TOKEN-GATE-01 で BUILT 済）に寄せられる。
直接置換だと dict を渡す既存経路が `validate_approval_by_id`（dict 拒否）で落ちるため、**dict/str どちらでも approval_id を抜くアダプタ**を1つ噛ませる。dict の中身は捨てるので**族C（自己申告）を排除**しつつ**後方互換**になる。

## §2. Part A — approval_registry アダプタ（骨格＋不変テスト）

配置: `twoder/approval_registry.py` の**末尾に追加**（既存の `_load_grant`/`validate_approval_by_id`/`consume_approval_by_id` は 1 バイトも変えない）。FILL×3。

```python
# ── 配線アダプタ（TOKEN-WIRING）: dict/str どちらの token でも approval_id を抜いて
#    台帳照合に委譲する。dict の中身(action_type 等)は真正性に使わない(族C)。既存関数は変更しない。
def _extract_approval_id(token_or_id):
    """dict/str から approval_id(str)を取り出す。str はそのまま。dict は approval_id フィールドのみ
    (中身の action_type 等は真正性に使わない=族C)。取れなければ None(=validate_approval_by_id が拒否)。"""
<<<FILL>>>


def validate_by_token(token_or_id, action_type, task_id, operation_class, ts):
    """dict/str どちらでも approval_id を抜いて validate_approval_by_id に委譲(台帳照合)。
    dict の中身は照合に使わない。approval_id が取れなければ拒否。"""
<<<FILL>>>


def consume_by_token(token_or_id, ts):
    """dict/str どちらでも approval_id を抜いて consume_approval_by_id に委譲。"""
<<<FILL>>>
```

不変テスト（配置: `tests/test_token_wiring.py`・全文同梱・FILL 無し）。**`test_forged_dict_rejected` と `test_dict_content_is_ignored` が心臓**（族C を守る）:

```python
import importlib

AUTH = importlib.import_module("twoder.authority")
MOD = "twoder.approval_registry"
ACTION = "USE_VLLM_INFERENCE"
OP = "DW_MACHINE_OP"
ACTOR = "2der-wiring-test"
TS = "2026-07-11T09:00:00"


def _m():
    return importlib.import_module(MOD)


def _grant(tid):
    return AUTH.grant_approval(ACTION, tid, OP, ACTOR, TS)


def test_dict_token_validates_via_ledger():
    m = _m(); tid = "TASK-WIRE-DICT"; tok = _grant(tid)
    r = m.validate_by_token(tok, ACTION, tid, OP, TS)          # dict を渡す
    assert r["ok"] is True, r["reasons"]


def test_str_id_validates_via_ledger():
    m = _m(); tid = "TASK-WIRE-STR"; tok = _grant(tid)
    r = m.validate_by_token(tok["approval_id"], ACTION, tid, OP, TS)   # str を渡す
    assert r["ok"] is True


def test_forged_dict_rejected():
    m = _m()
    forged = {"approval_id": "APPROVAL-forged", "action_type": ACTION,
              "task_id": "TASK-X", "operation_class": OP}       # 台帳に無い偽id+それらしい中身
    r = m.validate_by_token(forged, ACTION, "TASK-X", OP, TS)
    assert r["ok"] is False, "台帳に無い approval_id が中身の自己申告で通った(族C)"


def test_dict_content_is_ignored():
    m = _m(); tid = "TASK-WIRE-IGNORE"; tok = _grant(tid)
    tampered = dict(tok); tampered["action_type"] = "SOME_OTHER_ACTION"   # 中身を改竄
    r = m.validate_by_token(tampered, ACTION, tid, OP, TS)      # 引数 action_type は正しい
    assert r["ok"] is True, "dict の改竄 action_type が照合に使われている(中身を信じている)"


def test_consume_by_token_burns():
    m = _m(); tid = "TASK-WIRE-CONSUME"; tok = _grant(tid)
    assert m.validate_by_token(tok, ACTION, tid, OP, TS)["ok"] is True
    m.consume_by_token(tok, TS)
    assert m.validate_by_token(tok, ACTION, tid, OP, TS)["ok"] is False, "消費済みが再通過"


def test_non_token_rejected():
    m = _m()
    assert m.validate_by_token(True, ACTION, "TASK-Y", OP, TS)["ok"] is False   # bare boolean
    assert m.validate_by_token(None, ACTION, "TASK-Y", OP, TS)["ok"] is False
```

## §3. Part B — 6経路を新API経由に統一（既存修正）

| ファイル | 行 | import 追加 | 置換前 → 置換後 |
|---|---|---|---|
| `live_worker_runtime.py` | 94 / 97 | `from twoder import approval_registry as AR` | `AUTH.validate_approval(approval_token, …)` → `AR.validate_by_token(approval_token, …)` ／ `AUTH.consume_approval(approval_token, ts)` → `AR.consume_by_token(approval_token, ts)` |
| `gate4.py` | 48 / 55 | 同上（`AR`） | `A.validate_approval(approval, …)` → `AR.validate_by_token(approval, …)` ／ `A.consume_approval(approval, ts)` → `AR.consume_by_token(approval, ts)` |
| `operator.py` | 131 / 140 | 同上 | `A.validate_approval(approval, …)` → `AR.validate_by_token(approval, …)` ／ `A.consume_approval(approval, ts)` → `AR.consume_by_token(approval, ts)` |
| `ab_harness.py` | 61 / 66 | 同上 | `A.validate_approval(approval, …)` → `AR.validate_by_token(approval, …)` ／ `A.consume_approval(approval, ts)` → `AR.consume_by_token(approval, ts)` |
| `command_surface.py` | 63 / 67 | 同上 | `AUTH.validate_approval(token, …)` → `AR.validate_by_token(token, …)` ／ `AUTH.consume_approval(token, ts)` → `AR.consume_by_token(token, ts)` |
| `autonomous_git.py` | 66 | 同上 | `AUTH.validate_approval(approval_token, …)` → `AR.validate_by_token(approval_token, …)`（`consume` は未配線＝対象外） |

**引数は変えない**（`action_type`/`task_id`/`operation_class`/`ts` はそのまま）。**アダプタが dict/str 両対応**なので、既存の呼び出し元が dict token を渡しても str id を渡しても動く（後方互換）。

## §4. Part C — CONFORMANCE_PROBE を新経路向けに更新（既存修正）

`probe/conformance_probe.py` を新経路向けに更新する（配線が効いたことを再走行で測るため）:

- `ladder_symbols()`:
  - `("gate1_token", "twoder.authority.validate_approval")` → `("gate1_token", "twoder.approval_registry.validate_by_token")`
  - `("gate7_consumed", "twoder.authority.consume_approval")` → `("gate7_consumed", "twoder.approval_registry.consume_by_token")`
- `_gate1_token()`: `bind_real("twoder.approval_registry.validate_by_token")` を **str と dict の両方**で呼び、**両方 ok** を確認する probe に変える。`expected`/`actual` を「型不一致(str/dict)」ではなく「**台帳照合が dict/str 両方を通す**」に更新。台帳に GRANT がある id を使う（`grant_approval` → `validate_by_token`）。
- `_gate7_consumed()`: `consume_by_token` 経由に。
- 骨格の `bind_real`/`source_ref`/`run_ladder` は不変。§5 の T1–T12 が green を維持すること。

## §5. 受入条件

- **Part A**: `tests/test_token_wiring.py` 6/6 green（隔離下＝DS/EGL throwaway）。`_extract_approval_id`/`validate_by_token`/`consume_by_token` が追加され、既存3関数は bytes 不変。
- **Part B**: 既存の回帰テスト（`regression/test_live_worker_runtime.py` 等）が **green を維持**（配線後も dict token 経路が台帳照合で動く）。6ファイルに `AR` import と置換が入っている。
- **Part C**: **CONFORMANCE_PROBE 再走行**で `gate1_token` が **green（DIRECT 破断消滅）**。§5 の probe 不変テスト T1–T12 は green を維持。
- 3つ揃って ★3(B) は実走痕跡（再走行 BREAKAGE_LIST に DIRECT 無し）で DONE。

## §6. 範囲外

- **発行側**（`command_surface.issue_approval` が dict token を返す・webui 承認フロー）の approval_id 中心化は**別途**。消費側がアダプタで吸収するため本配線は発行側を変えない。
- `§9` 恒久原則の DE 台帳登記（正式採用）は Taka 承認で別途。本配線は原則の初適用。
