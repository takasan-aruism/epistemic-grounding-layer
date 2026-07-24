# 適合プローブ（CONFORMANCE PROBE）実装仕様 v0.4

> **FLOW NOTE — 2026-07-23 ANCHOR §1-1 Taka 裁定（まずここ）:**
> 本書は `egl/docs` に置かれた**実装指示**。実装インスタンス（Monitor `b0718vzrg`）が
> `twoder/probe/conformance_probe.py` ＋ `tests/`（`test_conformance_probe.py`・`conftest.py`）を
> **working tree に直接実装**し、§5 の不変テスト T1–T12 を green にする。
> **旧『本書を raw_input として submit / Qwen が実装 / CC=監査のみ』は本フローでは無効**（§1-1 で submit→runner は置換）。
> 実装契約は不変: **§4 骨格の `<<<FILL>>>` 以外は 1 バイトも変えない**（レビューで bytes 一致を担保）。
> **§5 の不変テストと conftest(`probe_env` fixture)は発注側同梱・worker は書かない/触らない。** commit は人間の扉＝**Taka**。
> 起草: CC-α。v0.3(Web) を土台に §4 へ固定 API `ladder_symbols`/`run` を追加し `probe_env` fixture を同梱
> （v0.3 の唯一 blocker＝`probe_env` 未同梱=`CC_AUDIT_2026-07-23_SEAM_v0_2_PROBE_v0_3.md` の E を解消）。


- **status:** SPEC / 起草: CLAUDE_WEB(v0.3) → **CC-α が v0.4 化** 2026-07-23 / **v0.3 を SUPERSEDE**
- **目的:** ★3 の死因が **1件ずつ直列にしか出てこない** 構造を壊す。境界の不一致を**一括採取**する。
- **これは支流ではない:** ループを回す作業そのもの（趣意書「註」の1問に対し前者）。
- **実装:** 実装インスタンス（Monitor `b0718vzrg`・working tree 直接）。**投入:** 本書を `egl/docs` へ投下（file signal）。**commit=Taka**。
- **前提工程:** `SEAM_PKG_MIRROR_v0_4`（death#6）が **12/12 green・commit `c1ffef5`** で完了済み。§3 gate3 で `twoder/seam/pkg_mirror.py` を使う。

### v0.2 からの修正

|#               |内容                                                                                                                                                                                                      |出所                 |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
|**骨格記法の訂正**     |`# === SKELETON:BEGIN/END ===` で固定区間を囲う書き方は**逆だった**。正本は **`<<<FILL>>>` 行だけが自由**で、それ以外は全て bytes 一致対象（`generate_via_runner.py:49`）。§4 を**完全ファイル**として書き直した                                                 |CC 監査 07-23        |
|**§8 step1 を削除**|「E1 補正を commit」は**存在しない作業**だった。death#5 は既に HEAD 反映済（`authority.py:133` ts込み hash / mint・validate 整合）、commit すべき diff 無し                                                                                 |CC 監査 07-23        |
|**gate1b の格上げ** |death#2 は OPEN 継続。原因は runner 側の hardcoded 既定 ts（`generate_via_runner.py:45`）で、authority の ISO 化では防げない。**#5 が HEAD に入って hash に ts が含まれた結果、残る退化源は呼び出し側の固定 ts だけになった**ので、gate1b は「検出」ではなく**「決着」**の資格を得た（§3）|CC 監査 07-23 ＋ 本書の帰結|
|**V-4（新規欠陥）**   |v0.2 は override された上流しか下流へ伝播させていない。**override されずに失敗した上流**（gate1b のような観測専用ゲート）も下流を汚染するのに DIRECT と記録されてしまう。→ `upstream_failed` を追加し `confidence` を3値化（§2.1）                                              |本書起草時に発見           |

**v0.2 で修正済み（記録として保持）:** V-1 override 汚染の非分離 / V-2 T7 と実 ts の非両立 / V-3 fault injection 機構の未指定。

-----

## §0. 何を解こうとしているか

★3 の死因は 4 件連続で **seam と runner の境界の不一致**だった:

