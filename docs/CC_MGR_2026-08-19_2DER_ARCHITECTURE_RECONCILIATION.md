開発者規律 確認済(v1.0)

# 2DER 全体構造・旧設計との照合 ―― **事実調査（評価なし）**

宛: Taka → **GPT へ渡す証拠資料** ／ 写: MGR / DESIGN / IMPL
／ **発: 監視（3Claude の外・Taka 直命 2026-08-19 19:2x / 19:5x 改訂）**
／ 台帳: **登記しない（★本線に介入しない・新ITEM 0）**

**★この資料は評価・優先順位づけを行わない（Taka 指示 2026-08-19 19:5x）。**
**★事実と出所のみを置く。良し悪し・順序・推奨は GPT 側で判断する。**

```
新規実装 0行 ／ 新規判断規則 0 ／ 新規台帳 0 ／ 既存仕様の書き換え 0 ／ front door への投入 0
本線（connector 本線接続 → delegated energize → 初回 real-repo）に触れていない
```

**出所の記法（全記述に付す）**
```
【正本】 Taka 逐語の仕様書（書き換え禁止）
【正規面】front door の API ／ 部品自身の公開関数の戻り値 ／ 台帳 ／ 部品の docstring 逐語
【補助】 私の import 解析・ファイル走査（★最終根拠にしない。正本か正規面へ戻した物だけを事実とする）
【探した範囲】「無い」と書く時に必ず併記
【UNKNOWN】どちらでも確定できなかった
```

**分類記号（A-6・全項目に適用）**
```
① 旧正本/台帳に在る    ② 現在実装が在る    ③ 本線に配線済み    ④ 実走済み
⑤ 本来の機能を満たした実証あり    ⑥ 呼び手0    ⑦ 未実装
⑧ 正式変更済み    ⑨ なし崩し変更疑い    ⑩ UNKNOWN
```

---

## §0 調査範囲

**読んだ正本 7本（全て `egl/docs/`）**

| # | 正本 | 日付 | 読んだ範囲 |
|---|---|---|---|
| 1 | `CC_MGR_2026-08-12_TAKA_ROUTE_AND_FUNCTION_SPEC_v0.1.md`（956行） | 08-12 | §0〜§26・結論（見出し全数／本文は §0-§14, §16-§17, §20-§26） |
| 2 | `CC_MGR_2026-08-14_TAKA_ROUTE_WORKER_VS_MANAGER_SPEC.md` | 08-14 | 全文 |
| 3 | `CC_MGR_2026-08-14_TAKA_NEXT_PHASE_AND_MANAGER_V0_SPEC_v0.1.md` | 08-14 | §0〜§4 ＋ MGR 訂正節 |
| 4 | `CC_DESIGN_2026-08-16_TAKA_GNW_CORRECTION_ORDER.md` | 08-16 | 全文 |
| 5 | `TAKA_2026-08-17_DOMAIN_DESIGN_ENGINE_v0.2.md`（109行） | 08-17 | 見出し全数 ＋ §12〜§20 |
| 6 | `RRI_CANONICAL_SPEC_v1_0.md`（v1.1） | 07-28 | §1〜§3（Taka 逐語部分）＋見出し全数 |
| 7 | `phase-1b-acquisition-boundary.md` | 07-05 | 見出し全数 ＋ 実装前追補（AB-1/2/3） |

**引いた正規面**
```
front door : /api/roadmap /api/ledgers /api/tasks /api/resolve
部品の公開面: route_adopt.route_table_view() ／ function_table.function_table_view()
              function_table.function_list() / function_index() / records_summary() / components()
              failure_memory / contract_from_plan / research_acquisition / egl.acquisition / egl.adapters
              rri.{request_type,preflight_gate,intent_strategy,research_intent,existence_grounding,
                   request_thread,request_resolution}
systemd    : twoder-{webui,manager,route-worker}.service
```

---

## §1 現在実装されている階層【正規面】

```
常駐 3
  twoder-webui.service        front door :8770（受け口 15）
  twoder-manager.service      manager_v0（650行 / 20関数）
  twoder-route-worker.service route_worker（297行）
Domain
  twoder/domain_dw.py         700行 / 11関数（DW ドメイン）
Worker（dev-workcell/dw/dispatch.py `_MAP` 9状態の actor_role）
  CODING_WORKER / INDEPENDENT_AUDITOR / MANAGER / BUILD_PLANNER / CLAUDE_SENIOR
```

**部品数【補助: import 解析。`test_*` と `regression/` を除く】**

| 箱 | 部品 | 他部品から import されている | されていない |
|---|---|---|---|
| ds | 6 | 2 | 4 |
| rri | 22 | 15 | 7 |
| egl | 174 | 37 | 137 |
| dev-workcell | 55 | 23 | 32 |
| twoder | 249 | 93 | 156 |
| **計** | **506** | **170** | **336** |

**★この336は「import 経路で辿れない数」。2026-08-18 実測では twoder の非import 138 のうち 127 は
台帳・文書・CLI に名前が出る【補助】。∴ 上限でも下限でもない。**

---

