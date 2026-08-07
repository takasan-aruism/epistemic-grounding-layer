# 【BUILD SPEC】`受入(2)` — **★1件では 足りません（★2件 選びます・★理由つき）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 01:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝1・3・4
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★新しい欄の発明0 ／ ★Claude の配線 ★上限10行**

---

## 1. ★★まず 依頼を 1つ 直します（★1件では 受入(2) が 永久に 満たせない）

```
★MGR の依頼 = ★『86件のうち 1件を 選び、在る／無い／辿れない を 機械が 答える』
★★実測 = ★★86件は ★全件 ★鍵を 持ちません（★`gaps` の 鍵の有無 = ★0/98）
★★★∴ ★どれを 選んでも ★答えは ★★『辿れない』の1つだけ。
★★★★∴ ★MGR の受入(2)『★"在る" と答えた時 = file が実在し symbol が その中に在ること』は
   ★★★永久に 発火しません（★"在る" が 出ないため）。
★★★★★∴ ★★2件 選びます ―― ★『辿れない』を示す1件 と ★『在る』を示す1件。
   ★これは 依頼を 広げたのでは なく、★★受入(2)が 成立する 最小の形です。
```

## 2. ★★私が 選んだ2件（★MGR は 選ばない・★私が 決める）

```
★★(あ) 『辿れない』側 = ★★`G-04`
     逐語: {"id":"G-04","summary":"DS に選別も断りの返答も無い(空入力は ValueError)",
             "kind":"gap","status":"OPEN","evidence":["READ: ds/phase0.py:101"]}
     ★機械が読める鍵の欄 = ★★無い
     ★★選んだ理由 = ★★いちばん惜しい例です ―― ★場所は `evidence` の 散文に 書いて在る
        （`READ: ds/phase0.py:101`）のに、★★機械が 読める欄に 入っていない。
        ★★『鍵が 無い』の 正体が ★『誰も 書かなかった』ではなく ★『散文にしか 無い』だと 見えます。
     ★★★都合のよい1件を 選んでいない ことの 説明 = ★これは ★★答えが 出ない側です。

★★(い) 『在る』側 = ★★`C-DS-RECORD`
     逐語: {"id":"C-DS-RECORD","repo":"ds","file":"ds/ds/phase0.py","symbol":"record_utterance", …}
     ★★私が 先に 確かめた = ★`ds/ds/phase0.py:91` に ★`def record_utterance(` が 在る（★逐語）
     ★★選んだ理由 = ★★`在る` が 実際に 出ることを ★確かめられる1件が ★要るからです。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
設計図の1つの記述について、実物へ辿れるか・在るかを判定する純関数 impl.trace_entry を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
entry   = dict。設計図の1つの記述。
sources = dict。ファイルの場所を鍵、そのファイルの中身(str)を値とする。
戻り値 = {"verdict": str, "file": str または None, "symbol": str または None, "missing": str または None}

★verdict は UNTRACEABLE / PRESENT / ABSENT の3語のいずれか。他の語を作らない。

★読み方は5通り。★上から順に、最初に当てはまった1つで決める。

(1) entry が dict でない
    → {"verdict":"UNTRACEABLE", "file":None, "symbol":None, "missing":"entry"}
(2) entry["file"] が str でない、または 前後の空白を除くと 空
    → {"verdict":"UNTRACEABLE", "file":None, "symbol":None, "missing":"file"}
(3) sources が dict でない、または entry["file"] が sources の鍵に無い
    → {"verdict":"UNTRACEABLE", "file":その file, "symbol":entry の symbol(str なら) または None,
       "missing":"source"}
(4) entry["symbol"] が str であり 前後の空白を除くと 1文字以上ある場合:
      その中身の中に "def <symbol>(" または "class <symbol>(" または "class <symbol>:" が
      1つでもあれば → {"verdict":"PRESENT", "file":…, "symbol":…, "missing":None}
      1つも無ければ  → {"verdict":"ABSENT",  "file":…, "symbol":…, "missing":None}
(5) symbol が 無い（str でない・空）
    → {"verdict":"PRESENT", "file":…, "symbol":None, "missing":None}
       ★理由: ファイルは 在ったのだから 場所としては 辿れている。

★大文字小文字は そろえない。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def trace_entry(entry, sources):
    # <<<FILL: この行を 実装で 置き換える（★この行は 残さない）>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★fixture は 実物の2件）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★実物(egl/docs/2DER_EXECUTION_ARCHITECTURE.json より・逐語)
G04 = {"id": "G-04", "summary": "DS に選別も断りの返答も無い(空入力は ValueError)",
       "kind": "gap", "status": "OPEN", "evidence": ["READ: ds/phase0.py:101"]}
CDS = {"id": "C-DS-RECORD", "repo": "ds", "file": "ds/ds/phase0.py",
       "symbol": "record_utterance", "status": "LIVE"}
SRC = {"ds/ds/phase0.py": "import json\n\ndef record_utterance(speaker, raw_text):\n    pass\n"}

def test_gap_without_a_file_field_is_untraceable():
    """★86件は 全件 これになる（★『無い』と 混ぜない）"""
    r = impl.trace_entry(G04, SRC)
    assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "file", r

def test_component_with_symbol_present_is_present():
    r = impl.trace_entry(CDS, SRC)
    assert r["verdict"] == "PRESENT" and r["file"] == "ds/ds/phase0.py", r

def test_component_with_symbol_missing_is_absent():
    r = impl.trace_entry(CDS, {"ds/ds/phase0.py": "import json\n"})
    assert r["verdict"] == "ABSENT" and r["symbol"] == "record_utterance", r

def test_file_not_in_sources_is_untraceable_not_absent():
    """★読めなかったのに『無い』と言わない（★規律 v1.17）"""
    r = impl.trace_entry(CDS, {})
    assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "source", r

def test_class_definition_counts_as_present():
    r = impl.trace_entry({"file": "a.py", "symbol": "Foo"}, {"a.py": "class Foo:\n    pass\n"})
    assert r["verdict"] == "PRESENT", r

def test_entry_without_symbol_is_present_when_the_file_is_there():
    r = impl.trace_entry({"file": "a.py"}, {"a.py": "x = 1\n"})
    assert r["verdict"] == "PRESENT" and r["symbol"] is None, r

def test_a_mention_is_not_a_definition():
    """★名前が 出てくるだけでは 在るとしない"""
    r = impl.trace_entry({"file": "a.py", "symbol": "record_utterance"},
                         {"a.py": "# record_utterance を呼ぶ\nrecord_utterance()\n"})
    assert r["verdict"] == "ABSENT", r

def test_blank_file_field_is_untraceable():
    r = impl.trace_entry({"file": "   ", "symbol": "x"}, SRC)
    assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "file", r

def test_non_dict_entry_is_untraceable():
    for x in (None, "G-04", [], 3):
        r = impl.trace_entry(x, SRC)
        assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "entry", x
<<<2DER:END>>>
```

## 4. ★★受入（★口・欄・★id を 載せる物として）

```
★(1) ★9本 全通（★worker が書く・★Claude は本文0行）
★(2) ★★`G-04` を 実物の資料と 実物の source で 通すと ★★`UNTRACEABLE` ／ `missing="file"`
     ★id = ★`G-04`（★報告に 書く）
★(3) ★★`C-DS-RECORD` を 通すと ★★`PRESENT` ／ `file="ds/ds/phase0.py"` ／ `symbol="record_utterance"`
     ★id = ★`C-DS-RECORD`（★報告に 書く）
     ★★私が 先に 確かめた根拠 = ★`ds/ds/phase0.py:91` に ★`def record_utterance(` が 在る
★★(4) ★★陰性 = ★★`UNTRACEABLE` が ★1件も `ABSENT` に なっていないこと
     ―― ★★ここが 混ざった時点で ★この機能は 無意味です（★MGR の指摘どおり）
★(5) ★新台帳0・新エンドポイント0 ／ ★(6) ★Claude の配線（★上限10行）
★(7) ★戻せる（★置いた1本を 2DER が commit する） ／ ★(8) ★61本を走らせない
```

## 5. ★★私が 言っていないこと

```
★『86件が 辿れるようになる』―― ★★1件も 辿れません。★★機械が『辿れない』と 言えるようになるだけです。
★『G-04 の 中身が 正しい』―― ★★見ていません。★★辿れないので 見に行けません。
★『鍵を 足す』―― ★★本件では 足しません（★1件 通してから 次を 決める＝MGR のとおり）。
★『意味の1行を LLM が 当てる』―― ★★本件には 入れていません。
   ★★理由 = ★★当てる前に ★『当てた先が 在るか』を 機械が 言える必要が 在り、★それが 本件です。
```
