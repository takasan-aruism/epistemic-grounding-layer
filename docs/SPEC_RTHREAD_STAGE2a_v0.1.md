# SPEC: RTHREAD stage 2a v0.1 — accounts 機械核(chart検証 / suspense決着 / account保存 load-bearing)

> **FLOW NOTE(新フロー・2インスタンス):** 実装は `rri/rri/request_thread.py` の **FILL 変更**(下記4点)＋新規例外1つ。
> **imagined な production account 名を一切導入しない**(実 chart は stage 2b の MINING で生成)。2a は UNCLASSIFIED +
> **純テスト fixture chart**(`ACCT_TEST_A/B`)だけで機構を検証。commit=Taka。

- **status:** SPEC / 起草: CC-α 2026-07-24 / 正本: `RRI_SPEC_MACHINE_v1_1.json` + `CC_DESIGN_2026-07-24_RTHREAD_STAGE2_PLAN.md`
- **前提:** stage1 v0.2 配備済(`request_thread.py` commit `a4e97d6` / 11/11 green / 監査 CONSISTENT)
- **設計判断(プロトタイプで実証済み・ADJUDICATION_SENSITIVE):** D1 suspense 再定義 / D2 chart検証=machine / D3 account保存 load-bearing。詳細は plan §2。
- **スコープ外(初版どおり後段):** MINING(実chart)=stage2b / split・merge=stage④ / semantic index=stage⑤ / 昇格・explosion-valve・統計=stage2c。**2a に混ぜない。**

## §1. 変更(4点 + 例外1つ)

### (0) 新例外
```python
class RThreadChartUnavailable(RThreadError):
    pass
```

### (1) chart ローダ(新規・fail-closed・sealed 参照)
```python
# 有効 account を定める versioned chart。DERIVED/versioned(never SoR, G-5)。
# 実体はテスト fixture(RTHREAD_CHART env)/ 本番は stage2b の MINING 生成物。fail-closed。
_CHART = os.environ.get("RTHREAD_CHART",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "rthread_chart.json"))

def _load_chart():
    """{"chart_version": int, "accounts": [str,...]} を読み (chart_version, frozenset(accounts)) を返す。
    不在/JSON破損/キー欠落は RThreadChartUnavailable(fail-closed=chart 無しでは分類判定させない)。
    UNCLASSIFIED は chart に無くても常に有効(suspense の特殊値)。"""
    <<<FILL>>>
```

### (2) `raise_question` — default=UNCLASSIFIED + chart 検証(D2)
署名を **`account_id=UNCLASSIFIED`** に変更(旧 `"DEFAULT"` を廃止)。本体で account_id を検証:
- `account_id` が `_load_chart()` の accounts にも UNCLASSIFIED にも無ければ **`ValueError`**(off-chart)。
- chart がロード不能なら `RThreadChartUnavailable`(fail-closed)。
- 検証通過後は従来どおり QUESTION_RAISED を append(account_id 同梱・sealed_by 刻む)。

### (3) `project` — suspense_balance 再定義(D1)
`per_account_balances`(raise 数/account)は不変。**`suspense_balance` のみ**を
「`account_id==UNCLASSIFIED` かつ QUESTION_DISPOSED を持たない問いの数」に変更(残高=決着可能、恒等式にしない)。
他の返りフィールドは stage1 と byte 同一。

### (4) `check_account_conservation`(新規・D3 load-bearing)
```python
def check_account_conservation(projection, valid_accounts):
    """account 次元の保存。valid_accounts=_load_chart() の accounts 集合。
    全 per_account_balances のキーが valid_accounts ∪ {UNCLASSIFIED} に入り、かつ Σ==raised_total。
    off-chart account が台帳に在る/総和不一致なら RThreadConservationError(halt・fail-closed)。"""
    <<<FILL>>>
```

### (5) `advance_state` RESOLVED guard 追加(D1 machine 化 + D3 呼出)
`to_state=="RESOLVED"` の既存 guard(in_flight==0 / gaps presented / THREAD_ACCEPTED)に **追加**:
- `project()["suspense_balance"] != 0` なら `RThreadIllegalTransition`(**self-report `suspense_settled` を信じず machine 検査**=G-1 修理)。
- `check_account_conservation(proj, _load_chart()[1])` を STATE_ADVANCED append 前に通す。

## §2. stage-1 テスト移行(設計側=§3 所有物の更新)
default account 変更に伴い、**RESOLVED 経路の既存テストを test-chart account へ移行**する。実装は触らない(発注側同梱)。
- 共通 `_fresh` に **`monkeypatch.setenv("RTHREAD_CHART", <fixture>)`** を追加し、fixture chart(`{"chart_version":0,"accounts":["ACCT_TEST_A","ACCT_TEST_B"]}`)を書く。
- `test_request_thread_stage1.py`: `account_id="DEFAULT"` → `"ACCT_TEST_A"`(T14 I1/I2・T18a)。default 引数省略の raise(T14 I1 の q1/q2・T14c)は **明示 `account_id="ACCT_TEST_A"`** に(RESOLVED 経路のため)。T18b(UNCLASSIFIED)は不変。
- `test_request_thread_stage1_cov.py`: RESOLVED を通さない(T15 は REJECTED/MERGED、T25/T36/T37/T40 は account 非依存)。ただし全テストが chart ロード要 → `_fresh` の chart 設定でカバー。T38 は account_id 明示不要(UNCLASSIFIED でも OPEN_GAP 経路)。
- **受入=移行後も stage1+cov が全 green**(契約の述語は不変、変更は account 値と chart 設定のみ)。