## §2 A-1 経路表システム

### 2-1 旧正本【正本1・正本2】

**「経路表システム」という概念の有無 → ①在る。正本1 §23 が定義している（逐語）:**
> 本システムは「経路表自動生成システム」ではない。経路表は出力の一つにすぎない。
> 実体は、**2DER内部の構造・機能・接続・稼働実績を、自己観測によって維持する内部モデル**である。
> 部品図、機能表、経路図、稼働記録を別々に管理するのではなく、**相互参照可能な一つの構造**として扱う。

**経路表Worker / Domain Manager 構想の有無 → ①在る。正本2 が一文定義で分けている（逐語）:**
> Route Worker = 2DERで実際に何がどこからどこへ通ったかを、証拠付きで観測・更新する機構。
> Manager = 2DERが実際に行ったことと、本来行うべきことを比較し、次に何をすべきかを決める機構。
> 境界 = 経路表は事実を言う。Manager はその事実の意味を判断する。

**3層分離【正本1 §2.3】** STATIC_EDGE（機械が確定）／ROUTE_EDGE（Worker が分類）／OBSERVED_EDGE（実行記録が確定）
**段A/B/C【正本1 §3】** 機械候補生成（LLM 0）→ Worker 限定メニュー分類 → 登録（Worker は書かない）
**出力は事実状態のみ【正本2 §4】** OBSERVED_BOTH_SIDES / SENDER_ONLY / RECEIVER_ONLY / PASSABLE / NOT_PASSABLE / NO_RECORD / UNKNOWN ／ ★PASSABLE ≠ CORRECT
**抽出対象【正本1 §5.2】** import / from import / function call / class利用 / **endpoint呼び出し / subprocess / shell呼び出し** / service呼び出し / repo間参照 / 既存runtime記録
**完了条件8つ【正本1 §26】** ①機械が未登録候補を自動生成 ②Worker が候補1件を限定メニューで分類 ③3層が区別されている ④Function を既存一覧から分類 ⑤「一覧に無い」を候補として保持 ⑥承認された Function が一覧へ追加 ⑦経路表・機能表・実績を front door から取得 ⑧Manager と Taka が repo 探索なしで状態確認

**★「系内部だけでは取得できない経路」という概念の有無 → 見当たらない。**
```
【探した範囲】正本7本の全文に対する語検索（自己観測 / 内部モデル / 観測面 / 外部観測 /
              外から観測 / 観測不能 / unobservable）
【結果】該当は 正本1 §23 の「自己観測によって維持する内部モデル」1箇所のみ。
        これは「内部観測で維持する」と述べており、「内部観測では取れない経路」を扱う記述ではない。
【分類】⑩UNKNOWN（正本に無いのか、私が読んだ範囲外に在るのかを確定できていない）
```

### 2-2 現在実装【正規面: `route_adopt.route_table_view()` 2026-08-19 19:3x】

```
total 225 ／ by_origin {hand: 18, machine: 207}
columns:
  exists                    243  鍵=v2 の静的候補（名前ごとに1件・自己/試験/docs を除外）／走査 1,140箇所・LLM 0
  observed                   68  鍵=送信側(handed_to)と受信側(received_from)の両方が在る対だけ／未登録 50
  exists_not_observed   233/243  鍵=相手の名前が実行の辺に一度も出ない
  exists_and_seen_by_name    10  鍵=名前が実行の辺に出ただけ（★『繋がった』ではない・注記は正規面の原文）
machine 207 の kind 内訳: from import 約150 ／ observed_both_sides 68 ／ import 6
```

### 2-3 旧設計のどこを実装しているか

| 旧設計【正本】 | 現在の部品【正規面】 | 分類 |
|---|---|---|
| 段A 機械候補生成 | `route_candidates_v2.candidates_v2` / `segment_candidates` / `callee_candidates` | ①②③④⑤ |
| 段B Worker 分類 | `route_edge_vote.run_once / list_votes`（model・prompt_version・input_hash・seed別 votes 保持） | ①②③④⑤ |
| 段C 登録 | `route_adopt.adopt / revoke / adopted_rows / route_table_view` | ①②③④⑤ |
| STATIC_EDGE | `columns.exists` = 243 | ①②③④⑤ |
| ROUTE_EDGE | machine 行の kind | ①②③④⑤ |
| OBSERVED_EDGE | `columns.observed` = 68 | ①②③④⑤ |
| 事実状態のみ出力 | `by_status`（linked / no_send / no_receive / no_locator / split_run / not_expected） | ①②③④⑤ |
| 常駐で自動更新 | `twoder-route-worker.service`（active） | ①②③④⑤ |
| `_use()` | GM が台帳を引く共通の口（2026-08-19 に付け替え） | ②③④⑤（①に無い＝正本外の追加） |

### 2-4 現在取得できる経路の情報源（全列挙）【正規面】

```
① 静的 import / from import   → columns.exists（走査 1,140箇所）
② 実行の辺（handed_to / received_from の両側）→ columns.observed（68）
③ 名前一致（末尾・小文字）     → exists_and_seen_by_name（10）
④ 人の手書き 18区間            → route_table.ROUTE（S01〜S18）
⑤ Worker の票                  → route_edge_vote.list_votes（seed別・input_hash つき）
```

