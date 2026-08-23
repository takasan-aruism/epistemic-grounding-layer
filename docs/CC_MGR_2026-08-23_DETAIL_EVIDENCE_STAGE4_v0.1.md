# 段4 — 明細へ「何を根拠にしたか」を接続する v0.1

**作成: Claude Code（MGR）／ 2026-08-23**
**基準: `TAKA_2026-08-23_LEDGER_DETAIL_DESIGN_MEMO_v0.1.md`（`ART-948e04d27a`）§9 情報源・証拠を明細へ接続する**
**前段: 現状対応表（`ART-576edd4ee2`）§2「処理 → 明細（finding/test結果/artifact を明細へ追記）」＝存在しない辺**

## 0. 探した範囲（設計を書く前に）

- §9 の語彙が既に在るかを5repoの `*.py` 全体で逐語 grep（`evidence_refs` / `source_evidence_ids` / `claim_ids` / `basis_kind`）
- 証拠を持つ台帳を front door の登記簿（`/api/ledgers`, 41本）から列挙
- 明細を読む consumer を `request_thread` の import で全件（12箇所）＋ ファイル名指しで全件
- ★台帳の直読はしていない。明細は `rri.request_thread` の所有API、痕跡は `/api/etrace`、登記簿は `/api/ledgers`

**途中で自分の計器を2回疑って直した**:
1. `/api/etrace` の返りを `events` で読んで「痕跡0件」と出した → 実際は `task_trace.events`。**0件は私の読み違い**
2. `check_conservation(...)["ok"]` と書いた → この関数は**不成立を例外で止める**ので返り値は None。
   「返りを真偽と読み違えない」と試験に明記した

---

## 1. 新しい語彙を作っていない — §9 の語は AEC に全部あった

| §9 が求めるもの | 既存の正本 | 場所 |
|---|---|---|
| source type | `basis_kind`（**閉じた9語**、JP表示名つき） | `egl/answer_evidence.py` |
| verification state | `validation_mode`（**閉じた6語**） | 同上 |
| source identifier | `evidence_refs` | 同上／`rri/rri/existence_grounding.py` |
| 「実測を名乗るなら根拠が要る」 | `_NEEDS_REF`（5語・fail-closed） | 同上（§7） |

**ただし AEC は本番で1件も使われていない**（consumer は `egl/experiments/run_aec_walking_slice.py` の1本のみ）。
`twoder/knowledge_packet_provenance.py` は本番配線済みだが、**packet 単位**であって明細単位ではない。

∴ **語彙は AEC から取り、置き場は RTHREAD に作った。**

### 層の掟を守るための写しと、その drift 対策

`rri` は `egl` を import しない（`request_thread.py` 逐語「本モジュールは stdlib 以外を import しない」／
状況表の `層飛ばし rri->egl:0` を壊さない）。∴ 語彙は**写し**で持つ。

**写しがずれる事故は試験で止める**: `rri/rri/test_question_evidence.py` が
`egl.answer_evidence` の現物と `BASIS_KINDS` / `VALIDATION_MODES` / `_NEEDS_REF` を**逐語で突き合わせ**、
ずれたらそこで落ちる。

---

## 2. 新しい event type を足す前の事前チェック（★自分で決めた7項目）

`QUESTION_EVIDENCE` を足すにあたり、**その type 名を読む場所ではなく、この event collection を
type非限定で読む全 consumer** を調べた。

| 読み口 | 未知の type をどう扱うか | 判定 |
|---|---|---|
| `_append` | `EVENT_TYPES` で検査**していない** | 通る |
| `project` | type を名指しで選ぶ | 無視される |
| `resolve_thread` | `project` を呼ぶだけ | 影響なし |
| `resolve_question` | 3つの type を名指し | 無視される |
| `list_questions` | 4つの type を名指し | 無視される |
| `list_account_proposals` | 2つの type を名指し | 無視される |
| `actors_of` / `list_typed` | 各1つを名指し | 無視される |

**collection を直接開く file は `request_thread.py` 自身だけ**（他は所有API経由の12箇所）。
`EVENT_TYPES` / `DISPOSALS` は**1バイトも足していない**（封印された定数。監査が逐語で照合している）。

**実証も試験に入れた**: `test_existing_readers_ignore_the_new_event` が、根拠を1件書いた後に
`list_questions` / `resolve_question` / `resolve_thread` / `list_typed` / `actors_of` が
**同じ答えを返す**ことを確かめる。`test_projection_and_conservation_are_untouched` は
**projection が1つも動かない**ことを確かめる（`before == after`）。

---

## 3. 足したもの

### 3.1 `rri/rri/request_thread.py`（sole writer）

- `record_evidence(thread_id, question_id, evidence_refs, basis_kind, validation_mode, ts, …)`
- `list_evidence(thread_id, question_id=None)` / `resolve_evidence(evidence_id)`
- `EVIDENCE_BASIS_KINDS` / `EVIDENCE_VALIDATION_MODES` / `EVIDENCE_NEEDS_REF`（AEC の写し）

**fail-closed**: 語彙外は `ValueError`。実測・観測・調査を名乗るなら `evidence_refs` が空だと `ValueError`。
**決定論 id**: 同じ入力を2回入れても `evidence_id` は増えない（試験で固定）。

### 3.2 ★粒度は「新しい語」ではなく「形」で分けた

```
question_id が 在る  → その明細1件の根拠
question_id が None → その依頼(thread)全体の根拠（＝明細まで絞れなかった）
```

**なぜ必要か（実測）**: 痕跡は task 単位では実在する（ED65242E **22件** / EF6826DC **47件**、
うち `RUNNER.run_test` が FAILED）が、**`question_id` を持つ証拠は0件**。
∴「明細まで絞れた」と「依頼までしか絞れない」を混ぜて記録すると、後から分けられない。

