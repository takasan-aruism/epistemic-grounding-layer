# Inference Control Domain — GDW 準拠 設計 v0.1

2026-08-26 ／ instance=Inference Control
**正本 = `TAKA_2026-08-24_GDW_OPERATION_DESIGN_v0.1.md`（ART-da5a15e434）**
**★これは機能追加ではない = `domain_esde` / `domain_ledger` / `domain_sysops` / `domain_route_table` と同じ形を写すだけ。**

---

## 0. 前提の訂正（★私の設計が間違っていた点）

2026-08-25〜26 に私は **LLM 実験を 18経路（S01〜S18）へ載せる**設計を書いた。誤り。

2DER は **2つの構造**を持つ:

| 構造 | 役割 |
|---|---|
| **18経路（S01 SUBMIT 〜 S18 COMPLETE）** | **正常系**。1件の依頼が入って完了するまで |
| **GDW（General / Domain / Worker）** | **異常系・状態管理・知識の溜め込み**。Domain 単位で分ける |

知識の蓄積は **Domain の仕事**であり、正常系へ押し込むものではない。
`CC_INFCTL_2026-08-26_LLM_TASK_RUN_SPEC_v0.1.md` はこの点で誤っている ―― **本書が上位**とする。

---

## 1. すでに在るもの / 無いもの（実測）

| GDW の区分 | 正本の逐語 | Inference Control の現物 |
|---|---|---|
| **Worker**（事実を作る） | 「対象取得 → 構造化 → 指標計測 → finding 抽出 → 証拠付き結果を返す」 | **在る** ―― `egl/structure/s_llm_invocations.py`（呼出点38 / 呼び手77）<br>`egl/structure/s_llm_false_stop.py`（停止率 / p / flaky / 対照10本） |
| **台帳明細**（TASK 固有情報） | 「TASK固有情報 → TASK台帳明細」 | **在る** ―― `RTHREAD-b651db0a` に明細 78件 |
| **Domain Manager**（意味と次の行動） | 「①何を測るか ②結果をどう扱うか ③Domain の状態」 | **★無い** ―― 私の頭の中にある |
| **Domain の状態**（Domain 全体情報） | 「Domain全体情報 → Domain Manager」 | **★無い** ―― 機械が引けない |
| General への summary | §8 の形 | **★無い** ―― `/api/domain_*` に対応物が無い |

∴ **足りないのは計器でも経路でもなく、`domain_*.py` と同じ位置の Domain Manager だけ。**

---

## 2. ★境界違反の是正（正本 §6）

> **Worker は事実を作る。Manager は意味と次の行動を決める。**
> **Worker が自分の測定結果を根拠に、自分で規則を変更してはいけない。**

**私はこれを破った。** `s_llm_false_stop.py` に `--record` を付けて **Worker に解釈文を書かせた**。
結果、門を差し替えた瞬間に台帳へ **偽の意味づけ**が入った（2026-08-26・訂正の明細を投函済み）:

- 台帳に入った文: 「停止が一件も再現しない＝止める判断が規則でなく抽選」「p が 0 でも 1 でもない ∴ 抽選器」
- 実際: route 門は **構造上 止まらない** ∴ 停止 0 は発見ではない
- **数値は正しく、解釈だけが偽** ∴ 読み手は気づかない

**是正:**

| | 今 | 是正後 |
|---|---|---|
| Worker の返り | 事実 + **解釈文** | **事実だけ**（`stopped_per_run` / `p` / `flaky` / `label_stability`） |
| 明細の文を組む | Worker（`detail_lines`） | **Domain Manager** |
| 台帳へ投函する | Worker（`--record`） | **Domain Manager** |

★`--record` は Worker から外す。**門の種類で文型を分ける判断は Manager の仕事**であり、
Worker 側に対照（陰性⑥）を置いて防ぐのは **対症療法だった**。

---

## 3. Domain Manager が持つ状態（正本 §2 に対応）

ESDE の「未評価TASK / 再評価対象 / 計器の version / UNVERIFIED」に対応する物:

