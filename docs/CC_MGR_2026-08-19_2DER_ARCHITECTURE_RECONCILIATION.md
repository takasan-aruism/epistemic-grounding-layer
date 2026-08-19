開発者規律 確認済(v1.0)

# 2DER 全体構造・旧設計との照合調査

宛: Taka ／ 写: MGR / DESIGN / IMPL ／ **発: 監視（3Claude の外・Taka 直命 2026-08-19 19:2x）**
／ 台帳: **登記しない（★Taka 指示＝本線に介入しない・新ITEM 0）**

**★新規実装 0行 ／ 新規判断規則 0 ／ 新規台帳 0 ／ 既存仕様の書き換え 0 ／ front door への投入 0。**
**★本線（connector 本線接続 → delegated energize → 初回 real-repo）には触れていない。**

**出所の区別（この資料の全記述に適用）**
```
【正本】 = Taka 逐語の仕様書（書き換え禁止の文書）
【正規面】= front door の API ／ 部品自身の公開関数の戻り値 ／ 台帳
【補助】 = 私の import 解析・ファイル走査（★最終事実にしない。正本か正規面で裏づけた物だけを事実として書く）
【UNKNOWN】= どちらでも確定できなかった
```

---

## §0 Executive Summary

**5系統のうち、旧設計と現在実装が大きく食い違っているのは 2系統だけだった。**
**ただしその2つは、これまでの報告で繰り返し誤って伝えられてきた箇所である。**

```
① 経路表システム   ★概ね一致。旧設計の3層(STATIC/ROUTE/OBSERVED)も段A/B/Cも実装されている
② 機能表システム   ★段3の完了条件は満たした。しかし ★期待機能≠実現機能 を表現する構造が無い
③ Manager階層      ★manager_v0 は当初から「駆動装置」。Domain Manager だったことは一度も無い
                   ∴ 8/18 の D責務分離は ★仕様変更ではなく「なし崩しの是正」
④ RRI 外部取得     ★RRI 側は 0。★★ただし EGL に取得層が実装済み・実走記録あり・本線呼び手0
                   ∴ これまでの「外部調査の口が0件」は ★層を取り違えた報告
⑤ Test/Bug Discovery ★★未実装。封印試験は Claude(DESIGN)が書いている
                   `contract_from_plan` は自ら「試験は作らず、渡された物をそのまま使う」と明記
```

**最も重い1点 ―― ⑤。**
商用利用で問題になる「まだテストされていない壊れ方を発見する能力」は、
**旧正本にも現在実装にも存在しない。**設計されたことも無い（§7・探した範囲を明記）。

**次に重い1点 ―― ④の誤報。**
「外部取得の口 0件」は 2026-08-17 以降 複数回 台帳と報告に出ているが、
**EGL `egl/acquisition.py` + `egl/adapters.py` は実装済みで、取得の実走記録が3台帳に残っている。**
正しくは「**RRI の Domain Worker としては未接続／EGL 層には在るが本線呼び手0**」。

---

## §1 旧2DER全体設計（正本から復元）

**読んだ正本 7本（全て `egl/docs/`）:**

| # | 正本 | 日付 | 何を定めるか |
|---|---|---|---|
| 1 | `CC_MGR_2026-08-12_TAKA_ROUTE_AND_FUNCTION_SPEC_v0.1.md`（956行） | 08-12 | **経路・機能管理システム**（＝「経路表システム」の本体） |
| 2 | `CC_MGR_2026-08-14_TAKA_ROUTE_WORKER_VS_MANAGER_SPEC.md` | 08-14 | Route Worker と Manager の**責務境界** |
| 3 | `CC_MGR_2026-08-14_TAKA_NEXT_PHASE_AND_MANAGER_V0_SPEC_v0.1.md` | 08-14 | **Manager v0**（＝駆動装置）の定義と受入 |
| 4 | `CC_DESIGN_2026-08-16_TAKA_GNW_CORRECTION_ORDER.md` | 08-16 | **General → Domain → Worker** 三層への是正 |
| 5 | `TAKA_2026-08-17_DOMAIN_DESIGN_ENGINE_v0.2.md` | 08-17 | Domain Manager の**6責務**・専門Worker・還流 |
| 6 | `RRI_CANONICAL_SPEC_v1_0.md`（v1.1） | 07-28 | RRI の目的・保証する12項目・禁止6項目 |
| 7 | `phase-1b-acquisition-boundary.md` | 07-05 | **外部取得層**（Acquisition Layer / Source Policy） |

**旧設計の骨格（正本 1・4・5 を合わせた形）**

```
人 → front door → ds（記録）→ rri（意図）→ egl（根拠）→ dev-workcell（工程）→ 成果物
                                   ↑
                 経路表システム（何が在り・何と繋がり・実際に通ったか）
                 機能表システム（各部品は何をするか・機能から逆引き）
                                   ↑
        General Manager → Domain Manager（DW / RRI / 経路表 / 2DER）→ Worker
```

