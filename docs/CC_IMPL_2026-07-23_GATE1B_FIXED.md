# 実装担当 → 設計/監査担当: gate1b 族E欠陥 修正完了（handoff signal）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-23
- 対応: `CC_DESIGN_2026-07-23_GATE1B_FIX_GO.md`（(A) 承認・既存 SPEC 準拠）

## 修正内容（`probe/conformance_probe.py` の `_gate1b_ts`・FILL のみ）

- 旧（族E欠陥）: `grant_approval` を**同一引数で2回直呼び**（`mint` を bind するも未使用）→ sha1 決定論で自明に同一 → 偽陽性で death#2 OPEN。
- 新（SPEC §3 準拠）: **実 mint 経路 `mint_token` を attempt 違いで2回**（`mint(1, task_id=…)` / `mint(2, task_id=…)`）→ `approval_id` 相異を測る。生 id は非記録（V-2）。
- 骨格（`bind_real`/`source_ref`/`run_ladder`）は byte 不変。

## 検証（決定論・隔離下）

- 骨格保存 `verify_skeleton_preserved` = True
- §5 不変テスト **T1–T12 = 10/10 維持**
- **再走行**: `gate1b_ts` = **passed=True**（death#2 は実経路で CLOSED）／ **DIRECT failing（非注入）= NONE → ★3(B) DIRECT-free**

## ハンドオフ（CC-α 担当分）

- anchor 死因ラダー **death#2 = OPEN→CLOSED** 更新（`mint_token(attempt)` で相異、検証一致）。
- 再走行で `gate1b`=green・DIRECT 無しを監査 → **★3(B) DONE 確定**。
- commit=Taka（配線＋token-gate＋本 gate1b 修正の束。working tree: `M probe/conformance_probe.py` ほか）。

## 位置づけ（自己申告）

これは私が作り込んだ**族E（代理を実物と取り違えた計器欠陥）**の修正。敵対レビュー（CC-α）が拾えたのは検出機構が正しく働いた結果。SPEC は最初から `mint_token` を指定しており、逸脱は私の FILL 実装側にあった。
