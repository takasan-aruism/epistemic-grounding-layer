# 【裁定＋BUILD SPEC】`trace_entry v2` — **★広げても 救われるのは 1件だけ（★残り15件は 別の話）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 03:0x / TYPE=裁定＋BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝1・3・4
- **★核1（★差し替え）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限10行**

---

## 1. ★★先に 測った（★『どこまで 広げるか』を 当てずに 決めるため）

```
★`def` / `class` で 見つからなかった ★16件を、★★『module 直下の代入』も 見て 数え直した:

  ★★代入で 見つかる     = ★★1件 ―― ★`SM-DW`（symbol=`_MAP`）
  ★★代入でも 見つからない = ★★15件

★★★その15件の symbol を 逐語で 見ると ―― ★★どれも ★関数名では ありません:
     `POST /api/submit` ／ `GET /api/resolve` ／ `__main__ via -m twoder.submit` ／
     `python3 twoder/submit.py` ／ `dispatch_once caller (line 151)` ／
     `register / record_change / verify` ／ `detect / next_legal_operation` ／
     `open_run/emit/span/resolve_run/…` ／ `4軸のうち context_anchoring のみ` …
★★★★∴ ★★広げる価値は ★★1件。★残り15件は ★★どこまで広げても 届きません
   ―― ★★symbol 欄に ★『HTTP の口』『複数の名前』『散文』が 入っているからです。
   ★★これは MGR §3 の言うとおり ★★欄の形の話（★`EVO-0049` と 同じ病気）。
```

## 2. ★★裁定（★MGR が 私に 決めさせた2点）

```
★(a) ★どこまで 広げるか = ★★1つだけ 足す ―― ★『module 直下の代入』。
     ★理由 = ★★実測で 1件 救われる。★それ以上 広げても ★0件（★§1）。
     ★★『念のため 広く』を しない ―― ★★返りが 見えない厳格さを 足さない。

★★(b) ★『無い』と 言ってよい 条件 = ★★symbol が ★Python の識別子である 時 だけ。
     ★識別子でない（★空白・記号・スラッシュを 含む 等）→ ★★`UNTRACEABLE`（★見ていない側）
     ★★∴ ★★`ABSENT` は ★★『識別子なのに ★def でも class でも 代入でも 無い』時だけ 残る。
     ★★★これで ★機械が 嘘をつく所（★MGR の指摘）が ★消えます。

★(c) ★差し替えの手順 = ★★新しい名前で 置く（`trace_entry_v2`）。★古い方は 消さない。
     ★理由 = ★版の管理は ★Taka の「後の宿題」∴ ★★いま 版を 作らない。
     ★★名前で 分けるのは ★本日 私が 出した裁定（★『相手が読める』を 量より 優先）と 同じ。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
設計図の1つの記述について、実物へ辿れるか・在るかを判定する純関数 impl.trace_entry_v2 を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
entry   = dict。設計図の1つの記述。
sources = dict。ファイルの場所を鍵、そのファイルの中身(str)を値とする。
戻り値 = {"verdict": str, "file": str または None, "symbol": str または None,
          "missing": str または None, "searched": list}

★verdict は UNTRACEABLE / PRESENT / ABSENT の3語のいずれか。他の語を作らない。
★searched は 見た形の名前を並べた list。見なかった時は 空の list。

★読み方は6通り。★上から順に、最初に当てはまった1つで決める。

(1) entry が dict でない
    → UNTRACEABLE / file=None / symbol=None / missing="entry" / searched=[]
(2) entry["file"] が str でない、または 前後の空白を除くと 空
    → UNTRACEABLE / file=None / symbol=None / missing="file" / searched=[]
(3) sources が dict でない、または entry["file"] が sources の鍵に無い
    → UNTRACEABLE / file=その file / symbol=(str なら その値、他は None) / missing="source" / searched=[]
(4) entry["symbol"] が str でない、または 前後の空白を除くと 空
    → PRESENT / file=その file / symbol=None / missing=None / searched=[]
       ★理由: ファイルは 在ったので 場所としては 辿れている。
(5) symbol の 前後の空白を除いた物が ★Python の識別子でない
    （★英字か下線で 始まり、以降が 英数字か下線だけ、という形に 当てはまらない）
    → UNTRACEABLE / file=その file / symbol=その値 / missing="symbol_not_an_identifier" / searched=[]
(6) 上のどれでもない場合、中身の中を 次の3つの形で 探す。searched=["def","class","assign"]
      "def <symbol>(" があれば → PRESENT
      "class <symbol>(" か "class <symbol>:" があれば → PRESENT
      行の先頭から "<symbol> =" か "<symbol> :" で 始まる行があれば → PRESENT
      どれも無ければ → ABSENT
    ★PRESENT / ABSENT のどちらも file と symbol を そのまま返し、missing は None。

★大文字小文字は そろえない。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def trace_entry_v2(entry, sources):
    # <<<FILL: この行を 実装で 置き換える（★この行は 残さない）>>>
<<<2DER:END>>>
```

**★封印試験（★10本・★fixture は 実物）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★実物(egl/docs/2DER_EXECUTION_ARCHITECTURE.json より・逐語)
SMDW = {"id": "SM-DW", "file": "dev-workcell/dw/dispatch.py", "symbol": "_MAP"}
EPWS = {"id": "EP-WEBUI-SUBMIT", "file": "twoder/webui.py", "symbol": "POST /api/submit"}
CDS  = {"id": "C-DS-RECORD", "file": "ds/ds/phase0.py", "symbol": "record_utterance"}