**正本1 §22 が定める「完成後に答えられる問い」（＝全体設計の到達点）**
```
部品起点: 「この部品は何をするものか」   Component → Function
機能起点: 「登記機能はどこにあるか」     Function  → Component
```

---

## §2 現在実装されている階層

**【正規面】常駐（systemd user unit・3つ）**
```
twoder-webui.service        front door :8770（受け口15）
twoder-manager.service      manager_v0（General 位置・駆動）
twoder-route-worker.service route_worker（経路表の育成）
```

**【正規面/補助】部品数（`test_*` と `regression/` を除く）**

| 箱 | 部品 | 他から読まれている | 読まれていない |
|---|---|---|---|
| ds | 6 | 2 | 4 |
| rri | 22 | 15 | 7 |
| egl | 174 | 37 | 137 |
| dev-workcell | 55 | 23 | 32 |
| twoder | 249 | 93 | 156 |
| **計** | **506** | **170** | **336** |

**★「読まれていない336」を「不要336」と読まない。**
2026-08-18 の実測では、twoder の非import 138本のうち **127本は台帳・文書・CLI に名前が出る**（＝別経路で使われる）。
**この336は「import 経路で辿れない数」であって、死んでいる数ではない。**【補助・上限でも下限でもない】

---

## §3 経路表システム

### 3-1 旧設計（正本1・正本2）

```
正本1 §2.3 3層分離
   STATIC_EDGE   コード上に接続が在る（機械が確定）
   ROUTE_EDGE    そのうち処理経路として意味を持つ（Worker LLM が分類）
   OBSERVED_EDGE 実行時に実際に通った（実行記録が確定）
正本1 §3 段A（機械が候補生成・LLM 0）→ 段B（Worker が限定メニューで分類）→ 段C（登録）
正本1 §2.1 Manager は探索しない ／ §2.2 Worker に自由探索させない ／ §2.4 Worker は存在を発明しない
正本2 §4 出力は事実状態に限定（OBSERVED_BOTH_SIDES / SENDER_ONLY / RECEIVER_ONLY /
        PASSABLE / NOT_PASSABLE / NO_RECORD / UNKNOWN）★PASSABLE ≠ CORRECT
正本2 §3 Route Worker が判断してはいけない5項目（期待機能か・結果は正しいか・必要か・連動・全体整合）
```

**★確認事項1「経路表Worker / Domain Manager に相当する設計が存在したか」→ 存在した。**
正本2 が Route Worker と Manager を**一文定義**で分けている（逐語）:
> Route Worker = 実際に何がどこからどこへ通ったかを、証拠付きで観測・更新する機構。
> Manager = 実際に行ったことと本来行うべきことを比較し、次に何をすべきかを決める機構。

**★確認事項2「内部で自動観測できる経路／内部観測では取得できない経路の両方を扱う構想が正本に在るか」**
→ **部分的に在る。**正本1 §2.3 は STATIC（観測に依らない）と OBSERVED（実行観測）を分けており、
「コード上に在るが通っていない」は表現できる。
**しかし「2DER の観測面の外に在る経路」という概念は、正本1・2 のいずれにも見当たらなかった。**
（探した範囲＝正本1 全956行の見出しと §2/§3/§5/§11、正本2 全文）→ **UNKNOWN 寄りの「無い」**

### 3-2 現在実装（【正規面】`route_adopt.route_table_view()` の戻り値）

```
total 225 ／ by_origin {hand: 18, machine: 207}
columns:
  exists                    243   鍵=v2の静的候補（名前ごとに1件・自己/試験/docs を除外）走査 1,140箇所・LLM 0
  observed                   68   鍵=送信側(handed_to)と受信側(received_from)の両方が在る対だけ／未登録 50
  exists_not_observed   233/243   鍵=相手の名前が実行の辺に一度も出ない
  exists_and_seen_by_name    10   鍵=名前が実行の辺に出ただけ ★『繋がった』ではない
```

**★確認事項3「現在の部品は旧設計のどこを実装しているか」**

| 旧設計 | 現在の部品【正規面で確認】 | 判定 |
|---|---|---|
| 段A 機械候補生成 | `route_candidates_v2.candidates_v2` / `segment_candidates` / `callee_candidates` | **一致** |
| 段B Worker 分類 | `route_edge_vote.run_once/list_votes`（model・prompt_version・input_hash・seed別 votes を保持） | **一致** |
| 段C 登録 | `route_adopt.adopt/revoke/adopted_rows/route_table_view` | **一致** |
| STATIC_EDGE | `columns.exists`（243） | **一致** |
| ROUTE_EDGE | `machine` 行の `kind`（from import 約150 / import 6） | **一致** |
| OBSERVED_EDGE | `columns.observed`（68）＝`observed_both_sides` | **一致** |
| 事実状態のみ出力 | `by_status`（linked / no_send / no_receive / no_locator / split_run / not_expected） | **一致** |
| 常駐で自動更新 | `twoder-route-worker.service`（active） | **一致** |
| `_use()` | GM が台帳を引く時の**共通の口**（2026-08-19 に付け替え） | **旧設計に無い・追加** |

