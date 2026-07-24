# CC 管理 → 設計担当(CC-α): Execution Architecture v0.2 開発依頼

- 発: CC 管理インスタンス(Read-only オブザーバー) / 2026-07-24
- 対象: `2DER Execution Architecture 修正版作業指示 v0.2`(CLAUDE_WEB 発)
- 前提: Taka 裁定 2026-07-24「開発は設計担当へ／管理インスタンスは監視統合」
- read-only / repo 無改変 / commit=Taka / :8005 不使用(管理側)

## 0. 管理側で実測済みの仕分け(再発明防止のため既存を明示)

v0.2 の要求の**大半は既存**。実測で確認済み:
- 決定論パイプライン `egl/structure/s1..s11`(16本)＋ derived jsonl 一式が実在
- human-readable 成果物 9本が既存(`2DER_LIVE_STATUS` / `_END_TO_END_WIRING_MAP` /
  `_LEDGER_FLOW` / `_LEDGER_REGISTRY` / `_MISSING_EDGES` / `_SYSTEM_RECONSTRUCTION` /
  `_MAINLINE_AND_BRANCHES` / `_CURRENT_FUNCTIONALITY_INVENTORY` / `_CAPABILITY_AND_ROADMAP`)
- **ただし大半が 2026-07-22 生成で、07-23/24 の進捗(RRI RTHREAD・★3 token gate・pkg_mirror・
  approval_registry 等 119 ファイル増)を未反映＝古い**

→ したがって本依頼は「ゼロから調査」ではなく **(a) 既存の現状更新 ＋ (b) 真に無い4軸の新規開発**。

## 1. 三者分担

| 担当 | 範囲 |
|---|---|
| **管理(私)** | 決定論ステージの再実行で現状更新／健全性監視／Executive Summary 維持／本依頼の追跡・照合・Taka 提示調整。**新コードは書かない** |
| **設計(CC-α)** | 下記 §2 の新4軸＋常設ゲート＋MD導出器の**仕様を書く**(骨格＋不変テスト同梱) |
| **実装** | CC-α の spec を実装／:8005 を要する抽出系(s2)の再実行 |

## 2. 開発してほしいもの(設計担当が仕様化する対象)

### B. LLM Invocation Map 【最優先】
- 目的: 全 LLM 呼出点の決定論台帳。RRI 条件スタンプ(T31)の前提資産
- 出力(案): `egl/structure/LLM_INVOCATIONS.jsonl`
- 各呼出点に: 呼出元 file:func / model / endpoint(:8005 等) / system_prompt source /
  context を**誰が組むか**(Python 構築 vs LLM 自己探索) / schema 強制の有無 /
  output validator / 失敗時処理 / 結果保存先 / 状態
- 走査手段: AST ＋ 文字列(`chat/completions` `/v1/` `8005/8006` `model=`)。LLM 不使用・決定論

### A. Runtime Entry 拡張
- 目的: Python 外の起動経路(現パイプラインの盲点)
- 出力(案): `ENTRYPOINTS_EXT.jsonl` — shell script / systemd unit / tmux / cron /
  runner 設定 / vLLM endpoint 設定

### C. Mandatory Read Paths
- 目的: 段ごと `required_by_design` vs `actually_loaded` の突合＝CONTEXT_GAP 検出
- 既提案の「ゲート被覆検査(どの入口がどのゲートに到達するか)」と同ステージに同居
- 出力(案): `READ_PATHS.jsonl`

### D. State Machine Map
- 目的: RRI / task / DW / worker / validation の状態機械の突合
- 同一概念の別名保持は矛盾種として既存 `CONTRADICTIONS.jsonl` に追加
- 出力(案): `STATE_MACHINES.jsonl`

### 常設ゲート化(v0.2 §5・完了条件)
- s10/s11 に既存の `--check` を全ステージへ拡張し CI に載せる
- 5 検査: (1)再生成バイト一致 (2)記録 symbol の実在 (3)未登録 LLM 呼出点の検出
  (4)未登録 entrypoint の検出 (5)PLANNED→CURRENT 誤昇格の検出
- **完了 = ゲートが1回以上「本物の乖離」を検出 or 陰性対照で赤を確認**(文書完成を成功としない)

### MD 導出器(乖離防止)
- 既存 `2DER_*.md` を JSON(derived jsonl)から**生成する導出器**に統一。MD を手書きしない
  (v0.2 §1「単一ソースからの導出」への回答)

## 3. 規律(v0.2 準拠・設計時に守る点)

- **状態語彙を新設しない**。既存2系(辺: LIVE/WIRED_UNENTERED/TEST_ONLY_ISLAND/... ,
  ラダー: documented/implemented/wired/executed/proven)に写像。PLANNED/UNKNOWN のみ新設可
- **PLANNED 出典は RRI 正式仕様のみ**。GPT 系列(Development Context Builder →
  Knowledge Dispatcher → ...)は `PROPOSAL_UNRECONCILED` で別記
  - ⚠ 実測所見: v0.2 §4 が出典正本とする **`RRI_SPEC_MACHINE_v1_1.json` は本体不在**。
    実在は `RRI_SPEC_MACHINE_PATCH_2026-07-24.json` ＋ `RRI_IMPL_SPEC_v0.1.md` ＋
    `SPEC_RTHREAD_STAGE1_v0.1.md`。**PLANNED 出典の正本を先に確定要**(Taka 裁定候補)
- README とコードの矛盾1件(管理側検出): `structure/README.md` は「LLM 不使用」と書くが
  `s1_symbols.py` / `s2_extract.py` は :8005 を参照。CONTRADICTED として記録推奨

## 4. 置き場・状態

- 成果物: `egl/structure/`(既存作法。新 Registry/Ledger を作らない)
- 本依頼の DE 化(着手/完了)は設計側で。管理側は照合・監視で並走
- ★3 と完全並行可。★3 を止めない
