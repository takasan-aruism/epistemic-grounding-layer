# 【BUILD SPEC】`trace_entry_v2`（★出し直し） — **★骨格に 目印の行を 置かない**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 16:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝4と1
- **★核1 ／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限6行 ／ ★封印試験は 前の版と ★同一**

---

## 1. ★★何を 変えたか（★1つだけ・★減らす直し）

```
★★骨格から ★`# <<<FILL: …>>>` の行を ★消しました。★それだけです。
★理由（★MGR 裁定(2)(3)・★元は 私の案）:
   ★『この行は 残さない』と 書いても ★★守られませんでした
     ―― ★逐語（★本日 15:38 の判定）『成果物の先頭に「<<<FILL: この行を 実装で 置き換える
        （★この行は 残さない）>>>」が残っており…』
   ★★∴ ★書き方で 直すのを やめ、★★置かない 形に します。
★★★これは ★足す直しでは ありません（★試験も 増やしません）。
```

## 2. ★★成立することを 先に 確かめた（★feasibility-first）

```
★共通テンプレートの 逐語 = 『★<<<FILL>>> が 無い場合: 骨格全体を bytes 一致で 保ち、
                            ★その続きに 実装を 書く。』
★★私が 機械で 確かめた（★`_skeleton_fixed_segments` / `verify_skeleton_preserved` に そのまま 通した）:
   ★FILL 無しの骨格 → ★固定区間は ★★骨格全体の1つ
   ★worker が 続きを 書いた物  → ★★通る（True）
   ★骨格を 書き換えた物        → ★★落ちる（True で 落ちる）
★★★∴ ★検査の 強さは ★1つも 落ちません。
```

## 3. ★★契約

**★依頼文（★届かないと 分かっていますが 規律どおり 書きます）**
```
設計図の1つの記述について、実物へ辿れるか・在るかを判定する純関数 impl.trace_entry_v2 を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
規則は 骨格の docstring に 書いてあります。骨格の行は 1文字も 変えず、その続きに 実装を 書いてください。
```

**★骨格（★★目印の行は 在りません）**
```
<<<2DER:SKELETON>>>
def trace_entry_v2(entry, sources):
    """設計図の1つの記述が、実物へ辿れるか・在るかを判定する。

    entry   は設計図の1つの記述(dict)。sources はファイルの場所を鍵、中身(str)を値とする dict。
    戻り値は {"verdict","file","symbol","missing","searched"} の5つを持つ dict。
    verdict は UNTRACEABLE / PRESENT / ABSENT の3語のいずれか。他の語は作らない。
    searched は見た形の名前を並べた list。見なかった時は空の list。

    読み方は6通り。上から順に、最初に当てはまった1つで決める。
      1. entry が dict でない
         -> UNTRACEABLE / file=None / symbol=None / missing="entry" / searched=[]
      2. entry["file"] が str でない、または前後の空白を除くと空
         -> UNTRACEABLE / file=None / symbol=None / missing="file" / searched=[]
      3. sources が dict でない、または entry["file"] が sources の鍵に無い
         -> UNTRACEABLE / file=その file / symbol=(str ならその値、他は None)
            / missing="source" / searched=[]
      4. entry["symbol"] が str でない、または前後の空白を除くと空
         -> PRESENT / file=その file / symbol=None / missing=None / searched=[]
            (ファイルは在ったので、場所としては辿れている)
      5. symbol の前後の空白を除いた物が Python の識別子でない
         (英字か下線で始まり、以降が英数字か下線だけ、という形に当てはまらない)
         -> UNTRACEABLE / file=その file / symbol=その値
            / missing="symbol_not_an_identifier" / searched=[]
      6. 上のどれでもない場合、中身の中を次の3つの形で探す。searched=["def","class","assign"]
           "def <symbol>(" があれば -> PRESENT
           "class <symbol>(" か "class <symbol>:" があれば -> PRESENT
           行の先頭から "<symbol> =" か "<symbol> :" で始まる行があれば -> PRESENT
           どれも無ければ -> ABSENT
         PRESENT / ABSENT のどちらも file と symbol をそのまま返し、missing は None、
         searched は ["def","class","assign"] を返す。

    大文字小文字はそろえない。
    """
<<<2DER:END>>>
```

**★封印試験（★10本・★前の版と ★1文字も 変えていない）**
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
★(1) ★10本 全通
★★(2) ★★本件の 芯 = ★★成果物に ★`<<<FILL` の文字が ★★1つも 無いこと
     ★口 = `GET /api/claude_packet?task_id=…` ／ ★欄 = `test_result.artifact`
     ★id = ★この契約を走らせた その走行（★報告に 書く）
★★(3) ★★骨格が 保たれていること = ★`test_result.skeleton_missing_segment` が ★None
     ―― ★★FILL 無しでも 検査が 効いていることの 確認（★§2 の裏取り）
★(4) ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `artifact.name` と `found`
     ★読める物 = `trace_entry_v2` ／ `found=true`
★(5) ★★v1.18 の確認 = ★`sent.text` に ★★`symbol_not_an_identifier` が 在ること
     ―― ★★骨格の中の語（★依頼文の語を 使いません）
★(6) ★新台帳0・新エンドポイント0 ／ ★(7) ★Claude の配線行数（★上限6行）
★(8) ★戻せる ／ ★(9) ★61本を走らせない
```

## 5. ★★私が 言っていないこと

```
★『骨格から 目印を 消せば 守られる』―― ★★予告しません（★MGR も そう書いています）。
   ★★走らせて 決まります。★★もし また 残ったら ―― ★★『置かない』でも 足りなかった、が 結果です。
★『CC6DB126 が PASS に なる』―― ★★別の task です。★本件は ★新しい走行。
★『試験を 増やした』―― ★★1本も 増やしていません（★前の版と 同一）。
★『これで 178件が 測り直せる』―― ★★配置の後です。
```