|# |不一致の次元               |検出手段       |費用              |現状                                   |
|--|---------------------|-----------|----------------|-------------------------------------|
|#2|呼び出し側の固定 ts          |live 走行の副作用|往復複数            |**OPEN**（`generate_via_runner.py:45`）|
|#3|引数が渡っていない（provenance）|live 走行 1本 |PROBE-PIPE-01 消費|解消                                   |
|#4|型（str / dict）        |live 走行 1本 |PROBE-PIPE-02 消費|実装未                                  |
|#5|フィールド値 3件            |人間の静的監査    |往復1回            |**HEAD 反映済**                         |
|#6|受入オラクルの位置            |人間の静的監査    |往復1回            |SEAM 仕様で解消予定                         |

**封印58本は全て緑のまま、live は4回死んだ。** 58本が全て spy（`_REAL_RUNNER`）だから。
**spy テストは「seam が想定する runner」を検証しており、「実際の runner」を検証していない。** この族は原理的に検出できない。

失敗族カタログの **族E（代理指標を結論にする）の境界版**。I2（`guided_json` 黙殺）と同型 ——
**計器が効いていないとき、出力は正常と見分けがつかない。**

**律速の正体: 1往復あたり欠陥1件。** 往復回数が唯一のコスト。**これを 2 回に落とす**（1 回にはならない。§2.1 参照）。

-----

## §1. 設計の中心 —— 偽装境界を移す

```
現行: [cw] → [seam] → ✂ spy ← 壊れる場所そのものを偽装している
本仕様: [cw] → [seam] → [runner] → [authority] → [台帳] → [sandbox] → [pytest]
                                                    ✂ここだけ偽装 → :8005 stub model
                                                    ✂ここだけ禁止 → 実 repo 書込み
```

> **原則: 偽装してよいのは「高価または非決定的なもの」と「人間の扉」だけ。
> 安いのに偽装した箇所が、そのまま欠陥の隠れ場所になる。**

**実物を走らせる:** token の鋳造・`validate_approval`・台帳の GRANT/CONSUMED・provenance 受け渡し・
sandbox 構築（`pkg_mirror`）・pytest 起動・`verify_skeleton_preserved`。

隔離は既存機構: **throwaway `EGL_DATA_DIR`**（AB-0005 で確立、DE-0378 で実績）。

-----

## §2. 中心機構 —— fail-fast をやめて collect する

本番の門は fail-closed が正しい。**しかし統合デバッグでは fail-fast が律速そのもの。**

### 2.1 汚染の分離（V-1 ＋ V-4）

下流のゲートは**上流が壊れたままの入力**を見ている。したがって下流の所見は実欠陥かもしれないし、上流の産物かもしれない。
区別せずに「1本の仕様で全部直す」と、幻の破断を直し、再走行で別の破断が出て、**往復が再直列化する**。

汚染源は 2 種類あり、v0.2 は片方しか追跡していなかった:

- **override 汚染** — 失敗したゲートを人工的に通した。下流は人工的な入力を見ている。
- **未修復汚染（V-4）** — 失敗したが override しなかった（＝観測専用ゲート）。下流は壊れた入力を見ている。

出力 `BREAKAGE_LIST.jsonl`:

```json
{"seq":3,"gate":"gate2_grant","expected_from":"twoder/authority.py:141-144",
 "expected":{"...":"..."},"actual_from":"twoder/generate_via_runner.py:42-44",
 "actual":{"...":"..."},"passed":false,"class":"FIELD_MISMATCH",
 "override_applied":false,"upstream_overrides":[],"upstream_failed":["gate1b_ts_nondegenerate"],
 "confidence":"CONDITIONAL_ON_UPSTREAM_FAILURE","injected":false,"unresolved":null}
```

**`confidence` は配管の依存関係の記録であって、次元独立性の判断ではない。**
gate1 の `action_type` 不一致が gate5 の `verify_skeleton_preserved` を汚染するとは限らない。
**その判断は Web が §8-4 で行う。** ツールは事実（何が上流で壊れていたか）だけを載せ、判断は載せない。