**★確認事項4「現在取得できる経路の情報源を全列挙」【正規面】**
```
① 静的 import / from import                → columns.exists（走査 1,140箇所）
② 実行の辺（handed_to / received_from）    → columns.observed（両側そろいのみ 68）
③ 名前一致（末尾・小文字）                 → exists_and_seen_by_name（10・★証拠として弱い）
④ 人の手書き 18区間                        → route_table.ROUTE（S01〜S18）
⑤ Worker の票                              → route_edge_vote.list_votes（seed別・input_hash つき）
```

**★確認事項5「現在取得できない経路の種類」**
```
(a) subprocess / shell 経由の呼び出し   ―― 正本1 §5.2 が抽出対象に挙げているが、
                                          columns の鍵は import と実行の辺のみ → ★未実装
(b) HTTP 経由（front door を叩く側）    ―― 同上 → ★未実装
(c) 動的 import / importlib             ―― 同上 → ★未実装
(d) 台帳ファイル経由の受け渡し           ―― 「口」ではなく「置き場」共有 → 経路として表現されない
(e) 人が手で運ぶ経路（Claude の中継）    ―― 記録に残らない → ★観測面の外
```
**探した範囲: `route_table_view().columns` の4鍵と `route_candidates_v2` の公開関数名。**
**(a)〜(c) は正本1 §5.2 に「最低限 機械的に取得する」と書かれた対象に含まれる ∴ ★旧仕様に対する未実装。**

**★確認事項6「『経路が存在しない』と『2DERの観測面から見えない』を機械的に区別できるか」**
→ **★部分的にできる。**
```
区別できる: 「コードに在るが実行で見ていない」 = exists_not_observed（233/243）★これは明示されている
区別できない: 「そもそもコードにも実行にも無い」 と 「上記(a)〜(e)で観測面の外に在る」
             ―― どちらも同じ「表に載らない」として扱われ、両者を分ける欄が無い
```
**∴ 正本2 §12「『見つからなかった』と『存在しない』を同一視しない」は、★経路表の粒度では未達。**
（ただし §17「材料完全性」の考えは `completion_from_materials` 側で `NOT_INSPECTED` として実装されている＝**別系統では実現済み**）

### 3-3 分類

| 区分 | 件 |
|---|---|
| **一致** | 段A / 段B / 段C / 3層分離 / 事実状態のみ / 常駐更新 / 票の保存形式（8件） |
| **正式変更** | 完成条件を Route System と Manager 統合の2段に分けた（正本2 追補・Taka 自身が実施） |
| **未実装** | subprocess / HTTP / 動的import の経路取得（正本1 §5.2）／「観測面の外」を表す欄 |
| **現在案の方が合理的** | `_use()` の共通口化（正本に無いが、正本1 §15 の性能要件＝「聞かれた問いだけ計算」と同じ向き） |

---

## §4 機能表システム

### 4-1 旧設計（正本1 §4.3 / §7 / §10 / §17 / §22）

```
Function は Component / Edge / Evidence と並ぶ独立概念（§4）
Function 名は ★既存一覧から選ぶ。Worker が創作しない（§4.3 / §10.1）
問いは3つ（§7）: ①この接続は経路か ②この部品は何をする所か ③この機能は既に在るか
必ず「一覧に無い」「判断できない」「近い物は無い」を選択肢に置く（§2.5 / §21.2）
票が割れたら確定しない（§9）
新規Function候補 → ★既存の承認経路で正式登録（§10.3）／新しい承認システムを作らない
段3 の終了条件（§16）= ★Function一覧が実際に1件増え、追加主体・承認根拠を front door から確認できる
```

### 4-2 現在実装（【正規面】`function_table.function_table_view()`）

```
records      170（5走行: 30/30/30/73/7）
list          9語（受信・検証・分類・登記・配送・監査・実行・rollback・確認）
by_origin    {hand: 8, machine: 1}
by_origin_note ★「hand の8語は module の定数＝記録から来ていない（実績と読まない）」
not_in_list  ルーティング / 停止管理 / 処理 / 判断 …（held つき）
near_names   [処理↔投票処理] [取得↔研究取得] [状態確認↔確認] [研究↔研究取得]
funnel       per_run に asked / any_not_in_list_vote / unanimous_not_in_list /
             name_captured / duplicate_of_existing
undecided    NOT_DECIDED の票を reason つきで保持
index_lookups {verify:57, human:0, machine:19} ＋ ★_key に「呼び手側が変えられる値 ∴ 証拠にしない」
```

