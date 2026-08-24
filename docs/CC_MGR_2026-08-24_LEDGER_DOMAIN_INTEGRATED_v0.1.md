# Ledger Domain Manager / Worker 統合仕様 v0.1 ―― General側成果の引き継ぎ統合

作成: Claude Code (MGR) / 2026-08-24 13:5x
親仕様（正本・逐語）: `egl/docs/TAKA_SPEC_2026-08-24_LEDGER_DOMAIN_v0.1.md` = **ART-dd54fb656c**
ITEM: `ITEM-2DER-EVO-0100`

★本書は親仕様を **置き換えない**。§14「過去記録を書き換えない」に従い、
親仕様の §0〜§23 はそのまま正本とし、本書は **実装済みの現状を突き合わせて追記する**。

★本書の全数字は **2026-08-24 13:4x〜13:5x に取り直した実測**。General側の報告値を転載していない。
一致した箇所・食い違った箇所の両方を下に明記する。

---

## A. 引き継いだ General 側の成果（EVO-0100 履歴 4件・逐語出所つき）

| # | AXIS | 成果 |
|---|---|---|
| 1 | `GM_LEDGER_WORKER_SURVEY_RESULT` | 全件調査。報告書 **ART-0d9bdaab46**。★「本当に無い」はほぼ無く、大半が「在るが呼ばれていない」 |
| 2 | `LEDGER_DOMAIN_WIRED_W1W2_AUTO_W3_GATED` | **GM→Ledger Domain→W1/W2/W3→台帳→GM を人手なしで1周**。新Worker0/新台帳0/新state0/新ID0 |
| 3 | `TEST_PROVENANCE_DETAIL_TO_VERDICT` | 明細→封印試験→test_result→evidence を **明細粒度**で通した |
| 4 | `HUMAN_ADJUDICATED_3_DETAILS_AND_TREE_IS_A_STALE_SNAPSHOT` | 3明細を人が科目裁定 → W3 候補 0→3。★**2層モデルは「分類できなかった」のではなく「一度も問うていない」** |

## B. 現物の確認（★ソースに在る≠動く を分けた）

| 物 | 実在 | 実走で確認したこと |
|---|---|---|
| `twoder/domain_ledger.py` | ○ 15,183 B | `ledger_classify_one` / `ledger_evidence_one` / `ledger_dispose_candidates` / `ledger_dispose_apply` / `ledger_summary` の5口。W1/W2/W3 は**既存機構を呼ぶだけ** |
| `twoder/manager_v0.py` | ○ | `DOMAIN_OPERATIONS["ledger"]` に5操作 / `DOMAIN_MODULES["ledger"]` に1行。★`to_domain`/`get_domain` は**汎用のまま**（dw / esde に続く3つ目） |
| `twoder/authority.py` POLICY | ○ | 3行を**実際に撃って確認**（下記 D） |
| `twoder/ledger_rates.py` | ○ 6,067 B | 実走して4率を取得（下記 C） |
| `twoder/test_provenance_seal.py` | ○ 6,885 B | 契約ブロックの**外**のマーカー ∴ `immutable_tests_sha256` 不変 |

## C. 4率 ―― ★朝から大きく動いた（`ledger_rates` を今この場で実走）

| 率 | 08-24 早朝(before) | 07:14(General最終) | **★13:4x(今)** |
|---|---|---|---|
| 機械記帳率 | 4.70% | 8.04% | **★20.29%** |
| Claude記帳率 | 95.30% | 91.96% | **★79.71%** |
| direct記帳率 | 95.59% | 92.38% | **★80.07%** |
| 未処分率 | 99.52% | 99.53% | **99.53%**（処分 5件のまま） |
| 未割当率 | 37.90% | 39.08% | **39.19%** |
| 明細総数 | 1,037 | 1,062 | **1,064** |

書き手の内訳（分母 818）:

```
MGR.backfill               619   ← ★Claude が手で書いた在庫(追記式 ∴ 永久に残る)
MANAGER_V0.feedback_one     94   ← 機械
DOMAIN_LEDGER.w2_evidence   65   ← ★機械(W2)
Claude Code (MGR)           30
ESDE_WORKER                  3   ← 機械
MANAGER_V0.tick              4   ← 機械
MGR(Taka 裁定(a) の実施)      3   ← 人の裁定3件
```

★**率は在庫、流量は別**（General側の指摘を実測で追認）。機械記帳率が 4.70%→20.29% へ動いたのは、
**常駐が回り続けて機械の行が増えた**ため。`MGR.backfill` 619件は減らない。