**修理の優先順位:** `DIRECT` から直す。`CONDITIONAL_*` は**候補**であって確定所見ではない。上流修正後の再走行で確定する。
**正直な上限: 往復は N 回 → 2 回。1 回にはならない。**

### 2.2 fault injection（T5/T6 用。実コードは 1 バイトも触らない）

- 注入は**呼び出し側 payload の変異のみ**。`FaultInjection` レジストリ（gate 名 → payload 変異関数）で管理。
- 注入由来のレコードは `injected: true`。**実所見と混ざらない。**
- **既定の走行では注入 0 件。** テスト以外から注入経路に到達できないこと（T10）。

-----

## §3. ゲートラダー

**列挙はコードから導出する。手書きの表を正本にしない。** 各エントリは callee の完全修飾シンボルを持ち、
解決できない行があれば halt する（死んだ手書き行を残さない = T8）。

|#     |ゲート                        |既知の位置（参考。正本はコード）                                    |種別      |
|------|---------------------------|----------------------------------------------------|--------|
|0     |provenance gate（DE-0301）   |`live_worker_runtime.py`                            |通過      |
|1     |token gate                 |`live_worker_runtime.py:94` / `authority.py:147-162`|通過      |
|**1b**|**ts 非退化検査**               |`authority.py:133` / `generate_via_runner.py:45`    |**観測専用**|
|2     |台帳 GRANT 照合                |grant=`authority.py:129-138`／照合=`validate_approval:147-162`（141-144 は `approval_consumed`）|通過      |
|3     |sandbox 構築（`pkg_mirror`）   |`twoder/seam/pkg_mirror.py`                         |通過      |
|4     |worker 呼出（stub）            |—                                                   |通過      |
|5     |`verify_skeleton_preserved`|DE-0512                                             |通過      |
|6     |受入テスト実行                    |`live_worker_runtime.py:116`(`_run_test`)。93-94 は test_command 定義|通過      |
|7     |CONSUMED 記帳                |台帳                                                  |通過      |

**観測専用ゲート**は `override=None` を持ち、失敗しても人工的に通さない。代わりに `upstream_failed` に載る（V-4）。

> **gate3 注記（v0.4）:** gate3 の sandbox 構築は実装済み `twoder/seam/pkg_mirror.py`（commit `c1ffef5`）を bind_real で呼ぶ。
> **既知の罠（両監査で記録済み）:** `twoder/operator.py` が stdlib `operator` を shadow する。gate3 が実 `twoder` を複製して
> PYTHONPATH に入れると `import operator` 連鎖が壊れうる。`MIRROR_EXCLUDE` 該当化か複製 root を PYTHONPATH 末尾に置く等で回避する（probe 実装時に確認）。

### gate1b —— death#2 をここで決着させる

ANCHOR は死因#2 を OPEN 継続とし、原因を runner 側の hardcoded 既定 ts（`generate_via_runner.py:45`）と特定した。
**#5 が HEAD に入って `approval_id` の hash に ts が含まれるようになった**ので、退化源は呼び出し側の固定 ts だけに絞られている。
したがって次の 1 検査が**必要十分**になった:

> **同一走行内で実 mint 経路を 2 回通し、`approval_id` が相異なること。**
> 相異なる → death#2 **CLOSED**。同一 → death#2 **OPEN**（呼び出し側の固定 ts 残存）。

生の `approval_id` は記録しない。`{"distinct": false}` のみ記録する（V-2 の規律）。
**「DE-0505 で消えた可能性大」は閉塞宣言にならない**（推測を結論にする＝族E）。**推測ではなく走行で決着する。**

-----

## §4. 骨格 —— 完全ファイル（`<<<FILL>>>` 以外は bytes 一致対象）

