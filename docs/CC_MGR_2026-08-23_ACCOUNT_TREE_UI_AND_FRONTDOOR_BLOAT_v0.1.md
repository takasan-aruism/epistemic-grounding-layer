# 勘定科目2層モデルのUI開通 ＋ front door 肥大の原因特定 v0.1

**作成: Claude Code（MGR）／ 2026-08-23**
**基準資料: `egl/docs/TAKA_2026-08-23_LEDGER_DETAIL_DESIGN_MEMO_v0.1.md`（`ART-948e04d27a`）§7 勘定科目 / §13 UIとの関係**

## 0. 探した範囲（「無い」と書く前に）

- `egl/structure/` の account 系ファイル全24本を列挙し、新モデル4本を特定
- `LEDGER_ACCOUNT_TREE{,_NAMES,_AXIS_NAMES}` `LEDGER_ACCOUNT_AXES_CANDIDATE` の
  **consumer を5repoの `*.py` 全体で逐語 grep**
- `/api/accounts` `/api/rthread` `/api/rthread_add` の consumer を `*.py` `*.js` `*.html` で全件
- ETRACE（782MB）を読む場所を5repo全体で列挙（12箇所）
- 台帳の直読はしていない（明細は `rri.request_thread` の所有API、task は front door 経由）

**1回失敗した**: `grep -rn -- "$ep" --include=*.py` と書いたため `--` 以降の `--include` が
オプションではなくファイル名として扱われ、`.jsonl` 台帳まで grep していた。`--include` を `--` の前へ移して数え直した。

---

## 1. 勘定科目 — 新モデルは存在するが、誰も読んでいなかった

### 1.1 現物

| ファイル | 中身 | 書き手 |
|---|---|---|
| `LEDGER_ACCOUNT_TREE.json` | 2層（大分類6 / 詳細52）・明細644件の割当 | `s_ledger_account_tree.py` |
| `LEDGER_ACCOUNT_TREE_NAMES.json` | 上の軸58本の命名（英語=正 / 日本語=併記） | `s_ledger_account_axis_names.py` |

`_meta` 逐語: **「★台帳ではない=毎回まるごと作り直す控え」**。∴ 登記簿に載せる対象ではなく、読むだけでよい。

### 1.2 実測した欠落

```
新モデルを読む consumer（生成段の外）      : ★0件
front door /api/accounts が出していたもの : 古い ACCOUNT_AXIS_NAMES.jsonl の ★7件
   → 中身は「引っ越し手続き」「交通費精算方法」＝試験で作った古いもの
∴ 58科目は画面に1件も出ていなかった（Taka の指摘は正しい）
```

### 1.3 足したもの（★読むだけ・書き込み0・新台帳0・新event type0・新ID体系0）

- `twoder/account_tree.py`（新規）— 2層モデルを読む部品。`(mtime,size)` で控えを持つ。
  - **「無い」/「読めない」/「名前が決まっていない」を分ける**:
    `NOT_GENERATED` / `UNREADABLE: …` / `name=None` のまま＋候補を添える
  - 実測 58件中 **2件が `UNRESOLVED_NO_CONSENSUS`**（`LCAT-d23a39ff` 候補=監査検証タスク/監査確認業務/監査検証作業、
    `LDET-15a929ca` 候補なし）。**空欄で塗り潰さず「命名未確定」と出す**
- `/api/accounts` に `tree` 欄を**別に**足した（既存 `axes`/`candidates` は1文字も触っていない）
- `/api/rthread` に明細1件ごとの `account` と、**分母つきの `account_coverage`** を足した
- UI: 勘定科目タブに2層の木、明細表に「勘定科目」列、旧 `account_id` は「旧 科目」列として残す

### 1.4 対照2本での実測（front door 経由）

| task | 明細 | 新モデルで科目が付いた | 既存 `account_id` |
|---|---|---|---|
| `TASK-2DER-ED65242E` | 27 | **27 / 27** | UNCLASSIFIED 27/27 |
| `TASK-2DER-EF6826DC` | 13 | **13 / 13** | UNCLASSIFIED 13/13 |

ED65242E の内訳: アカウント選択ロジック11 / 書籍名検証8 / ステータス検証ルール3 / ステータス2 / 関数実装1。
**旧い機構が78%を未分類のまま置いていた明細に、新モデルは100%科目を付けている。**

構造化明細（`typed`）は `question_id` を持たない別の並びのため、段3で作った既存の対応付け
`requirement_gaps.match_questions`（先頭40字一致・決定論）で繋いだ。**実測 26/33**。
**残り7件は対応が付かないので `None` のまま出す**（推測で結ばない）。

### 1.5 まだ繋がっていないこと（正直に）

- 母数は `list_account_proposals` の**648件**であって、明細総数ではない。
  提案が立っていない明細には科目が付かない。
- 新モデルは**読むだけ**。`account_gate.decide` / `approve_account` の判定経路には接続していない。
  ∴ `QUESTION_ACCOUNT_PROPOSED` の `NOT_DECIDED 99.1%` は**1件も動いていない**。
