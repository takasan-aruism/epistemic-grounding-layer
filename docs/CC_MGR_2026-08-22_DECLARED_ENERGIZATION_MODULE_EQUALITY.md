# declared — AXIS = `ENERGIZATION_MODULE_EQUALITY`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3` / **ESDE 正本 v0.1**)
**★実装の前に置く1枚。★コードは1行も変えていない。**（probe は `/tmp` のコピーで実行・原本不触）
item: `ITEM-2DER-EVO-0087` の1件のみ ／ 測ったHEAD: twoder `e3e3bd1` / dev-workcell `68c3b4c` / egl `218c666`

---

## AXIS

```
AXIS: ENERGIZATION_MODULE_EQUALITY
SCOPE:
  entry:       本番の path(/home/takasan + dev-workcell)から twoder.bridge_minter を import できること
  exit:        mint した token が apply 側の isinstance(patch_bridge.py:79 / :355)を通ること
  authority:   発行 0・変更 0
  persistence: 新規 0（既存 file の import 行のみ）
  components:  twoder/bridge_minter.py, twoder/patch_bridge.py, twoder/bridge_reconciler.py,
               twoder/apply_cycle.py, twoder/source_to_patch.py, twoder/operator.py
```

**昇格先**: 正本 §8 の例 **`SAFE_EXISTING_FILE_MODIFICATION`**。
その先が Taka の関心（Claude 破棄）の律速① ―― 本日実測で **Claude commit 5/5 が既存ファイル変更／機械の commit 2/2 は新規ファイルのみ**。

## ② 全件調査（作用ベース・探した範囲 = `ds rri egl dev-workcell twoder` の `*.py` 全件）

| # | 実測 | 状態 |
|---|---|---|
| 1 | `_EnergizedApply` の定義は**本番に1つだけ** `twoder/patch_bridge.py:46`（他は `regression/test_harness_reverify.py:73,89` の試験内） | PRESENT |
| 2 | apply 側の読み方 = `apply_cycle.py:22` / `source_to_patch.py:85` の `from twoder import patch_bridge as PB`（**package**） | PRESENT |
| 3 | minter 側の読み方 = `bridge_minter.py:26` `from patch_bridge import _EnergizedApply` ／ `:27` `import bridge_reconciler as rc`（**top-level**） | PRESENT |
| 4 | 正規 path で `twoder.bridge_minter` を import → **`ModuleNotFoundError: No module named 'patch_bridge'`** | **BROKEN** |
| 5 | `twoder/regression/` に `patch_bridge.py` は**無い**（`ls` で確認） | ABSENT |
| 6 | `/home/takasan/twoder` を path に足すと `twoder/operator.py` が stdlib `operator` を隠して `ImportError` | **BROKEN** |
| 7 | **∴ 成立する path が存在しない**（監査が対照つきで独立再現） | **UNREACHABLE** |
| 8 | `twoder/operator.py` は **204行の実物**で、3箇所が `twoder.operator` として package 名で import ∴ **消す対象ではない** | PRESENT |
| 9 | 試験ハーネス4本（`verify_minter_B` / `verify_throwaway_first` / `gate_s4_energization` / `jrev0010_attacks`）も**現在 実行不能** | **UNREACHABLE** |
| 10 | 来歴：`operator.py` 追加 **2026-07-11** / `bridge_minter.py` 追加 **2026-07-19**（8日後）∴ **最初からこの形**。「後から壊れた」ではない | PRESENT |

### ★正本 §13 について（断定しない）

正本は「mint 側と apply 側の `_EnergizedApply` が別 class identity ∴ CONFLICT」と書く。
**現在の実測ではその状態に到達しない** ―― 定義は本番に1つだけで、`bridge_minter` が load できない以上
**2つの module object が共存する場面が起きない**。
∴ **§13 の CONFLICT は現在 観測され得ない。正本が誤っているとは書かない**（書かれた時点と状態が違う可能性）。
**UNVERIFIED として正本側へ戻す。**

### ★実装前の feasibility probe（`/tmp` のコピー・原本不触）

```
from patch_bridge import _EnergizedApply   → from twoder.patch_bridge import _EnergizedApply
import bridge_reconciler as rc             → from twoder import bridge_reconciler as rc

★import = 成功
★_EnergizedApply が apply 側と同一 class か = True
★mint_real_energize 在り / _REQUIRED_REQUEST_KEYS = 10 欄
```

## ③ 因果鎖

```
① import      正規 path から twoder.bridge_minter を読む          ← ★欠損(a) 現在 ModuleNotFoundError
② class 取得   _EnergizedApply を apply 側と同一 object で持つ      ← ★到達しない
③ mint        mint_real_energize が token を返す                   ← ★到達しない
④ isinstance  patch_bridge.py:79 / :355 が token を通す            ← ★到達しない
⑤ 書込        apply_patch_bounded が実 repo へ書く                 ← ★到達しない
```