> **記法の規律:** `<<<FILL>>>` 行のみが自由区間。**それ以外は 1 バイトも変えてはならない**（docstring・コメント・空行を含む）。
> 整形・型注釈の追加・docstring の要約は違反。FILL 区間のインデントは worker が文脈に合わせる。
> 
> **仮定 A1’（訂正後・残存する不確実性）:** FILL マーカーの字面を `<<<FILL>>>` 単独行と仮定。
> ラベル付きや BEGIN/END 対を要求する実装なら、**字面のみ**置換する。**区間の境界は変えない。** 不明なら halt して差し戻す。
> 
> **仮定 A2:** パッケージ名 `twoder`、配置 `twoder/probe/conformance_probe.py`。
> **仮定 A3:** `run_minimal_slice` / `validate_approval` の完全修飾名は**推測しない**。
> ラダー定義（FILL 区間）に置き、`bind_real` が解決できなければ halt する。**推測で代替実装を作るのは違反。**
> **仮定 A4:** throwaway `EGL_DATA_DIR` の作法は AB-0005 / DE-0378 準拠。
> **仮定 A5:** :8005 stub は HTTP 層で差し替え（エンドポイント環境変数の切替を第一候補とする）。

配置: `twoder/probe/conformance_probe.py`

```python
"""CONFORMANCE PROBE — 境界不一致の一括採取器。

claim ceiling: 言えるのは「ここに不一致がある」のみ。「不一致は無い」は言えない。
走査しなかったゲートは UNRESOLVED_NOT_TRAVERSED。ラダーの網羅性は保証しない
(UNRESOLVED_LADDER_COMPLETENESS)。stub model を通すため worker 出力の質は
一切測っていない。測っているのは配管のみ。

confidence は配管の依存関係の記録であって、次元独立性の判断ではない。
上流が壊れていた事実だけを載せ、それが下流に効いたかどうかは判断しない。
"""
from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Optional
<<<FILL>>>

PROBE_SPEC = "SPEC_CONFORMANCE_PROBE_v0_3"
CLAIM_CEILING = "MISMATCHES_LOCATED_UNDER_TRAVERSED_GATES_ONLY"

# BREAKAGE_LIST の全フィールド。ここに無いキーを足すのは仕様変更。
BREAKAGE_FIELDS = (
    "seq", "gate", "expected_from", "expected", "actual_from", "actual",
    "passed", "class", "override_applied", "upstream_overrides", "upstream_failed",
    "confidence", "injected", "unresolved",
)

# 再実行バイト一致(T7)の比較から除外する揮発フィールド。列挙で固定する。
# 時刻・乱数・パスを観測するゲートは、生値ではなく導出ブール値を記録すること。
# 生値を actual に載せた瞬間 T7 が赤くなる。それが仕様どおりの捕捉である。
VOLATILE_FIELDS = ("probe_run_id", "wall_clock")


class ProbeHalt(RuntimeError):
    """解決できない前提に当たったら回避策を発明せず halt する(ANCHOR §5-6)。"""


def bind_real(dotted: str) -> Any:
    """実シンボルを名前で解決する。spy へのフォールバックは禁止。

    解決できなければ halt。代替実装・モック・try/except: pass は違反(族B/族E)。
    """
    mod_name, _, attr = dotted.rpartition(".")
    if not mod_name:
        raise ProbeHalt(f"UNRESOLVED_SYMBOL_PATH:{dotted}")
    try:
        mod = __import__(mod_name, fromlist=[attr])
        obj = getattr(mod, attr)
    except Exception as exc:
        raise ProbeHalt(f"UNRESOLVED_IMPORT:{dotted}:{type(exc).__name__}") from exc
    origin = f"{getattr(obj, '__module__', '')}.{getattr(obj, '__qualname__', '')}".lower()
    if "spy" in origin or "fake" in origin or "stub" in origin:
        raise ProbeHalt(f"SPY_BOUND_WHERE_REAL_REQUIRED:{dotted}->{origin}")
    return obj


def source_ref(obj: Any) -> str:
    """expected_from / actual_from は inspect 由来で作る。手書き文字列は禁止(族C)。"""
    try:
        path = inspect.getsourcefile(obj)
        lines, start = inspect.getsourcelines(obj)
    except Exception as exc:
        raise ProbeHalt(f"UNRESOLVED_SOURCE:{obj!r}:{type(exc).__name__}") from exc
    return f"{path}:{start}-{start + len(lines) - 1}"


@dataclass
class GateOutcome:
    """1ゲートの観測結果。override=None のゲートは観測専用(人工的に通さない)。"""

    passed: Optional[bool]
    expected: Any = None
    actual: Any = None
    expected_from: Optional[str] = None
    actual_from: Optional[str] = None
    cls: Optional[str] = None
    unresolved: Optional[str] = None
    injected: bool = False
    override: Optional[Callable[[], None]] = None


def _record(seq, gate, outcome, override_applied, overrides, failed):
    """汚染源を2種類とも載せる。override されなかった上流の失敗も下流を汚染する(V-4)。"""
    rec = {
        "seq": seq,
        "gate": gate,
        "expected_from": outcome.expected_from,
        "expected": outcome.expected,
        "actual_from": outcome.actual_from,
        "actual": outcome.actual,
        "passed": outcome.passed,
        "class": outcome.cls,
        "override_applied": override_applied,
        "upstream_overrides": list(overrides),
        "upstream_failed": list(failed),
        "confidence": (
            "CONDITIONAL_ON_OVERRIDE" if overrides
            else "CONDITIONAL_ON_UPSTREAM_FAILURE" if failed
            else "DIRECT"
        ),
        "injected": outcome.injected,
        "unresolved": outcome.unresolved,
    }
    if tuple(rec.keys()) != BREAKAGE_FIELDS:
        raise ProbeHalt("BREAKAGE_SCHEMA_DRIFT")
    return rec


def run_ladder(ladder, sink) -> None:
    """fail-fast をやめて collect する。汚染は全て記録に残す。

    halt 後の未走査ゲートは UNRESOLVED_NOT_TRAVERSED として必ず出力する。
    空欄を「合格」と読ませないため(C2 規則)。
    """
    overrides: list[str] = []
    failed: list[str] = []
    halted = False
    for seq, (gate_name, gate_fn) in enumerate(ladder):
        if halted:
            sink(_record(seq, gate_name,
                         GateOutcome(passed=None, unresolved="UNRESOLVED_NOT_TRAVERSED"),
                         False, overrides, failed))
            continue
        try:
            outcome = gate_fn()
        except ProbeHalt:
            halted = True
            sink(_record(seq, gate_name,
                         GateOutcome(passed=None, unresolved="UNRESOLVED_PROBE_HALTED"),
                         False, overrides, failed))
            continue
        except Exception as exc:
            outcome = GateOutcome(
                passed=None, unresolved=f"UNRESOLVED_GATE_RAISED:{type(exc).__name__}")
        applied = False
        if outcome.passed is False and outcome.override is not None:
            outcome.override()
            applied = True
        sink(_record(seq, gate_name, outcome, applied, overrides, failed))
        if applied:
            overrides.append(gate_name)
        elif outcome.passed is not True:
            failed.append(gate_name)


def ladder_symbols():
    """ラダー各ゲートの (gate_name, callee_dotted) を返す。手書き表を正本にせず、ラダー定義から
    導出する(T8)。各 dotted は callee の完全修飾名。bind_real で解決できなければ halt。
    fixture(probe_env)がこの API を呼ぶため、シグネチャは骨格固定(本体のみ FILL)。"""
<<<FILL>>>


def run(inject=None):
    """実配管でゲートラダーを collect モード(run_ladder)で走らせ BREAKAGE レコードの list を返す。
    実 run_minimal_slice / validate_approval / grant_approval / mirror_package /
    verify_skeleton_preserved を bind_real で解決して呼ぶ(spy 禁止=T1)。
    gate4 の worker 呼出は stub chat_fn を注入し :8005 に一切触れない(T3)。sandbox は tempfile、
    実 repo は無改変(T4)。台帳隔離(EGL_DATA_DIR throwaway)は呼び出し側 fixture が設定する。
    inject: fault injection 指定(テスト専用の payload 変異、[(gate_name/field), ...] 相当)。
            既定 None=注入0件(T10)。注入由来レコードは injected=True(実所見と混ぜない=T5/T6)。
    fixture(probe_env)がこの API を呼ぶため、シグネチャは骨格固定(本体のみ FILL)。"""
<<<FILL>>>


<<<FILL>>>
```