**★段3 の終了条件は満たしている**（machine=1・2026-08-19 02:38・新規実装0行）。
**★ただし正本 §16 が求める「追加主体・承認根拠を front door から確認できる」は、
`list` の行に `registered_by` / `registered_at` / `from_component` の欄として在る**（hand の8語は全て null）。

### 4-3 Taka の指定：A（期待機能）と B（実現機能）の二面

**★結論：現在の機能表は B を表現できない。**

| 問い | 現在の構造で保持できるか | 根拠【正規面】 |
|---|---|---|
| A. 設計上 何をするために作られたか | **△** | `list` の名前＋`components` の sends/returns。ただし**契約の requirement 文とは結ばれていない** |
| B. 実際には何として機能したか | **✗** | 機能表に**実走結果を持つ欄が無い**。records は「Workerが何と答えたか」の記録であって実走ではない |
| 機能名を誰が付けるか | **○** | `origin`(hand/machine) ＋ `registered_by` |
| 本当にその機能だったと誰が確認するか | **✗** | 確認主体の欄が無い |
| 実走回数 | **✗** | 機能表には無い（task 側の `generation.per_attempt` には在る＝**別台帳**） |
| 成功条件 / 失敗条件 | **✗** | 機能表には無い（契約の `expected` / `prohibited` に在る＝**別文書**） |
| 未確認 | **○** | `undecided` ＋ `not_in_list.held` |

**★Taka の例（`apply_unified_diff` V1 は設計上「unified diff 適用」だが実走 16試験中12通過）を
機能表に載せる欄は 現在1つも無い。**
V1 の失敗は **契約文書と task 記録**に残っており、機能表からは引けない。

**∴ 現在の機能表は「Function 名の一覧」であって「機能表」ではない。**
正本 §22 の2問（部品→機能／機能→部品）のうち、**機能→部品は `function_index` が在るが実データが 0〜1件**
（【正規面】`function_index("登記","machine")` = `{in_list: true, components: [], count: 0}`）。

### 4-4 分類

| 区分 | 中身 |
|---|---|
| **一致** | 3つの問い／「一覧に無い」等の選択肢／票の保存／割れたら確定しない／既存承認を使う（5件） |
| **未実装** | 実走結果・成功失敗条件・確認主体・実走回数を機能に結ぶ欄（＝B 面まるごと） |
| **なし崩し疑い** | **無い**（段3 は宣言どおり1件で止めており、拡大していない） |

---

## §5 Manager / Domain / Worker 階層

### 5-1 旧設計

**正本3（08-14）― Manager v0 の定義（逐語）**
> Manager v0 は**知的な上司ではなく、台帳を見て既存の運行規則どおりにシステムを進める駆動装置**とする。

**正本3 §2.3 Manager v0 が判断しないもの**：設計の良し悪し／コードの内容／戦略的優先順位／権限境界の変更／不可逆な変更の承認／未知の例外への創作的対処

**正本4（08-16 GNW 是正指示・逐語）**
> 現在の manager_v0 を中心とした構成を、**単一Managerの高機能化として進めないこと**。
> General Manager → Domain Managers → Workers の三層構造である。
> **General ManagerがDomain固有処理を持ち始めた場合、それを「便利だから追加」とせず、職責越境として検出できるようにする。**

**正本5 §16 Domain Manager の6責務**
(1)勘定科目分類 (2)必須材料集合と必要Worker決定 (3)Worker起動 (4)結果統合 (5)不足・衝突・未知の判定 (6)Domain設計・Contract群・Work Unitへの変換

### 5-2 Taka の問い：manager_v0 は当初の Domain Manager と同じものか

**★答え：違う。manager_v0 は最初から「Execution Manager / 駆動装置」として定義されている。**

```
08-14 正本3   manager_v0 = 駆動装置（判断しないもの6項目を明示）
              ★この時点で GNW（General/Domain/Worker）という語は正本に無い
08-16 正本4   Taka が GNW 三層を提示。「General Manager は存在しない」と明言
              ∴ ★manager_v0 は「General の位置に座っている駆動装置」という状態になった
08-18 05:03  D責務9件を domain_dw へ分離（787行/21機能 → 364行/16機能 ＋ 468行/9機能）
```

**∴ 役割が「Domain Manager → Execution Manager」へ変化したのではない。**
**逆で、「駆動装置として定義された物に、Domain の仕事が後から溜まった」。**
**8/18 の分離は仕様変更ではなく ★正本3・正本4 への復帰（是正）である。**

**★では「なし崩しに変わった」のはどこか ―― 溜まった側。**
正本4（08-16 03:0x）の後、manager_v0 は 611行/18機能 → 787行/21機能 まで増えた。
増えた機能（契約投入・受領・名前検査・成果物配置・commit・保留処理）は
**8/18 の分類で D 判定 9件のうちに含まれている**【正規面: 台帳 EVO-0073 の分類結果】。
**∴ 正本4 が禁じた「単一Managerの高機能化」が 2日間 進行し、その後 自ら是正された。**
**★これは台帳に記録されている（＝隠れていない）が、正本3 の Manager v0 定義文には反映されていない。**