### 2-5 現在取得できない経路の種類

```
(a) subprocess 経由        【正本1 §5.2 の抽出対象に明記】→ columns の鍵に無い → ⑦未実装
(b) shell 呼び出し経由      【同上】                        → ⑦未実装
(c) endpoint（HTTP）経由    【同上】                        → ⑦未実装
(d) 動的 import / importlib 【正本に記載なし】               → ⑩UNKNOWN（規定の有無が不明）
(e) 台帳ファイル経由の受け渡し（口ではなく置き場の共有）      → ⑩UNKNOWN
(f) 人が手で運ぶ経路（Claude の中継）→ 記録に残らない        → ⑩UNKNOWN
【探した範囲】route_table_view().columns の4鍵 ／ route_candidates_v2 の公開関数名 ／ 正本1 §5.2
```

### 2-6 「存在しない」と「見えていない」の区別

```
区別できる  : 「コードに在るが実行で見ていない」= exists_not_observed（233/243）★明示欄あり
区別できない: 「コードにも実行にも無い」 と 「上記(a)〜(f)で観測面の外に在る」
              → 両者とも「表に載らない」として扱われ、分ける欄が無い
関連【正本2 §12 逐語】「『見つからなかった』と『存在しない』を同一視しない」
別系統での実装状況: `completion_from_materials` 側には `NOT_INSPECTED`（＝未調査）が在る
                   （2026-08-19 の実測で「語0件の時 CONDITION_NOT_MET と出していた」を分離した）
【分類】経路表の粒度では ⑦未実装 ／ 材料の粒度では ②③④⑤
```

---

## §3 A-2 機能表システム

### 3-1 旧正本【正本1 §4.3 / §7 / §9 / §10 / §16 / §22】

```
Function は Component / Edge / Evidence と並ぶ独立概念（§4）
Function 名は既存一覧から選ぶ。Worker が創作しない（§4.3 / §10.1）
問い3つ（§7）①この接続は経路か ②この部品は何をする所か ③この機能は既に在るか
必ず「一覧に無い」「判断できない」「近い物は無い」を選択肢に置く（§2.5 / §21.2）
票が割れたら原則確定しない（§9）／票は「Worker判定の再現性」として記録
新規Function候補 → 既存の承認経路で正式登録（§10.3）／新しい承認システムを作らない（§19）
段3 終了条件（§16）= Function一覧が実際に1件増え、★追加主体・承認根拠を front door から確認できる
最終的に答える2問（§22）部品→機能 ／ 機能→部品
```

### 3-2 現在実装【正規面: `function_table.function_table_view()` 2026-08-19 19:3x】

```
records      170（5走行: 30 / 30 / 30 / 73 / 7）
list          9語（受信・検証・分類・登記・配送・監査・実行・rollback・確認）
by_origin    {hand: 8, machine: 1}
by_origin_note（正規面の原文）「★hand の8語は module の定数=★記録から来ていない(★実績と読まない)」
list の各行の欄  name / function_id / origin / registered_by / registered_at / from_component
                 ★hand 8語は registered_by・registered_at・from_component が全て null
not_in_list  ルーティング(twoder.route_table) / 停止管理(twoder.stopped_actions) / 処理 / 判断 …（held つき）
near_names   [処理↔投票処理] [取得↔研究取得] [状態確認↔確認] [研究↔研究取得]
funnel       per_run に asked / any_not_in_list_vote / unanimous_not_in_list /
             name_captured / duplicate_of_existing
             （例: ETR-9b6d70615ffa は asked 30 / name_captured 0）
undecided    NOT_DECIDED の票を seed 別・reason 付きで保持
index_lookups {verify: 57, human: 0, machine: 19}
             _key（正規面の原文）「★どちらも呼び手側が変えられる値 ∴ 鍵を添えて出す(v0.3 §13.3)」
function_index("登記","machine") = {"in_list": true, "components": [], "count": 0}
components  key / sends / returns / source / origin（例 DISPATCH.next_legal_operation）
```

### 3-3 EXPECTED（宣言機能）と OBSERVED（実現機能）の二面

| Taka 指定の問い | 現在の構造で保持できるか | 根拠【正規面】 | 分類 |
|---|---|---|---|
| A. 何をするために作ったか | 部分的 | `list.name` ＋ `components.sends/returns`。**契約の requirement 文とは結ばれていない** | ②（欄は在るが不完全） |
| B. 実際には何として機能したか | **できない** | 機能表に実走結果の欄が無い。`records` は Worker の回答記録であって実走記録ではない | ⑦未実装 |
| 誰が機能名を付けるか | できる | `origin`（hand/machine）＋ `registered_by` | ②③④ |
| 誰が実現機能を確認するか | **できない** | 確認主体の欄が無い | ⑦未実装 |
| 実走回数 | **機能表では不可** | task 側 `/api/resolve` の `generation.per_attempt` に在る（**別台帳**） | ⑦（機能表として） |
| 成功条件 | **機能表では不可** | 契約の `expected` に在る（**別文書**） | ⑦（機能表として） |
| 失敗条件 | **機能表では不可** | 契約の `prohibited` に在る（**別文書**） | ⑦（機能表として） |
| 未確認 | できる | `undecided` ＋ `not_in_list.held` | ②③④⑤ |

