# 【BUILD SPEC v3】`EVO-0049` — **★『分からない』を signals に載せる（★列挙は増やさない）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 19:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035` ／ 台帳: `ITEM-2DER-EVO-0049`
- **★v2 からの差は ★docstring 4本の言い回しだけ**（★`assert`・★`def test_` の名前・★fixture は ★1文字も変えない）
- **★v1 からの差は ★試験を1本 足しただけ**（★既存8本は ★1本も緩めない・★依頼文は ★1文字も変えない）
- **★足した理由**: ★`binder_present` が True の時に ★`context_supplied` を ★見てしまう実装が ★通った（MGR 実測）。★規則の ★順序が ★縛られていなかった
- **★v1.8 の宣言**: **★核は在る・1件**（`intent_status_from_signals`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **2〜4行**（★`signals` に1欄）
- **★`decision` の5語は ★1つも増やさない**（★MGR 裁定(ii)）／ **★新しい検知を作らない**
- **★新台帳0・★新エンドポイント0・★2本目の patterns を作らない**

---

## 1. ★★新しく測るものは無い（★実測）

```
★`rri/rri/preflight_gate.py:250-253` の signals は ★既に 次を持っている（逐語）:
      "binder_present": False, "binder_reason": reason, "binder_candidates": found,
      "context_supplied": context is not None
★★∴ ★『文脈が無くて読み取れない』は ★★この2欄から ★決定論で導ける
   （★input-clarity の逐語『文脈が無く読み取れない → ★でっち上げず素直に判断不能』と ★同じ形）
★★★∴ ★作るのは ★★『導く1つの関数』だけ。★検知は ★作らない・★触らない。
```

## 2. ★★契約

**★依頼文**
```
警告の理由から意図の読み取り状態を決める純関数 impl.intent_status_from_signals を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
signals = dict（preflight_gate が作る警告の理由。関係する欄は
          "binder_present": bool, "context_supplied": bool）
戻り値 = str。★NOT_ASSESSED / CLEAR / INDETERMINATE_NO_CONTEXT / AMBIGUOUS の★4語のいずれか。
         ★他の語を作らない。

・signals が dict でなければ "NOT_ASSESSED"。
・"binder_present" が bool でなければ "NOT_ASSESSED"。
・"binder_present" が True なら "CLEAR"（束縛先が在る＝読める）。
・ここから先は "binder_present" が False の場合:
    ・"context_supplied" が bool でなければ "NOT_ASSESSED"。
    ・"context_supplied" が False なら "INDETERMINATE_NO_CONTEXT"（文脈が渡されていない）。
    ・"context_supplied" が True なら "AMBIGUOUS"（文脈は在るのに束縛先が無い）。
・★情報が足りない時は "NOT_ASSESSED" を返す（★決めつけない）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def intent_status_from_signals(signals):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★fixture は `preflight_gate.py:250-253` の実物の形）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# 実物の signals(逐語): matched_surface / binder_present / binder_reason /
#                       binder_candidates / context_supplied / surface_rule / match_mode / binder_rule
BASE = {"matched_surface": "それ", "binder_present": False, "binder_reason": "no-binder",
        "binder_candidates": [], "context_supplied": False,
        "surface_rule": "SURF-RULE-001", "match_mode": "SENTENCE_INITIAL_BARE",
        "binder_rule": "BIND-RULE-001"}

def test_no_context_is_indeterminate():
    """★context_supplied が False の時は ★INDETERMINATE_NO_CONTEXT を返す"""
    assert impl.intent_status_from_signals(BASE) == "INDETERMINATE_NO_CONTEXT"

def test_context_but_no_binder_is_ambiguous():
    """★文脈が在り ★束縛先が空の時は ★AMBIGUOUS を返す"""
    assert impl.intent_status_from_signals(dict(BASE, context_supplied=True)) == "AMBIGUOUS"

def test_binder_present_is_clear():
    assert impl.intent_status_from_signals(dict(BASE, binder_present=True)) == "CLEAR"

def test_binder_present_wins_even_without_context():
    """★束縛先が在る時は ★binder_present だけで ★CLEAR を決める（★順序が効くこと）"""
    s = dict(BASE, binder_present=True); s.pop("context_supplied")
    assert impl.intent_status_from_signals(s) == "CLEAR"
    assert impl.intent_status_from_signals(dict(BASE, binder_present=True,
                                                context_supplied="yes")) == "CLEAR"

def test_non_dict_is_not_assessed():
    assert impl.intent_status_from_signals(None) == "NOT_ASSESSED"

def test_missing_binder_field_is_not_assessed():
    s = dict(BASE); s.pop("binder_present")
    assert impl.intent_status_from_signals(s) == "NOT_ASSESSED"

def test_missing_context_field_is_not_assessed():
    """★欄が欠けている時は ★NOT_ASSESSED を返す"""
    s = dict(BASE); s.pop("context_supplied")
    assert impl.intent_status_from_signals(s) == "NOT_ASSESSED"

def test_all_four_words_are_reachable():
    got = {impl.intent_status_from_signals(None),
           impl.intent_status_from_signals(dict(BASE, binder_present=True)),
           impl.intent_status_from_signals(BASE),
           impl.intent_status_from_signals(dict(BASE, context_supplied=True))}
    assert got == {"NOT_ASSESSED", "CLEAR", "INDETERMINATE_NO_CONTEXT", "AMBIGUOUS"}, got

def test_never_outside_the_four():
    for s in (None, "x", {}, BASE, dict(BASE, context_supplied=True),
              dict(BASE, binder_present=True), dict(BASE, binder_present="yes")):
        assert impl.intent_status_from_signals(s) in (
            "NOT_ASSESSED", "CLEAR", "INDETERMINATE_NO_CONTEXT", "AMBIGUOUS")
<<<2DER:END>>>
```

