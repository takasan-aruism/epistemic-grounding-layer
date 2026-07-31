# 【調査】DW には**★多段も、監査と実務の分離も、既に在る** — ★Taka の記憶は正しい

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-31 14:3x / TYPE=FINDING
- **運用方針 確認済（版: v2.9）** ／ **正典**: `TAKA_2026-07-31_LLM_DESIGN_MULTISTEP_AND_SEPARATE_AUDIT.md` ／ **受領**: `D-170`
- **★新しい名前で置いた** ／ **★実装していない・提案していない。★確認だけ**

---

# 1. ★確認の表（★`D-170` §2 の形式）

| # | 項目 | ★現状 | ★根拠（ファイル:行） | ★在るのに使っていないか |
|---|---|---|---|---|
| **a-1** | **多段の状態機械** | **★在る。6段**: `CREATED→PLAN` → `READY_FOR_IMPLEMENTATION→GENERATE` → `READY_FOR_AUDIT→AUDIT` → `DISPOSITION_REQUIRED→DISPOSE` / `READY_FOR_REGENERATE→REGENERATE` → `READY_FOR_UPPER_REVIEW→UPPER_REVIEW` → `COMPLETE` | `dev-workcell/dw/dispatch.py:31-38` | **★使っていない**（★本日 `PLAN` より先へ1度も進んでいない） |
| **a-2** | **段ごとに LLM を別に呼ぶか** | **★別に呼ぶ。**`PLAN` は `BUILD_PLANNER`、`GENERATE` は `CODING_WORKER`、`AUDIT` は `INDEPENDENT_AUDITOR` ＝ **★1回で全部を作らせていない** | `dispatch.py:97-118`（PLAN）／`webui.py:289-330`（`cw`）／`webui.py:287`（auditor） | **★`GENERATE` 以降 未使用** |
| **b-1** | **作る側と確かめる側が別アクターか** | **★別である。**`CODING_WORKER`→`QWEN_LIVECODER` ／ **`INDEPENDENT_AUDITOR`→`QWEN_AUDITOR`** | `dispatch.py:41-46`（`DEFAULT_ACTORS`） | — |
| **b-2** | **★監査は宣言だけか、担当者が居るか** | **★★居る。★実体がインスタンス化されて登録されている**: `auditor = AD.QwenAuditor(seed=101, supervised=True)` | **`twoder/webui.py:287`** | **★使っていない**（★`AUDIT` に到達していない） |
| **b-3** | **★どう「分離」しているか** | **★別 session / ★別 seed / ★別 system-prompt**（逐語: 「別 session/seed/system-prompt で分離した auditor（★単一 weight 上の separate run）」）。★seed=101（★planner/worker とは別） | **`dev-workcell/dw/adapters.py:123-135`** | — |
| **b-4** | 監査が何を見るか | **★実装ずみ**: `IMPLEMENTATION_PACKET` ＋ `DIFF` ＋ `TEST_RESULT` ＋ **`RELEVANT_FAILURE_PATTERNS`**（★過去の失敗パターンも渡している） | `adapters.py:131-135` | **★使っていない** |
| **c** | **★今回の実行で呼ばれたか** | **★呼ばれていない。**★本日の4回の投入はすべて `PLAN` で停止（★`GENERATE` を押さない裁定のため） | 本日の実測（`TASK-2DER-…` 4件とも `READY_FOR_IMPLEMENTATION` で停止） | — |
| **d** | **★在るのに使っていないもの** | **★`GENERATE` / `AUDIT` / `REGENERATE` / `DISPOSE` / `UPPER_REVIEW` の5段。★および `QwenAuditor` 一式** | 上記 | **★これが「作らなくてよいもの」である** |

---

# 2. ★結論（★短く）

> ### **★Taka の記憶は正しい。★「ある程度」ではなく、★作る側と確かめる側は★別 seed・別 system-prompt で★既に分かれており、★実体も登録されている。**
> ### **★我々は それを ★一度も動かしていない。**

```
★★∴ 「多段にする」「監査と実務を分ける」を★新しく作る必要は★無い。
★★∴ 今回 作るべきものは ★0件である。
★★∴ 残っているのは「★動かしていない5段を、★動かすかどうか」の判断だけである。
```

---

# 3. ★正直に書く（★線を越えない）

```
★★「在る」は「動く」ではない（★我々が本日 何度も言ってきた線）。
   ★`GENERATE` 以降は ★本日1度も呼ばれていない ∴ ★動作は★未確認である。
★★`QwenAuditor` が★実際に有効かは★測っていない。★「監査が在るから③が直る」とは★書かない。
★★③（既に取れているものを作り直さない）は ★PLAN の段の問題である。
   ★AUDIT は ★GENERATE の後に来る ∴ ★③をそのまま直すものではない。
   ★★ただし「★作る側と確かめる側を分ける」という★形は、★PLAN の段にも当てられる（★これは設計案であり、★私は今 出さない）。
```

---

# 4. ★MGR §3 への同意（★我々自身の実例）
```
★本日 私の計器は6回 誤り、★6回とも「★機械 → 目視」の2段で救われた。
★★特に Ap01 は、★機械が大文字小文字で見落とし、★目視で拾った。
★★∴ 「作る側と確かめる側を分けると効く」は、★我々の中では★実測で支持されている。
★★2DER の中では ★配線は在るが ★実測が無い。★これが今の差である。
```

---

# 5. ★私は次の一手を出さない（★確認だけという指示のまま）
```
★★`D-170` §2 は「★実装しない。★提案しない。★確認だけ」である ∴ ★守る。
★★材料だけ置く: ★動かしていない5段のうち、★`GENERATE` を押すかどうかは
   ★★Taka の案件である（★2DER が書いたコードを production に入れるかは彼の判断・`D-129` §3-3 で据え置き）。
★★∴ ★次に進むには ★Taka の判断が要る所に当たっている。
```

---
**決めたこと**: **①DW には多段（6段の状態機械・段ごとに別の LLM）も、監査と実務の分離（`CODING_WORKER`→`QWEN_LIVECODER` と `INDEPENDENT_AUDITOR`→`QWEN_AUDITOR`）も既に在り、監査は宣言だけでなく `QwenAuditor(seed=101, supervised=True)` として実体が登録されている（別 session・別 seed・別 system-prompt で分離） ②∴ 今回 作るべきものは0件で、残るのは「動かしていない5段（`GENERATE`/`AUDIT`/`REGENERATE`/`DISPOSE`/`UPPER_REVIEW`）を動かすかどうか」の判断だけ ③ただし「在る」は「動く」ではない——本日 `PLAN` より先へ1度も進んでおらず動作は未確認であり、「監査が在るから③が直る」とは書かない（③は PLAN の段の問題で、AUDIT は GENERATE の後に来る） ④確認だけという指示を守り、次の一手は出さない——`GENERATE` を押すかは Taka の案件である。**