**Taka が挙げた実例の所在**
```
apply_unified_diff V1: 設計上=unified diff 適用 ／ 実走=16試験中12通過（複数hunk・空入力・末尾改行なし で失敗）
  この事実が在る場所: 契約文書 CC_DESIGN_2026-08-19_CONTRACT_APPLY_UNIFIED_DIFF.md ＋ task 記録
  ★機能表からは引けない（B面の欄が無いため）
```

### 3-4 段3 完了条件の充足状況

```
【正本1 §16 段3 終了条件】Function一覧が実際に1件増え、追加主体・承認根拠を front door から確認できる
【正規面】by_origin.machine = 1（2026-08-19 02:38・新規実装0行）
         list に registered_by / registered_at / from_component の欄が在る
【分類】②③④⑤（条件は満たしている）
【併記】machine 1件の後、以後の成長条件は正本に規定が無い → ⑩UNKNOWN
```

---

## §4 A-3 Manager / Domain / Worker 階層

### 4-1 旧正本

**【正本3 §2.1 逐語】**
> Manager v0 は**知的な上司ではなく、台帳を見て既存の運行規則どおりにシステムを進める駆動装置**とする。

**【正本3 §2.3】Manager v0 が判断しないもの**
設計の良し悪し／コードの内容／複数案件の戦略的優先順位／権限境界の変更／不可逆な変更の承認／未知の例外への創作的対処

**【正本3 §2.6】受入条件（v0）**
Claude が書いた実装行数 = 0 ／ MGR・Taka が run 系の口を手で叩いた回数 = 0 ／
READY から Manager 自身が実装工程へ進める ／ 停止工程と理由が台帳から一意に引ける ／
Manager が勝手に設計・コード修正を行わない ／ 既存の正式な実行口を使い裏口を新設しない ／
既定経路の通常応答・既存非回帰を壊さない

**【正本4（GNW 是正指示）逐語】**
> 現在の manager_v0 を中心とした構成を、**単一Managerの高機能化として進めないこと**。
> General Manager → Domain Managers → Workers の三層構造である。
> **General ManagerがDomain固有処理を持ち始めた場合、それを「便利だから追加」とせず、職責越境として検出できるようにする。**
> 現在確認されている領域候補は少なくとも、**DW / RRI / 経路表 / 2DER(Towder)** である。

**【正本5 §16】Domain Manager の6責務**
(1)案件の勘定科目分類 (2)必須材料集合と必要Worker の決定 (3)Worker の起動 (4)結果の統合
(5)不足・衝突・未知の判定 (6)Domain設計・Contract群・Work Unit への変換

**【正本5 §12】** 「役割概念は Domain Manager Design、実行機能は Domain Design Engine、利用主体は各 Domain Manager」

### 4-2 階層別の現在実装【正規面】

| 階層 | 旧正本での名前 | 現在の実体 | 分類 |
|---|---|---|---|
| 全体 / 経営層 | General Manager【正本4】 | **無し。Claude MGR が代行**（正本4 で Taka が「現状 General Manager は存在しない」と明言） | ①⑦ |
| Domain | DW | `twoder/domain_dw.py` 700行/11関数 | ①②③④⑤ |
| Domain | 経路表 | `twoder/route_worker.py` 297行（常駐） | ①②③④⑤ |
| Domain | RRI | **無し** | ①⑦ |
| Domain | 2DER(Towder) | **無し** | ①⑦ |
| Execution Manager | （正本に語なし） | `manager_v0.py` の tick / _queue / _last_task / _machine_turn | ⑩（語の対応が正本に無い） |
| Worker | CODING_WORKER | `dw/adapters` → Qwen | ①②③④⑤ |
| Planner | BUILD_PLANNER | `twoder/build_planner.py` | ①②③④⑤ |
| Auditor | INDEPENDENT_AUDITOR | `dw/adjudicator` 360行 | ①②③④⑤ |
| Senior | CLAUDE_SENIOR | headless `claude -p`（UPPER_REVIEW 908回の実績） | ①②③④⑤ |

**【探した範囲】** systemd user unit 3つ ／ `twoder/*.py` の `domain_` 接頭辞 ／ 正本4 §3 の母集団4

### 4-3 manager_v0 の変遷（Taka 指定の5問）

