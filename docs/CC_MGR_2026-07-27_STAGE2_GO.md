# CC 管理(MGR) → 設計/監査(CC-α): **段2 へ GO — Execution Architecture 本体の作成**（HANDOFF）

- `BUILD_ROLE: 参照`（実装源は `EXEC_ARCH_WORK_ORDER_v0_1.md` 全文）
- **宛: DESIGN/AUDIT(CC-α)** / 写: Taka / 発: MGR / 2026-07-27 / TYPE=HANDOFF
- **運用方針 確認済（版: v1.9）**

## 0. 権限
Taka 直接発話（2026-07-27・逐語）: **「続けて。」**
**段0（所在）と段1（繋がっているか）は答えが出た。** **∴ 段2 に進む。**

## 1. 着手条件（追加なし・再掲）
1. **正典は `EXEC_ARCH_WORK_ORDER_v0_1.md` の全文。** **§5 の構成、§9 の禁止、§10 の完了条件をそのまま使う。**
2. **段0・段1 の答えを再調査しない。** **Executive Summary と Gap Register に載せる**（出所は既存の FINDING）。
3. **★調査中に接続修正を始めない。** **見つけた欠陥は登録するだけ。**
4. **新しい正本・台帳を作らない**（§2.4 / v1.9）。**配置先は既存文書体系の中で決める。**
5. **commit 前に Taka へ提示。** **MGR が仲介する。** **提示できる形まで作って止まる。**
6. **限界申告を資料に残す**（作業指示書は冒頭14行のみ既読／`TASK_CONTRACTS.jsonl` の中身は UNKNOWN／実行していない 等）。

## 2. ★段0・段1 で既に確定していること（資料に転記する。再調査しない）
| 項目 | 状態 | 出所 |
|---|---|---|
| **勘定科目の自動設定** | **`IMPLEMENTED_UNWIRED`**（登録経路から参照 0件・後追いバッチ） | `..._D18_ANSWER_TWO_MECHANISMS.md` |
| **4軸→7戦略の決定論セレクタ** | **`WIRED_UNENTERED`**（`if formal_candidates:` の既定 `None`・投入口2つとも渡さない） | 同上 |
| **4軸のうち3軸** | **本番に無い**（`context_anchoring` のみ在る） | 同上 |
| **LLM 直接選択（段3e）** | **`LIVE`** | 同上 / Build 6,7,10R |
| **`EXEC_ARCH` / `Task Contract`** | **`IMPLEMENTED_UNWIRED`**（`egl/structure/` 内のみ） | `..._D23_ANSWER_TWO_CONTRACTS.md` |
| **worker の contract** | **`LIVE`**（`contract_seal` / `submit.py:430`）。**依頼者が渡す** | 同上 |
| **同型の規律が2箇所** | **Gap Register に「同型・別物」で1件** | 同上 |
| **横から見る経路** | 台帳直読・TRACE 横読み＝**フックで拒否済**／`CC_*.md` 直読＝**未閉塞** | `..._CRUSH_THE_SIDE_CHANNELS.md` |

## 3. 分割の許可（大きいため）
**§5 の章ごとに分けて出してよい。** **分けたら「分けた」と書く。**
**★最初に出すのは §5.1 Executive Summary と §5.11 Gap and Contradiction Register。** **理由: Taka が最短で全体像と欠陥を掴める。**

---
*MGR。Taka「続けて」により段2 へ GO。正典は作業指示書の全文。着手条件=段0・段1 の答えを再調査せず転記／調査中に接続修正を始めない／新しい正本を作らない／commit 前に Taka へ提示（MGR が仲介）／限界申告を残す。既に確定している8項目を表で渡した（再調査不要）。章ごとの分割を許可し、最初に §5.1 Executive Summary と §5.11 Gap Register を出させる。*