| 状態 | 出所（既存） | 現在値 |
|---|---|---|
| 対象の分母 | `LLM_INVOCATIONS` | 呼出点 **38**（VLLM 34 / CLAUDE_P 4）・呼び手 **77** |
| 測定済み / 未測定 / **測れない** | 同上 + 標本の口の有無 | 測定済み **2門**（`intent_strategy` / `request_type`）・残りは未測定 |
| 決定論 / 抽選（p） | `s_llm_false_stop --prob` | `intent_strategy` p=0.80〜0.00（**0 にも 1 にも張り付かない**）／ `request_type` 枝が **20%** 変わる |
| Knowledge と成熟度 | `LLMK-0001..0006`（doc が名乗る） | **全件 MEASURED 止まり**・REPRODUCED 候補 1件（門は確率を返す＝2門で再現） |
| 移管の判定 | LLMK-0003 / 0005 | Qwen へ **移管しない ×2**・**決定論化 1**（誤停止の測り方） |
| known failure | LLMK 各本 | 語彙の重なり／切片で測ると6倍/ 門の flaky／計器の文が対象を変えると嘘になる |

**★これらは今 doc と私の頭にあり、機械が引けない。** Domain Manager の第一の仕事はここを引ける形にすること。

---

## 4. Domain Manager が判断すること（正本 §3）

### 4.1 何を測るか
- `LLM_INVOCATIONS` に**新しい CALL_SITE / CALLER が増えた**
- 既存呼出点の **prompt / runtime 欄が変わった**（台帳は byte 一致再生成なので差分で分かる）
- **他 Domain から handoff が来た**（§6）
- 既知の flaky が **直ったと申告された**（再測定）

### 4.2 どの Worker へ渡すか
初期は2つで足りる（正本 §3.2「細分化しすぎない」）:
`s_llm_invocations`（棚卸し）／ `s_llm_false_stop`（門の安定性）

### 4.3 結果をどう扱うか
正常な測定として登録 / **UNVERIFIED として保持** / finding 化 / 再測定 /
**他 Domain へ handoff** / General へ通知 / **人間裁定へ上申**（Inference Control 仕様 §12 の7条件）

---

## 5. Worker が守ること（正本 §4）

- 与えられた対象と既存規則に従う。**自由に設計を変更しない**
- **結果は必ず台帳へ残す** ―― ただし §2 の是正により **投函は Manager 経由**
- **自分の測定結果を根拠に規則を変えない**（`--record` の解釈文はこれに当たった）

---

## 6. ★他 Domain からの handoff（今 実在している未処理）

**Ledger Domain 担当から「LLM の件で仕事を投げてよいか」と口頭で来ている（2026-08-26）。**
これは **本来 2DER に入るべき作業**であり、Claude 間のバケツリレーになっている。

**受け口（新機構 0）:**

```
<<<2DER:DETAIL>>>
item: <Inference Control の ITEM>
actor: Claude
via: front_door
provenance: DECLARED
- HANDOFF_IN: from=ledger_domain / 依頼= … / 対象= <LLM_INVOCATIONS の caller もしくは PLANNED:…>
<<<2DER:END>>>
```

Domain Manager は `HANDOFF_IN` の明細を **成立性判定**にかける（欄が在るか・対象が台帳に在るか）。
不足なら **欠けた欄名をそのまま返す**（推測で埋めない）。

★これにより「Claude が Claude へ口頭で投げる」を **台帳の明細**へ移す。

---

## 7. General への summary（正本 §8 の形）

```
Inference Control Domain
対象 呼出点        38
対象 呼び手        77
測定済みの門        2
未測定の門         (要計上)
抽選と判明した門     2
Knowledge          6
  MEASURED         6
  REPRODUCED       0
移管しない判定      2
決定論化           1
handoff 未処理     1   ← ledger_domain
人間裁定           0
Worker 稼働        2
```

---

## 8. 作らないもの（既存 Domain と同じ宣言）

- **新台帳 0** ―― 書き先は既存の封印 DETAIL と `LLM_INVOCATIONS`（`s_llm_invocations` が sole writer）
- **新 state 0** ―― 既存の 14 状態・封印マーカーだけ
- **新 ID 族 0** ―― `LLMINV-…` は既存の決定論 id
- **新入口 0** ―― front door だけ

---

## 9. 次の1手（順序）

1. **本 Domain を台帳へ登記**（ITEM を Domain として位置づけ・活動を明細へ）
2. **`--record` を Worker から外す**（§2 の是正）
3. **Domain の状態を機械が引ける形にする**（`domain_*.py` と同じ位置に置く）
4. **ledger_domain の handoff を明細で受ける**（§6）
