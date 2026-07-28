# 設計/監査 → MGR（写: Taka / IMPL）: **D-47 — `request_thread.py` は書きかけの残骸ではない。★正典 SPEC 3本 + 監査5本を通った正規の成果物である。捨てられた形跡は無い**

- `BUILD_ROLE: 参照`（**調査のみ。★配線していない・`request_thread` を呼んでいない・実装案を書いていない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-29 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8` — `§12` を最大版で読んだ値）**
- **受領**: `CC_MGR_2026-07-29_D46_RECEIVED_DEFINED_BUT_UNCONNECTED.md`（問い4件）

## 0. ★結論
> **MGR の問い「正典なのか、書きかけで捨てられたものなのか」への答え:**
> **★正典である。書きかけではない。捨てられた形跡は無い。**
> **★接続されていない理由は、別に在る**（§4）。

---

## 1. 問い① — 由来（git 実測・打ち切り無し）
```
再現: git -C rri log --format="%h %ad %s" --date=short --follow -- rri/request_thread.py
総件数: ★3 / 確認 3 / 打ち切り無し

02bb767 2026-07-24 RRI RTHREAD stage 1 v0.1a: 複式保存則の核 (I1/I2) + 状態機械 + projection
154be50 2026-07-24 RRI RTHREAD stage 2a: accounts 機械核 (chart検証/suspense決着/account保存 load-bearing)
f9f132d 2026-07-24 RRI RTHREAD stage 2a F-2 cleanup: 到達不能な suspense guard を除去
```
**ファイル冒頭の自己申告**（実読）:
```
"""RTHREAD stage 1 — 依頼ID(1接触=1スレッド)の帳簿。複式保存則(I1 処分次元 / I2 科目次元)+状態+projection。
   sole writer of rthread_events.jsonl。first-class store は event stream のみ(architecture)。
   RTHREAD は projection(fat record を作らない=裁定#25)。信頼フィールドは呼出側封印(G-1)。"""
```
> **★「裁定#25」「G-1」への言及が在る。** **∴ 設計裁定に紐づいて書かれている。** **思いつきではない。**

## 2. 問い② — 正典から参照されているか（★されている）
```
再現: grep -rl "request_thread|RTHREAD|rthread" egl/docs --include=*.md
総件数: ★78 文書 / 確認 78 / 打ち切り無し
```
**★専用の SPEC が3本在る:**
| 文書 | 位置づけ |
|---|---|
| **`SPEC_RTHREAD_STAGE1_v0.1.md`** | 段1 の仕様 |
| **`SPEC_RTHREAD_STAGE1_v0.2.md`** | 同 改訂 |
| **`SPEC_RTHREAD_STAGE2a_v0.1.md`** | 段2a の仕様 |
| `RRI_IMPL_SPEC_v0.1.md` | RRI 実装仕様（上位） |

**★監査が5本通っている:**
```
CC_AUDIT_2026-07-24_RTHREAD_STAGE1_IMPL_CONSISTENCY.md
CC_AUDIT_2026-07-24_RTHREAD_STAGE1_v0.1a_CONSISTENT.md
CC_AUDIT_2026-07-24_RTHREAD_STAGE1_v0.2_CONSISTENT.md
CC_AUDIT_2026-07-24_RTHREAD_STAGE2a_CONSISTENT.md
CC_AUDIT_2026-07-24_RTHREAD_STAGE2a_F2FIX_CONSISTENT.md
```
> **∴ SPEC → 実装 → 監査（CONSISTENT）の1周が★5回回っている。**
> **★これは「書きかけ」の反対である。** **我々の手続きを最後まで通った成果物である。**

## 3. 問い③ — 捨てられた形跡（★無い。むしろ後続の設計が続いている）
```
2026-07-25 CC_DESIGN_RTHREAD_STAGE2b_REDESIGN_PLAN.md   ← 段2b の作り直し計画
2026-07-25 CC_DESIGN_RTHREAD_2b-r2_AXIS_FREEZE_HANDOFF.md / CC_IMPL_..._BUILT.md
2026-07-25 CC_DESIGN_RTHREAD_2b-r3_REFREEZE_HANDOFF.md   / CC_IMPL_..._BUILT.md
```
**★「作り直し」は段2b（勘定科目の軸）であって、★段1の状態機械ではない**（実読）:
> **stage2b PLAN §0:「hard 不変量は問い台帳（stage1 I1＝ゼロ落ち禁止・一度だけ処分）のみ。★account 次元は soft。」**
> **∴ 段1（＝終了条件・状態機械）は★hard 不変量として維持されている。** **作り直しの対象外である。**

**★捨てられた形跡は1件も見つからなかった。** **探索範囲は `egl/docs` の md 78文書＋git 履歴3件である。**

## 4. ★なぜ接続されていないのか（1件、実物が見つかった）
```
egl/docs/CC_IMPL_2026-07-24_RRI_HALT.md（実読）

「RRI_IMPL_SPEC v0.1 について halt（フロー矛盾＋成果物3未投下）」
 1. フロー矛盾（要 Taka 裁定）: spec は 実装者=Qwen（raw_input→submit）と明記。
    ANCHOR §1-1（実装＝本 CC インスタンス）と食い違う。
    ★「RRI が新フロー（実装インスタンス）か旧フロー（Qwen submit）か」が未確定。
    spec 自身の「矛盾規則: halt」に従い停止。
 2. 成果物3 未投下: 骨格＋不変テストが egl/docs に無い。
 必要な確定: (a) RRI の実装フロー裁定 (b) 成果物3 の投下
 「実装インスタンスは着手せず待機」
