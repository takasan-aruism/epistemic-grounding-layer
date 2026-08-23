# 勘定科目2層モデルの chart 採用 v0.1 — Taka 裁定の実行記録

**作成: Claude Code（MGR）／ 2026-08-23**
**裁定（逐語）:**

> 新LEDGER_ACCOUNT_TREEをrthreadの有効科目体系として採用する。
> ただし命名未確定2件は、確定済み56件と同じ意味で「完成済み科目」とは扱わない。
> IDとして既に安定しており分類結果に使用されているならchartへの登録自体は許可してよいが、
> UNRESOLVED である事実を保持すること。名前をMGRが勝手に確定してはならない。

**前提: 段5 構造判定（`ART-9aff0cedf4`）の欠落①**

---

## 0. 着手前の全件調査

`rthread_chart.json` を読む／書く場所を5repoで逐語 grep。

| | 場所 | 採用の影響（★事前に確定した） |
|---|---|---|
| **書き手** | `twoder/approve_account.py` **のみ** | ★掟を壊さない＝採用の口も**同じ module に置いた** |
| 読み手1 | `rri/rri/request_thread.py:_load_chart` → `raise_question` | 許容が**広がるだけ**（拒否が減る方向）。安全 |
| 読み手2 | 同 `check_account_conservation` | `allowed` が広がるだけ。安全 |
| 読み手3 | `twoder/account_gate.adopted()` → `_menu()` / `_prompt()` | ★**5→63件**。名前が引けず id だけになる → **要対処** |
| 読み手3' | `account_gate.decide()`（決定論の段） | `ACCOUNT_AXES_v3.json` に tree id は無い → **変化なし** |
| 読み手4 | `twoder/account_candidates.py:20` | `ACC-`+sha1 でしか照合しない → **変化なし** |

`_load_chart` は `chart_version` と `accounts` の2キーしか読まず、追加キーは無視することも確認した。

---

## 1. ★裁定の数え方と実測を突き合わせた（ここで1回ずれた）

最初の実装は「完成済み＝`CONSENSUS_EXACT`」とした。実測すると **55件**で、裁定の「確定済み56件」と合わない。

```
CONSENSUS_EXACT          55
CONSENSUS_CONSOLIDATED    1   ← 名前「ステータス」。合議をまとめて決めたもの
UNRESOLVED_NO_CONSENSUS   2   ← ★これが 裁定の言う「命名未確定2件」
                         ──
                         58
```

∴ **`CONSOLIDATED` を未確定側に落とすと 55/3 になり裁定とずれる。**
「名前が合議で付いたか」を基準にして **56 / 2** に揃えた。
ただし **`EXACT` と `CONSOLIDATED` は束ねず、内訳をそのまま返す**（粒度を潰さない）。
この一致は封印試験 `test_counts_match_the_ruling_56_settled_and_2_unresolved` で固定した。

---

## 2. ★名前を MGR が確定していないこと

- 命名未確定2件は **`name=None` のまま**。候補（監査検証タスク／監査確認業務／監査検証作業）を
  **名前に昇格させていない**
- `adopted()` は `name_status` を併せて返す ＝ **「命名未確定」と「名前がたまたま無い」を混同させない**
- LLM へ渡す一覧では **`（命名未確定）`** と書く（空欄で塗り潰さない）
- 封印試験 `test_unresolved_axes_keep_name_none` / `test_settled_means_a_name_was_agreed_not_that_mgr_named_it`
  で固定した

| axis_id | level | 明細数 | name_status |
|---|---|---|---|
| `LCAT-d23a39ff` | 1（大分類・**最大の161件**） | 161 | UNRESOLVED_NO_CONSENSUS |
| `LDET-15a929ca` | 2 | 11 | UNRESOLVED_NO_CONSENSUS |

---

## 3. 足したもの

### 3.1 `twoder/approve_account.py` — `admit_ledger_tree_accounts(approved_by, ts, dry_run=True)`

