# 実装担当 → 設計/監査担当: Task Contract（機械＋種）BUILT

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-25
- 対応: `CC_DESIGN_2026-07-25_TASK_CONTRACT_HANDOFF.md`（DE-0525・私の ACD flag 由来）
- repo=egl。決定論・LLM 不使用・:8005/GPU 不使用。役割: 実装=機械＋決定論の種のみ／判断項目は設計が後で authored。

## 成果物（working tree・未commit）

- `egl/structure/s_task_contract.py`（機械: 契約種生成＋C/D 再導出＋`--check`）
- `TASK_CONTRACTS.jsonl`（**17 種**・decision 項目は空で正直）／`CANONICAL_STATES.jsonl`（**空**・authored 待ち）
- `READ_PATHS.jsonl`（C・契約駆動）／`STATE_MACHINES.jsonl`（D・正規化駆動）を再導出（supersede）
- `s_exec_arch_acd.py`（**A-only へ縮退**）＝二重 writer 解消（下記）

## 検証（Stage B 同水準・負の制御 load-bearing）

- **byte一致再生成**・**契約スキーマ検査**（4項目・`allowed_writes.via` の sole-writer 実在）GREEN。
- **3 負の制御が load-bearing**（実測）:
  1. **auto-collapse 禁止**: 同綴り別 canonical（DUP→A/B）を注入 → 機械は同一へ寄せず [A,B] を保持（寄せたら RED）。同綴り別意（D の本物矛盾）を消さない。
  2. **C 検出力**: `required_inputs` に未読資料 → `MISSING` を出す。
  3. **D 検出力**: `CREATED` を両 machine で同 canonical へ写像 → cross-machine 衝突を再検出（dw/workcell + parallel_router）。
- **正直な空状態**: 種の `required_inputs` は全て `UNRESOLVED_NO_CONTRACT`（17）、CANONICAL 空ゆえ D は全 `UNRESOLVED_NO_CANONICAL`（52）。**捏造ゼロ**。空辞書・空契約でも機械が正しく UNRESOLVED を出すことを実証（§4）。
- 種（決定論候補）は実測: 例 `s_embed_axes` → expected_outputs=[EMBED_AXES_CANDIDATE.jsonl, EMBED_AXES_STABILITY.json]、actually_loaded 4件、via=self(open w)。

## ★ 二重 writer の解消（handoff の supersede 意図を実装）

- handoff §2「READ_PATHS/STATE_MACHINES を契約/正規化駆動へ更新」で s_task_contract がこの2ファイルを書く → **committed の ACD も同2ファイルを書いていて二重 writer（ACD --check が RED 化）**を確認。
- handoff「A は完成クローズ・C/D は契約へ再導出」に従い、**ACD を A-only（ENTRYPOINTS_EXT のみ）へ縮退**（build_D は s_task_contract が import する helper として残置）。→ **ACD --check GREEN / s_task_contract --check GREEN の両立**・sole-writer 尊重（A=ACD, C/D=task_contract）。
- ※これは committed ツール（ACD）の修正を含む。handoff の supersede 指示に沿った実装として実施・報告します。

## ハンドオフ

- 次: **CC 独立再監査（byte一致 + 負の制御 + 正直な UNRESOLVED + 二重 writer 解消）→ CONSISTENT → commit=Taka → DE 起票**。
- その後、**設計が seed 契約（required_inputs）と CANONICAL_STATES を少しずつ authored** して C/D が実タスクで点灯（本ビルド範囲外・継続）。私の ACD flag（C の出典欠落 / D の写像）が本抽象化を駆動しました。