| 問い | 事実 | 出所 |
|---|---|---|
| 元の Domain Manager か | **違う**。正本3（08-14）が「駆動装置」と定義。この時点で GNW という語は正本に無い | 【正本3 §2.1】 |
| Execution Manager / queue runner へ変化したか | **変化ではない**。最初から駆動装置として定義され、後から Domain の仕事が加わった | 【正本3】＋【正規面: 08-18 の分類結果】 |
| いつ変化したか | 08-16 03:0x（正本4 到着）以降 611行/18機能 → 787行/21機能。08-18 05:03 に D責務9件を分離 | 【補助: git log】＋【正規面: 台帳 EVO-0073】 |
| 正式裁定済みか | **GNW 三層の導入＝⑧正式（正本4・Taka 自身）／D責務分離＝⑧正式（正本4 に基づく是正）** | 【正本4】 |
| 台帳・仕様へ反映済みか | **台帳＝反映済み（EVO-0073 に分類結果と行数）／★正本3 の定義文＝未反映** | 【正規面】＋【正本3 全文】 |

**08-16〜08-18 に増えた機能（★08-18 の分類で D 判定 9件に含まれるもの）**【正規面: EVO-0073】
```
契約投入が断られた理由を残す ／ 保留された契約を飛ばす ／ 飛ばす鍵を骨格sha へ ／
試験が通った成果物を機械が置いて commit ／ 実装前の名前検査を引く
```
**【分類】⑨なし崩し変更疑い（是正済・台帳に記録あり・正本3 未反映）**

### 4-4 分離後の現状【正規面 2026-08-19 19:3x】

```
General  manager_v0.py  650行 / 20関数
         tick / _machine_turn / _queue / _queue_write / _queue_add / _last_task / _set_last_task /
         set_current_task / _use / _norm_key / to_domain / whose_turn / item_state / main /
         _call / _record ＋ D への委譲4つ（contract_with_precheck / submit_next_contract /
         receive_finished / record_stages・各6行前後）
Domain   domain_dw.py   700行 / 11関数
         _contract_docs / _submitted_shas / contract_with_precheck / precheck_names /
         submit_next_contract / _append_index / _place_and_commit / receive_finished / record_stages
分離時   787行/21関数 → 364行/16関数 ＋ 468行/9関数（★中身の書き換え0・置き場所のみ）
分離後   General が 364 → 650行（増えた4関数 = set_current_task / to_domain / whose_turn / item_state）
```

---

## §5 A-4 RRI 外部情報取得

### 5-1 旧正本

**【正本6 §1-2 Taka 逐語】**
> 本来、雑なユーザの意図を元に、それを具体的内容に落としつつ、**外部内部の情報を利用して**ユーザの目的そのものも具体化させ…

**【正本6 §2】DW へ渡す時点で揃っている12項目**
依頼者と発話者／元の逐語／文脈／意図／曖昧さ・不足・矛盾／必要な前提情報／**調査済み情報と根拠**／未確認事項／実行目的／制約／完了条件／保存先や案件との関係

**【正本6 §3】禁止6項目**
生の依頼文をそのまま DW へ渡さない／台帳の直接参照で不足を補わない／4軸を生成せず直感で7戦略を選ばない／根拠を保存せず次工程へ進めない／**不足情報を暗黙に補完しない**／RRI を単なるルーターとして実装しない

**【正本7】外部取得層の設計**
Acquisition Layer（adapter 方式）／Source Policy（静的 source list ではなく policy）／LegIntent（SearchPlan と Acquisition の必須ブリッジ）／`required_source_kind`（要求）と `observed_source_kind`（観測）の分離／`transport_status` と `content_status` の分離（200 でも CHALLENGE_PAGE / AUTH_WALL / EMPTY を弾く）／取得失敗は coverage についての知識

### 5-2 現在実装（Taka 指定の5分類）

**(1) 内部情報取得【正規面: 各 module の公開関数】**
```
request / thread 管理  rri.request_thread    open_thread / raise_question / annotate_question
preflight              rri.preflight_gate    detect / next_legal_operation / hold_facts / is_suppressed /
                                             load_patterns / past_reference_object / quantitative_object / binder_state
意図の解決             rri.intent_strategy   surface_signals / build_facts / build_prompt / resolve /
                                             stops_before_action / resolve_consensus
依頼種別               rri.request_type      classify_request_type
実在確認               rri.existence_grounding build_queries / load_claim_status / claim_status /
                                             document_frequency / check_existence
調査意図               rri.research_intent   classify_blockage / need_validation / form_resolution_requirements
【分類】②③④⑤
```

**(2) acquisition method 選択【正規面: `twoder/submit.py` が `_rec("SELECTED_ACQUISITION_METHOD", …)` で記録する値の全数】**
```
9種
  EGL_DE_ADMISSION          submit.py:214
  BLOCKED_DEAD_APPROACH     submit.py:371
  RRI_PREFLIGHT_HOLD        submit.py:405
  RRI_INTENT_HOLD           submit.py:486
  ★WEB_RESEARCH_ACQUISITION submit.py:542
  RUNTIME_INSPECTION        submit.py:608
  RESUME                    submit.py:676
  DW_IMPLEMENTATION         submit.py:693
  EGL_RESEARCH              （submit.py 内・行番号は上記grepの対象外）
選択の主体: `rri.request_resolution.select_strategy`（docstring 逐語「interpretation strategy selector(spec v0.2 §7-9)」）
            ＋ submit.py の分岐（research_signal / preflight / request_type の結果で決まる）
【分類】②③④⑤
```