```
> **★接続されていない理由は「捨てられたから」ではない。**
> **★`RRI_IMPL_SPEC v0.1` が halt しており、その halt を解く裁定（a）が★出ていないからである。**
> **★つまり `request_thread.py` は「halt の手前まで作られて、そこで待っている」状態である。**

**★これは推測ではない。** **halt 文書が「必要な確定」を2件挙げて「待機」と書いている。**
**★ただし、その裁定が後日出たかどうかを私は確かめていない**（§6-1）。

## 5. 問い④ — `G-54` の分類（MGR は未読と書いた）
| | |
|---|---|
| **`G-54`** | **★部分定義**（D-46 §3 で報告済） |
| **辿れる** | **RRI の記録 id**（`RSIG-00329` を front door で `resolved=True` まで実測） |
| **辿れない** | **判断結果**（`request_type` / `INTENT_STRATEGY` / `RRI_PREFLIGHT`）／**残差**（`RRI_RESIDUAL`）／**`trace_id`・`task_id` の紐付け**（実物が `null`） |
| **★他の3件との違い** | **`G-51`〜`G-53` は「定義が在って未接続」。** **`G-54` は★定義そのものが無い**——Event Trace は本日作ったものであり、参照構造を誰も定義していない |

## 6. ★未確認（先に書く）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`RRI_HALT` の「必要な確定(a)(b)」が後日出たかを確かめていない** | **★これが次に確かめるべき1点である。** CC-α / MGR の指示があれば |
| 2 | **`SPEC_RTHREAD_*` 3本の中身を読んでいない**（存在と題名のみ確認） | CC-α / 必要なら |
| 3 | **78文書のうち、実際に読んだのは4本**（`RRI_HALT` / `STAGE2b PLAN` / 一覧の題名） | **★「78文書を確認した」とは書いていない。一覧したのが78、読んだのが4である** |
| 4 | **`rri` repo 以外に同種の状態機械が在る可能性** | CC-α / 必要なら |

## 7. ★禁止事項の遵守
- **配線していない。** **`request_thread` を1度も呼んでいない。**
- **「こう繋ぐべき」を書いていない。** **実装案を書いていない。**
- **投入していない。台帳を直読していない。**

---
*CC-α D-47（調査のみ）。★MGR の問い「正典なのか書きかけで捨てられたものなのか」への答え=**正典である。書きかけではない。捨てられた形跡は無い**。①由来=git 履歴3件（2026-07-24 に stage1 v0.1a→stage2a→F-2 cleanup）で、ファイル冒頭が「裁定#25」「G-1」に言及＝設計裁定に紐づいて書かれている。②正典からの参照=`egl/docs` の md 78文書が言及し、**専用 SPEC が3本**（`SPEC_RTHREAD_STAGE1_v0.1`/`v0.2`/`SPEC_RTHREAD_STAGE2a_v0.1`）＋上位の `RRI_IMPL_SPEC_v0.1`、**監査が5本 CONSISTENT で通っている** ∴ SPEC→実装→監査の1周が5回回っており「書きかけ」の反対である。③捨てられた形跡=**1件も無い**。むしろ後続（2026-07-25 の stage2b 作り直し）が続いているが、**作り直しの対象は段2b の勘定科目の軸であって段1の状態機械ではない**——stage2b PLAN §0 が「hard 不変量は問い台帳(stage1 I1)のみ。account 次元は soft」と明記 ∴ 段1（終了条件・状態機械）は hard 不変量として維持されている。★**接続されていない理由の実物が見つかった**=`CC_IMPL_2026-07-24_RRI_HALT.md` が「`RRI_IMPL_SPEC v0.1` についてフロー矛盾（実装者が Qwen か実装インスタンスか未確定）と成果物3未投下により halt。実装インスタンスは着手せず待機」と書いている ∴ **捨てられたからではなく、halt を解く裁定が出ていないから**であり、`request_thread.py` は「halt の手前まで作られてそこで待っている」状態である（推測ではなく halt 文書が「必要な確定」2件を挙げて「待機」と書いている。**ただしその裁定が後日出たかは確かめていない**）。④`G-54` の分類=**部分定義**で、RRI の記録 id は front door で `resolved=True` まで実測できるが判断結果・残差・`trace_id`/`task_id` の紐付けは辿れず、**`G-51`〜`G-53` が「定義が在って未接続」なのに対し `G-54` は定義そのものが無い**（Event Trace は本日作ったもので参照構造を誰も定義していない）。★未確認=**`RRI_HALT` の「必要な確定(a)(b)」が後日出たかを確かめていない（これが次に確かめるべき1点）**／`SPEC_RTHREAD_*` 3本の中身は未読（存在と題名のみ）／**78文書は一覧しただけで読んだのは4本**（「78文書を確認した」とは書いていない）／`rri` 以外に同種の状態機械が在る可能性は排除していない。★配線せず `request_thread` を1度も呼ばず、実装案も繋ぎ方も書いていない。*
