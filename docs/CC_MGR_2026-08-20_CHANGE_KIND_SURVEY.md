# 変更種別 ―― 2DER が **表現できる 形** の 全件調査（★実装 0 ／ ★ESDE 形式）

**2026-08-20 21:0x ／ ★`8020A9D6` を 通す ための 特例で 扱わない ―― ★表現形態の 不足と して 扱う**

---

## AXIS: `CHANGE_KIND_EXPRESSIBILITY`

```
SCOPE:
  entry       : PLAN(build_planner) の 受入検査
  exit        : 実 repo 反映（`_place_and_commit` ／ `apply_cycle`）
  authority   : PLAN validate（fail-closed）／ real repo は bridge_minter の Taka 門
  persistence : PLAN payload(event log) ／ sandbox workspace ／ git
  components  : contract_from_plan / build_planner / generate_via_runner / qwen_worker /
                adjudicator / _place_and_commit / source_to_patch+apply_cycle
```

---

## 1. ★★変更種別ごとの 実測（★契約器に 実際に 通した）

| 種別 | PLAN が 宣言 | **contract_from_plan の 実測** | GENERATE が 作る | test が 検証 | AUDIT | 実 repo 反映 |
|---|---|---|---|---|---|---|
| **K1 新規関数作成** | `target_file="impl.py"` ＋ `from impl import <名>` | **`reason=None`（★通る）** ／ skeleton `def make_diff(a, b):` | sandbox の `impl.py` **全文** | `from impl import <名>` を 呼ぶ | 受理 | **`_place_and_commit` → `twoder/<関数名>.py`（★稼働中）** |
| **K2 新規file作成** | `target_file="linkage_gate.py"` | **`unexpected_target`** | ― | ― | ― | ― |
| **K3 既存関数変更** | `target_file="bridge_minter.py"` | **`unexpected_target`** | ― | ― | ― | ― |
| **K4 既存file 局所変更** | `target_file="impl.py"` ／ 試験に 関数 import 無し | **`no_function_name`** ★← `8020A9D6` の 停止 | ― | ― | ― | ― |
| **K5 複数file変更** | `target_file="impl.py"`（★1件しか 書けない） | `reason=None`（★**契約は 通る**） | **sandbox の 1 file のみ** | 1 file 分 | ― | **`apply_cycle` が `REFUSED_MULTI_FILE`** |

```
★★＝ ★2DER が 端から 端まで 表現できるのは ★★K1 だけ。
★K2/K3 = ★入口(許可リスト)で 止まる ／ K4 = ★契約の 形で 止まる ／
★K5 = ★契約は 通る が ★★下流(単一file制約)で 破れる ＝ ★★対等性の 崩れが 遅れて 出る。
```

---

## 2. EQUALITY（対等性）★★これが 本件の 核心

```
canonical_protocols:
  ★PLAN 側     = `target_file`(1件) ＋ `test_body`(★`from <module> import <name>` を 要求)
  ★GENERATE 側 = ★sandbox に ★`target_file` **1件を 全文 生成**（`qwen_worker` が `open(...,'w')`）
  ★test 側     = `pytest -q <test_file>` ／ ★`from impl import <name>` 前提
  ★反映 側     = ★`_place_and_commit`= **関数名 → `twoder/<name>.py` の 新規配置**
                 ★`apply_cycle`      = **既存 file への 差分適用**（★未接続）
compatible   : ★K1 のみ（PLAN → GENERATE → test → 反映 が ★同じ protocol に 載る）
incompatible : ★K3/K4 ―― ★『既存 file の 一部を 直す』を ★★PLAN も test も 反映も 表せない
               ★K5 ―― ★PLAN は 表せる が ★GENERATE と 反映が 1 file しか 扱えない
unknown      : ★K2（★許可リストに 足せば 通るかは 未実測）
status       : ★★CONFLICT
```

**★`no_function_name` は 「試験の 書き方の 問題」では ありません。**
**★★『生成物＝1つの 新しい 関数』という 前提が ★契約・生成・試験・配置の 4面に 焼き付いて いる** のが実体です。

---

## 3. SYMMETRY（対称性）

```
pairs / required=5 / present=1 / missing=3 / unverified=1
  ✔ 新規関数作成 ↔ `_place_and_commit`（新規配置）            … PRESENT
  ✘ 既存関数変更 ↔ ★『既存 file を 対象に する 契約』         … MISSING
  ✘ 既存file局所変更 ↔ ★『関数を 作らない 変更の 試験契約』   … MISSING
  ✘ 複数file変更 ↔ ★『複数 file の 適用』                     … MISSING（★単一file制約）
  ☐ 新規file作成 ↔ ★許可リスト                                … UNVERIFIED
```

---

## 4. LINKAGE（連動性）

```
edges / declared=5 / observed=1 / broken=4
  E_K1 PLAN→GENERATE→test→_place_and_commit   status=OBSERVED（★本日 稼働中の 経路）
  E_K2 PLAN(新規file)→…                        status=BROKEN（`unexpected_target`）
  E_K3 PLAN(既存関数)→…                        status=BROKEN（`unexpected_target`）
  E_K4 PLAN(局所変更)→…                        status=BROKEN（`no_function_name`）★実走で 取得
  E_K5 PLAN→GENERATE→…→apply                  status=BROKEN（`REFUSED_MULTI_FILE`）
```

