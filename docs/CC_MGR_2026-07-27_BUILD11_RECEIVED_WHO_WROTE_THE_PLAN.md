# CC 管理(MGR) → 設計/監査(CC-α): **Build 11 受領。修理は実証された。★ただし「誰が PLAN を書いたか」は未解決**（HANDOFF）

- `BUILD_ROLE: 参照` / **宛: DESIGN/AUDIT(CC-α)** / 写: Taka / 発: MGR / 2026-07-27 / TYPE=HANDOFF
- **運用方針 確認済（版: v1.7）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD11_NEW_TASK_THROUGH_PLAN_BUILT.md`（**未監査**）

## 1. 受領
- **★修理の実証**: `run_next` の返りに **`planner_outcome` キーが存在**（値は `null`）。**Build 10 ではキー自体が無く、10R では証拠②③が成立しなかった。本 build で初めて直接観測できた。**
- **PLAN が記録され `READY_FOR_IMPLEMENTATION` に到達。** 依頼文は1文字も変えず、`run_until_barrier` を使わず、間に他の submit を挟んでいない。
- **`twoder/ledger_query.py` は削除済**（参照ゼロを確認してから実行）。**2本目の読み口は残っていない。**
- **★IMPL が「到達経路」を自分で明示した**: **(A) 自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。** ——**移行の実態を、報告の定型として毎回可視化する形になっている。良い。**

## 2. ★未解決（監査 D-19・これ1つ）
```
dispatched      : true
auto_served     : None
planner_outcome : null
nlo             : actor_role=MANAGER / actor_id=CLAUDE
→ PLAN は記録され READY_FOR_IMPLEMENTATION になった
```
> **★この3つ（`dispatched: true` / `auto_served: None` / `planner_outcome: null`）が同時に成り立つのは、どの経路か。**
> **∴ PLAN を書いたのは、Qwen planner か、決定論テンプレか、それ以外か。**

- **IMPL が判定しなかったのは正しい**（観測だけでは決まらない）。
- **★「Qwen が書いた」と読み替えない。** **`auto_served` が `None` である以上、それは言えない。**
- **確かめ方はコード構造の直読でよい**（v1.3 §2-1 の許可範囲）。**「動く」と書くなら再現コマンドを併記すること**（v1.5）。
- **`planner_outcome` が `null` である理由も同じ問いの一部である。**

## 3. 過大にしない（Taka へはこう上げた）
- **示せたのは「捨てられていた理由を運ぶ経路が、本番で生きている」ことだけ。**
- **PLAN が1本記録された。誰が書いたかは未確定。**
- **「2DER が作れるようになった」とは書かない。**

## 4. 次（D-19 の後）
**PLAN の中身が使えるものなら、優先度1（`ids.resolve` の配線）はその PLAN に沿って進められる。** **中身の評価は D-19 の後に。**
**worker には進めない**（範囲外・既定どおり）。

---
*MGR。Build 11 受領（未監査）。★修理は実証された（`planner_outcome` キーが本番の応答に存在。Build 10 では無く 10R では確かめられなかった）。PLAN が記録され READY_FOR_IMPLEMENTATION に到達。ledger_query.py は削除済で2本目の読み口は残っていない。IMPL が「到達経路(A) 自分で読んで転記した」を定型で明示したのは良い。★未解決 D-19=`dispatched: true` / `auto_served: None` / `planner_outcome: null` が同時に成り立つのはどの経路か、PLAN を書いたのは Qwen か決定論テンプレか。「Qwen が書いた」と読み替えない。過大にしない=示せたのは理由を運ぶ経路が生きていることだけで、誰が書いたかは未確定。*
