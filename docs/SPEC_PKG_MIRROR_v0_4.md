> **FLOW NOTE — 2026-07-23 ANCHOR §1-1 Taka 裁定（本書を読むのはまずここ）:**
> 本書は `egl/docs` に置かれた**実装指示**。実装インスタンス（Monitor `b0718vzrg`）が
> `twoder/seam/pkg_mirror.py` を **working tree に直接実装**し、§3 の不変テストを **12/12 green** にする。
> **旧『本書を raw_input として submit / `generate_via_runner` 経由』は本フローでは無効**
> （§1-1 で submit→runner は置換。§5 の配線記述も旧経路前提で参考のみ）。
> 実装契約は不変: **§2 骨格の `<<<FILL>>>` 以外は 1 バイトも変えない**（レビューで bytes 一致を担保）。
> §3 不変テストは発注側同梱・**worker は書かない/触らない**。commit は人間の扉＝**Taka**。
> sandbox 受入名は `impl.py`/`test_impl.py`、コミット時配置は `twoder/seam/pkg_mirror.py`（§2 冒頭注記のとおり）。
> 起草: CC-α。本文は監査済み v0.4（`CC_AUDIT_2026-07-23_PKG_MIRROR_v0_4.md` で Finding 1/2 解消確認）を **§2/§3 バイト不変**で転記。

---

# パッケージ複製 seam（PKG MIRROR）実装仕様 v0.4

- **status:** SPEC / 起草: CLAUDE_WEB 2026-07-23 / **v0.3 を SUPERSEDE**
- **位置づけ:** ★3(A) death#6 の恒久修正。`CONFORMANCE_PROBE_v0_5` の前提工程。
- **実装:** Qwen（runner 方式）。**投入:** 本書を raw_input として submit。
- **claim ceiling:** `MIRROR_MECHANISM_PROVEN_ON_REPRESENTATIVE_SYNTHETIC_PACKAGE_INCLUDING_SELF_HOSTING`
  **言えないこと:** 実 `twoder` パッケージに対する挙動（プローブ gate3 が測る）／`generate_via_runner` への配線。

### v0.3 からの修正（`docs/CC_AUDIT_2026-07-23_PKG_MIRROR_v0_3.md` 由来）

|#      |内容                                                                                                                                                                                                                                                                                               |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**Y-1**|**Finding 1（確定 blocker）を解消。** sandbox 内の artifact 名は `impl.py`、テストは `test_impl.py`、実行は `cwd=ws` の `pytest test_impl.py`（`generate_via_runner.run_runner` / `live_worker_runtime.py:104-106,116`）。v0.3 の `_load_artifact` は `pkg_mirror.py` を探しており **3 経路とも外れて 0/10 だった。** → §3 で `impl.py` を正本にした|
|**Y-2**|**Finding 2 を構造的に回避。** `_run_test` は env 無指定・`PYTHONPATH` 未設定（`live_worker_runtime.py:36-41`）＝ **sandbox で `import twoder` が成立する保証が無い。** → 受入検査を**実 twoder に一切依存しない合成パッケージ**の上で行う形に変えた（§3.1）。実パッケージ挙動はプローブ gate3 へ移した                                                                            |
|**Y-3**|**death#7 を命名。** 「sandbox に `PYTHONPATH` が張られていない」は本仕様固有ではなく、**パッケージを import するテストを持つ task が全て構造的に受からない**という runner 方式の天井。#6 の兄弟として死因ラダーに載せる（§0.2）                                                                                                                                               |
|**Y-4**|**v0.3 の記述を1件撤回。** 「テンポラリの偽パッケージで代替したら S3/S4 が無意味になる（族A）」は**私の過剰主張だった。** 撤回理由と、それでも失われるものを §3.1 に明記した                                                                                                                                                                                            |

-----

## §0. 解く問題

### §0.1 death#6

新規モジュールを産出する task は、**受入オラクル（pytest）と artifact が別の名前空間に居るため原理的に 7/7 を取れない。**
`import twoder.approval_registry` が sandbox の artifact ではなく実パッケージ（未存在）を見に行き、collection error で落ちる。

**採らない案:** 「CONSUMED + artifact 産出で ACCEPT、7/7 は後で」→ 受入判定を弱い信号に置き換える形。**族A の再生産。**

### §0.2 death#7（新規命名。Y-3）