- 大分類1本（161件・最大）の**名前が決まっていない**ため、画面に「命名未確定」が出る。

---

## 2. ★front door 肥大 — 原因を特定して直した

### 2.1 見つかった経緯

`/api/task_index` を front door 経由で呼んだら **140秒**かかった。UI の既定待ちは **120秒**
（`webui.py` の `MS_DEFAULT=120000`）∴ **運転タブが画面上でタイムアウトしていた。**

### 2.2 計器を疑った（自分の測定が壊れている可能性を先に潰した）

| 測り方 | 結果 |
|---|---|
| 段ごとに手で計った合計 | 11.58秒 |
| `task_index()` を**直呼び** | **0.49秒**（595 task・None は1件も無し） |
| HTTP 経由 | 140秒 → 67.7秒（ばらつく） |
| **再起動直後**の HTTP | **0.556秒** |

∴ **遅いのは `task_index` ではなく、front door プロセスが使ううちに劣化すること**だった。
劣化した時の実測: **RSS 7.9GB / CPU 97.6%**（起動直後は 23MB）。

### 2.3 口ごとに肥大を測った

```
/control                          3回  0.02s   +0MB
/api/rthread?task_id=…            3回  8.27s   +107MB
/api/accounts                     3回  0.05s   -2MB
★/                                3回 27.45s  ★+5,596MB
/api/etrace                       3回  0.42s   +194MB
```

トップページ `/` の中を切り分けると:

```
build_report   0.09s
validate       0.07s
render_report_page  ★4.75s  ★+3,763MB   （出力は 12KB の HTML）
  └ CMDS.list_pending_approvals()  ★4.77s  ★+3,762MB  （★返りは 23行）
      └ twoder/stopped_actions.py:39
```

### 2.4 原因（1行）

```python
for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
```

`p` = `ds/data/event_trace.jsonl` = **782MB**。
これを **丸ごと文字列に載せ、さらに行の一覧としてもう1本**持つ。**23行を返すために。**

**ETRACE を読む他の11箇所は元から1行ずつ流していた**（`function_table.py` ×2 / `question_review.py` /
`route_adopt.py` ×2 / `artifact_registry.py` / `route_edge_vote.py` / `route_candidates_v2.py` ×2 /
`observed_edges.py`）。**ここだけが例外だった。**

### 2.5 直したもの・確かめたこと

`twoder/stopped_actions.py` に `_iter_lines(path)` を足し、**その1行だけ**差し替えた
（本体の字下げも判定も1文字も変えていない）。

**受入は「エラーが出ない」ではなく「前と同じ数字」で取った**:

| | 直す前 | 直した後 |
|---|---|---|
| `list_stopped_actions` 単体 | 4.84秒 / 最高 RSS 3,804MB | **0.84秒 / 20MB** |
| 返り | 23件 | **23件** |
| **行の内容と順序** | — | **完全一致（`old == got` が True）** |
| front door `/` 3回後の RSS | 5,803MB | **53MB** |
| その直後の `/api/task_index` | 67〜140秒 | **0.48秒** |

比較は git の `HEAD:stopped_actions.py` をその場で `exec` して、**同じプロセス・同じ入力**で取った。

---

## 3. 触っていないもの

- 既存974明細 / `raise_question` の署名 / `EVENT_TYPES` / `DISPOSALS` / `KINDS`
- 既存の `account_id`（`UNCLASSIFIED`）の値と `account_gate` の判定経路
- 古い `/api/accounts` の `axes` `candidates` `columns` `raw_rows`
- `LEDGER_ACCOUNT_TREE*.json` の中身（読むだけ・再生成していない）
- ETRACE を読む他11箇所

## 4. 未確認・次に回すもの

1. **`/api/rthread` が 3回で +107MB / 8.27秒**。原因未特定（`detail_refs` が `grep`/`find` を
   subprocess で呼んでいる分が疑わしいが**測っていない**）。別件として残す。
2. **`/api/etrace` が 3回で +194MB**。同上。
3. **782MB の `event_trace.jsonl` 自体**をどうするか（分割・圧縮・保持期間）は決めていない。
   今回は読み方だけ直した。**ファイルは1バイトも触っていない。**
4. 新モデルを `account_gate` の判定へ接続するかは**未着手**（今回は表示のみ）。
5. 大分類 `LCAT-d23a39ff`（161件・最大）の命名が未確定。命名段の再実行は別インスタンスの担当。

## 5. 試験

`twoder/regression/test_account_tree.py`（新規9本）を含め、
`test_requirement_structure` 12 / `test_detail_refs` 12 / `test_requirement_gaps` 9 / `test_account_tree` 9
= **42本 全通過**。`rri/rri/test_actor_recorded.py` 12本も全通過。

`twoder/regression/` をディレクトリごと pytest にかけると、同居する非pytestファイルが
import 時に `sys.exit` を呼ぶため `INTERNALERROR` になる。**試験ファイルを名指しで走らせること。**
