# GDW 裁定3件の正本仕様 v0.1 — Domain の語 / Worker の門 / 測定語

- 起票: CC_ALPHA(監視) 2026-08-24
- 親: ITEM-2DER-EVO-0099（GDW運用設計）
- 上位正本: `TAKA_2026-08-24_GDW_OPERATION_DESIGN_v0.1.md`（ART-da5a15e434）
- Taka 裁定: 2026-08-24（本文に逐語で引く）

---

# ① Domain の語 — DOMAINS 16件とは別物

## Taka 裁定（逐語）

> 既存 DOMAINS には入れない。既存16件が「開発対象領域」で、今回の Domain Manager が「運用上の
> 責任領域」なら、同じ Domain でも階層が違います。無理に同じ表へ入れると後で意味が壊れます。
> ただし新台帳もまだ作らない。まず既存の「責務・actor・manager・routing」を表現する欄を全件調査し、
> 適切な登記先がなければ、その時点で上位概念を設計する。現時点では 語の定義だけ正本仕様に固定し、
> DOMAINS 16件とは別物と明記でよいです。

## 1.1 全件調査の結果（2026-08-24 実測）

責務・actor・manager・routing を表現する語彙表は **10本**あった。

| 表 | 場所 | 件数 | 何を表すか |
|---|---|---|---|
| `DOMAINS` | `twoder/domain_specialization_schema.py:12` | 16 | **開発対象領域**（UI / API / DATABASE / NETWORK …） |
| `ROLES` | `dev-workcell/dw/workcell.py:31` | 5 | **役**（MANAGER / WORKER / AUDITOR / ADJUDICATOR / RUNTIME） |
| `COMPONENTS` | `twoder/artifact_registry.py:25` | 12 | **成果物の持ち主**（DS/RRI/EGL/DW/TWODER/AUTHORITY/…） |
| `ACTORS` | `egl/docs/cc_register.py:27` | 4 | 文書の宛先（MGR/DESIGN/IMPL/TAKA） |
| `ACTORS` | `twoder/detail_seal.py:42` | 6 | 明細の主体（2DER/Claude/MGR/Taka/External/UNKNOWN） |
| `ACTORS` | `twoder/progress_seal.py:18` | 6 | 同上（★別ファイルに同名で重複） |
| `STAGES` | `twoder/progress_seal.py:19` | 8 | 段（DETECT…RESPOND） |
| `STAGES` | `twoder/contract_progress.py:1` | 7 | 段（CREATED…USED）★別の軸で同名 |
| `ROUTES` | `twoder/routing_contract.py:18` | 3 | 経路（AUTO/SENIOR/TAKA） |
| `ROUTES` | `twoder/task_selector.py:174` | 3 | 同上（★重複） |

**どれも「運用上の責任領域」を表していない。**

- `DOMAINS` 16 は開発対象（Taka 裁定どおり別物）。
- `ROLES` 5 は**役**であって領域ではない（ESDE Domain Manager の「役」は MANAGER）。
- `COMPONENTS` 12 は成果物の持ち主。ESDE は含まれない。

## 1.2 事実上の登記はコード上の表に在る

運用上の Domain 名は現在 **`twoder/manager_v0.py` の `DOMAIN_OPERATIONS` のキー**にしか無い。

```
DOMAIN_OPERATIONS = {"dw": [...], "route_table": [...], "esde": [...], "ledger": [...]}   # ← 4件
```

★これは**台帳ではなくコード上の対応表**。∴ **適切な登記先は無い。**

★`domain` という名の欄を持つ既存の口は **`HUMAN_ESCALATION_LEDGER.domain` 1本だけ**で、
**語彙の縛りが無い**（`open_escalation` は `r.setdefault("domain", None)` するだけ）。
実際 `HESC-f840c4e2323a` に `domain='ESDE'` を自由文字列として書いた（★私が書いた）。

## 1.3 語の定義（★これを正本とする。新台帳は作らない）

**Domain（運用上の責任領域）** — 2DER の運用を分割する単位。
各 Domain はちょうど1つの Domain Manager が持ち、次の3つだけを決める:

1. **何を測る／何を処理するか**（対象の選別）
2. **結果をどう扱うか**（意味づけ・次の行動）
3. **Domain の状態**（General へ返す要約）

**Domain は `DOMAINS`（開発対象領域・16件）とは別物。** 階層が違う。
`DOMAINS` は「どんな技術領域の仕事か」、Domain は「誰が運用の責任を持つ区画か」。
★同じ表に入れてはならない。

現在の Domain（**4件**・出所は `manager_v0.DOMAIN_OPERATIONS`・2026-08-24 実測）:

| Domain | Domain Manager | 操作 | Worker |
|---|---|---|---|
| `dw` | `twoder/domain_dw.py` | 6 | dev-workcell |
| `route_table` | `twoder/domain_dw.py`（★実体は分離前・足場負債） | 1 | — |
| `esde` | `twoder/domain_esde.py` | 3 | `egl/structure/s_esde_evaluate.py` |
| `ledger` | `twoder/domain_ledger.py` | 5 | 同モジュール内（W1/W2/W3） |

## 1.4 まだやらないこと（★Taka 裁定どおり）

- 新台帳を作らない。
- `DOMAINS` に足さない。
- 上位概念（Domain を登記する表）の設計は、**登記先が要ると分かった時点**で始める。
  ★いま要ると言える根拠はまだ無い（Domain は3〜4件で、コード上の表で足りている）。

---

# ② Worker が勝手に実行しない8種 — authority の門にする

## Taka 裁定（逐語）