> **`_run_test` は `subprocess.run(test_command, cwd=workspace)` を env 無指定で呼ぶ（`live_worker_runtime.py:36-41`）。
> sandbox に `PYTHONPATH` は張られない。したがって「sandbox で `import twoder` できる」は仕様の暗黙前提であり、未保証。**

CC は再現を試みたが、稼働中の 2DER/vLLM 負荷と切り分けられず **INDETERMINATE**。
ただし**「env を渡していない」というコード事実は確定**なので、依存する設計を書いてはならない。

**#6 と #7 は兄弟である。** #6 は「artifact がパッケージ名前空間に居ない」、#7 は「パッケージがそもそも見えない」。
**そして seam の配線（`PYTHONPATH` = sandbox root ＋ パッケージ複製）は、両方を同時に閉じる。**
本仕様は seam を作るところまで。配線は §5 のとおり範囲外。

### §0.3 ブートストラップ限定条項

本仕様自身が新規モジュールなので、素直に書くと死因#6 に自分で当たる。条件を機械判定にして限定する。

> **条項:** 発注側の不変テストは、**artifact が `twoder.*` を静的 import しない task に限り**、
> artifact をファイルパス直ロード（`importlib.util.spec_from_file_location`）で受け入れてよい。

**なぜ族A（オラクルの弱体化）ではないか:** 死因#6 の本体は「**artifact 自身の内部 import が解決できない**」ことにある。
`import twoder.authority` を持つ artifact をパス直ロードしても内部 import は解決できない —— **だから seam が要る。**
stdlib しか import しない artifact は、パス直ロードでも実関数が実引数で走り実 sha256 で突合される。**測る中身は変わらない。**

判定は **AST 検査で機械化**する（S10）。適格性: `pkg_mirror`=適格／`conformance_probe`=適格／`approval_registry`=**不適格 → seam が必要**。

**免除で終わらせない。** S8 で **`mirror_package` が自分自身を複製し、複製された側がパッケージ経由で import されて動く**ことを検査する。

-----

## §1. 設計

### §1.1 複製

sandbox 内に **パッケージを byte-for-byte 複製**し、artifact をパッケージ相対パスへ配置。`PYTHONPATH` は sandbox root。

**なぜ複製が必要か（罠の記録）:** sandbox に `<pkg>/` を作るだけだと、`__init__.py` の有無で
「実パッケージを shadow して他モジュールの import が全部落ちる」か「artifact が解決されない」かの二択になる。中間が無い。

**「実コード」主張の接地:** `MIRROR_MANIFEST.json`（パス→sha256）を必ず出力し、
**artifact と生成した中間 `__init__.py` 以外の全エントリが元と sha256 一致すること**を機械検査する（族C の適用）。

### §1.2 サブパッケージ

`artifacts` のキーは `/` を含んでよい（例 `seam/pkg_mirror.py`）。

- 中間ディレクトリが無ければ作り、**空の `__init__.py` を生成**する。
- 生成した `__init__.py` は manifest の `"created"` に載せ、**`"files"` の sha256 突合対象から外す**（元に対応物が無いため）。
- 中間パスが元側に**ファイルとして**存在したら halt（`seam` が `seam.py` だった等）。

**人間の扉2枚は無傷:** `pkg_root` には 1 バイトも書かない。書き先が `pkg_root` 配下へ解決されたら halt。

-----

## §2. 骨格 —— 完全ファイル（`<<<FILL>>>` 以外は bytes 一致対象）

> **記法（CC 監査で確定）:** 判定は部分文字列 `"<<<FILL"`（`generate_via_runner.py:53`）。**複数 FILL 可・位置制約なし**（A5/A6）。
> `<<<FILL>>>` 以外は **1 バイトも変えてはならない**（docstring・コメント・空行を含む）。整形・型注釈追加・docstring 要約は違反。
> **骨格検査は非 FILL 塊の `find()` 順序一致しか見ない ＝ 挿入は検出できない。** 骨格の名前の再定義は S9 で禁止する。
> 
> **sandbox 内のファイル名は `impl.py`（artifact）と `test_impl.py`（不変テスト）。**
> `twoder/seam/pkg_mirror.py` はコミット時（人間の扉2枚目）の配置先であって、**受入時の名前ではない。**

