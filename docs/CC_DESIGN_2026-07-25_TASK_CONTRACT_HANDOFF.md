# 設計/監査 → 実装: Task Contract（EXEC_ARCH の一段抽象化）発注

- 発: 設計/監査(CC-α) / 2026-07-25 / repo=egl / **決定論・LLM 不使用(判断部は人手/別途)・:8005/GPU 不使用**
- 正本: DE-0525(A/C/D は Task Contract 欠落の発見) + `docs/CC_DESIGN_2026-07-25_EXEC_ARCH_ACD_HANDOFF.md` + 本 handoff
- 背景: A/C/D の C/D が解けなかった根本原因＝「比較対象(正典)が未定義のまま比較させていた」。個別修正でなく**各タスクに契約を持たせる**。
- **A は完成クローズ**(比較不要)。本発注は C/D を契約から再導出できるようにする。

## 0. 役割分担（重要・遵守）
- **実装(Qwen/CC-impl)= 機械を作る**: 契約の型・C/D 再導出・ゲート・**決定論で導出できる契約項目の候補生成**。
- **設計(CC-α)= 判断を書く**: 意味判断が要る項目（`required_inputs` の"読むべき"、状態の canonical 意味）を authored。**Taka は裁定のみ**（設計でも確定できない曖昧のみ上げる）。
- したがって本ビルドは「機械＋種(seed)」まで。**全タスクの契約を一括で埋めない。空から慎重に育てる。**

## 1. 型（2 ファイル）

### `structure/TASK_CONTRACTS.jsonl`（1 タスク 1 行）
```
task_id          : 対象タスク(例 s_embed_axes)
required_inputs  : 読むべき資料 [paths]           ← 判断=設計が書く。未記述は UNRESOLVED_NO_CONTRACT
expected_outputs : 生成物 [paths]                 ← 決定論導出可(impl 候補生成)
allowed_writes   : {path, via}  書込先と経路       ← 決定論導出可(sole-writer/API 名)
normalization    : 使う正規化辞書の参照(既定 CANONICAL_STATES)
```
- **決定論で出せる項目（expected_outputs / allowed_writes / actually_loaded）は impl が候補生成**。設計が確認して確定。
- **`required_inputs` は設計が authored**。無い間はそのタスクを `UNRESOLVED_NO_CONTRACT` と正直表示（faking しない）。

### `structure/CANONICAL_STATES.jsonl`（正規化辞書・authored）
```
raw_symbol : 生の状態名(例 Completed / 完成 / DONE)
canonical  : 寄せ先(例 STATE_DONE)
authored_by: 誰が確定したか
```
- **原則: 綴り一致で自動 collapse しない。** 意味を見て寄せる。**意味が別なら別 canonical**（同綴り別意=D が実検出した本物の矛盾を消さないため）。
- **未確定の状態は `UNRESOLVED_NO_CANONICAL`**（勝手に寄せない）。辞書は空から始めてよい。

## 2. 機械（`structure/s_task_contract.py` が生成）
- **C 再導出 → `READ_PATHS.jsonl` を契約駆動に更新**: 各契約タスクで `required_inputs`(契約) vs `actually_loaded`(AST 実測) → `MISSING`(=CONTEXT_GAP) / `OK`。契約なきタスクは `UNRESOLVED_NO_CONTRACT`。
- **D 再導出 → `STATE_MACHINES.jsonl` を正規化駆動に更新**: 各状態を `CANONICAL_STATES` で canonical へ写像 → **(machine, canonical) で cross-machine 衝突**を検出。未写像は `UNRESOLVED_NO_CANONICAL`（auto-collapse 禁止）。
- 出力は `egl/structure/`。新 Ledger/Registry を作らない。MD は jsonl 導出。

## 3. 常設ゲート = `structure/s_task_contract.py --check`（全 GREEN で PASS）
1. **byte 一致再生成**（契約・辞書 pin 入力から）。
2. **契約スキーマ検査**（4 項目・型）。`allowed_writes.via` が実在の sole-writer/API を指すこと。
3. **auto-collapse 禁止検査（陰性対照）**: 同綴り別 canonical のペアを注入 → 機械が**勝手に同一へ寄せない**ことを確認（寄せたら RED）。
4. **C 検出力（陰性対照）**: `required_inputs` に実際に読まれない資料を1つ持つ契約を注入 → `MISSING` を出す（出なければ RED）。
5. **D 検出力（陰性対照）**: 既知の cross-machine 衝突(CREATED/CLOSED)が canonical 経由で再検出されること。

## 4. 完了条件（Stage B 同水準）
- ゲートが**本物の乖離を1回以上検出、または陰性対照で赤を確認**して初めて完了（§3-3/4/5 のいずれか実測）。空辞書・空契約でも**機械が正しく UNRESOLVED を出す**ことは示すこと。

## 5. 受入（設計/監査が独立再検証）
- 私が fresh 再実行して契約・辞書・C/D 再導出が **byte 一致**・`--check` GREEN robust。
- 陰性対照（auto-collapse 禁止 / C MISSING / D 衝突）で**実際に RED/検出が出る**（load-bearing）。
- 契約なき所が `UNRESOLVED_NO_CONTRACT`、未写像が `UNRESOLVED_NO_CANONICAL` で**正直に空いている**（捏造ゼロ）。

## 6. 完了後
- `CC_IMPL_2026-07-25_TASK_CONTRACT_BUILT.md` → 設計独立再監査 → CONSISTENT → **commit=Taka** → DE 起票。
- その後、**設計(私)が seed 契約と canonical を少しずつ authored** して C/D が実タスクで点灯していく（本ビルドの範囲外・継続作業）。
- 想定と実測がズレたら silently 合わせず BUILT に正直記録。過剰主張より正直な UNRESOLVED。

---
*設計/監査 CC-α。実装は本ファイル保存でトリガ。判断項目(required_inputs/canonical)は設計が後で埋める—impl は機械と決定論候補まで。疑義は途中でも報告可。*