**自由区間の内訳（末尾 FILL）:** stub model / throwaway 環境の構築と後始末 / 各ゲートの probe 実装 /
`FaultInjection` レジストリ / ラダー定義（callee の完全修飾シンボルを含む） / CLI エントリポイント /
`BREAKAGE_LIST.jsonl` の書き出し。

-----

## §5. 不変テスト（発注側同梱。worker は書かない・触らない）

|#          |内容                                                                    |これが守るもの            |
|-----------|----------------------------------------------------------------------|-------------------|
|**T1**     |実 `run_minimal_slice` / 実 `validate_approval` を import して呼ぶ。spy 使用 0 件|族E。spy への退化        |
|**T2**     |実行前後で canonical 台帳が sha256 バイト一致                                      |SoR 汚染             |
|**T3**     |`:8005` へ 1 回も接触しない                                                   |権限・予算              |
|**T4**     |実 repo に 1 バイトも書かない                                                   |人間の扉               |
|**T5 陽性対照**|不一致 2 件を注入 → **2 件とも**現れる（1件で止まらない）                                   |fail-fast 退化       |
|**T6 陰性対照**|注入 2 件のうち 1 件を除去 → **その 1 件だけ**消える                                    |**族A。プローブ自身の空振り検出**|
|**T7**     |再実行で `VOLATILE_FIELDS` を除きバイト一致                                       |計測の再現性             |
|**T8**     |ラダー全エントリの callee が解決し `source_ref` が成功する                              |手書き表の腐敗            |
|**T9**     |全レコードの `*_from` が実在ファイルの実在行範囲を指す                                      |族C。手書き申告           |
|**T10**    |既定走行で `injected=true` が 0 件                                           |注入機構の漏出            |
|**T11**    |override 済み上流がある下流は `CONDITIONAL_ON_OVERRIDE`                         |V-1                |
|**T12**    |**override されずに失敗した上流**がある下流は `CONDITIONAL_ON_UPSTREAM_FAILURE`       |**V-4。観測専用ゲートの汚染** |

