# 提出束 MANIFEST — 2026-07-21

作成: Claude Code（CC-0 / INSPECTION_ONLY。本束は既存バイトの**収集**であり、新規執筆・改変は行っていない）
検証: `sha256sum -c SHA256SUMS.txt`（束内の全26ファイル）

## 収集時点の基準

| 対象 | 値 |
|---|---|
| repo HEAD | egl `e8b9046` / twoder `739c8ba` / rri `622e6ea` / ds `1b7fda6` / dev-workcell `fd87840` |
| emit_api.py | sha256 `6bf41034…` (4837 B) |
| registry workcell_events.json | sha256 `5c50e435…` (956 B) |
| runner.py (v0.2.3) | sha256 `074ef2c5…` (28746 B) |
| patch_bridge.py | `5ca50050…` / bridge_reconciler.py `41c404ca…` / bridge_minter.py `d77c5530…` |
| energization-minter-design-v0.1.md | `57126163…` (9016 B) |

---

## 提出できたもの（5/8）

### 02_ledger/ — REVIEW_LEDGER.jsonl および JREV-0009 の正式記録 ✅
- `REVIEW_LEDGER.jsonl` — JREV-0001..0010 全10件（egl 正本そのもの）
- `JREV-0009.ledger-record.json` — 同ファイルから JREV-0009 を pretty 抽出（内容は同一バイト由来）
- `REFERENCE_REVIEW_PACKET_JREV0008.md` — 参考。JREV-0009 は 0008 の re-battle であり、攻撃設定・スコープは 0008 パケットが原文

### 03_design/ — energization-minter-design-v0.1.md ✅
egl/docs 正本をそのまま。

### 04_code/ — bridge_reconciler.py / bridge_minter.py ✅
twoder 正本。文脈上必要なため `patch_bridge.py`（§2 wiring 側）を同梱。

### 05_de/ — DE-0474、DE-0475 の原記録 ✅
- `DE-0474_DE-0475.raw.jsonl` — DESIGN_EVIDENCE_LEDGER.jsonl からの**逐語抜粋**（改行・キー順そのまま）
- `DE-04xx.pretty.json` — 可読用の整形版（同一内容）

### 06_runtime/ — 現行 emit_api / vLLM 呼出実装 / 現存 systemd unit ✅
- `emit_api.py` + `emit_api.PROVENANCE.txt` — **Qwen3.6-35B-A3B が M1 packet で生成したバイトそのもの**（run 20260719T131242Z-028d21d9、model_reply_sha256 == on-disk sha256）。D-2 により Claude Code は編集不可
- `runner_v0.2.3.py` — workcell runner。vLLM 呼出の実装本体（`call_vllm`, L208–）
- `EXCERPT_call_vllm.py.txt` — 該当箇所の抜粋（レビュー導線用。正本は runner_v0.2.3.py）
- `run-with-proxy.sh` — trust-path glue。unit の `%i` 検証と stage-2 socat ブリッジ
- `workcell-runner@.service` / `vllm-socket-proxy.service` / `twoder-status.service` — 現存する systemd unit 3本（実バイト）
- `registry_workcell_events.json` — 現行 registry（後述の不在1件に該当）

### 01_jrev/ — JREV-0010 の実体（パケット本体は不在。下記参照） ⚠️
- `JREV-0010.ledger-record.json` — 正式記録（scope / 2 defects / post-fix 検証を含む最も完全な一次記録）
- `jrev0010_attacks.py` — A1..A6 の novel attack 実装
- `gate_s4_energization.py`（11 injections）/ `gate_reconciler_readonly.py`（AST read-only 証明）— 恒久機構
- `verify_reconciler_A.py` / `verify_minter_B.py` — §2 検証オラクル

---

## 提出できないもの（3/8）— 実在しないため

### ❌ 1. JREV-0010 パケット「本体」（REVIEW_PACKET_JREV0010.md）
**存在しない。** `egl/docs/` にあるパケット .md は JREV-0002..0008 のみ。JREV-0009 / JREV-0010 は
パケット .md を起こさず、REVIEW_LEDGER への記録＋攻撃スクリプト＋恒久 gate で運用した。
代替として 01_jrev/ に**実体**を収めた。整形されたパケット .md が必要なら、ledger 記録と
攻撃スクリプトから遡及生成できる（新規執筆になるため Taka 裁定が要る／未実施）。

### ❌ 2. writer registry
**存在しない。** 現行 `registry/workcell_events.json` は `{registry_version, owner, note, kinds}` の
**kinds 10種のみ**で、writer_id / 許可 kind / 許可 lane の登録簿は未実装。
これは DE-0475 の WA-2 指摘そのものであり、帰結として **DE-0474 束縛1（非 runner writer は外部登録、
無登録 writer = 構造欠陥）は現状 governance-only で機械強制されていない**（W1a 構築待ち）。
束には現行 registry の実バイトを収め、不足は上記のとおり明示する。

### ❌ 3. Watcher 用 systemd unit
**存在しない。** Watcher は未構築（設計は v0.2 DRAFT のみ、canonical 版なし = DE-0478）。
`systemctl` 実測で存在する 2DER 系 unit は `workcell-runner@.service` / `vllm-socket-proxy.service` /
`twoder-status.service` の3本のみで、いずれも Watcher 用ではない。
束には**現存3本の実バイト**を収めた（Watcher unit を書き起こす場合の既存の封じ込め水準
— NoNewPrivileges / ProtectSystem=strict / PrivateNetwork / SystemCallFilter — の参照として）。

---

## 注記

- 本束は SoR ではない。正本は A=egl core events.jsonl / B=DESIGN_EVIDENCE_LEDGER / C=emit_api EventStore（DE-0474 3-SoR 宣言）。
- 束内ファイルはすべて既存バイトのコピー。Claude Code による編集・要約・書き換えは 0 件（MANIFEST.md と EXCERPT のみが本セッション生成物で、EXCERPT は runner_v0.2.3.py の逐語部分抜粋）。
- JREV-0009 / JREV-0010 とも adjudicator=GPT は **PENDING（Taka 中継待ち）**。本束はその中継材料。