`grain` という新語を作らず、**question_id の有無**で表した。

### 3.3 `twoder/ids.py` — ★片肺を最初から作らない

- `QE-` を解決する枝を足した（`Q-` より**前**に置く＝前方一致で食われないため）
- **`Q-` の解決に根拠を同梱した**

2026-08-23 に `recorded_by` を `list_questions` にだけ足して `ids.resolve` が答えず、
Taka に**片肺**を指摘された。∴ **根拠は最初から両方の口に置いた。**

### 3.4 `twoder/detail_refs.py`

`ID_PREFIXES` に `QE-` を足した（`Q-` より前）。明細の原文が根拠 id を指せるようになった。
`Q-` が食われていないことを確認済み。

---

## 4. 本番の台帳で1件通した（ED65242E）

| 記帳 | 明細 | basis_kind / validation_mode | evidence_refs |
|---|---|---|---|
| `QE-9c0f0460` | `Q-9d3f4bb0`（#4 FACT: account_gate.py が LLM に選ばせている） | LOCAL_CODE_OBSERVATION / OBSERVED | `ART-630e5f23cb` |
| `QE-7cc9e60b` | `Q-19be9e79`（#13 CONSTRAINT: 承認経路は現行のまま） | LOCAL_CODE_OBSERVATION / OBSERVED | `ART-ae789b58f7` |
| `QE-f5e1410a` | **（依頼粒度）** | LOCAL_MEASUREMENT / MEASURED | `ETR-274933fb43b9-0025` |

すべて `recorded_by="Claude Code (MGR)" / recorded_via="direct"`（**横から書いたことを隠さない**）。

### 4.1 途中で1本、台帳の穴を埋めた

明細 #4 が指す `twoder/account_gate.py` は**実体は在るのに ARTIFACT_REGISTRY(4,547行)に登記が無かった**。
根拠として引ける id が無いと §9 の「repo/file/commit へ戻れる」が成り立たないため、登記した
→ `ART-630e5f23cb`（`content_hash sha256:9c0b2929…` / `git_blob_sha 5a76578c…`）。

### 4.2 受入（★戻れることを実際に確かめた）

```
記録した3つの evidence_refs が front door /api/resolve で 引けた : 3/3（★死んだ参照0）
明細 → 根拠 → 実体 が 1本で 辿れた                              : 2/2
/api/resolve?id=QE-9c0f0460 が 根拠1件を 返す                    : ○
/api/resolve?id=Q-9d3f4bb0  が evidence を 同梱して 返す         : ○
★複式保存則 raised=27 resolved=0 open_gap=0 in_flight=27         : 例外なし（記帳の前後で不変）
★既存の口: /api/rthread 明細27・構造化33・科目27 ／ /api/task_index 595件・完了88件（変化なし）
試験 66本 全通過（新規12本を含む）
```

---

## 5. ★推測で結ばなかったもの（ここが段4 の限界）

ED65242E の失敗試験は `test_impl.py::test_not_in_list_valid` の1件。
TEST 明細 #23 は「2. NOT_IN_LIST + book_name が10〜15文字 -> status == PENDING」であり、**人が読めば対応する**。

**だが決定論の鍵が無い。**

- 封印試験は依頼文より**後に**生成される（`goal` 1,868字に `<<<2DER:IMMUTABLE_TESTS>>>` は**無い**）
- 生成時に「どの明細から出た試験か」を記録していない
- 試験名と明細本文の間に、順序以外の一致は無い

∴ **依頼粒度で記録した。** 明細に結ぶには、**試験を生成する側が鍵を刻む**必要がある（DW/EGL 側の仕事）。

### 5.1 いま届く範囲（分母つき）

| 経路 | 実測 |
|---|---|
| 構造化された明細 | **33 / 974**（ED65242E のみ） |
| そのうち参照を持つ | **4 / 33** |
| 参照から既存明細へ決定論で届いた | **3 / 4**（#0 は先頭40字が一致せず） |
| そのうち根拠 id を持てた | **2 / 3**（#14 の `classify_account` は**未実装**＝これから作る物・正常） |

**段4 の辺は通ったが、通る幅はまだ狭い。** 広げる律速は段4ではなく、
**明細の構造化が1 task にしか適用されていないこと**である。

---

## 6. 触っていないもの

- 既存974明細 / `raise_question` の署名 / `EVENT_TYPES` / `DISPOSALS` / `STATES` / `TRANSITIONS`
- `project` / `check_conservation` の計算（**数は1つも動いていない**）
- `account_gate` の判定経路 / 既存の `account_id`
- `egl/answer_evidence.py`（**読んだだけ**）／ `LEDGER_ACCOUNT_TREE*.json`
- UI（`webui.py`）— ★本件では1バイトも触っていない（担当が別インスタンスへ移ったため）

## 7. 未確認・次に回すもの

1. **明細 → 封印試験の鍵**。生成側が刻む必要がある（§5）。DW/EGL 側の設計。
2. **構造化が 33/974**。既存明細へ遡って構造化するかは未決（Taka 裁定「新規のみ」が既に在る）。
3. `match_questions` の先頭40字一致が **3/4**。外れた1件（#0）は原文の先頭が違う。閾値は動かしていない。
4. **調査結果(RIREQ)を返す front door の口が0件**。`/api/scout` の出力は依然として揮発している。
   「返せない」が結果であり、それが次に作る読み口である。
5. AEC 本体（`egl/answer_evidence.py`）を本番へ配線するかは未決。今回は**語彙だけ借りた**。