### 5-3 現在の階層【正規面】

```
General   twoder/manager_v0.py    650行 / 20関数
          tick / _machine_turn / _queue* / _last_task / whose_turn / item_state / to_domain /
          set_current_task / main ＋ D への入口4つ（6行前後の委譲）
Domain    twoder/domain_dw.py     700行 / 11関数（DW ドメイン）
          contract_with_precheck / precheck_names / submit_next_contract / receive_finished /
          record_stages / _place_and_commit / _contract_docs / _submitted_shas / _append_index
Domain    twoder/route_worker.py  297行（経路表ドメイン・常駐）
Worker    dev-workcell/dw/_MAP 9状態
          CODING_WORKER / INDEPENDENT_AUDITOR / MANAGER / BUILD_PLANNER / CLAUDE_SENIOR
```

**★RRI Domain Manager / 2DER(Towder) Domain Manager は ★存在しない。**
（探した範囲: systemd user unit 3つ・`twoder/*.py` のうち `domain_` 接頭辞・正本4 §3 の母集団）

### 5-4 分類

| 区分 | 中身 |
|---|---|
| **一致** | Manager v0 = 駆動装置（現在の General の tick/queue/whose_turn はこの定義の範囲） |
| **正式変更** | GNW 三層の導入（08-16・Taka 自身の是正指示）／D責務の分離（08-18・是正指示に基づく） |
| **なし崩し疑い** | ★08-16〜08-18 の 611→787行（D の仕事が General に溜まった）。**台帳には残るが正本3 未反映** |
| **未実装** | RRI Domain Manager ／ Towder Domain Manager ／ **General Manager の中身**（現在 Claude が代行） |

---

## §6 RRI 外部情報取得

### 6-1 旧設計

**正本6（RRI 正典 v1.1・Taka 逐語）**
> 本来、雑なユーザの意図を元に、それを具体的内容に落としつつ、**外部内部の情報を利用して**ユーザの目的そのものも具体化させ…

**正本6 §3 禁止事項**：生の依頼文をそのまま DW へ渡さない／台帳の直接参照で不足を補わない／
4軸を生成せずに直感で7戦略を選ばない／根拠を保存せず次工程へ進めない／
**不足情報を暗黙に補完しない**／RRI を単なるルーターとして実装しない

**正本7（Phase 1b 取得境界）**：Acquisition Layer（adapter 方式）／Source Policy／LegIntent／
`required_source_kind`（要求）と `observed_source_kind`（観測）の分離／
`transport_status` と `content_status` の分離（200 でも challenge / auth wall / empty を弾く）

### 6-2 現在実装

**A. RRI 側の内部取得【正規面: 各 module の公開関数】**
```
request/thread 管理  rri.request_thread   open_thread / raise_question / annotate_question
preflight            rri.preflight_gate   detect / next_legal_operation / hold_facts / is_suppressed
意図の解決           rri.intent_strategy  surface_signals / build_facts / resolve / resolve_consensus
依頼種別             rri.request_type     classify_request_type
実在確認             rri.existence_grounding  build_queries / claim_status / document_frequency / check_existence
調査意図             rri.research_intent  classify_blockage / need_validation / form_resolution_requirements
```

**B. RRI 側の外部取得 → ★0**
`rri/rri/*.py` の HTTP 呼び出しは **全て `localhost:8005`（ローカル vLLM）**。
【補助＋正規面: `intent_strategy.py:38` `research_intent.py:17` の `_ENDPOINT` 既定値】
**∴ RRI に Web / API / 外部文書 / 人間 / sensor を取りに行く口は無い。**

**C. ★ただし EGL には取得層が実装されている**【正規面: module の公開関数】
```
egl/acquisition.py  mk_leg_intent / acquire / run_acquisition / mk_search_result_snapshot /
                    emit_observation_if_eligible / extract_fragment / evaluate_leg_requirement
egl/adapters.py     fetch_http_static / fetch_github / fetch_github_search / fetch_github_issue /
                    fetch_github_prov / fetch / classify_content   ★外部HTTPを実際に行う
egl/source_policy.py  Source Policy（正本7 §3）
```
**実走記録【正規面: /api/ledgers】**
```
egl/data_acq_live/events.jsonl       12行  LIVE
egl/data_acq_task/events.jsonl       23行  LIVE
egl/data_sleepmode_acq/events.jsonl   7行  LIVE
egl/ENERGIZATION_LEDGER.jsonl         2行  ★ORPHAN（書き手が居ない）
```
**本線の呼び手【補助: import 解析】= 0**
（呼んでいるのは `test_acquisition.py` / `test_admission.py` / `test_etb.py` / `demo_acquisition_*.py` のみ）

### 6-3 ★これまでの報告の訂正