★**鍵の違いを1件明示する**: `unassigned_num = 417` と `unclassified_effective = 176` は**別の鍵**。
前者は「割当eventが無い明細」、後者は「有効科目が UNCLASSIFIED に落ちる明細」。混ぜてはいけない。

## D. authority ―― ★門は実際に効いている（撃って確認）

| action_type | decision | auto |
|---|---|---|
| `LEDGER_CLASSIFY` | AUTO_EXECUTE | True |
| `LEDGER_RECORD_EVIDENCE` | AUTO_EXECUTE | True |
| `LEDGER_DISPOSE_QUESTION` | **REQUIRES_APPROVAL** | **False** |

逐語 reason: *"declaring a detail RESOLVED/REJECTED/MERGED is an adjudication, never automatic (Taka 2026-08-24)"*

★親仕様 §13「自動実行してはいけないもの」と**既に一致している**。新しい段は増えていない（3×3 のまま）。

## E. W3 の現在地 ―― 候補3件で正しく止まっている

```
scanned_threads      698
candidates             3   (Q-31d11de9 / Q-54cea911 / Q-28be2dd5 ・すべて RESOLVED 提案)
blocked_unclassified   0
根拠                    QE-45d32432 / QE-0cb20301 / QE-24eac0b8
                        basis_kind=LOCAL_MEASUREMENT / validation_mode=MEASURED
                        evidence_refs=ETR-f8ec80f68285-0009
read_only            true   ★台帳に1バイトも書かない
```

★親仕様 §11「ObservationとDecisionを分離」・§4 W3「自動処分を原則としない」と**既に一致**。

## F. ★中核の原因 ―― ACCOUNT_TREE は古いスナップショット（★私の実測でも再現・より強い数字が出た）

`egl/structure/LEDGER_ACCOUNT_TREE.json` mtime = **2026-08-23T04:31:36** / revision `614241f622f53c4e` / n_members 644

| 区分 | 明細数 | tree が値を持つ | 被覆 |
|---|---|---|---|
| スナップショットより**前** | 1,025 | 644 | 62.8% |
| ★スナップショットより**後** | **78** | **0** | **★0.0%** |
| 合計 | 1,064 | 644 | 60.5% |

さらに割当との突き合わせ:

```
割当済み(uniq)          647
  ★うち tree 由来        644
  ★tree に無いのに割当     3   ← 人の裁定3件(Taka 裁定(a))
★tree にあるが未割当       0   ← ★W1 は tree を完全に汲み尽くしている
```

★★**これが決定的**: `tree にあるが未割当 = 0`。
∴ **W1 は正常に動いており、供給が尽きている**。新しい78件は tree に**1件も無い**（0.0%）ので、
**W1 は構造的に空を引き続ける**。未割当率 39.19% はモデルの不能ではなく **上流の停止**である。

生成器 `egl/structure/s_ledger_account_tree.py` の**非試験の呼び手 = 0件**（全5repo走査・ヒット4件はすべて docstring/コメント）。
∴ **手で回すしかない**。

★General側の値との差: General は「26時間新しい」と書いたが、今は**33時間**。
新規78件は**増え続けている** ∴ 放置すると被覆は単調に下がる。

## G. 親仕様の各項が「既に在る / 在るが未接続 / 一部在る / 本当に無い」のどれか（Phase 1 の先取り分）

★これは §2 の管理対象19種の全件分類**ではない**。今回引き継いだ範囲だけの分類である。
全件分類は Phase 1 で別途行う。**0件と書かない＝測っていない箇所は「未測」と書く**。