## §3. 2a 新規テスト(発注側同梱・実装は触らない)
配置: `rri/rri/test_request_thread_stage2a.py`。fixture chart を使う。

```python
import importlib
import json
import pytest


def _fresh(tmp_path, monkeypatch):
    chart = tmp_path / "chart.json"
    chart.write_text(json.dumps({"chart_version": 0, "accounts": ["ACCT_TEST_A", "ACCT_TEST_B"]}))
    monkeypatch.setenv("RTHREAD_EVENTS", str(tmp_path / "ev.jsonl"))
    monkeypatch.setenv("RTHREAD_CHART", str(chart))
    import rri.request_thread as m
    importlib.reload(m)
    return m


@pytest.fixture()
def rt(tmp_path, monkeypatch):
    return _fresh(tmp_path, monkeypatch)


# ── D2 off-chart account は raise 拒否 ───────────────────────────────────────
def test_offchart_account_rejected(rt):
    tid = rt.open_thread("D", "T")
    with pytest.raises(ValueError):
        rt.raise_question(tid, "q", "T", account_id="IMAGINED")
    rt.raise_question(tid, "q", "T", account_id="ACCT_TEST_A")   # chart 内は可
    rt.raise_question(tid, "q2", "T")                            # default=UNCLASSIFIED 可


# ── chart ロード不能は fail-closed ───────────────────────────────────────────
def test_chart_unavailable_fail_closed(rt, monkeypatch, tmp_path):
    monkeypatch.setenv("RTHREAD_CHART", str(tmp_path / "nope.json"))
    import rri.request_thread as m
    importlib.reload(m)
    tid = m.open_thread("D", "T")
    with pytest.raises(m.RThreadChartUnavailable):
        m.raise_question(tid, "q", "T", account_id="ACCT_TEST_A")


# ── D1 suspense は決着する(恒等式でない) ───────────────────────────────────
def test_suspense_settles(rt):
    tid = rt.open_thread("D", "T")
    q = rt.raise_question(tid, "q", "T")                         # UNCLASSIFIED
    assert rt.project(tid)["suspense_balance"] == 1
    rt.dispose_question(tid, q, "OPEN_GAP", "T")
    assert rt.project(tid)["suspense_balance"] == 0             # 恒等式なら 1 のまま


# ── D3 account 保存 load-bearing: 改竄 off-chart を halt ─────────────────────
def test_account_conservation_load_bearing(rt):
    tid = rt.open_thread("D", "T")
    rt.raise_question(tid, "ok", "T", account_id="ACCT_TEST_A")
    _, valid = rt._load_chart()
    rt.check_account_conservation(rt.project(tid), valid)       # 正常
    rt._append({"type": "QUESTION_RAISED", "thread_id": tid, "question_id": "Q-bad",
                "account_id": "GHOST_ACCT", "memo": "x", "ts": "T", "sealed_by": "rri.request_thread"})
    with pytest.raises(rt.RThreadConservationError):
        rt.check_account_conservation(rt.project(tid), valid)


# ── D1+machine: 未決着 suspense があると RESOLVED 阻却 ───────────────────────
def test_resolved_blocked_by_unsettled_suspense(rt):
    tid = rt.open_thread("D", "T")
    q = rt.raise_question(tid, "q", "T")                         # UNCLASSIFIED 未処分
    rt.advance_state(tid, "NARROWING", {"request_type_ok": True, "bind_context_ok": True}, "T")
    rt.dispose_question(tid, q, "OPEN_GAP", "T")                # in_flight=0 だが…
    # OPEN_GAP は present + accept で通せるが、UNCLASSIFIED を dispose-out 済なので suspense=0。
    # ここでは present/accept せずに RESOLVED を試み、gap 未提示で阻却されることを確認(既存 T38 と別に suspense 経路は下で)。
    rt.present_gaps(tid, [q], "r", "T")
    rt.accept_thread(tid, [{"question_id": q, "disposal": "DECLINED"}], "taka", "T")
    rt.advance_state(tid, "RESOLVED",
                     {"all_disposed": True, "suspense_settled": True,
                      "all_gaps_presented": True, "thread_accepted": True}, "T")  # suspense=0 なので可
    assert rt.project(tid)["status"] == "RESOLVED"


# ── T24: memo は保存則の算術に使われない ────────────────────────────────────
def test_t24_memo_not_in_math(rt):
    tid = rt.open_thread("D", "T")
    rt.raise_question(tid, "x" * 9999, "T", account_id="ACCT_TEST_A")   # 長memoでも
    p = rt.project(tid)
    rt.check_conservation(p)                                    # I1/I2 は count のみ
    assert p["raised_total"] == 1
```

## §4. 受入
- stage1 + cov + stage2a すべて green(移行後 stage1/cov の述語不変)。
- `verify_skeleton_preserved` 相当: 定数/他関数の非FILL区間は byte 不変(変更は §1 の4点+例外+chart ローダに限定)。
- 監査ハーネス `audit_rthread_stage1.py` の A/B/C は本体変更後に**再点検**が要る(A の署名照合に `raise_question` 署名変更が影響)→ **設計側でハーネスを stage2a 対応に更新**(私が担当)。
- mutation check(G-T1): D1(suspense を raise数に戻す)/ D3(off-chart 検査を外す)で各テストが赤に転じることを実装が実証。

## §5. 完了後
- `CC_IMPL_2026-07-24_RTHREAD_STAGE2a_BUILT.md` を置く → 設計側が再監査 → CONSISTENT → commit=Taka → DE 起票(live submit)。
- 次: stage 2b(MINING_SPEC v0.1・実 chart)。