**(3) repo / ledger / runtime 取得**
```
runtime  RUNTIME_INSPECTION（submit.py:608）／ twoder/runtime_inspection.py
ledger   /api/resolve /api/roadmap /api/ledgers ／ 各 repo の *.jsonl
repo     route_candidates_v2 の静的走査（1,140箇所）
【分類】②③④⑤
```

**(4) 外部取得（Web / API / 外部文書 / 人間 / sensor）**
```
★rri/rri/*.py の HTTP 呼び出しは 全て localhost:8005（ローカル vLLM）
   【正規面: intent_strategy.py:38 / research_intent.py:17 の _ENDPOINT 既定値】
   ∴ RRI の module 自身は 外部へ出ない

★★ただし 外部取得は front door の本線パスに配線されている:
   twoder/submit.py:532  if research_sig["acquisition_needed"]:
   twoder/submit.py:542    _rec("SELECTED_ACQUISITION_METHOD", "WEB_RESEARCH_ACQUISITION")
   twoder/submit.py:546    from twoder import research_acquisition as RA
                           RA.run_research_acquisition(research_sig, …, fetch_issues=True)
   twoder/research_acquisition.py（209行）  from egl import core, acquisition as ACQ, source_policy as SP
   egl/acquisition.py    mk_leg_intent / acquire / run_acquisition / mk_search_result_snapshot /
                         emit_observation_if_eligible / extract_fragment / evaluate_leg_requirement
   egl/adapters.py       fetch_http_static / fetch_github / fetch_github_search / fetch_github_issue /
                         fetch_github_prov / fetch / classify_content   ★実際に外部 HTTP を行う
   起動条件: rri.research_signal が「外部の技術的失敗語」を検出した時のみ
   門: assert_acquisition_before_dw（取得前に DW 実験を started させない）
【分類】①②③（配線済み）
【実走】egl/data_acq_live 12行 ／ data_acq_task 23行 ／ data_sleepmode_acq 7行 ／
        data_sleepmode_claim 22行（全て LIVE）【正規面: /api/ledgers】
        ★ただし ds_events.jsonl（committed）に WEB_RESEARCH_ACQUISITION は ★0件
        【探した範囲: git grep HEAD -- ds_events.jsonl】
        WEB_RESEARCH_ACQUISITION の出現箇所【補助: git grep HEAD】= submit.py ＋ regression 3本
【④実走】△（EGL 側データ台帳に 64行 ／ 本線 ds 記録では 0件）
【⑤機能を満たした実証】⑩UNKNOWN
【人間 / sensor からの取得】⑦未実装（探した範囲: rri の公開関数全数 ／ submit.py の 9 method）
```

**(5) 外部取得結果を証拠として RRI へ戻す経路**
```
submit.py:554  _rec("EGL_SOURCE_REFS", [f["observation_id"] for f in acq["findings"] …])
               → 取得結果の observation_id が実行記録に載る
rri/rri/residual_update.py  「RRI residual/focus update from an EGL admission outcome — return-loop」
               【正規面: module docstring 逐語】
【分類】②（部品は在る）／③④⑤は ⑩UNKNOWN（本線での実走を確認できていない）
```

### 5-3 この資料の前版（2026-08-19 19:2x）の記述に対する訂正

```
前版の記述: 「EGL に取得層が実装済み・実走記録あり・★本線呼び手0」
★訂正    : 「本線呼び手0」は誤り。
            twoder/submit.py:546 が research_acquisition を呼び、それが egl.acquisition を呼ぶ。
            ＝ front door の本線パスに配線されている。
訂正の根拠 : submit.py:532-560 の逐語 ／ research_acquisition.py の import 行
なお さらに前（2026-08-17 以降の台帳・報告・Share の資料3本）の
「外部調査＝口が0件」も誤り。
```

---

## §6 A-5 Test / Bug Discovery

### 6-1 現在持っている物（列挙）【正規面】

| 名前 | 実体 | 何をするか（docstring / 公開関数） | 分類 |
|---|---|---|---|
| sealed / immutable tests | `contract_seal` / `extract_test_names` | 契約に試験を封じる・名前を取り出す | ②③④⑤ |
| failure_memory | `failure_memory.load_records / check / record_hit / recurrence_count / annotate_recurrence` | docstring 逐語「**read-only consult** of distilled failure records」「**NEVER replaces resolved intent / routing**。WARNING_REFERENCE / OPEN_GAP / SENIOR_REVIEW_CANDIDATE / REGRESSION_REFERENCE / BLOCK のみ emit」 | ②③④⑤ |
| 失敗の型 | `twoder/failure_memory.jsonl` 7行 LIVE | 型そのもの（7種） | ②③④ |
| 失敗の再発 | `twoder/failure_recurrence.jsonl` 143行 LIVE | 同一失敗の回数 | ②③④ |
| 過去failure参照 | `recent_failure_for_stage` / `failure_classifier_schema` / `failure_classifier_retry_guard` | 工程別の直近失敗 | ② |
| 資源の事前検査 | `failure_resource_precheck` | 走らせる前に資源を見る | ② |
| AUDIT | `dw/adjudicator`（360行）／`dw/disposition`／`dw/upper_review_gate` | 差分と試験結果を別主体が見る | ①②③④⑤ |
| REGENERATE | `_MAP: READY_FOR_REGENERATE` | 監査で戻ったら再生成 | ①②③④⑤ |
| disposition | `dw/disposition.mechanically_dispositionable` | 所見を機械処分できるか判定 | ②③④⑤ |
| regression | `twoder/regression/*.py` **100本** | 既存の壊れを繰り返さない | ②③④⑤ |
| 監査の見落とし測定 | `sample_for_audit` / `record_blind_audit` / `judge_miss_from_records` / `false_negative_rate` | 盲検で監査の見落とし率を測る（2026-08-18 に5部品・acceptance 5/7） | ②③④ |