```
これまでの記載（台帳・報告・私の資料3本）: 「外部調査＝口が0件。5repo の .py を全部検索して確認」
★正しくは                              : 「RRI の Domain Worker としては 未接続（0）」
                                          「EGL 層には ★実装済み・実走記録あり・★本線呼び手0」
```
**誤りの原因は 探した範囲の書き落とし。**「外部調査 Worker」という名前で探すと EGL の `acquisition` は出ない。
**★これは「無いと書く前に探した範囲を書く」の失敗例そのものである（私自身も 3本の資料で同じ誤りを配った）。**

### 6-4 分類

| 区分 | 中身 |
|---|---|
| **一致** | RRI の内部取得（thread / preflight / 意図解決 / 実在確認）は正本6 §2 の方向で実装 |
| **存在するが呼び手0** | **EGL Acquisition Layer 一式**（adapters / source_policy / LegIntent） |
| **未実装** | 外部取得結果を**証拠として RRI へ戻す経路**（正本6 が求める「暗黙にやらず根拠を残す」の後段） |
| **UNKNOWN** | 正本上、外部取得の**主体が RRI か EGL か**が明示されていない（正本6 は「RRI の仕事の一部」、正本7 は EGL の層として定義） |

---

## §7 Test / Bug Discovery（★独立項目）

### 7-1 現在持っている物【正規面: module の公開関数 ／ ファイル数】

| 名前 | 実体 | 何をするか |
|---|---|---|
| 封印試験 | `contract_seal` / `extract_test_names` | 契約に試験を封じ、名前を取り出す |
| 過去失敗の照合 | `failure_memory.check / record_hit / recurrence_count` | **読むだけ**（docstring 逐語: `read-only consult`・`NEVER replaces resolved intent / routing`） |
| 失敗の再発 | `failure_recurrence.jsonl`（143行・LIVE） | 同じ失敗の回数 |
| 失敗の型 | `failure_memory.jsonl`（7行・LIVE） | 型そのもの（★7種） |
| 資源の事前検査 | `failure_resource_precheck` | 走らせる前に資源を見る |
| 監査 | `dw/adjudicator`（360行）/ `dw/disposition` / `dw/upper_review_gate` | 差分と試験結果を別主体が見る |
| やり直し | `_MAP: READY_FOR_REGENERATE` | 監査で戻ったら再生成 |
| 非回帰 | `twoder/regression/*.py` **100本** | 既存の壊れを繰り返さない |
| 盲検の監査 | `sample_for_audit` / `record_blind_audit` / `judge_miss_from_records` / `false_negative_rate` | 監査の見落とし率を測る（2026-08-18 に5部品） |

### 7-2 A（与えられたテストを通す能力）と B（未知の壊れ方を発見する能力）

**★A = 在る。★B = 無い。**

**Bが無いことの直接証拠【正規面: 部品自身の docstring 逐語】**
```
twoder/contract_from_plan.py の docstring 1行目:
  「実装計画から、契約の文字列を組む。★試験は作らず、渡された物をそのまま使う。」
```
**∴ 封印試験の中身を書いているのは 契約の依頼者＝Claude(DESIGN)。機械ではない。**

**さらに、試験生成に関わる語が `contract_from_plan` の全153行に 1つも無い**【補助】:
```
「境界」0 ／「異常」0 ／ boundary 0 ／ edge case 0 ／「過去」0 ／ failure 0 ／ error 0
```

**Taka が挙げた連鎖（仕様 → 正常系 → 境界条件 → 異常系 → 過去失敗 → 類似失敗 → 組合せ → 新規テスト候補）**
**を機械的または LLM で生成する部品は、探した範囲に存在しない。**
```
探した範囲:
  ① twoder/ のファイル名（gen*test / test*gen / case / fuzz / property / hypothesis）→ 該当 0
     （`test_generate_via_runner_spec.py` は runner の仕様試験であって生成器ではない）
  ② dev-workcell/dw/ の全13部品 → 試験生成に当たる物 0
  ③ egl/docs/*.md 全文の "bug discovery|バグ発見|テスト生成|未知の壊れ|境界条件" → ★該当文書 0
  ④ 正本1〜7 の見出し → 試験生成／欠陥発見を定めた節 0
```

**★∴ TEST / BUG DISCOVERY 能力は 未実装であり、旧正本でも設計されていない。**
**これは「実装が遅れている」ではなく「設計項目として存在したことが無い」。**

### 7-3 なぜ「AUDIT が在るから bug discovery も在る」と読んではいけないか

【正規面: 2026-08-18 の DISPOSE 比率実測・母数 508 task・取りこぼし0】
```
findings 総数 178（findings を持つ task 125）
category 別: test_failure 97(54.5%) / scope_expansion 27 / requirement_not_implemented 25 /
             test_not_load_bearing 9 / self_report_primitive 9 …
```
**AUDIT が見つけているのは「与えた試験が落ちた」「頼んでいない物を作った」「試験が実質何も支えていない」。**
**＝ 与えられた仕様と差分の突き合わせであって、★未知の入力で壊れる所を探してはいない。**