| 親仕様の項 | 状態 | 根拠（今回の実測） |
|---|---|---|
| §3 三層構造(GM→Domain→Worker) | **EXISTS** | `to_domain`/`get_domain` が汎用のまま3つ目の Domain を受けた |
| §4 W1 分類 | **EXISTS（供給が止まっている）** | tree にあるが未割当 0 / 新規78件の被覆 0.0% |
| §4 W2 証拠 | **EXISTS** | `DOMAIN_LEDGER.w2_evidence` 65件を実際に書いている |
| §4 W3 処分 | **EXISTS（候補まで・門で停止）** | 候補3 / `read_only:true` / gate=REQUIRES_APPROVAL |
| §4 W4 Relation Integrity | **PARTIAL** | 個別に実測した欠陥は在る（task_id 形式差・repo境界・stale projection）が**常設のWorkerは無い** |
| §4 W5 Lifecycle | **MISSING（未測を含む）** | 今回の走査では該当する常設機構を見ていない。★「無い」と断定せず Phase 1 で確認する |
| §5 OPEN に理由を要求 | **MISSING** | `OPEN_REASON_UNKNOWN` に相当する語を今回の範囲では見ていない（未測） |
| §7 Stale管理 | **PARTIAL** | ★`ACCOUNT_TREE` の stale は**検出できた**が、検出したのは人(Claude)であって常設機構ではない |
| §8 記録がある≠管理されている | **確認済み・是正済み(1件)** | EVO-0094 の `status_note` 全件None → 07:12 に記帳（本件が §8 の実例） |
| §12 自動実行可能範囲 | **EXISTS** | W1/W2 が AUTO_EXECUTE×REVERSIBLE |
| §13 自動実行してはいけない | **EXISTS** | W3 が REQUIRES_APPROVAL・実際に拒否する |
| §14 過去記録を書き換えない | **EXISTS（実践済み）** | refs 抽出器で履歴を消さず読む側で取り直した（ART-d6809170f9） |
| §16 対等性/対称性/保存則 | **PARTIAL** | 保存則 I1/I2 は `request_thread` に在る。対等性(WRITE→RESOLVE)の常設検査は無い |
| §18 Domain の集約状態 | **EXISTS** | `ledger_summary()` が rates / writer_counts / dispose_candidates を返す |
| §9・§10 類似・経験再利用 | **EXISTS（observation-only）** | `DONOR_HAS_IT` は `OBSERVATION_ONLY_RULES` に置いたまま（ART-5c362bb73f） |

## H. ★統合して名指しできた「次の1手」

親仕様 §21 Phase 2（Observation）へ進む前に、**W1 の上流が止まっている**ことが最大の閊え。

```
s_ledger_account_tree.py（呼び手0・手回し）
      ↓ 33時間 動いていない
LEDGER_ACCOUNT_TREE.json（644件で固定）
      ↓
W1 = detail_backfill（tree が値を持つ物しか割り当てない）
      ↓ ★tree にあるが未割当 = 0 = 汲み尽くし済み
新規78件 → ★被覆 0.0% → ★永遠に空を引く
      ↓
未割当率 39.19%（下がらない）
      ↓
W3 の候補が増えない（UNCLASSIFIED_FORBIDDEN_DISPOSAL で止まる）
      ↓
未処分率 99.53%（動かない）
```

★**これは1本の因果**であり、途中のどこを直しても他が動かない。
★但し **私は実装していない**。親仕様 §21 は Phase 1 = Inventory が先であり、
生成器の実行頻度は Taka の裁定事項（General 側も同じ裁定を求めて止まっている）。

## I. ★やっていないこと（隠さない）

- §2 の管理対象19種の**全件分類はしていない**（今回は引き継ぎ範囲のみ）
- §22 の完了条件20項目の**全件判定はしていない**
- W5 Lifecycle / §5 OPEN理由 を「無い」と**断定していない**＝今回の走査範囲外＝**未測**
- `ACCOUNT_TREE` の再生成を**していない**（呼び手0のまま・裁定待ち）
- W3 の3候補を**処分していない**（承認1回が要る・自分に承認を出さない）
- 実装0行（本書は記録のみ）

## J. ★計器の自己監査（親仕様 §15）

本書を書く途中で**自分の計器の欠陥を1件**踏んだので記録する。

★生の `LEDGER_ACCOUNT_TREE.json` を直読して `_by_question` を引き、**0件・被覆0.0%** と出した。
★誤り。`_by_question` は生ファイルに無く `account_tree.load()` が `details`/`members` から組み立てる。
正しい口で引き直すと **644件・被覆60.5%**。
★教訓＝**正本の読み口を使う。生ファイルの直読で「無い」と言わない**。
（親仕様 §15 の「0件は『0件だった』のか『取得できなかった』のかを区別する」の実例）

★本書の分母と探索範囲:
- 明細の分母 = `RT.count_questions()["questions"]` = **1,064**（thread 698）
- 呼び手の探索範囲 = 5repo（twoder / rri / ds / egl / dev-workcell）の `*.py` `*.sh`
- 除外 = 試験ファイル（`test_` 先頭 / `/test` を含むパス）
- 取得不能 = 0件（今回の走査ではすべて読めた）
