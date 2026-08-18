# 宛: Taka / 設計 / 監査 ―― GM 管理アーキテクチャ案 v0.1 の照合（第1回）

**実装していない。新 Manager・新台帳・新口 0。**
**★印の無い記述は 2026-08-18 の実測。「推測」と書いた欄だけが推測。**

## 0. まず ―― 提案の前提が1つ、実測で覆る

### §6「機能表が存在しない」 → **★存在する**

```
twoder/function_table.py  18,730 B ／ 公開関数 13
逐語「★機能表(★正本 §25 段3)=★人体図鑑の裏側=★機能から索引できる形」
     「★一覧＋『一覧にない』＋『決められない』は account_gate と同じ形」  ← ★3値を既に持つ
     「★新台帳0・口0増・新しい承認工程0」                                ← ★§11 の条件を既に満たす
公開関数に ★記録から生成する物が在る:
  candidates_from_records / funnel_from_records / undecided_from_records
```

**§6 が「作るべき」と言う機能（記録から機械生成・3値・新台帳0）は、既に実装されている。**

### ただし ―― **在るが育っていない**

```
種の機能 8語   受信 / 検証 / 分類 / 登記 / 配送 / 監査 / 実行 / rollback
               ★origin="hand"（人が書いたと 自分で 申告している＝2DER 製の数を濁らせない作法）
記録           90件 ／ 3走行 × 30件（seed 違いの合議）
funnel         asked 30 ／ ★name_captured 0 ／ duplicate_of_existing 0
undecided      `DISPATCH.next_legal_operation` 等が NOT_DECIDED
```

**器は在り、走り、収穫が 0。** 「一覧に無い」票は出ているのに新機能名を1つも採れていない。
**∴ §6 の作業は「新設」ではなく「★なぜ収穫0なのかの原因調査」になる。**

## 1. 既に持っている物（実測・今夜引いた分）

| 提案の要求 | 既存資産 | 状態 |
|---|---|---|
| §6 機能表 | `twoder/function_table.py` | **在る**／記録生成あり／**収穫0** |
| §7 経路表 | `twoder/route_table.py` **18区間** | **在る**／★Domain 区間 **0**／自動更新なし（最終 commit は [Claude実装]） |
| §4 実行状態・手番 | `dw/dispatch.py::_MAP` **9状態** ＋ `whose_turn`（2026-08-18 実装） | **在る**・LLM 0回 |
| §4 供給主体 | `webui._machine_registry()` **5役** | **在る**（CODING_WORKER / INDEPENDENT_AUDITOR / MANAGER / BUILD_PLANNER / CLAUDE_SENIOR） |
| §4 権限境界 | `_MAP.claude_barrier` ／ `taka_authority` ／ 門の `runnable` | **在る**（今夜 `decide_rearm_v2` で権威として使用） |
| §2 Work Unit | `assemble_work_unit_v2`（2026-08-18・2DER 製） | **在る**／★台帳には入っていない |
| §1 勘定科目 | `account_gate` ／ `approve_account` ／ 軸 **2本** | **在る**／★軸 2/5 科目 |
| §4 成果・証拠 | `/api/etrace`（task面・run面） | **在る**／★task 面は 18区間中 6 しか引けない |
| §9 台帳 | `roadmap_registry`（ITEM/PHASE/ROADMAP・append-only） | **在る**／`set_status` `register_item` で書ける |

## 2. できないこと（実測で確定した欠陥）

| # | 欠陥 | 実測 |
|---|---|---|
| A | emit の多くが `task_id` を持たない | **65箇所中 48（74%）** ／ 経路表 18区間中 **9** が task から引けない |
| B | **本線実行と実験実行を分ける欄が無い** | etrace の 13欄すべてに該当なし。`run_id` は代理にならない（本線経由でも None が多数） |
| C | 経路表が「必須／条件付き」を持たない | `S07` と `S14/S15` を分けられない |
| D | 経路表に Domain Manager の線が **0区間** | `domain` `material` `role` `work_unit` の語が **全部0** |
| E | `handoff`（送り側）が揃う区間が限られる | 片側だけの区間が在る |
| G | 依存が構造欄でなく散文にしか無い | `EVO-0019` は `depends_on` 2件とも DONE なのに `status_note` の文で止まっていた |
| **H** | **PLAN の供給元・失敗理由が後から引けない** | `view` の鍵は `has_plan`(真偽)のみ／PLAN 記録 8件すべて `identity=None`（**EVO-0075** に登記） |