```python
"""パッケージ複製 seam — 新規モジュール artifact を実パッケージ名前空間で受け入れる。

death#6: 受入オラクル(pytest)と artifact が別名前空間に居るため、新規モジュールを
産出する task は原理的に 7/7 を取れなかった。オラクルを弱める(CONSUMED+産出で ACCEPT)
のは族A の再生産なので採らない。artifact 側をパッケージ相対に置く。

death#7: sandbox に PYTHONPATH が張られない(live_worker_runtime.py:36-41)ため、
本モジュールは実パッケージの可視性に依存してはならない。pkg_root は引数で受け取り、
自分で探しに行かない。

claim ceiling: pkg_root への書込みは 0 バイト。複製は sandbox 内のみ。
複製が元と同一であることは MIRROR_MANIFEST の sha256 でのみ接地する。
生成した中間 __init__.py は元に対応物が無いため sha256 突合の対象外とし、
manifest の "created" に分離して載せる。空欄にしない。

本モジュールは stdlib 以外を import しない。これは §0.3 ブートストラップ限定条項の
適格条件そのものであり、S10 が AST で機械検査する。twoder.* の import を足したら違反。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
<<<FILL>>>

MIRROR_MANIFEST = "MIRROR_MANIFEST.json"

# 複製から除外するもの。ここを増やすのは仕様変更であり、worker が判断してはならない。
MIRROR_EXCLUDE = ("__pycache__", ".pyc", ".pyo", ".so", ".git")


class MirrorHalt(RuntimeError):
    """解決できない前提に当たったら回避策を発明せず halt する(ANCHOR §5-6)。"""


<<<FILL>>>


def sha256_file(path: str) -> str:
    """ファイルの sha256 を返す。manifest と検査の唯一の突合手段。"""
<<<FILL>>>


def mirror_package(pkg_root: str, sandbox_root: str, artifacts: dict) -> dict:
    """pkg_root を sandbox_root/<pkgname>/ へ複製し、artifacts を追加配置する。

    引数:
      pkg_root    : 複製元パッケージのディレクトリ。読み取り専用。呼び出し側が与える。
      sandbox_root: 複製先の親。PYTHONPATH に入る側。
      artifacts   : パッケージ相対パス -> bytes。キーは "/" を含んでよい
                    (例 {"seam/pkg_mirror.py": b"..."})。

    返り値:
      {"pkg": str,                     # os.path.basename(pkg_root)
       "files": {rel_path: sha256},    # 複製 + artifact。元と突合する対象
       "artifacts": [rel_path],        # 突合対象外(worker 生成物)
       "created": [rel_path]}          # 生成した中間 __init__.py。突合対象外

    規律(いずれも違反したら MirrorHalt。例外を握り潰さない=族B):
      1. artifacts のキーが既存ファイルを指したら halt。本 seam は新規モジュール専用。
      2. 書き先の realpath が pkg_root 配下に解決されたら halt(複製元の保護)。
      3. artifacts のキーが `..` や絶対パスを含んだら halt(traversal)。
      4. 中間パスが元側にファイルとして存在したら halt(seam.py と seam/ の衝突)。
      5. 複製後、artifacts と created を除く全ファイルの sha256 が元と
         一致しなければ halt。
      6. manifest は sandbox_root/MIRROR_MANIFEST へ必ず書く。書けなければ halt。
    """
<<<FILL>>>
```

**自由区間:** 追加 import（**stdlib のみ**）／補助関数／`sha256_file` 本体／`mirror_package` 本体。

-----

## §3. 不変テスト（発注側同梱。worker は書かない・触らない）

sandbox 内のファイル名は **`test_impl.py`**。**FILL は無い。全文がそのまま同梱される。conftest は作らない。**

### §3.1 合成パッケージで検査する（Y-2 / Y-4）

**v0.3 の「偽パッケージで代替したら族A」は撤回する。** 撤回理由:

`mirror_package` は `pkg_root` を**引数で受け取り一様に扱う**。したがって「複製が bytes 一致する」「複製元に書かない」
「shadow せず intra-package import が生きる」「サブパッケージを生成する」「自分自身をホストできる」は、
**代表性のある合成パッケージで完全に検査できる。** 実 `twoder` を使う必要は無い。

**それでも失われるものを明示する（過小主張もしない）:**

- 実 `twoder` 固有の構造（サイズ・特殊ファイル・深い入れ子）に対する挙動 → **`UNRESOLVED_REAL_PKG_UNTESTED`**
- 「実 repo が無傷」の**直接**証明 → 一般性質（規律2の halt）としては検査されるが、実 repo 実体に対しては未検査