**止まっているのは①の1点。②〜⑤はすべてその帰結。**
各点の「誰が作る／何を作る／どこに保存／誰が読む／無い時どう止まる／本線で呼ばれる」：
①=Python の import 機構が作る／module object／`sys.modules`／`bridge_minter` 自身が読む／無ければ
`ModuleNotFoundError` で**呼び手側が落ちる**（fail-closed）／本線の呼び手は**現在 0**。

## ④ DESIGN_HOLD 判定

**推測が残る点 ＝ 0。**①〜⑩と probe をすべて実測から引いた。∴ **DECISION = GO**。

## ⑤ ESDE 宣言（正本 §12 の全欄）

```
EQUALITY   canonical_protocols: [twoder.patch_bridge._EnergizedApply]
           compatible:   [apply_cycle, source_to_patch]（どちらも package import）
           incompatible: [bridge_minter（top-level import ∴ 現在 load 不能）]
           unknown:      []
           ★identity rule: module object の同一性（`is`）
           status: ★BROKEN（CONFLICT ではない ―― 衝突する2者が共存できないため）

SYMMETRY   pairs: [mint↔apply, grant↔revoke, apply↔rollback]
           required 3 / present 0 / missing 1（MINT_MODULE_NOT_IMPORTABLE）
           unverified 2（grant↔revoke と apply↔rollback は①が塞がるため測れない）

LINKAGE    edges: E1 import→class取得 / E2 class取得→mint / E3 mint→isinstance / E4 isinstance→書込
           declared 4 / observed 0 / broken 1（E1）/ unverified 3

HIERARCHY  boundaries: [package 境界, authority 境界, bridge→real repo]
           required 3 / passed 3 / violation 0 / unreachable 0
           ★層は破っていない。詰まりであって違反ではない。

R1_END_TO_END      status: UNREACHABLE ／ evidence: 正規 path で import が落ちる
R2_DENOMINATOR     required: twoder.bridge_minter を読む本線の呼び手 ／ observed: ★0 ／ status: BROKEN
R3_INTERNAL_GATES  gates: [import, isinstance(:79), isinstance(:355)]
                   passed: [] / failed: [import] / unverified: [isinstance ×2]
R4_REJECTION       rejection_conditions:
                     ①token が _EnergizedApply でない → TypeError（patch_bridge.py:79）
                     ②energize_token が _EnergizedApply でない → refuse（:355）
                   actually_rejected: [] ★実装後に発火させる
                   unexpected: [] ／ status: UNVERIFIED

UNDERSTANDING  candidate: ENERGIZATION_MODULE_EQUALITY
               requires: [①が塞がる, ②が同一 class になる, ④が通る]
               evidence: [probe（/tmp・原本不触）で ①②が成立し class 同一を確認]
               unresolved: [③④⑤は本線で未実走]
               result: ★UNKNOWN（まだ ESTABLISHED にしない）

---

## ⑨ 追記 2026-08-22 13:35 ―― R3 を実測で更新（★ESTABLISHED にはしない）

`EVO-0088` で harness 5本が走るようになったので、**`verify_minter_B.py` を実走させて
止まる位置を測った**（実 repo 書込 0・workspace は `tempfile`）。

```
落ちた位置（traceback 逐語）
  patch_bridge.py:361  bridge_apply_connector → apply_patch_bounded(..., energize=energize_token,
                                                repo_identity=energize_token.repo_identity)
  patch_bridge.py:292  apply_patch_bounded   → _apply_to_working(...)
  patch_bridge.py:146  raise ValueError('apply: %s' % _r.get('reason'))
                       # ★当てられない=★書かない(fail-closed)
  ValueError: apply: ★no_hunk
```

**★門の順序を source で確認した（推測しない）:**

```
:355  bridge_apply_connector  if not isinstance(energize_token, _EnergizedApply): return NOT_ENERGIZED
        → ★通った（NOT_ENERGIZED の dict を返さず traceback が先へ進んでいる）
:???  apply_patch_bounded     if not repo_identity: raise         → ★通った
                              energize.repo_identity != repo_identity: raise → ★通った
                              validate_artifact(expected_base, expected_fingerprint) → ★通った
:94   _apply_to_working 開始
:100  _require_energize(workspace_dir, energize)
        → ★通った（★落ちたのは :146 ∴ :100 は実行され例外を出していない）
        ★中身 = isinstance(_EnergizedApply) の TypeError ＋ grant != realpath の ValueError
:146  ★ここで止まる = no_hunk
```

### ★意味

**因果鎖 ①import ②class 取得 ③mint ④isinstance は ★4つとも通った。**
**⑤書込 だけが到達していない。しかも止めているのは energization ではない。**

```
R3_INTERNAL_GATES  gates: [import, isinstance(:355), _require_energize(:100)]
                   passed: ★[import, isinstance(:355), _require_energize(:100)]  ←★3/3
                   failed: []
                   status: ★UNVERIFIED（★本線では未観測）
                   evidence: harness(verify_minter_B・tempfile・実repo書込0)では3つとも通った
