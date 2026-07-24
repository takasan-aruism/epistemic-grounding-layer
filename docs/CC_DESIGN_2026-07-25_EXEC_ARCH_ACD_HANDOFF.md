# 設計/監査 → 実装: EXEC_ARCH A/C/D 統合発注（1 本の s-stage + 5 ゲート）

- 発: 設計/監査(CC-α) / 2026-07-25 / repo=egl / **決定論・LLM 不使用・:8005/GPU 不使用**
- 正本: `docs/CC_MGR_2026-07-25_EXEC_ARCH_ACD_DEV_HANDOFF.md`(発注) + `docs/CC_MGR_2026-07-24_EXEC_ARCH_v0.2_DEV_HANDOFF.md`(v0.2 §3-A/C/D・§7-3) + 本 handoff
- テンプレ: Stage B `structure/s_llm_invocations.py` + `LLM_INVOCATIONS.jsonl` + `--check`(同 s-stage 型・同ゲート型に統一)
- 位置づけ: P2(地図側・補助)。**★3=2b-r2 は DE-0524 で決着済み**につき、帯域競合なく着手可。
- **1 本にまとめる**: 3 軸を別体系にせず、単一モジュール `structure/s_exec_arch_acd.py` が 3 jsonl を生成し統一 `--check` を持つ。

## 0. 規律（v0.2 準拠・spec に内蔵。違反=RED / REJECT）
- **状態語彙を新設しない。** 既存 2 系へ写像のみ:
  - 辺: `structure/EDGE_INVENTORY.jsonl` / `s4_edges.py`（`LIVE` / `WIRED_UNENTERED` / …）
  - ラダー: `s7_traceability.py`（`documented` / `implemented` / `wired` / `executed` / `proven`）
  - 第3の語彙体系は v0.2 が最も禁じた事故。新種を作ったら RED。
- **C2 規則**: `NO` は被覆下でのみ主張。静的未解決は `UNRESOLVED_<理由>`（例 `UNRESOLVED_DYNAMIC_DISPATCH`）で正直に停止。`UNKNOWN` と曖昧化しない。
- **調査中の修正禁止**: 切断・矛盾を見つけても直さず `structure/CONTRADICTIONS.jsonl`（既存・新種を作らない）に積む。
- 決定論（ファイル種別＋文字列。LLM 判定なし）。出力は `egl/structure/`。**新 Registry/Ledger を作らない。** MD は jsonl から導出（手書きしない）。
- **§4 PLANNED レーンは範囲外**（出典正本の裁定が Taka 保留中のため触れない）。

## 1. A. Runtime Entry 拡張 → `structure/ENTRYPOINTS_EXT.jsonl`
Python 外の起動経路（現パイプラインの盲点）を決定論走査:
- 対象: shell script(`*.sh`) / systemd unit(`*.service`,`*.timer`) / tmux 起動 / cron(`crontab`,`*.cron`) / runner 設定 / vLLM endpoint 設定（`:8005`/`:8006` 等の serve 定義）。
- 各行フィールド: `{source_file, kind(SHELL|SYSTEMD|TMUX|CRON|RUNNER|VLLM_ENDPOINT), launch_target, args, status}`。
- `status` は**辺語彙へ写像**（`LIVE` / `WIRED_UNENTERED` / …）。新語彙禁止。判別不能は `UNRESOLVED_<理由>`。

## 2. C. Mandatory Read Paths → `structure/READ_PATHS.jsonl`
- 段ごと `required_by_design` vs `actually_loaded` を突合 → 差分= **`CONTEXT_GAP`**（資料は在るが実行時に読まれていない）。
- フィールド: `{stage, path, required_by_design(bool), actually_loaded(bool), verdict(OK|CONTEXT_GAP|UNRESOLVED_<理由>)}`。
- **ゲート被覆検査を同居**: どの entrypoint(A) がどの `--check` ゲートに到達するかを対応付け、**到達しない入口=未被覆**を別掲。

## 3. D. State Machine Map → `structure/STATE_MACHINES.jsonl`
- RRI / task / DW / worker / validation の状態機械を突合。
- フィールド: `{machine, state_symbol, mapped_to(edge|ladder 語彙), source_file}`。
- **同一概念の別名保持（alias 矛盾）は新種を作らず `structure/CONTRADICTIONS.jsonl` に追加。**

## 4. 常設ゲート（必須）= `structure/s_exec_arch_acd.py --check`（5 検査・全 GREEN で PASS）
1. **再生成バイト一致**: 3 jsonl を pin 入力から再生成して byte 完全一致。
2. **記録 symbol の実在**: 各 jsonl が指すファイル/シンボルが実在（消えた参照=RED）。
3. **未登録 entrypoint 検出**（A の陰性対照）: 既知の起動経路を1つ隠す→ゲートが未登録として RED を出す（＝検出力の実証）。
4. **未登録 read-path / 未到達ゲート検出**（C の陰性対照）。
5. **状態機械の別名矛盾検出**（D の陰性対照）: 既知の別名衝突を注入→ CONTRADICTIONS 経路で捕捉。

## 5. 完了条件（Stage B と同水準・文書完成を成功としない）
- **常設ゲートが 1 回以上「本物の乖離」を検出、または陰性対照で赤を確認**して初めて完了。Stage B は s_embed_axes 追加を実捕捉して実証済（DE-0523）＝同水準を A/C/D にも要求。

## 6. 受入（設計/監査が独立再検証）
- 私が fresh 再実行して 3 jsonl が **byte 一致**・`--check` GREEN robust。
- 陰性対照（§4-3/4/5）で**実際に RED が出る**ことを実測（検出力 load-bearing）。
- **新状態語彙ゼロ**（辺/ラダーへの写像のみ）。矛盾は CONTRADICTIONS.jsonl に積まれ、コード上で修正していないこと。
- `NO` 主張がすべて被覆下（未被覆は `UNRESOLVED_<理由>` で正直停止）。

## 7. 完了後（ハンドオフ）
- `CC_IMPL_2026-07-25_EXEC_ARCH_ACD_BUILT.md` → 設計/監査が独立再監査 → CONSISTENT → **commit=Taka** → DE 起票（「A/C/D 3 軸を Stage B 型ゲートで統一・実乖離 or 陰性対照で検出実証」）。
- 想定と実測がズレたら silently 合わせず BUILT に正直記録し裁定を仰ぐ（2b-r1/2b-r2 と同規律）。過剰主張より正直な NO を優先。

---
*設計/監査 CC-α。実装は本ファイル保存でトリガ。P2 だが ★3 は決着済につき本線帯域あり。疑義は途中でも CONTRADICTIONS or 報告で上げてよい。*