---

## 5. HIERARCHY（階層性）

```
required=4 / passed=3 / violation=1 / unreachable=0
  ✔ PLAN の fail-closed は 働いて いる（★通すべきでない 物では なく ★『表せない 物』を 止めた）
  ✔ authority 境界（real repo は Taka 門）
  ✔ 新規配置(`_place_and_commit`) と 既存変更(`apply_cycle`) は ★別部品に 分かれて いる
  ★violation = ★★『変更種別』という 概念が ★どの 層にも 無い
     ―― ★PLAN も contract も packet も ★『何を する 変更か』を ★1欄も 持たない
     ＝ ★層を 跨いで 暗黙に K1 を 仮定して いる
```

---

## 6. R1〜R4

```
R1 END_TO_END : ★K1 のみ OBSERVED ／ K2〜K5 は ★到達しない
R2 DENOMINATOR: 表現できる 種別 = ★★1/5
R3 INTERNAL   : PLAN validate は ★到達し ★拒否した（★通過して いない）
R4 REJECTION  : ★4条件を 実走で 発火
   `unexpected_target`(K2,K3) ／ `no_function_name`(K4) ／ `REFUSED_MULTI_FILE`(K5)
   ★unexpected = ★★K5 が ★契約段では 通って しまう こと（★下流で 初めて 破れる）
```

---

## 7. ★★自己参照問題（★ご指示：先に 解決経路を 示せ）

```
★この 修理（★変更種別を 表現できる ように する）自体が ★★K3/K4 に 当たる
   ―― ★`contract_from_plan` ／ `build_planner` は ★★既存 file で ある。
★★∴ ★いまの 門では ★この 修理を 2DER に 実装させられない（★★自己参照）。
★★解決経路は 2つ しか 無い（★実測から）:
   ★(甲) ★K1 の 形で 作る ―― ★『変更種別を 判定する 新しい 関数』を ★1つ 作らせる
        （例: ★与えられた PLAN から 変更種別を 返す 純関数）
        → ★`_place_and_commit` が ★`twoder/<関数名>.py` として ★実 repo に 置く（★稼働中の 経路）
        → ★その 関数を ★既存 file から 呼ぶ 1行だけを ★別途 繋ぐ
        ★★＝ ★2DER が 作れる 形に 分解する。★『既存 file の 変更』は ★最後の 1行だけに 縮む。
   ★(乙) ★Taka 裁定で ★Claude が 代行実装する
        ★★但し ご指示で ★A/B 代行は 禁止 ／ ★本件も 同じ 種類 ∴ ★私からは 選ばない。
★★私の 判断 = ★(甲) が ★禁止条件を 1つも 破らない（★検査を 消さない ／ 特例を 作らない ／
   ★既存 file 変更を 省略しない ―― ★★『2DER が 作れる 単位に 分ける』だけ）。
★★但し ★最後の 1行（★呼び出しを 繋ぐ）は ★★K4 の まま 残る ∴ ★そこは Taka 裁定が 要る。
```

---

## 8. UNDERSTANDING / CREATION / DECISION

```
UNDERSTANDING:
  candidate  : `EXISTING_FILE_MODIFICATION`（★2DER が 既存コード変更を 表現・生成・検証・反映できる 能力）
  requires   : ★変更種別の 語 ／ 種別ごとの test 契約 ／ 種別ごとの 反映経路 ／ 複数file の 扱い
  evidence   : ★本日の 実測（K1 のみ OBSERVED ／ K2〜K5 BROKEN）
  unresolved : ★★①種別を どの 層に 持たせるか ②K4 の test 契約を どう 定義するか
               ③K5(複数file)を 今回 含めるか ④自己参照の 最後の 1行
  result     : ★★UNKNOWN（★ESTABLISHED に しない）
CREATION: NOT_EVALUATED
DECISION: ★★DESIGN_HOLD
```

**★実装案を 1つに 確定できて いません ∴ ★commit も 投入も しません。**
**★`8020A9D6` は 再投入して いません。★特例・検査削除・Claude 代行 いずれも して いません。**

---

## 9. ★Taka 裁定を 要求する 点（★4件）

```
★① ★『変更種別』を どこに 持たせるか（★PLAN の 新しい 鍵 ／ 既存欄の 解釈 ／ 別の 面）
★② ★K4（既存file 局所変更）の ★正規の test 契約を 何と するか
   ―― ★ご指示の 方向「★変更対象 file / 対象箇所 と 要求された 変更を 試験する」を
     ★具体の 契約に する には ★『対象箇所』を どう 機械が 表すか を 決める 必要が 在る
★③ ★K5（複数file変更）を ★今回の 範囲に 含めるか（★含めると 単一file制約に 触れる）
★④ ★自己参照の 最後の 1行（★新関数を 既存 file から 呼ぶ 接続）を どう するか
```