**★商用化条件として残す:**
```
現在: 契約に書かれた試験を通す ＝ A
不足: 契約に書かれていない壊れ方を見つける ＝ B
     （境界値・空入力・型違反・複数hunk・末尾改行・組合せ・過去失敗からの類推）
     ★2026-08-19 の apply_unified_diff V1 が 16試験中12通過で落ちた4件は、
       まさに B の領域（複数hunk・空入力・末尾改行なし）であり、
       ★V1 を書いた時点では誰も その4件を試験に入れていなかった。
```

---

## §8 旧仕様 → 現在実装の差分表

| # | 系統 | 旧正本 | 現在 | 判定 |
|---|---|---|---|---|
| 1 | 経路 | 3層分離(STATIC/ROUTE/OBSERVED) | columns 4鍵で実装 | 一致 |
| 2 | 経路 | 段A 機械候補生成・LLM 0 | `route_candidates_v2` | 一致 |
| 3 | 経路 | 段B Worker 限定メニュー分類 | `route_edge_vote`（seed別票・input_hash） | 一致 |
| 4 | 経路 | 段C 登録主体は Manager か 2DER 本体 | `route_adopt` ＋ 常駐 route_worker | 一致 |
| 5 | 経路 | 事実状態のみ出力・PASSABLE≠CORRECT | `by_status` 6語 | 一致 |
| 6 | 経路 | §5.2 subprocess / shell / endpoint も抽出 | import と実行の辺のみ | **未実装** |
| 7 | 経路 | 「見つからない」と「存在しない」を分ける | 経路表の粒度では分かれていない | **未実装** |
| 8 | 経路 | 完成条件を2段に分ける | 分けた（正本2 追補） | 正式変更 |
| 9 | 機能 | 3つの問い＋「無い」選択肢 | 実装済（`not_in_list` / `undecided`） | 一致 |
| 10 | 機能 | 票が割れたら確定しない | `undecided` に reason つきで保持 | 一致 |
| 11 | 機能 | 段3 = 一覧が1件増える | machine=1（08-19 02:38） | 一致 |
| 12 | 機能 | ―（正本に規定なし） | **実走結果・成功失敗条件・確認主体の欄が無い** | **未実装**（正本にも無い） |
| 13 | Manager | v0 = 駆動装置・判断しない6項目 | tick/queue/whose_turn/item_state | 一致 |
| 14 | Manager | GNW 三層 | G(650行) / D(700行+297行) / W(9状態) | 正式変更 |
| 15 | Manager | 単一Managerを高機能化しない | 08-16→08-18 に 611→787行へ肥大 → 是正 | **なし崩し疑い（是正済・正本未反映）** |
| 16 | Manager | Domain = DW / RRI / 経路表 / Towder | DW と 経路表 のみ | **未実装**（RRI / Towder） |
| 17 | Manager | General Manager | **中身は Claude が代行** | **未実装** |
| 18 | RRI | 外部内部の情報を利用 | 内部○ / 外部✗（RRI 側） | **未実装** |
| 19 | RRI | 取得層(adapter/Source Policy/LegIntent) | **EGL に実装済** | **存在するが呼び手0** |
| 20 | RRI | 外部取得結果を証拠として戻す | 経路なし | **未実装** |
| 21 | Test | ―（正本に規定なし） | A のみ／B は無い | **未実装（設計もされていない）** |
| 22 | 全体 | §22 部品→機能 / 機能→部品 | `function_index` は在るが実データ 0〜1件 | **部分** |

---

## §9 存在 / 配線 / 実走 / 機能成立 の4段階表

**★この4つを混同しない。**

| 対象 | ①存在 | ②配線 | ③実走 | ④本来の機能を満たす | 根拠 |
|---|---|---|---|---|---|
| 経路表 段A/B/C | ○ | ○ | ○ | ○ | route_table_view 225行・68 observed |
| route_worker 常駐 | ○ | ○ | ○ | ○ | systemd active・machine 207 |
| 機能表 一覧 | ○ | ○ | ○ | **△** | machine=1 のみ。B面の欄が無い |
| `function_index` | ○ | ○ | ○ | **✗** | `count: 0`（引ける実データが無い） |
| manager_v0（General） | ○ | ○ | ○ | **△** | 駆動は満たす／全体判断は Claude 代行 |
| domain_dw（Domain） | ○ | ○ | ○ | ○ | 08-18 分離後 自走で 2件 COMPLETE |
| RRI 内部取得 | ○ | ○ | ○ | ○ | preflight/意図解決は本線で動作 |
| **EGL Acquisition Layer** | **○** | **✗** | **○（試験・demo のみ）** | **UNKNOWN** | 呼び手0／実走記録は3台帳に在る |
| `patch_bridge` | ○ | ○（08-19） | ○ | ○（08-19 10条件成立） | 08-19 に `_apply_to_working` 修正で成立 |
| `autonomous_git` | ○ | **✗** | ✗ | UNKNOWN | 既定 False・本番呼び手0（08-14 実測） |
| **Test/Bug Discovery(B)** | **✗** | ― | ― | ― | 探した範囲4つで該当0 |
| 上申（人へ） | ○ | ○ | ○ | **△** | 08-17 human 22 / routed 0 |
| 上申（Claude上級監査へ） | ○ | ○ | ○ | ○ | UPPER_REVIEW 908回 |
| 台帳 55冊 | ○ | ― | LIVE 22 | ― | ORPHAN 11 / IDLE 11 / REPLICA 9 |