> 規律だけでは弱いです。これは今回作ろうとしている構造そのものに関わります。
> ただし8種をそのまま8個の新ルールにしない。既存 authority の OBSERVE / REVERSIBLE / IRREVERSIBLE と
> 既存POLICYで表現できるか全件照合して、既存の門で拘束できるものは既存へ載せる。表現不能な差分だけ追加する。
> 特に「Workerは提案・観測まではできるが、状態変更はManager/authorityを通す」という境界は、
> 文書規律ではなく機械的に破れない方がいいです。

## 2.1 8種の出所

上位正本 §5「**Manager判断を必要とする**」:
state変更 / 正本変更 / authority変更 / requiredの新規定義 / code修正 /
destructive operation / findingの処分 / Domain境界を越える操作。

## 2.2 全件照合（8種 × 既存 POLICY 27行）

| # | 8種 | 既存で表現できるか | 対応する既存行 |
|---|---|---|---|
| 1 | state変更 | **手段が無い** | — |
| 2 | 正本変更 | **手段が無い**（landing は `COMMIT_PUSH`） | `COMMIT_PUSH`(IRREVERSIBLE) |
| 3 | authority変更 | **できる** | `CHANGE_AUTHORITY_CEILING`(IRREVERSIBLE) |
| 4 | requiredの新規定義 | **手段が無い**（②と重なる） | — |
| 5 | code修正 | **手段が無い**（landing は `COMMIT_PUSH`） | `COMMIT_PUSH` |
| 6 | destructive operation | **できる** | `KILL_OR_RESTART` / `STOP_SERVICE` / `MODEL_LOAD_UNLOAD` / `CHANGE_GPU_ALLOC` / `CHANGE_SERVE_SCRIPT` / `RESTART_VLLM`（全て IRREVERSIBLE） |
| 7 | findingの処分 | **同型が在る**（ESDE 側に処分の口がまだ無い） | `LEDGER_DISPOSE_QUESTION`(REQUIRES_APPROVAL) |
| 8 | Domain境界を越える操作 | **構造で塞がっている** | `to_domain` は `NO_DOMAIN` なら呼ばない |

★「手段が無い」= **ESDE Worker にその口が1つも無い**。書く口は下の4つで全部。

## 2.3 ESDE Worker が書く口（★全件・実測）

| 口 | 何をするか | 段 |
|---|---|---|
| `RT.record_evidence` | 根拠を追記 | 追記式 |
| `RT.raise_question` | finding を明細1行にする | 追記式 |
| `RT.record_actor` | 誰が書いたかを残す | 追記式 |
| `ds.etrace.emit` | 観測記録 | 追記式 |

**4つとも既存の値を書き換えない** ∴ `REVERSIBLE`。

## 2.4 追加した差分 — **1行だけ**

```
"ESDE_RECORD_EVALUATION": (AUTO_EXECUTE,
  "ESDE Worker write-back of one evaluation — append-only
   (record_evidence / raise_question / record_actor / etrace.emit);
   never rewrites an existing value; produces facts only, never a disposition",
  REVERSIBLE)
```

★`LEDGER_RECORD_EVIDENCE` を**再利用しなかった**理由: あの行は `record_evidence` **だけ**を名乗って
おり、`raise_question` / `record_actor` を含まない。**名前と中身をずらさない。**

## 2.5 門の掛け方（★`domain_ledger` の前例と同じ形）

`s_esde_evaluate.write_to_detail` の冒頭で `authority.gate(ESDE_WRITE_ACTION)` を呼び、
`requires_approval` なら **1バイトも書かずに返す**。

★門を Worker 側に置いた理由 = **Domain を経由せず Worker を直接叩いても外れない**ため
（Taka 逐語「文書規律ではなく機械的に破れない方がいい」）。

## 2.6 封印試験（★通ることだけ見ない。実際に拒否させた）

| 試験 | 結果 |
|---|---|
| 1. 現行の行為は通るか | `requires_approval=False` ✅ |
| 2. **POLICY から外したら止まるか** | `wrote=False / why="authority: requires approval"` ／ **書く前に返っている**（`thread_id=None`） ✅ |
| 3. 未知の行為（将来 state 変更を足した場合） | `gate("ESDE_ADVANCE_STATE") requires_approval=True` ✅ |
| 4. 計器の回帰 | `s_esde_evaluate --check` **GREEN** 維持 ✅ |

★★**効き目の本体は「この行為が通ること」ではなく「POLICY に無い行為が止まること」。**
将来ここに状態変更を足しても、行為名が POLICY に無ければ fail-closed で止まる
（`authority.py` L125-126）。

---

# ③ ACTOR_ACTIONS の測定語 — 今は足さない

## Taka 裁定（逐語）

> 今は足さない。STRUCTURE据え置き。ここは急いで語彙を増やす必要がありません。
> 実際に STRUCTURE 代用によって、「測定」と「構造化」が区別できず、authority・routing・台帳集計の
> どれかで誤判定が発生した、という実例が出てから分離すればいいです。

## 3.1 現状（変更なし）

`rri/rri/request_thread.py:179` `ACTOR_ACTIONS = ("RAISE","ANNOTATE","PROPOSE_ACCOUNT","DISPOSE","STRUCTURE")`

ESDE Worker は `record_actor(..., action="STRUCTURE", ...)` を使う。**据え置き。**

## 3.2 分離する条件（★これを満たしたら再提起する）

**STRUCTURE 代用が原因で、次のどれかに誤判定が出た実例が1件出たとき。**

1. `authority` — 行為の段の判定が「測定」と「構造化」で変わるべきなのに同じになった
2. `routing` — 行き先が変わるべきなのに同じになった
3. 台帳集計 — 分母／分子が「測定」と「構造化」を混ぜたために誤った数を出した

★実例が出るまで**語彙を増やさない**。
★実例が出たら、この節に「いつ・どの集計で・どう誤ったか」を書いてから分離を提案する。
