# 【BUILD SPEC】`EVO-0055` (B) — **★成果物が repo に在るかを ★機械が見る**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 22:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035` ／ 台帳: `ITEM-2DER-EVO-0055`
- 依頼: MGR 逐語「★(3)その後 設計が (B)成果物が置かれたか の BUILD SPEC」
- **★v1.8 の宣言**: **★核は在る・1件**（`artifact_presence`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **8〜14行**（★走査＋1欄）
- **★保存0・★新台帳0・★新エンドポイント0**（★`/api/resolve` の record に ★1欄）

---

## 1. ★なぜ要るか（★本日の実物）

```
★`locate_failure` は ★走行の記録は在るのに ★★repo の .py に ★0件だった。
★★監視インスタンスが ★手で grep するまで ★誰も気づかなかった。
★★★worker の成果物は ★tempfile 配下で ★消える(G-90) ∴ ★★『動いた』と『残った』は ★別物である。
★★★★∴ ★★人に『置いた』と申告させない。★★機械がファイルを見る（v0.3 §13.3）。
```

## 2. ★★契約

**★依頼文**
```
成果物が置かれたかを判定する純関数 impl.artifact_presence を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
skeleton = str（契約の骨格。例 "def locate_failure(route, events):"）
sources  = { "パス": "そのファイルの中身", ... }
戻り値 = {"name": str|None, "found": bool, "paths": [str, ...]}

・name = skeleton の中で 最初に現れる "def " に続く識別子。
  ★行の先頭の空白は無視してよい。"def " の直後から "(" の直前までを 名前とする。
  ★"def " が無ければ name は None。
・name が None なら found は False、paths は []。
・paths = sources のうち、その中身の ★どれかの行が（★先頭の空白を除いて）
  ★"def " + name + "(" で ★始まるファイルのパス。★昇順に並べる。
  ★★"def " が付かない ただの呼び出しは 数えない。
  ★★名前の一部が一致するだけ（例 name="f" に対する "def f2("）も 数えない。
・found = paths が空でないこと。
・sources が dict でなければ found は False、paths は []（★例外にしない）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def artifact_presence(skeleton, sources):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★骨格は 2026-08-05 の実測）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

SK = "def locate_failure(route, events):"                 # ★実測(34字)
SK_FILL = "def artifact_presence(skeleton, sources):\n    # <<<FILL: ここに実装>>>"

def test_name_is_taken_from_the_skeleton():
    v = impl.artifact_presence(SK, {})
    assert v["name"] == "locate_failure", v

def test_name_is_taken_even_with_a_fill_marker():
    v = impl.artifact_presence(SK_FILL, {})
    assert v["name"] == "artifact_presence", v

def test_found_when_a_file_defines_it():
    v = impl.artifact_presence(SK, {"twoder/locate_failure.py": "def locate_failure(route, events):\n    pass\n"})
    assert (v["found"], v["paths"]) == (True, ["twoder/locate_failure.py"]), v

def test_a_call_is_not_a_definition():
    """★呼び出しだけの行は ★数えない（★部分一致で誤検知しない）"""
    v = impl.artifact_presence(SK, {"twoder/webui.py": "x = locate_failure(route, events)\n"})
    assert (v["found"], v["paths"]) == (False, []), v

def test_a_longer_name_is_not_a_match():
    """★name='locate_failure' に対して 'def locate_failure_v2(' は ★別物"""
    v = impl.artifact_presence(SK, {"a.py": "def locate_failure_v2(x):\n    pass\n"})
    assert v["found"] is False, v

def test_indented_definition_counts():
    v = impl.artifact_presence(SK, {"b.py": "class C:\n    def locate_failure(self, route, events):\n        pass\n"})
    assert v["found"] is True, v

def test_paths_are_sorted():
    src = {"z.py": "def locate_failure(a, b):\n    pass\n",
           "a.py": "def locate_failure(a, b):\n    pass\n"}
    assert impl.artifact_presence(SK, src)["paths"] == ["a.py", "z.py"]

def test_no_def_in_skeleton_gives_none():
    v = impl.artifact_presence("# no function here", {"a.py": "def anything(x):\n    pass\n"})
    assert (v["name"], v["found"], v["paths"]) == (None, False, []), v

def test_non_dict_sources_is_not_raised():
    v = impl.artifact_presence(SK, None)
    assert (v["found"], v["paths"]) == (False, []), v
<<<2DER:END>>>
```

## 3. ★Claude の配線（★8〜14行と予告）

```
★(a) ★契約の骨格は ★CREATE イベントの contract から取る（★`generate()` が ★既に そうしている）
★(b) ★走査する範囲 = ★5つの repo の ★`.py`・★★深さ2まで（★`twoder/*.py` と ★`rri/rri/*.py` 等が入る）
     ★★深い再帰で ★repo 全体を舐めない（★上限を外さない）
★(c) ★`/api/resolve?id=TASK-…` の record に ★`artifact` を1欄（★`sent` と ★同じ流儀・★新しい口を作らない）
★★保存しない = ★呼ばれた時に ★その場で読む
```

## 4. 受入

```
★(0) ★worker が書く（★Claude は本文0行）・★9本 全通
★(1) ★★本日の契約に当て、★逐語で書く:
     ★`locate_failure` → ★★`found=False`（★2026-08-05 実測＝★repo に0件）
     ★`gate_decision` / `effective_state` / `route_table` → ★★`found=True`（★陽性対照）
     ★★★どちらかが ★予想と違えば ★『違った』と ★paths を ★そのまま書く（★合わせに行かない）
★(2) ★走査した ★ファイル数と ★所要時間を ★書く（★上限が効いていることの確認）
★(3) ★保存が0（★新しいファイル・台帳・欄を ★作っていない）
★(4) ★人が書いた『置いた』の宣言を ★1つも読んでいないこと
★(5) ★sha256 一致 ／★(6) ★Claude の配線行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★★★予告を投入前に書く: ★行数 ／ ★(1) の 4件の found
```

## 5. ★★これで分からないこと（★先に言う）

```
★★『同じ名前の別物』を ★区別しない（★名前一致だけ）―― ★中身が ★契約を満たすかは ★見ていない
★★★`found=True` は ★『置かれた』であって ★『正しい』ではない
★★★★深さ2の外に ★置かれた成果物は ★見えない（★上限の代償・★見えない時は ★`found=False` と出る）
★★★★★∴ ★★`found=False` は ★『置かれていない』と ★『見える所に無い』の ★両方を含む。
   ★どちらかは ★この口では ★決まらない。★決めたい時は ★paths が空である事実を ★そのまま報告する。
```

## 6. 禁止

```
★人に『置いた』と申告させる ／ ★その宣言を ★証拠にする
★深さの上限を ★外す ／ ★`.py` 以外を ★走査する ／ ★保存する
★成果物の ★中身を ★判定する（★在るかどうかだけ）
★新しい台帳・エンドポイントを作る（★`/api/resolve` の record に足す）
★★『成果物が正しく置かれた』と書く（★§5・★在るかどうかしか見ていない）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