## 3. ★Claude の配線（★2〜4行）

```python
# preflight_gate.py:250-253 の signals に 1欄 足す（★_gate_referent だけ）
                "signals": {..., "binder_rule": "BIND-RULE-001",
                            "intent_status": intent_status_from_signals({...上と同じ辞書...})},
```
```
★`decision` は ★触らない（★CLARIFY_FIRST のまま＝★既に隔離する）
★★`_gate_past_reference`(:186 の signals)は ★触らない（★1つずつ）
★★★`submit.py` も ★触らない（★`signals` は ★既に `_rec("RRI_PREFLIGHT", …)` で ★台帳に載っている＝:309-311）
```

## 4. 受入

```
★(0) ★worker が書く（★Claude は本文0行）・★9本 全通
★(1) ★★文脈なしで ★指示語だけの投入を1本 行い、★`RRI_PREFLIGHT.signals.intent_status` が
     ★★`INDETERMINATE_NO_CONTEXT` と ★逐語で読める
     ★★★再現できなければ ★『再現できなかった』と書いて ★止まる（★捏造した入力を作らない）
★(2) ★`decision` が ★`CLARIFY_FIRST` のままであること（★5語が ★増えていない）
★(3) ★DW task が ★作られないこと（★隔離は ★既存のまま＝★submit.py:312）
★(4) ★`_gate_past_reference` の signals が ★1文字も変わっていないこと
★(5) ★sha256 一致 ／★(6) ★Claude の配線行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★★★予告を投入前に書く: ★行数 ／ ★(1) で出ると思う語
```

## 5. ★★これで分からないこと（★先に言う）

```
★★これは ★『何を隔離するか』を ★1行も増やさない ―― ★増えるのは ★★『なぜ隔離したか』の1語だけ。
★★★中の表に ★行が増えない限り ★★捕まる入力は ★今日と同じである（★人の手順が回って初めて増える）。
★★★★`observed_count` 等は ★依然 誰も書かない ∴ ★自動抑制は ★動かないまま（★別件・名指し済）
★★★★★`AMBIGUOUS` と `INDETERMINATE_NO_CONTEXT` の ★どちらが多いかは ★測っていない ∴ ★書かない
```

## 6. 禁止

```
★`decision` に ★6語目を足す（★裁定(ii)）／ ★新しい検知規則を ★作る
★`_gate_past_reference` を ★同時に触る ／ ★`submit.py` を ★触る
★2本目の patterns を作る ／ ★外(:8793)のプロセスを ★呼ぶ
★情報が足りない時に ★`INDETERMINATE_NO_CONTEXT` と ★決めつける（★`NOT_ASSESSED`）
★★『分からない入力を隔離できるようになった』と書く（★§5・★行は増えていない）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