**この2つはプローブ gate3 が測る。** 受入をそこに依存させない ―― death#7 が未確定である以上、
実 `twoder` を import する受入テストは**走る前に落ちる**（Finding 2）。**走らないオラクルは緑と区別できない＝族A。**

合成パッケージは**代表性**を持たせる: `__init__.py` ／ 平坦モジュール ／ **intra-package import を含むモジュール** ／ サブパッケージ。

```python
import ast, hashlib, importlib.util, json, os, subprocess, sys
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))


# --- artifact のロード（Finding 1: sandbox の artifact 名は impl.py） -----------
def _load_artifact():
    """runner は tp["target_file"]（既定 "impl.py"）へ書き、cwd=ws で pytest を回す。
    探索名を pkg_mirror.py にしていたのが v0.3 の 0/10 の原因。
    見つからなければ静かに skip せず落とす。skip は族A(空振り)。"""
    for cand in (os.environ.get("ARTIFACT_PATH"),
                 os.path.join(_HERE, "impl.py"),
                 os.path.join(os.getcwd(), "impl.py")):
        if cand and os.path.isfile(cand):
            spec = importlib.util.spec_from_file_location("_pkg_mirror_artifact", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.__artifact_path__ = cand
            return mod
    raise RuntimeError(f"BOOTSTRAP_HALT: impl.py not found (_HERE={_HERE} cwd={os.getcwd()})")


M = _load_artifact()
mirror_package, MirrorHalt = M.mirror_package, M.MirrorHalt
MIRROR_MANIFEST = M.MIRROR_MANIFEST
SRC = open(M.__artifact_path__).read()


# --- 合成パッケージ（Finding 2: 実 twoder を import しない） --------------------
@pytest.fixture()
def pkg_root(tmp_path_factory):
    """複製元の役。代表性のため intra-package import とサブパッケージを含める。
    名前を twoder にしないのは、実パッケージとの取り違えを構造的に不可能にするため。"""
    root = tmp_path_factory.mktemp("src") / "synthpkg"
    (root / "sub").mkdir(parents=True)
    (root / "__init__.py").write_text("")
    (root / "alpha.py").write_text("ALPHA = 1\n")
    (root / "beta.py").write_text("from synthpkg.alpha import ALPHA\nBETA = ALPHA + 1\n")
    (root / "sub" / "__init__.py").write_text("")
    (root / "sub" / "gamma.py").write_text("GAMMA = 3\n")
    return str(root)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _tree_sha(root):
    out = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            out[os.path.relpath(os.path.join(dp, fn), root)] = _sha(os.path.join(dp, fn))
    return out


def _run(sandbox, code):
    return subprocess.run([sys.executable, "-c", code], cwd=str(sandbox),
                          env={**os.environ, "PYTHONPATH": str(sandbox)},
                          capture_output=True, text=True)


# S1: artifact がパッケージ相対で import できる
def test_s1_artifact_importable_under_package(tmp_path, pkg_root):
    m = mirror_package(pkg_root, str(tmp_path), {"newmod.py": b"VALUE = 41 + 1\n"})
    r = _run(tmp_path, "import synthpkg.newmod as m; print(m.VALUE)")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "42"
    assert "newmod.py" in m["artifacts"] and m["pkg"] == "synthpkg"


# S2: shadow で壊していない。intra-package import とサブパッケージが生きる
def test_s2_existing_modules_still_importable(tmp_path, pkg_root):
    mirror_package(pkg_root, str(tmp_path), {"newmod.py": b"VALUE = 1\n"})
    r = _run(tmp_path, "import synthpkg.beta as b, synthpkg.sub.gamma as g;"
                       " print(b.BETA, g.GAMMA)")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "2 3"


# S3: 複製の接地。artifact と created 以外は元と sha256 一致
def test_s3_mirror_is_byte_identical(tmp_path, pkg_root):
    m = mirror_package(pkg_root, str(tmp_path), {"newmod.py": b"VALUE = 1\n"})
    exempt = set(m["artifacts"]) | set(m["created"])
    checked = 0
    for rel, digest in m["files"].items():
        if rel in exempt:
            continue
        assert digest == _sha(os.path.join(pkg_root, rel)), rel
        checked += 1
    assert checked >= 5, f"突合対象が {checked} 件。空振りしている(族A)"
    assert json.load(open(os.path.join(str(tmp_path), MIRROR_MANIFEST)))["files"] == m["files"]


# S4: 複製元に 1 バイトも書かない(人間の扉を守る規律の本体)
def test_s4_source_untouched(tmp_path, pkg_root):
    before = _tree_sha(pkg_root)
    mirror_package(pkg_root, str(tmp_path), {"seam/newmod.py": b"VALUE = 1\n"})
    assert _tree_sha(pkg_root) == before


# S5: 既存ファイルの上書きは halt(本 seam は新規モジュール専用)
def test_s5_overwrite_halts(tmp_path, pkg_root):
    with pytest.raises(MirrorHalt):
        mirror_package(pkg_root, str(tmp_path), {"alpha.py": b"# hijack\n"})


# S6: path traversal は halt
@pytest.mark.parametrize("bad", ["../evil.py", "/tmp/evil.py", "a/../../evil.py"])
def test_s6_traversal_halts(tmp_path, pkg_root, bad):
    with pytest.raises(MirrorHalt):
        mirror_package(pkg_root, str(tmp_path), {bad: b"x\n"})


# S7 陰性対照: 複製を1バイト壊すと S3 の突合が赤くなる
def test_s7_negative_control(tmp_path, pkg_root):
    m = mirror_package(pkg_root, str(tmp_path), {"newmod.py": b"VALUE = 1\n"})
    exempt = set(m["artifacts"]) | set(m["created"])
    victim = next(r for r in m["files"] if r not in exempt and r.endswith(".py"))
    mirrored = os.path.join(str(tmp_path), m["pkg"], victim)
    open(mirrored, "ab").write(b"\n")
    assert _sha(mirrored) != _sha(os.path.join(pkg_root, victim))


# S8 自己ホスティング: 自分自身を複製し、複製側がパッケージ経由で動く
# ブートストラップ免除(§0.3)を免除のままにしない。サブパッケージ生成も同時に通る。
def test_s8_self_hosting(tmp_path, pkg_root):
    m = mirror_package(pkg_root, str(tmp_path), {"seam/pkg_mirror.py": SRC.encode()})
    assert "seam/__init__.py" in m["created"]
    r = _run(tmp_path, "from synthpkg.seam.pkg_mirror import mirror_package as f;"
                       " print(f.__name__)")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "mirror_package"


# S9: 骨格で定義した名前の重複定義禁止(挿入は骨格検査では防げない)
def test_s9_no_redefinition():
    names = []
    for node in ast.parse(SRC).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names += [t.id for t in node.targets if isinstance(t, ast.Name)]
    for g in ("mirror_package", "sha256_file", "MirrorHalt",
              "MIRROR_MANIFEST", "MIRROR_EXCLUDE"):
        assert names.count(g) == 1, f"{g} が {names.count(g)} 回定義されている"


# S10: ブートストラップ適格条件。twoder.* の静的 import 禁止
def test_s10_no_intra_package_static_import():
    for node in ast.walk(ast.parse(SRC)):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert not a.name.startswith("twoder"), a.name
        elif isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("twoder"), node.module
```