---

## §10 正本へ反映が必要な変更

**★私は反映しない（Taka 指示・調査のみ）。反映が要る差分だけを挙げる。**

```
① 正本3（Manager v0）へ:
   GNW 三層の導入により manager_v0 は「General 位置の駆動装置」になった。
   08-18 に D責務9件を domain_dw へ分離した事実を、定義文の側に反映する必要がある。
   ★現状、正本3 を読むと「manager_v0 が全部やる」ように読める。

② 正本1（経路・機能仕様）へ:
   §5.2 が挙げる抽出対象のうち subprocess / shell / endpoint / repo間参照 は未実装。
   「当面 import と実行の辺のみ」と現状を書くか、未実装として残すかの判断が要る。

③ 正本1 §22 へ:
   「機能→部品」は口が在るが実データ 0〜1件。完成条件に ★件数の下限を書く必要がある
   （現状の段3 終了条件「1件増える」は 2026-08-19 に満たされ、以後の成長条件が無い）。

④ 機能表（正本に節が無い）へ:
   ★期待機能（EXPECTED）と実現機能（REALIZED）の二面が、正本のどこにも規定されていない。
   Taka の今回の指示が初出。正本へ節を足すか、別正本を立てるかの判断が要る。

⑤ RRI 正本6 と EGL 正本7 の境界:
   外部取得の主体が RRI か EGL か、正本間で明示されていない（§6-4 UNKNOWN）。

⑥ Test / Bug Discovery:
   ★正本が存在しない。商用化条件として節を立てるかどうかの判断が要る。
```

---

## §11 Repo自己更新 完了後の残課題

**（★今回の本線＝connector / delegated energize / 初回 real-repo が終わった後に残る物）**

```
① General Manager の中身（現在 Claude 代行）
② RRI Domain Manager ／ Towder Domain Manager（母集団4のうち2つが不在）
③ 機能表の B面（実走・成功失敗条件・確認主体・実走回数）
④ EGL Acquisition Layer の本線接続（在るが呼び手0）＋ 結果を RRI へ戻す経路
⑤ ★TEST / BUG DISCOVERY（B）―― 設計から
⑥ 経路の観測面の拡張（subprocess / HTTP / 動的import）
⑦ 「観測面の外」を表す欄（存在しない と 見えない の区別）
⑧ 並列実行（正本5 §15・現在は直列維持・Taka 保留）
```

---

## §12 数字での報告

```
調べた旧仕様 / 正本            ★7本
  （正本1 は956行のうち §0-§22 の主要節、他6本は全文または主要節）

現行部品数                     ★506（5repo・test_* と regression/ を除く）
  内訳 ds 6 ／ rri 22 ／ egl 174 ／ dev-workcell 55 ／ twoder 249

配線済み（他部品から読まれている）★170
呼び手0（import 経路で辿れない） ★336
  ※★「不要336」ではない。08-18 実測では twoder の非import 138 のうち 127 は
    台帳・文書・CLI に名前が出る。この336は上限でも下限でもない【補助】

§8 差分表 22項目の分類
  旧仕様と一致                 ★9
  正式に変更済み               ★3   （完成条件の2段化 / GNW 三層 / D責務分離）
  なし崩し変更の疑い           ★1   （manager_v0 の 611→787行・★是正済だが正本未反映）
  未実装                       ★8   （経路の抽出対象3種 / 観測面の外の欄 / 機能表B面 /
                                      RRI外部取得 / 戻す経路 / RRI・Towder の Domain /
                                      General の中身 / Test-Bug Discovery）
  存在するが呼び手0            ★1   （EGL Acquisition Layer）
  UNKNOWN                      ★2   （外部取得の主体が RRI か EGL か ／
                                      「観測面の外に在る経路」という概念が正本に在るか）
```

**★訂正1件（この調査で判明・私が配った資料3本すべてに入っている誤り）**
```
誤: 「外部を調べる口＝0件。5repo の .py を全部検索して確認」
正: 「RRI の Domain Worker としては未接続（0）／
     ★EGL に Acquisition Layer が実装済み・実走記録3台帳・本線呼び手0」
→ /home/takasan/Share の3資料も この訂正が要る（★本資料の提出後に直す）
```

**ここで停止する。**（実装・設計変更・ITEM 起票・front door への投入は行っていない）