**A〜E・G・H は、そのまま §5 の inventory 分類を阻害する。**
「未観測」と「未実行」を分けるには A が要り、「本線／実験」を分けるには B が要る。

## 3. ★ID の族が既に 6つ以上ある（§2 への警告）

実測で確認した ID 族:

```
ITEM-2DER-EVO-xxxx    台帳の item（depends_on / task_ids / artifact_ids / evidence_de_ids / change_ids / authority / acceptance）
PHASE-2DER-EVO-xx     phase（11本）
TASK-2DER-xxxxxxxx    DW の task（9状態の状態機械）
DE-xxxx               設計証拠 ／ CHG-xxxx 変更
ART-xxxxxxxxxx        成果物（absolute_path / content_hash / exists / component_owner）
WU-xx-xxxx            Work Unit（assemble_work_unit_v2・★台帳外）
RTHREAD-xxxxxxxx / Q-xxxxxxxx / JREV-xxxx / INTV-（0017）
```

**「Work Unit」を新概念として足すと 7つ目以降になる。**
§10-1 の指示どおり、**新概念を作る前に `ITEM` と `WU` の重複を先に解く**べき。
**私の見立て（推測）**: `ITEM` が既に §2 の Project 相当（depends_on・phase・authority・acceptance を持つ）。
`WU` は台帳外の別族なので、**どちらかに寄せないと 2つの Work Unit が並立する。**

## 4. 提案のうち「既に答えが在る」もの

| 提案 | 既存 |
|---|---|
| §4 「GM は Domain の内部実装を読まない」 | **今夜そう作った** ―― `to_domain` が操作名から Domain を選び委譲（G の名指し 4→3） |
| §4 「手番・barrier を Operations から取る」 | `whose_turn`（`_MAP` の引き算・LLM 0回）。**★ただし権限の門を見ない**（別 item） |
| §6 「3値（在る／一覧に無い／決められない）」 | `function_table` が **既に同じ形**（`account_gate` と同型と自称） |
| §11 「新台帳0・新口0」 | `function_table` の docstring が **既に同じ宣言** |
| §9-4 「UNKNOWN を許す」 | `verify_material` が `NO_MATERIAL/UNVERIFIED/ESTABLISHED/CONDITION_NOT_MET` の4語で既に実装 |

## 5. 何をするために何が要るか（最小の順序）

**先に測るべきは §5 の inventory ではなく、inventory を測れるようにする欄。**

```
1. A（emit に task_id）      … これが無いと 18区間中 9 が task から引けない
2. B（本線／実験の欄）        … これが無いと「走らせてよい集合」を作れない
3. H（PLAN の供給元・失敗理由）… これが無いと 3件の停止原因が永久に不明（EVO-0075）
4. D（経路表に Domain 区間）  … これが無いと Domain の未接続を経路表が検出できない
5. §6 の収穫0 の原因調査      … 器は在るので「なぜ採れないか」だけ
```

**1〜4 が埋まって初めて §5 の 11分類が機械で出せる。**
**現状で機械分類できる割合は測っていない（★未測）。**

## 6. まだ測っていないもの（隠さない）

- §8 RRI の外部取得 capability が機械で引けるか ―― **未測**
- §3 管理属性（勘定科目で取れる分／不足分）の切り分け ―― **未測**
- §5 未了 26件を既存台帳だけで 11分類できる割合 ―― **未測**
- §10-4 Operations Domain の既存機能一覧 ―― **未測**
- §10-5 Management Audit 相当の既存監査部品 ―― **一部のみ**（`upper_review_gate` / `conformance` / EVO-0019 の3部品を確認）

## 7. 私からの1点（提案書への指摘）

**§6 の前提誤りは、今夜 MGR が11回やった失敗と同じ型。**

> **「知らないから作る」** ―― 既存資産を引く前に、新設を設計してしまう。

`function_table.py` は 18,730 B・公開関数13・記録90件で**既に在り**、
§6 が要求する性質（記録生成・3値・新台帳0）を**既に満たしている**。

**∴ v0.2 では、各節の冒頭に「既存資産を引いた結果」を先に置くことを提案する。**
これは `ITEM-2DER-EVO-0076`（MGR が既存機能を使わず自作するのを止める）と**同じ処方**であり、
**人・Claude・設計のどれにも同じ型が出ている**ことを示している。