R4_REJECTION       rejection_conditions:
                     ①token が _EnergizedApply でない → TypeError（_require_energize）
                     ②energize_token が _EnergizedApply でない → refuse NOT_ENERGIZED（:355）
                   actually_rejected: ★①を実発火（★監査が対照2件で実行）
                     対照A energize=None      → TypeError 'not an _EnergizedApply (write requires energization)'
                     対照B energize=別クラス  → ★同じ TypeError
                   unexpected: [] ／ status: ★①OBSERVED / ②UNVERIFIED
```

### ★訂正（2026-08-22 13:45）―― `OBSERVED_IN_TEST` は造語だった

私は上表で当初 `status: OBSERVED_IN_TEST` と書いた。**正本§3 の語彙に無い。**
正本の状態語は **10語のみ** ―― `PRESENT / ABSENT / OBSERVED / BROKEN / UNVERIFIED / UNKNOWN /
UNREACHABLE / CONFLICT / ESTABLISHED / REJECTED`。
§3 逐語「禁止：…読み替えない」に対し、**私は読み替えでなく新語を作った ―― 同じ穴。**
∴ **`UNVERIFIED`（本線未観測）＋ evidence 行に「harness では通った」を書く形へ直した。**
**語は増やさない**（監査も増やさない側を推奨。★Taka へは上げない ―― 我々で決着できる）。

### ★「:100 が通った」は推論から 対照へ（監査が実行）

```
① source の順序（確定・再調査不要）
   _apply_to_working の関数内で _require_energize は ★7行目 / _APPLY(no_hunk) は ★51行目
   ∴ ★前者が先。
② ★但し「落ちた行が後だから前は通った」は ★推論のまま ∴ ★門を直接撃った
   対照A  energize=None      → ★TypeError 'not an _EnergizedApply (write requires energization)'
   対照B  energize=別クラス  → ★同じ TypeError
   ∴ ★energization 門は ★実在し ★実際に拒否する。
   ★verify_minter_B が :146 まで到達したなら :100 は通っている＝★対照で裏づけた。
```

**★正本§10⑨「拒否条件を全列挙し、各拒否を実際に発火させる」―― ①は発火済。②は未了。**

### ★それでも ESTABLISHED にしない（理由を明記する）

```
① これは ★regression harness の実走であり ★本線ではない。
   正本§11 逐語「単体試験・sandbox 成功を本線成功として扱う」= ★禁止。
② workspace は ★tempfile.mkdtemp ∴ ★real repo への書込は 1度も起きていない。
③ R2 分母は ★変わらず 0 = twoder.bridge_minter を読む ★本線の呼び手は今も 0件。
④ R4 の拒否条件2つを ★まだ実発火させていない。
```

**∴ `UNDERSTANDING.result` は ★UNKNOWN のまま。`SAFE_EXISTING_FILE_MODIFICATION` へは昇格させない。**

### ★新しく分かったこと ―― 止まる位置が移った

```
before(08-22 02:00)  ①import で止まる（ModuleNotFoundError）
after (08-22 13:35)  ⑤書込の直前で止まる（no_hunk）

★止めているのは ★fixture であって energization ではない。
★既記録の別 finding = HARNESS_FIXTURE_PREDATES_UNIFIED_DIFF_CONTRACT
  （fixture が '+ NEW' を渡し @@ ヘッダを持たない ／ apply_unified_diff は 2026-08-19 導入）
★この AXIS では直さない。★別 AXIS の材料として渡す。
```

CREATION   status: NOT_EVALUATED
DECISION   GO
```

## ⑥ 置く最小差分（★まだ置いていない）

```
twoder/bridge_minter.py  ★2行だけ
  :26  from patch_bridge import _EnergizedApply
       → from twoder.patch_bridge import _EnergizedApply
  :27  import bridge_reconciler as rc
       → from twoder import bridge_reconciler as rc
```

- **判定も authority も門も触らない**
- **`operator.py` に触らない**（204行の実物・3箇所が package 名で import）
- **`patch_bridge.py` に触らない**（apply 側は既に package import で正しい）
- 新語彙 0 ／ 新台帳 0 ／ 新 state 0 ／ 新 front door 0

## ⑦ 記録して保留（この AXIS では直さない）

```
REGRESSION_HARNESS_UNRUNNABLE   試験4本が top-level import のため現在 実行不能。
                                ∴ DE-0438「2026-07-19 完走実績」は現在 再現できない。
EVO-0085 の因果鎖⑥⑦の格下げ    observed 0 → ★UNREACHABLE（監査の要求）。別途 EVO-0085 に記帳する。
正本§13 の CONFLICT             ★UNVERIFIED として正本側へ戻す（Taka へ報告）。
```