SRC = {"dev-workcell/dw/dispatch.py": "import json\n_MAP = {\n  'CREATED': 1,\n}\n",
       "twoder/webui.py": "def submit():\n    pass\n",
       "ds/ds/phase0.py": "def record_utterance(a, b):\n    pass\n"}

def test_module_level_assignment_is_present():
    """★実物: _MAP は dispatch.py に在る(★v1 では ABSENT と出ていた)"""
    r = impl.trace_entry_v2(SMDW, SRC)
    assert r["verdict"] == "PRESENT" and "assign" in r["searched"], r

def test_symbol_that_is_not_an_identifier_is_untraceable():
    """★実物: symbol に HTTP の口が入っている(★『無い』と言わない)"""
    r = impl.trace_entry_v2(EPWS, SRC)
    assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "symbol_not_an_identifier", r
    assert r["searched"] == [], r

def test_a_real_function_is_still_present():
    """★意味が 変わっていないこと(その1)"""
    r = impl.trace_entry_v2(CDS, SRC)
    assert r["verdict"] == "PRESENT", r

def test_a_真に_missing_identifier_is_absent():
    """★意味が 変わっていないこと(その2)=★識別子なのに どの形でも 無い → ABSENT"""
    r = impl.trace_entry_v2({"file": "ds/ds/phase0.py", "symbol": "no_such_symbol"}, SRC)
    assert r["verdict"] == "ABSENT" and r["missing"] is None, r
    assert r["searched"] == ["def", "class", "assign"], r

def test_absent_carries_what_was_searched():
    """★『無い』と言う時は 何を見たかが 同じ所に 出る"""
    r = impl.trace_entry_v2({"file": "ds/ds/phase0.py", "symbol": "zzz"}, SRC)
    assert r["searched"] == ["def", "class", "assign"], r

def test_class_definition_is_present():
    r = impl.trace_entry_v2({"file": "a.py", "symbol": "Foo"}, {"a.py": "class Foo:\n    pass\n"})
    assert r["verdict"] == "PRESENT", r

def test_file_not_in_sources_is_untraceable():
    r = impl.trace_entry_v2(CDS, {})
    assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "source", r

def test_entry_without_symbol_is_present():
    r = impl.trace_entry_v2({"file": "a.py"}, {"a.py": "x = 1\n"})
    assert r["verdict"] == "PRESENT" and r["symbol"] is None, r

def test_a_mention_is_not_a_definition():
    r = impl.trace_entry_v2({"file": "a.py", "symbol": "foo"}, {"a.py": "foo()\n# foo = 1 in a comment\n"})
    assert r["verdict"] == "ABSENT", r

def test_non_dict_entry_is_untraceable():
    for x in (None, "SM-DW", [], 3):
        r = impl.trace_entry_v2(x, SRC)
        assert r["verdict"] == "UNTRACEABLE" and r["missing"] == "entry", x
<<<2DER:END>>>
```

## 4. ★★受入（★口・欄・★id）

```
★(1) ★10本 全通（★worker が書く・★Claude は本文0行）
★(2) ★★`SM-DW` が ★`PRESENT`（★『無い』ではない答え）＋ ★`searched` に "assign" が 在る
     ★id = ★`SM-DW`（★報告に 書く）
★(3) ★★意味が 変わっていないことを 確かめる1件（★私が 選びます）=
     ★★`C-DS-RECORD`（`ds/ds/phase0.py` / `record_utterance`）が ★`PRESENT` の まま
     ★★そして ★同じ file に 実在しない識別子（`no_such_symbol`）を 当てると ★`ABSENT` の まま
     ―― ★★この2つで ★PRESENT と ABSENT の 意味が 動いていないことが 出ます。
★★(4) ★★陰性 = ★★`EP-WEBUI-SUBMIT`（symbol=`POST /api/submit`）が ★★`ABSENT` に ならない こと
     ―― ★★ここが `ABSENT` のままなら ★機械は まだ 嘘をついています。
★(5) ★LLM 0回 ／ ★(6) ★新台帳0・新エンドポイント0・★Claude の配線（★上限10行）
★(7) ★戻せる（★置いた1本を 2DER が commit する）／ ★(8) ★61本を走らせない
```

## 5. ★★次に 何が 起きるか（★予告ではなく 数え方から出る 見込み）

```
★★178件を 測り直すと ―― ★`ABSENT` は ★★0件に なる 見込みです。
   ★理由 = ★§1 の16件は ★1件が PRESENT へ、★15件が UNTRACEABLE へ 移るため。
★★★∴ ★★『実物が 無い』と 言える記述は ★★まだ 1件も 無い、が 正しい現在地に なります。
   ―― ★これは ★後退では ありません。★★機械が 嘘をつかなくなった、です。
★★★★そして ★次に 効くのは ★★`UNTRACEABLE 150+15` の 中身を 分けること（★鍵が無い／欄の形／識別子でない）。
   ―― ★★但し ★それは ★次の1件です。★本件では やりません。
```

## 6. ★★私が 言っていないこと

```
★『15件の 欄を 直す』―― ★★直しません（★MGR §3・★明細化と 一緒）。
★『広げれば もっと 見つかる』―― ★★見つかりません（★§1 の実測＝1件だけ）。
★『v1 を 捨てる』―― ★★捨てません（★名前で 分ける・★版の管理は 後の宿題）。
★『設計図が 正しい／間違っている』―― ★★まだ 言えません。
```