配置: `tests/test_conformance_probe.py`。**骨格ではないので FILL は無い。全文がそのまま同梱される。**

```python
import json, os
import pytest
from twoder.probe.conformance_probe import (
    BREAKAGE_FIELDS, VOLATILE_FIELDS, bind_real, source_ref, run_ladder,
    GateOutcome, ProbeHalt,
)


def _strip(recs):
    return [{k: v for k, v in r.items() if k not in VOLATILE_FIELDS} for r in recs]


# T5 陽性対照: 2件注入 → 2件とも出る(1件で止まらない)
def test_t5_positive_control_two_faults_both_surface(probe_env):
    recs = probe_env.run(inject=["gate1_token/action_type", "gate2_grant/actor"])
    assert {r["gate"] for r in recs if r["injected"]} == {"gate1_token", "gate2_grant"}


# T6 陰性対照: 1件だけ除去 → その1件だけ消える(プローブ自身が空振りしていない証明)
def test_t6_negative_control_removal_is_localized(probe_env):
    both = probe_env.run(inject=["gate1_token/action_type", "gate2_grant/actor"])
    one = probe_env.run(inject=["gate2_grant/actor"])
    assert {r["gate"] for r in one if r["injected"]} == {"gate2_grant"}
    assert _strip([r for r in both if not r["injected"]]) == \
           _strip([r for r in one if not r["injected"]]), "注入除去が実所見を動かしている(汚染)"


# T7 再現性: 揮発フィールドを除きバイト一致
def test_t7_deterministic_across_runs(probe_env):
    a, b = probe_env.run(), probe_env.run()
    assert json.dumps(_strip(a), sort_keys=True) == json.dumps(_strip(b), sort_keys=True)


# T8 ラダーに死んだ手書き行が無い
def test_t8_ladder_entries_all_resolve(probe_env):
    for _name, dotted in probe_env.ladder_symbols():
        assert source_ref(bind_real(dotted))


# T9 出所は inspect 由来(手書き文字列禁止)
def test_t9_source_refs_are_real(probe_env):
    for r in probe_env.run():
        for key in ("expected_from", "actual_from"):
            if r[key] is None:
                continue
            path, _, span = r[key].rpartition(":")
            lo, _, hi = span.partition("-")
            assert os.path.isfile(path), r[key]
            assert 0 < int(lo) <= int(hi) <= len(open(path).readlines()), r[key]


# T10 既定走行では注入 0 件
def test_t10_no_injection_by_default(probe_env):
    assert not [r for r in probe_env.run() if r["injected"]]


# T11 override 下流は確定所見にしない(V-1)
def test_t11_downstream_of_override_is_conditional():
    out = []
    run_ladder([("g0", lambda: GateOutcome(passed=False, override=lambda: None)),
                ("g1", lambda: GateOutcome(passed=False))], out.append)
    assert out[0]["confidence"] == "DIRECT" and out[0]["override_applied"] is True
    assert out[1]["confidence"] == "CONDITIONAL_ON_OVERRIDE"
    assert out[1]["upstream_overrides"] == ["g0"] and out[1]["upstream_failed"] == []


# T12 override されなかった上流の失敗も下流を汚染する(V-4)
def test_t12_downstream_of_unfixed_failure_is_conditional():
    out = []
    run_ladder([("g0_observe", lambda: GateOutcome(passed=False)),   # override 無し=観測専用
                ("g1", lambda: GateOutcome(passed=False))], out.append)
    assert out[0]["confidence"] == "DIRECT" and out[0]["override_applied"] is False
    assert out[1]["confidence"] == "CONDITIONAL_ON_UPSTREAM_FAILURE"
    assert out[1]["upstream_failed"] == ["g0_observe"] and out[1]["upstream_overrides"] == []


# 全緑なら下流も DIRECT のまま(T11/T12 が常時 CONDITIONAL を返す退化の防止)
def test_all_pass_keeps_downstream_direct():
    out = []
    run_ladder([("g0", lambda: GateOutcome(passed=True)),
                ("g1", lambda: GateOutcome(passed=True))], out.append)
    assert [r["confidence"] for r in out] == ["DIRECT", "DIRECT"]


# halt 後は空欄にせず UNRESOLVED_NOT_TRAVERSED を出す(C2 規則)
def test_halt_emits_not_traversed_for_remainder():
    out = []
    def boom():
        raise ProbeHalt("x")
    run_ladder([("g0", boom), ("g1", lambda: GateOutcome(passed=True))], out.append)
    assert out[0]["unresolved"] == "UNRESOLVED_PROBE_HALTED"
    assert out[1]["unresolved"] == "UNRESOLVED_NOT_TRAVERSED" and out[1]["passed"] is None
```

