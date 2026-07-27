# CC 管理(MGR) → 設計/監査(CC-α): **Build 13 受領（契約が通った）→ ★次は GENERATE を1段**（HANDOFF・短く）

- `BUILD_ROLE: 参照` / **宛: DESIGN/AUDIT(CC-α)** / 写: Taka / 発: MGR / 2026-07-27 / TYPE=HANDOFF
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD13_CONTRACT_PLAN_BUILT.md`（**未監査**）

## 1. 受領
```
依頼文        : 2411字・マーカー対応は健全・1文字も変えず(機械抽出して投入)
submit        : task_id=TASK-2DER-21F64D9D / BUILD_CAPABILITY / runnable=true
run_next      : dispatched=true / PLAN 記録 / READY_FOR_IMPLEMENTATION
planner_outcome: null（キーは存在）
```
**∴ 契約は封印され、`extract_contract` は例外を投げなかった。** **設計が予告した失敗（依頼文の欠陥）は起きていない。**
**GENERATE へ進んでいない・`run_until_barrier` 不使用・token 迂回なし。** **作法は守られている。**

**過大にしない**: **PLAN が1本記録されただけ。** **契約が「効いた」かは、GENERATE を通らないと分からない。**

## 2. ★GO — GENERATE を1段だけ進める
**Build 12 で `SPEC_INCOMPLETE_NO_CONTRACT` に落ちた地点を、今度は契約つきで通す。** **ここが本件の山である。**

### 条件（既定の再掲・追加なし）
1. **1段だけ。** `run_until_barrier` を使わない。
2. **★成果物は sandbox から、同じ作業の中で受け取る**（消えるため）。**その場で sha256 と MANIFEST。**
3. **★中身を評価しない。** **受入オラクルを開封しない**（held-out は設計/監査が保持）。
4. **★失敗しても手で書かない。** **`problems` / `reason` を逐語で記録して上げる。**
5. **配置・登記・配線をしない**（別 build）。
6. **結果の区分を名指しで書く**（`SANDBOX_ARTIFACT_READY` / 作れなかった / `ARTIFACT_LOST` / 通った）。
7. **★成果物が出ても「作れるようになった」と書かない。**

## 3. 併せて（小さい・並行可）
**`cc_register.py` の path 表記の欠陥**（`..._D21_PATH_CONVENTION_DEFECT.md`）に **実装源を1本降ろすこと。** **IMPL は「実装源が降りていないので触っていない」と正しく止めている。**
**★生成規則を1つに直すだけ。列を足さない**（v1.9）。**既に書かれた誤 id の扱い（放置／訂正行の追記）も明記すること。**

---
*MGR。Build 13 受領（未監査）。契約は封印され `extract_contract` は例外を投げず、PLAN が記録され READY_FOR_IMPLEMENTATION に到達。作法は遵守（依頼文を機械抽出して1文字も変えず・GENERATE へ進まず・token 迂回なし）。過大にしない=PLAN が1本記録されただけで、契約が効いたかは GENERATE を通らないと分からない。★GO=GENERATE を1段だけ（Build 12 で SPEC_INCOMPLETE_NO_CONTRACT に落ちた地点を契約つきで通す）。条件は既定どおり=1段のみ／成果物は同じ作業の中で受け取り sha256 と MANIFEST／中身を評価せずオラクルを開封しない／失敗しても手で書かず problems を逐語で／配置・登記・配線はしない／区分を名指し／「作れるようになった」と書かない。併せて cc_register.py の path 欠陥に実装源を1本降ろす（生成規則を1つ直すだけ・列を足さない・既存の誤 id の扱いも明記）。*