**AUDIT が実際に見つけている物【正規面: 2026-08-19 の DISPOSE 比率実測・母数 508 task・引けなかった task 0】**
```
findings 総数 178（findings を持つ task 125）
  test_failure 97(54.5%) ／ scope_expansion 27(15.2%) ／ requirement_not_implemented 25(14.0%) ／
  test_not_load_bearing 9 ／ self_report_primitive 9 ／ dead_guard ／ failure_pattern_recurrence
機械処分可能 97 task(77.6%) ／ judgment-required 28 task(22.4%) ／ 実際に Claude DISPOSE 到達 11回
```

### 6-2 A（与えられたテストを通す能力）と B（未テストの壊れ方を発見する能力）

**A = ②③④⑤（上表のとおり）**

**B = ⑦未実装**

**直接根拠【正規面: 部品自身の docstring 逐語】**
```
twoder/contract_from_plan.py docstring 1行目:
  「実装計画から、契約の文字列を組む。★試験は作らず、渡された物をそのまま使う。」
引数: contract_from_plan(requirement, target_file, test_plan, test_body)
      ★test_body（試験の本文・完全な python source）は ★呼び手が渡す
∴ 封印試験の中身を書いているのは 契約の依頼者（DESIGN = Claude）。機械ではない。
```

**Taka が挙げた連鎖を生成する部品の有無**
```
仕様 → 正常系 → 境界条件 → 異常系 → 過去失敗 → 類似失敗 → 組合せ → 新規テスト候補
【探した範囲 4つ・結果は全て 0】
 ① twoder/ のファイル名（gen*test / test*gen / case / fuzz / property / hypothesis）→ 該当0
    （test_generate_via_runner_spec.py は runner の仕様試験であり生成器ではない）
 ② dev-workcell/dw/ の全13部品名 → 該当0
 ③ egl/docs/*.md 全文の語検索「bug discovery / バグ発見 / テスト生成 / 未知の壊れ / 境界条件」→ 該当文書0
 ④ 正本7本の見出し全数 → 試験生成・欠陥発見を定めた節 0
【補助】contract_from_plan 全153行の語出現:
   「境界」0 ／「異常」0 ／ boundary 0 ／ edge case 0 ／「過去」0 ／ failure 0 ／ error 0 ／ empty 3
```

**【分類】B について: ①旧正本に無い ＋ ⑦未実装（＝設計項目として存在した記録が無い）**

**関連する実測（評価ではなく事実として併記）**
```
2026-08-19: apply_unified_diff V1 は 16試験中12通過。失敗4件は 複数hunk・空入力・末尾改行なし。
            V1 の封印試験にその4件は含まれていなかった。
            【出所: CC_MGR_2026-08-19_APPLY_UNIFIED_DIFF_V2_PASSED.md ほか】
```

---

## §7 A-6 分類表（①〜⑩）

