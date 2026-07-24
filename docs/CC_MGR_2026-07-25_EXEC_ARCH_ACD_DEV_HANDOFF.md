# CC 管理 → 設計担当(CC-α): EXEC_ARCH Stage A/C/D 発注書

- 発: CC 管理インスタンス(Read-only オブザーバー) / 2026-07-25
- 対象: `2DER Execution Architecture 修正版作業指示 v0.2`(CLAUDE_WEB 発) §3-A/C/D・§7-3
- 前提: Taka 裁定 2026-07-25「A/C/D は並走で着手・★3(2b-r2)を止めない」
- read-only / repo 無改変 / commit=Taka / :8005 不使用(全ステージ決定論・LLM 不使用)

## 0. 優先度(最重要・遵守事項)

| 順 | タスク | ストリーム | 位置づけ |
|---|---|---|---|
| **P1** | RTHREAD **2b-r2**(軸凍結+多重所属+濃淡) | ★3 = RRI 本線 | **クリティカルパス。これを止めない** |
| **P2** | 本発注 **EXEC_ARCH A/C/D** | 地図側・補助 | 2b-r2 の裏・空き帯域で流す並走タスク |

A/C/D は RRI を加速しない。**2b-r2 の設計/実装/監査に一切割り込まないこと。** P1 の帯域が空いた時に P2 を進める。

## 1. 依頼 = A/C/D 統合 spec 1 本(骨格＋不変テスト＋各 --check ゲート)

Stage B(`s_llm_invocations.py` + `LLM_INVOCATIONS.jsonl` + `--check`)を**テンプレとして流用**する。
3 軸を別体系にせず、同じ s-stage 型・同じゲート型で統一。

### A. Runtime Entry 拡張 → `ENTRYPOINTS_EXT.jsonl`
- Python 外の起動経路(現パイプラインの盲点): shell script / systemd unit / tmux / cron / runner 設定 / vLLM endpoint 設定
- 各点に: 起動元ファイル / 種別 / 起動対象 / 引数 / 状態
- 走査: 決定論(ファイル種別＋文字列)。LLM 不使用

### C. Mandatory Read Paths → `READ_PATHS.jsonl`
- 段ごと `required_by_design` vs `actually_loaded` の突合 = CONTEXT_GAP 検出
- 「ゲート被覆検査(どの入口がどのゲートに到達するか)」を同ステージに同居
- 「資料は在るが実行時に読まれていない」を検出

### D. State Machine Map → `STATE_MACHINES.jsonl`
- RRI / task / DW / worker / validation の状態機械を突合
- 同一概念の別名保持は**新種を作らず既存 `CONTRADICTIONS.jsonl` に追加**

## 2. 規律(v0.2 準拠・spec に内蔵)

- **状態語彙を新設しない**。既存 2 系(辺: LIVE/WIRED_UNENTERED/... , ラダー: documented/implemented/wired/executed/proven)へ写像。第 3 の語彙体系は v0.2 が最も禁じた事故
- **C2 規則を輸入**: `NO` は被覆下でのみ主張。静的未解決は `UNRESOLVED_<理由>` として正直に停止(UNKNOWN と曖昧化しない)
- **常設ゲート必須**(各段 `--check`): (1)再生成バイト一致 (2)記録 symbol の実在 (3)未登録 entrypoint 検出 (4)未登録 read-path/未到達ゲート検出 (5)状態機械の別名矛盾検出
- **完了条件**: 文書完成を成功としない。**ゲートが 1 回以上「本物の乖離」を検出 or 陰性対照で赤を確認**して初めて完了(Stage B は s_embed_axes 追加を捕捉して既に実証済＝同じ水準を A/C/D にも要求)
- **§4 PLANNED レーンは本発注の範囲外**。PLANNED 出典正本の裁定(Taka 保留中)に依存するため、A/C/D では触れない

## 3. 成果物・置き場・報告

- 出力: `egl/structure/`(既存作法。新 Registry/Ledger を作らない)
- MD は JSON(derived jsonl)から**導出**。手書きしない
- DE 化(着手/完了)は設計側で。evidence 欄は DE 番号と commit hash で引く
- **調査中の修正禁止**: 切断を見つけても直さず Gap Register(`CONTRADICTIONS.jsonl`)に積む
- 管理側(私)は照合・ゲート監視・Taka 提示で並走。新コードは書かない

## 4. 管理側からの申し送り(実測所見)

- README 矛盾 1 件: `structure/README.md`「LLM 不使用」 vs `s1_symbols.py`/`s2_extract.py` の :8005 参照。D の別名矛盾検出とは別枠だが CONTRADICTED 登記推奨
- Stage B ゲートは現在 **RED**(s_embed_axes.py の新規呼出点 1 点が未登録)。台帳再生成+DE 化で解消するが commit=Taka のため保留中。A/C/D 着手前に B の RED を畳むか、A/C/D と同 DE で畳むかは設計側判断
