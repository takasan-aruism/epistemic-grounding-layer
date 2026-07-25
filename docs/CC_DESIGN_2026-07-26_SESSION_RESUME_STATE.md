# セッション resume 状態（2026-07-26 時点）— 新セッションはこれを読んで再開

- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=STATUS(resume)
- 目的: セッション中断→新セッションで同じ作業に戻るための state + 次アクション + 運用文脈。
- 今セッションで DE-0524〜0542（19 DE）を admit・commit・push 済み（全 remote 同期）。

## 0. 私の役割 / 通信 / 運用（新セッションが最初に把握）
- 私＝**DESIGN/AUDIT (CC-α)**。**IMPL は別 CC インスタンス**（egl/docs に handoff ファイルを保存すると自動起動）。**MGR** は管理インスタンス。
- 通信規約＝`instance_comms_protocol.md`（[[instance_comms_protocol]]）: `egl/docs` に `CC_<FROM>_<date>_<topic>_<TYPE>.md` を置く＝送信。TYPE∈{HANDOFF/FINDING/ADJREQ/ADJRESULT/STATUS}。裁定要求は `CC_DESIGN_*_ADJREQ.md`(宛MGR)。
- **監視を再武装せよ**（前セッションの monitor はセッション終了で死ぬ）: `egl/docs` の新規 `CC_MGR_*` / `CC_AUDIT_*` / `CC_IMPL_*`(BUILT+**FINDING**) + `structure/CONTRADICTIONS.jsonl` 増加 を persistent Monitor で拾う。
- **標準ループ**: DESIGN が handoff → IMPL build → 私が独立再監査（rubber-stamp せず・一次情報で検証）→ commit=Taka → DE。
- **commit 規律**: commit=Taka（各 commit で GO を取る）。2コミット型（artifacts→ledger DE）。cross-repo は egl/ds/twoder 各 commit+push（[[2der_repo_topology]]）。
- **DE 記録は front door 経由**: `structure/de_submit_route.py` の `record_de(candidate)`（既定=submit front door・実 ts）。**candidate に `generated_by_principal`/`claiming_principal`="CLAUDE_CODE"・`generation_mode`="DIRECT" を明示**（内部アクター開示。忘れると UNKNOWN_PRINCIPAL=DE-0541 の失敗）。rollback=`route="direct"`/`DE_ROUTE=direct`。
- **meta self-heal hook**: egl は `core.hooksPath=hooks` 設定済。structure/*.py を commit すると hook が LLM_INVOCATIONS/TASK_CONTRACTS を自動 regen+再ステージ（DE-0536）。
- **HF env**（e5/Qwen ローカル）: `HF_HOME=/home/takasan/.cc_tmp/hf_home HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`（root .locks 回避）。
- **:8005** = Qwen3.6-35B-A3B（健全）。

## 1. ★最優先の未決（新セッションが最初にやる）
### (A) arm-C2 の BUILT【到着済み・未監査】→再監査→commit（meta gap も解消）
- **`CC_IMPL_2026-07-26_INTENT_PROBE_ARMC2_DEFS_BUILT.md` が 2026-07-26 セッション終了直前に到着（未監査）。** 成果物 `structure/s_intent_probe_armc2.py` + データ。handoff=`CC_DESIGN_2026-07-26_INTENT_PROBE_ARMC2_DEFS_EXAMPLES_THINK_HANDOFF.md`。
  - 内容: 各二択に**定義+具体例**（弱2二択 `b_probe_type` INTENT↔PREMISE / `b_multi_type` CHOICE↔BMV に対比例）、**think on/off 比較**、私の案=**seed 多数決 + abstain(unsure)**。弁別は決定論集計のまま。
- **新セッションの最初のアクション**: この BUILT を独立再監査（決定論再判定・弱2二択の改善したか・think on/off delta・abstain 率・全 gate GREEN・DE は front door+CLAUDE_CODE）→ 結果を MGR/Taka へ → commit=Taka。
- **⚠️ meta gap（要解消）**: 現 HEAD の `LLM_INVOCATIONS`(28 CALL_SITE)/`TASK_CONTRACTS`(24) は**未 commit の `s_intent_probe_armc2.py` を参照**している（前 commit 時 hook が dir 全体 scan したため）。ローカルは GREEN だが **clean checkout では --check RED**。**arm-C2 を commit する時に `s_intent_probe_armc2.py` 込みで commit すれば自動 reconcile**。忘れず armc2.py を入れること。

### (B) record_de の CLAUDE_CODE 自動開示（DE-0541 flag の item 2・保留）
- 現状 `record_de`/submit は principal を自動注入しない→candidate に明示要。**構造化（record_de が CLAUDE_CODE を自動 inject）するか**は Taka 保留中（1+2 のうち 2）。当面は candidate に明示で回避。

## 2. 進行中の2大ライン
### ライン① front-door 移行(A)（MGR 主導・[[project_2der_offramp]] / [[ai-must-be-internal-actor-not-intruder]]）
- Claude 肩代わり機能を機能ごと正面玄関へ。**slice1 完了**（DE 記録を submit front door 経由に・DE-0538 同値/0539 submit ts/0540 switch）。DE-0540/0542 は CLAUDE_CODE 開示で front door 記録済み。
- **次スライス② = 開発作業を DW workcell 経由へ（MGR 優先・最重要）**。その後: 直叩き de_admission パスの閉塞（さらに後）。**直叩きは現状 未閉塞・並行運用（rollback 余地）**。

### ライン② 意図調べ(GAP-RRI-5) Qwen 研究（MGR/Taka 主導）
- DS-RRI 初手「意図を調べる」を構造で強制。§7 4軸→§9 7戦略メニューを決定論固定・判断のみ Qwen。正本=`docs/EGL_REQUEST_RESOLUTION_RESEARCH_INTENT_SPEC_v0_2.md §7/§9`。
- **測定済(DE-0541/0542)**: A 単発thinkOFF(戦略一致0.54) / B 単発thinkON(軸妥当0.74→0.85 だが戦略不変・probe悪化) / **C 二択並列+決定論集計(0.58・単発の失った細分 F3/F7 を回復・probe6/6・最速最安)**。
- **知見**: thinking は原子判断を上げるが複雑戦略は直さない。**「LLM に二択のみ・弁別は決定論集計」(Taka 核心=2DERの良いメニュー思想)が方向として実証**。残弱点は2二択(probe_type/multi_type)に局在。
- **次(arm-C2 の後)**: 弱2二択の鋭利化・seed 多数決・論争 fixture(F4/F5)ラベル再検討。

## 3. ★3 本線（RTHREAD/帳簿）の状態
- **「見つける層」完成（DE-0537）**: 構造マイニング(NO_STABLE)→意味埋め込み軸→2b-r2凍結→2b-r3再凍結規律+Taka承認→命名。
- v2 に1軸凍結（AX2-48354b9a="JSONLファイル解析CLI"）+ v1軸(AX-72ead44e="Pythonモジュール実装")。2b-r3 機構は propose→Taka承認で稼働。
- 恒久機構: 通信protocol v0.1 / 監視 v2 / meta self-heal hook / prompt衛生 standing rule / DE-corpus除外(front-door DE が 2b軸を汚さない)。
- P2 継続候補: 契約(required_inputs)/CANONICAL_STATES の authoring 継続（[[exec_arch_task_contract_pivot]]）。

## 4. 健全性（中断時点）
- 全 gate ローカル GREEN。3 repo（egl/ds/twoder）同期。rri 無改変。**唯一の既知 transient = §1(A) の meta gap（armc2 commit で解消）**。

---
*新セッションへ: MEMORY.md → 本 doc の順で読み、監視を再武装し、arm-C2 BUILT（または MGR/Taka の新指示）から再開せよ。measure-first・独立再監査・commit=Taka・front door 記録は不変。*