- **既定は `dry_run=True`**（1バイトも書かず、何が起きるかだけ返す）
- `approved_by` が空なら拒否（**人の承認が要る**）
- 一覧を手で持たず、**現物 `LEDGER_ACCOUNT_TREE_NAMES.json` から読む**
- `approve_account` は**1文字も触っていない**（LLM が出した新名称を人が1件ずつ承認する別経路。
  `MIN_OCCURRENCES=2` はその経路の規律であり、軸は候補一覧に載らない＝実測済み）
- 採用した事実を **ETRACE へ emit**（chart は版と id しか持てないため）

### 3.2 `twoder/account_gate.py` — `adopted()` が2層モデルの命名も読む

**名前を旧い命名台帳へ複製していない**（2箇所になるとずれる）。`account_tree` 経由で読むだけ。
これが無いと chart 5→63 で **58件が名前の無い id として LLM の選択肢に並び、選ばせる一覧が壊れる**。

---

## 4. 受入（すべて実測）

```
chart 版         : 3 → ★4
chart 科目       : 5 → ★63（★増えたのは58件だけ）
★既存5件         : すべて残っている（ACC-1e5f5c5a / ACC-53c96ac2 / ACC-d32cd53e /
                    ACC-dc4c648f / AX-cee7bf57）
★保存則           : 本番 RTHREAD-4d89c66c で I1/I2 とも例外なし（raised=27）
★LLM の選択肢     : adopted 63件（名前つき61 / ★命名未確定2）／ menu 65項目
                    （NOT_IN_LIST・NOT_DECIDED を含む）
★front door       : /api/accounts 旧 axes 7件 無傷 ／ 新 tree カテゴリ6・詳細52
                    /api/rthread  明細27・科目27（変化なし）
試験              : twoder 53本 ＋ rri 41本 ＝ ★94本 全通過（新規11本を含む）
```

### 4.1 ★段5 の門が実際に開いた（隔離環境・本番と同じ chart を複製して実行）

```
LDET-04574589（確定済み・ワークフロー検証ルール） 起票=通った → ★RESOLVED 通った
LCAT-d23a39ff（★命名未確定）                     起票=通った → ★RESOLVED 通った
LDET-NOPE（存在しない）                          起票=★拒否（off-chart account_id）
I1/I2 例外なし
```

**段5 構造判定の欠落①が解けた。** 存在しない id は従来どおり fail-closed で拒否される。

---

## 5. 触っていないもの

- **既存明細の `account_id`** — 974件は `QUESTION_RAISED` が UNCLASSIFIED のまま。**書き換えていない**
- `approve_account` / `MIN_OCCURRENCES` / `ACCOUNT_AXIS_NAMES.jsonl` / `ACCOUNT_AXES_v3.json`
- `dispose_question` / `DISPOSALS` / `UNCLASSIFIED_FORBIDDEN_DISPOSAL` / `present_gaps`
- `LEDGER_ACCOUNT_TREE*.json`（**読んだだけ**）／ `webui.py`（担当が別インスタンス）

## 6. 次に要るもの（段5 の残り）

裁定で**欠落①だけ**が解けた。②③④は残っている。

| 欠落 | 状態 |
|---|---|
| ① chart に58科目が無い | ★**解けた**（本記録） |
| ② 決まった科目を既存明細へ書き戻す書き手が無い | **未着手**。局所判断＝私の権限。**次はここ** |
| ③ `dispose_question` が `QUESTION_RAISED` の初期値しか見ない | ★**上申が要る**（③既存正本と矛盾／⑧安全境界。出口規則は裁定 ADJUDICATION_SENSITIVE:16） |
| ④ `present_gaps` の本番呼び手が0件 | 私の管轄外（DS） |

**②を作っても③が無いと既存明細は RESOLVED にできない**（新規起票なら①だけで通る）。
∴ ②を先に作り、③は②の実測を添えて改めて上げる。

## 7. 未確認

- `LCAT-d23a39ff` は**最大の大分類（161件）が命名未確定**のまま。命名段の再実行は別インスタンスの担当
- `account_gate.decide()`（決定論の段）は依然 `ACCOUNT_AXES_v3.json`（旧）を見ており、
  2層モデルの軸ベクトルを使っていない。**採用しても決定論の段は新モデルを使わない**
- LLM の選択肢が 5→63 に増えたことが `decide_with_llm` の精度にどう効くかは**測っていない**
