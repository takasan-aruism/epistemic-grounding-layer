# declared — AXIS = `REGRESSION_HARNESS_USES_TOPLEVEL_IMPORT`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3` / **ESDE 正本 v0.1**)
**★実装の前に置く1枚。★コードは1行も変えていない。**
item: `ITEM-2DER-EVO-0088` の1件のみ ／ 測ったHEAD: twoder `972d7e0` / dev-workcell `68c3b4c` / egl `cfefb67`

**★なぜこれをやるか**: この5本が走らない限り、mint / apply / rollback / reconciler の区間は
**測れない**（`DE-0438`「2026-07-19 完走実績」は現在 再現できない）。
∴ 正本 §8 の `SAFE_EXISTING_FILE_MODIFICATION` を **ESTABLISHED にする前提**が揃わない。

---

## AXIS

```
AXIS: REGRESSION_HARNESS_USES_TOPLEVEL_IMPORT
SCOPE:
  entry:       twoder/regression/ の5本を python3 で起動する
  exit:        5本が import を通り、各自の判定を最後まで出す（PASS/FAIL は問わない）
  authority:   発行 0・変更 0
  persistence: 新規 0（既存 file の import 行のみ／試験は tempfile 内で完結）
  components:  gate_s4_energization.py, jrev0010_attacks.py, verify_minter_B.py,
               verify_reconciler_A.py, verify_throwaway_first.py,
               twoder/patch_bridge.py, twoder/bridge_reconciler.py, twoder/bridge_minter.py
```

## ② 全件調査（作用ベース／★監査の確定3点は再調査していない）

| # | 実測 | 状態 |
|---|---|---|
| 1 | `twoder/regression/*.py` は **100本**（私も独立に数えた） | PRESENT |
| 2 | top-level import を使うのは **5本だけ**。★全部 energization 経路 | PRESENT |
| 3 | 5本の該当行は一様：`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` ＋ `import patch_bridge as pb` / `import bridge_reconciler as rc` / `import bridge_minter as bm`（`verify_reconciler_A` のみ `bm` 無し＝2本） | PRESENT |
| 4 | **既存95本の作法**：`sys.path.insert(0, "/home/takasan")` が **83本で最多**、`from twoder import X as Y` が package 形式の標準 | PRESENT |
| 5 | 5本が読む3 module は package 形式で**全て import 可**（最後の1つは `twoder 972d7e0` で通った） | PRESENT |
| 6 | 5本とも `tempfile.mkdtemp` で完結。**実 repo の path は無い**（`repo_identity` は throwaway） | PRESENT |

**∴ 修理は「既存の作法へ揃える」だけ。新しい作法を作らない。**

## ③ 因果鎖

```
① 起動      python3 twoder/regression/<file>.py
② path      sys.path.insert が ★regression/ を指す        ← ★欠損(a)
③ import    import patch_bridge → ★ModuleNotFoundError    ← ★到達しない
④ 実行      各試験の判定                                   ← ★到達しない
⑤ 出力      PASS/FAIL の行                                 ← ★到達しない
```

各点：①=OS が起動／②=`sys.path` に文字列を1つ足す／保存先なし／③が読む／
無ければ ③で `ModuleNotFoundError` になり **起動側が落ちる**（fail-closed）／本線の呼び手は**現在 0**。

**止まっているのは②の1点。③〜⑤はその帰結。**

## ④ DESIGN_HOLD 判定

**推測が残る点 ＝ 0**（①〜⑥すべて実測）。∴ **DECISION = GO**。
★ただし **「直せば試験が PASS する」とは書かない** ―― exit は「**判定を最後まで出す**」であり、
PASS/FAIL は実走で初めて分かる。

## ⑤ ESDE 宣言（正本 §12 全欄）

```
EQUALITY   canonical_protocols: [twoder.patch_bridge / twoder.bridge_reconciler / twoder.bridge_minter]
           compatible:   [regression 95本（package 形式）]
           incompatible: [regression 5本（top-level 形式）]
           unknown:      []
           ★identity rule: module の完全修飾名
           status: ★BROKEN（5本は canonical 名を使っていない）

SYMMETRY   pairs: [試験を書く側 ↔ 走らせる側]
           required 1 / present 0 / missing 1（HARNESS_NOT_RUNNABLE）/ unverified 0

LINKAGE    edges: E1 起動→path / E2 path→import / E3 import→実行 / E4 実行→判定出力
           declared 4 / observed 1（E1）/ broken 1（E2）/ unverified 2

HIERARCHY  boundaries: [package 境界, 試験↔本番の責務差]
           required 2 / passed 2 / violation 0 / unreachable 0
           ★試験は本番 module を読むだけで本番を変えない。層は破っていない。

R1_END_TO_END      status: UNREACHABLE ／ evidence: import が落ちる（実測）
R2_DENOMINATOR     required: 5 ／ observed: ★0 ／ status: BROKEN
R3_INTERNAL_GATES  gates: [import, 各試験自身の門] / passed: [] / failed: [import]
                   unverified: [各試験自身の門]
R4_REJECTION       rejection_conditions:
                     ①存在しない module 名 → ModuleNotFoundError
                     ②stdlib を隠す名前が path に在る → ImportError（operator 衝突）
                   actually_rejected: [①②とも 2026-08-22 に実発火済（EVO-0087 の調査中）]
                   unexpected: [] ／ status: OBSERVED

UNDERSTANDING  candidate: ENERGIZATION_HARNESS_RUNNABLE
               requires: [②が塞がる, 5本が判定を最後まで出す]
               evidence: [] ★実走前
               unresolved: [PASS/FAIL の中身]
               result: ★UNKNOWN

CREATION   status: NOT_EVALUATED
DECISION   GO
```

## ⑥ 置く最小差分（★まだ置いていない）

**5本それぞれ、import 行だけ。既存95本の作法へ揃える。**

```
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  → sys.path.insert(0, "/home/takasan")          # ★83本と同じ
import patch_bridge as pb        → from twoder import patch_bridge as pb
import bridge_reconciler as rc   → from twoder import bridge_reconciler as rc
import bridge_minter as bm       → from twoder import bridge_minter as bm
```

- **試験の中身（判定・門・期待値）は1行も触らない**
- `operator.py` / `patch_bridge.py` / 本番 module に触らない
- 新語彙 0 ／ 新台帳 0 ／ 新 state 0 ／ 新 front door 0
- **影響は 5 / 100 本。残り95本は該当しない**

## ⑦ 実走で見るもの（R1）

```
5本を1本ずつ起動し、①import を通ったか ②判定を最後まで出したか ③その判定は何か を記録する。
★PASS を目標にしない。★FAIL でも「判定が出た」なら exit は成立。
★FAIL の中身は 別の finding として記録する（この AXIS では直さない）。
```

## ⑧ 触っていないもの

`EVO-0085` の writer 4欠損 ／ `EVO-0087`（import 済・呼び手0のまま）／ 並行運用 `EVO-0084` ／
正本§13 の UNVERIFIED 差戻し ／ `merge_records` ／ 未commit 30件。