### conftest（`probe_env` fixture・発注側同梱。worker は書かない・触らない）

配置: `tests/conftest.py`。§4 骨格の固定 API `run()`/`ladder_symbols()` への薄いラッパ。

```python
"""CONFORMANCE PROBE 発注側 fixture(worker は書かない・触らない)。

隔離規約(AB-0005 / DE-0378): throwaway EGL_DATA_DIR で台帳(DS event 流)を隔離する。
:8005 は触らない(run() が既定 stub chat_fn を使う=T3)。実 repo は無改変(T4)。
probe_env は conformance_probe の固定 API run()/ladder_symbols() への薄いラッパ。
ここに配管知能は無い(判断は probe 側)。"""
import os
import shutil
import tempfile

import pytest

from twoder.probe import conformance_probe as CP


class _ProbeEnv:
    """run()/ladder_symbols() を conformance_probe へ委譲するだけ(自作しない=導管)。"""

    def run(self, inject=None):
        return CP.run(inject=inject)

    def ladder_symbols(self):
        return CP.ladder_symbols()


@pytest.fixture()
def probe_env():
    d = tempfile.mkdtemp(prefix="probe_egl_")
    saved = {k: os.environ.get(k) for k in ("EGL_DATA_DIR",)}
    os.environ["EGL_DATA_DIR"] = d
    try:
        yield _ProbeEnv()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(d, ignore_errors=True)
```