> **S7 / S8 / S10 が心臓。** S7 が無いと S3 は常に緑を出せ（族A）、S8 が無いとブートストラップ免除が免除のまま残り、
> S10 が無いと免除の適格条件が人間の裁量になる。

-----

## §4. 受入条件

- **12/12**（S1–S10、S6 は 3 パラメータ）。部分緑は BUILT 止まりで DONE ではない。
- `verify_skeleton_preserved` で FILL 以外の bytes 一致。
- **`pytest.skip` を使わないこと。** 前提が無ければ落とす。skip は「何も出ませんでした」を緑で出す族A。
- **`import twoder` に依存しないこと。** death#7 が未確定な間、依存した瞬間に走る前に落ちる。

## §5. 範囲外として明示するもの

- **`generate_via_runner` への配線。** 本仕様は seam を作るだけ。**配線の有無はプローブ gate3 が測る。**
  本仕様の DONE は BUILT を意味する。**配線は #6 と #7 を同時に閉じる**（§0.2）
- 実 `twoder` に対する挙動 → **`UNRESOLVED_REAL_PKG_UNTESTED`**（プローブ gate3）
- 複製コスト → **`UNRESOLVED_MIRROR_COST`**。複数パッケージ横断 → **`UNRESOLVED_MULTIPKG`**
- 既存モジュールの**差替え** task。S5 で明示的に halt。別 seam の主題。