| # | 対象 | ① 旧正本 | ② 実装 | ③ 配線 | ④ 実走 | ⑤ 機能実証 | ⑥ 呼び手0 | ⑦ 未実装 | ⑧ 正式変更 | ⑨ なし崩し疑い | ⑩ UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 経路 段A 機械候補生成 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 2 | 経路 段B Worker 分類 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 3 | 経路 段C 登録 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 4 | 3層分離 STATIC/ROUTE/OBSERVED | ○ | ○ | ○ | ○ | ○ | | | | | |
| 5 | 事実状態のみ出力 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 6 | route_worker 常駐 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 7 | `_use()` 共通口 | ✗ | ○ | ○ | ○ | ○ | | | | | ○(正本外) |
| 8 | 経路: subprocess 取得 | ○ | ✗ | | | | | ○ | | | |
| 9 | 経路: shell 取得 | ○ | ✗ | | | | | ○ | | | |
| 10 | 経路: endpoint(HTTP) 取得 | ○ | ✗ | | | | | ○ | | | |
| 11 | 「観測面の外」を表す欄 | ✗ | ✗ | | | | | ○ | | | ○ |
| 12 | 完成条件の2段化 | ○ | ― | | | | | | ○ | | |
| 13 | 機能表 3つの問い＋「無い」 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 14 | 機能表 票が割れたら確定しない | ○ | ○ | ○ | ○ | ○ | | | | | |
| 15 | 機能表 段3（1件増える） | ○ | ○ | ○ | ○ | ○ | | | | | |
| 16 | `function_index`（機能→部品） | ○ | ○ | ○ | ○ | **✗**(count 0) | | | | | |
| 17 | 機能表 B面（実走/成功/失敗/確認主体） | ✗ | ✗ | | | | | ○ | | | |
| 18 | Manager v0 = 駆動装置 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 19 | GNW 三層 | ○ | ○ | ○ | ○ | ○ | | | ○ | | |
| 20 | D責務9件の分離 | ○ | ○ | ○ | ○ | ○ | | | ○ | | |
| 21 | manager_v0 の 611→787行 | ― | ― | | | | | | | ○ | |
| 22 | General Manager の中身 | ○ | ✗ | | | | | ○ | | | |
| 23 | Domain: DW | ○ | ○ | ○ | ○ | ○ | | | | | |
| 24 | Domain: 経路表 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 25 | Domain: RRI | ○ | ✗ | | | | | ○ | | | |
| 26 | Domain: 2DER(Towder) | ○ | ✗ | | | | | ○ | | | |
| 27 | RRI 内部取得 | ○ | ○ | ○ | ○ | ○ | | | | | |
| 28 | acquisition method 選択（9種） | ○ | ○ | ○ | ○ | ○ | | | | | |
| 29 | **外部取得（Web/GitHub）** | ○ | ○ | **○** | **△** | ― | | | | | ○(⑤) |
| 30 | 外部取得結果を RRI へ戻す | ○ | ○ | ⑩ | ⑩ | ⑩ | | | | | ○ |
| 31 | 人間 / sensor からの取得 | ✗ | ✗ | | | | | ○ | | | |
| 32 | Test A（与えた試験を通す） | ○ | ○ | ○ | ○ | ○ | | | | | |
| 33 | **Test B（未知の壊れ方の発見）** | **✗** | **✗** | | | | | **○** | | | |
| 34 | `autonomous_git` | ○ | ○ | ✗ | ✗ | ― | ○ | | | | ○ |
| 35 | `patch_bridge` | ○ | ○ | ○ | ○ | ○(08-19 10条件) | | | | | |
| 36 | 上申（人へ） | ○ | ○ | ○ | ○ | △(human 22/routed 0) | | | | | ○ |
| 37 | 上申（Claude 上級監査へ） | ○ | ○ | ○ | ○(908回) | ○ | | | | | |

---

## §8 数字

```
【調査した旧仕様 / 正本】                        ★7本
  （正本1 は956行のうち見出し全数＋本文 §0-§14, §16-§17, §20-§26。他6本は全文または主要節）

【現行部品数】                                   ★506（5repo・test_* と regression/ を除く）【補助】
  ds 6 ／ rri 22 ／ egl 174 ／ dev-workcell 55 ／ twoder 249

【他部品から import されている】                 ★170【補助】
【import 経路で辿れない】                        ★336【補助・上限でも下限でもない】

【§7 分類表 37項目の内訳】
  ①旧正本に在る                                 ★31
  ②現在実装が在る                               ★25
  ③本線に配線済み                               ★22
  ④実走済み                                     ★22（うち △1 = 外部取得）
  ⑤本来の機能を満たした実証あり                 ★20（うち △1 = 上申・✗1 = function_index）
  ⑥呼び手0                                      ★1（autonomous_git）
  ⑦未実装                                       ★11
  ⑧正式変更済み                                 ★3（完成条件の2段化 / GNW三層 / D責務分離）
  ⑨なし崩し変更疑い                             ★1（manager_v0 の 611→787行・是正済・正本3 未反映）
  ⑩UNKNOWN                                      ★7

【正本と現在実装の対応が取れない項目】
  正本に在るが実装が無い（①○②✗）             ★6
    subprocess / shell / endpoint の経路取得 ／ General Manager の中身 ／ Domain RRI ／ Domain Towder
  実装が在るが正本に無い（①✗②○）             ★1  `_use()` 共通口
  正本にも実装にも無い（①✗②✗）               ★4
    「観測面の外」を表す欄 ／ 機能表 B面 ／ 人間・sensor からの取得 ／ **Test B（Bug Discovery）**
```

**【この資料自身に含まれる訂正 2件】**
```
訂正1（前版 19:2x → 本版）
  誤: 「EGL Acquisition Layer は 本線呼び手0」
  正: twoder/submit.py:546 が本線パスから research_acquisition を呼び、それが egl.acquisition を呼ぶ
      ＝ ★配線済み。実走は EGL 側データ台帳に 64行／本線 ds 記録には 0件

訂正2（2026-08-17 以降の台帳・報告・/home/takasan/Share の資料3本）
  誤: 「外部を調べる口＝0件」
  正: 上記のとおり配線済み。誤りの原因は探した範囲の書き落とし
      （「外部調査 Worker」という名前で探すと egl/acquisition.py は出ない）
  → Share の3資料は未修正（★本資料の提出後に直す）
```

**評価・優先順位づけは行っていない。この資料はここで閉じる。**