> **T5 / T6 / T12 が本仕様の心臓。** これらが無いプローブは「何も出ませんでした」を出力でき、それは族A そのもの。
> T1–T4 は既存の隔離規約（AB-0005 / DE-0378）の適用なので conftest 側の fixture として実装する。

-----

## §6. claim ceiling

- 言えること: **「ここに不一致がある」**（行番号つき、`confidence` つき）
- **言えないこと:**
  - 「不一致は無い」→ 未走査は `UNRESOLVED_NOT_TRAVERSED`。空欄を「合格」と読ませない
  - 「ラダーが全ゲートを覆っている」→ `UNRESOLVED_LADDER_COMPLETENESS`
  - `CONDITIONAL_*` が実欠陥であること → 上流修正後の再走行で確定させる
  - `CONDITIONAL_*` が実欠陥で**ない**こと → 汚染の記録であって否定ではない
  - worker 出力の質 → stub model を通すため一切測っていない。測っているのは配管のみ
- **例外的に確定できるもの:** **death#2**。gate1b は #5 が HEAD に入った後の唯一の退化源を直接測るので、
  `distinct` の値が CLOSED / OPEN の判定として十分である（§3）

-----

## §7. 運用

```
CC が単独で走らせる（Taka 不要・:8005 不要・repo 無改変）
        ↓
BREAKAGE_LIST.jsonl を生のまま relay する ← CC は要約・解釈しない
        ↓
Web が DIRECT 所見を 1 本の仕様で一括修正
        ↓
再走行 → CONDITIONAL 所見が確定/消滅 → 2 巡目で空になる
```

**CC の職掌との整合（新フロー §1-1）:** 実装は**実装インスタンス**（working tree 直接）。CC-α は起草＋設計整合監査。
**実行は決定論スクリプトの起動**であり監査行為に含まれる、と仮定する。
ただし **CC は BREAKAGE_LIST を要約・解釈・優先順位付けしてはならない**（Qwen/Web が出力できるもの）。
**生の jsonl を relay するのみ。** 異論があれば Taka 裁定。

**修理後は捨てない。** `s10 --check` / `s11 --check` と同じ**常設ゲート**に載せる。
以後、境界の値を変えた瞬間に不一致が出る。**gate1b はそのまま death#2 の恒久回帰ゲートになる。**

-----

## §8. 直近の実行順

1. ~E1 補正を commit~ → **削除。** death#5 は HEAD 反映済で commit すべき diff 無し（CC 監査 07-23）
1. ✅ **`SEAM_PKG_MIRROR_v0_4` 実装済・12/12・commit `c1ffef5`**（death#6。**本仕様の前提**・達成済）
1. **本仕様を `egl/docs` へ投下 → 実装インスタンスが実装 → CC 設計整合監査 → 走行** → `BREAKAGE_LIST` 取得（**death#2 は gate1b で決着**）
1. Web が `DIRECT` 所見を 1 本の仕様で一括修正。
   **death#2 の修正（`generate_via_runner.py:45` の hardcoded 既定 ts 撤去）はここに含める。**
   §9 の恒久原則を同時に適用すれば #4（型不一致）も同じ仕様で消える
1. 再走行 → `CONDITIONAL_*` を確定/消滅させる
1. TOKEN-GATE-01（`approval_registry`）を canonical funnel で構築 → ★3(A) DONE

## §9. 併せて提案する恒久原則（族C / #2 / #4 / #5 を構造的に殺す）

> **境界を跨ぐ値は、両側が同じコンストラクタから作る。**

台帳の `sole writer` 規律（DE-0491）のインターフェース版。
**死因 #2 / #4 / #5 は全て同じ形をしている ——** token を `mint` する側と `validate` する側が別々にフィールドを組み立てている。
#5 を authority 側で直しても、呼び出し側に固定 ts が残っていた（#2）のがその証拠。
**同一コンストラクタから作れば、フィールド不整合も型不整合も固定既定値も表現不可能になる。**

プローブは**出血を止める**（検出）。この原則は**族を殺す**（予防）。両方要る。
本原則の DE 化は Taka 裁定待ち。**プローブの投入はこれを待たない。**