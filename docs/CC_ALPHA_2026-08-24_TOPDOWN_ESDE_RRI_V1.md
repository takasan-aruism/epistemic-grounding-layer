# 2DER ESDE Top-Down Knowledge Architecture / RRI Integration V1

- 素案: Taka（GPT案 v0.1・2026-08-24）
- V1: CC_ALPHA(監視) 2026-08-24 —— **Phase 1 全件調査を実施し、素案を実測で書き換えたもの**
- 親: 新規 item（EVO-0099 とは別。ESDE Domain の **Top-Down 側**）
- 上位正本: `TAKA_2026-08-24_GDW_OPERATION_DESIGN_v0.1.md`(ART-da5a15e434) /
  `CC_ALPHA_2026-08-24_GDW_THREE_RULINGS_SPEC_v0.1.md`(ART-7308ecee62)

---

# 0. V1 の結論を先に —— 素案の前提が1つ大きく違う

素案は「Top-Down ESDE を**作る**」という前提で書かれている。
**全件調査の結果、素案が求める機構の大半は既に実装されていた。そして本線から呼ばれていない。**

| 素案の節 | 素案の想定 | **実測** |
|---|---|---|
| §6 Source Authority「語彙を新設する前に既存語を全件調査する」 | 新設候補9語 | ★**既存 `SOURCE_KINDS` 14語で全部表現できる**（下表） |
| §4 Source / Authority | 新規に持たせる | ★**在る** —— `ENTITY_REGISTRY`（host/path → entity + source_kind） |
| §6「RRIがどのsourceを先に探すべきか」 | 決められるようにする | ★**在る** —— `preferred_classes` 7 / `supplementary_classes` 3 / `discovery_classes` 4 |
| §22 RRI Search Planning「検索PLANを持つ」 | 将来型 | ★**在る** —— `egl/egl/pipeline.py:79` が `SPLAN` を発行・:174 で更新 |
| §10-11 knowledge routing | 将来型 | ★**内部側は在る** —— `QUERY_CLASS_DOMAINS`（query class → 必須 domain・**versioned**） |
| §21 「LLMが分類→そのまま正本にしない」 | 理想 | ★**規則として実装済** —— 逐語「LLM は confirm/downgrade/unresolved のみ、**elevate 不可**」 |
| §5「本文を全保存しない」 | 基本原則 | ★**実装済** —— `extract_fragment` / `content_hash`（fragment 単位） |
| §7 Version | 持つ | ★**無い** —— `version_scope` / `source_version` は **grep 0件** |
| §8 Freshness | 重要責務 | ★**無い** —— 知識の寿命の欄は **0件**（`stale` の既存 hit は経路表の話で別物） |
| §15-16 Retention / cache | 概念 | ★**無い** —— 知識キャッシュは 0件 |
| §22 external canonical first | 前提 | ★**探せない** —— `discovery_classes` は宣言だけで**アダプタ0件** |

★★そして最大の1件:

**この機構全体が本線から呼ばれていない。**
`egl/egl/acquisition.py` / `pipeline.py` の呼び手は **demo / test / experiments / `egl/autonomy` だけ**。
**`twoder/` からの呼び手は 0件**（front door・`manager_v0`・全 Domain Manager を grep 実測）。
`egl/autonomy` に常駐サービスも無い（`systemctl --user` 実測 0件）。

∴ **V1 の Phase 2 は「Knowledge Map を作る」ではなく「在るものを本線へ繋ぐ」。**

## 0.1 ★「在る」だけでなく「今も動く」ことを確かめた（通信0・2026-08-24 実測）

★★私が「配線しろ」と言うなら、**配線先が動くことを先に確かめる義務がある**
（★確かめずに提案すると「動かない物へ繋げ」と言ったことになる）。

★通信は一切していない —— `adapter_class="ACQ_MANUAL"` + `injected`（hermetic）。
★本物のデータにも触っていない —— `EGL_DATA_DIR` を scratchpad へ向けた。

| 段 | 結果 | 発行された id |
|---|---|---|
| `core.run_start` | OK | `RUN-00001` |
| `SP.mk_source_policy` | OK | `SPOL-00001` |
| `P.mk_gap` | OK | `KGAP-00001` |
| `P.mk_search_plan` | OK | `SPLAN-00001` |
| `ACQ.mk_leg_intent` | OK | `LEG-00001` |
| `ACQ.acquire(injected)` | OK | `ARUN-00001` |

★★語彙も**実際に引けた**（V1 の主張の再確認）:

| 呼び出し | 返り |
|---|---|
| `qualify_locator("https://docs.vllm.ai/en/latest/")` | **`('OFFICIAL_DOCS', 'vLLM')`** |
| `qualify_locator("https://github.com/vllm-project/vllm")` | **`('OFFICIAL_REPOSITORY', 'vLLM')`** |
| `qualify_locator("https://example.invalid/x")` | **`('UNKNOWN', None)`** ← ★強い種別を捏造しない |
| `policy_match("OFFICIAL_DOCS", "OFFICIAL_DOCS")` | `True` |
| `policy_match("OFFICIAL_DOCS", "COMMUNITY_REPORT")` | `False` |

**11/11 通った。落ちたもの 0。**

★★∴ **素案 §11「Knowledge Route」の中核は既に動いている。**
`locator → (source_kind, entity)` が機械で出て、`required` と `observed` の一致も判定できる。
★**足りないのは呼び出し元 1箇所だけ。** これが Phase 2 の全内容。

---

# 1. 全件調査（Phase 1・実装0）

## 1.1 分類（素案 §32 の EXISTS / UNWIRED / PARTIAL / MISSING）

| 素案が要求するもの | 実体 | 数 | 分類 |
|---|---|---|---|
| source 種別の語彙 | `egl/egl/source_policy.py:13` `SOURCE_KINDS` | **14** | **EXISTS** |
| source の信頼階層 | `source_class_for` → PRIMARY / SECONDARY / GENERATED | 3 | **EXISTS** |
| 探索順（どれを先に見るか） | `SOFTWARE_TECHNICAL_V1.preferred / supplementary / discovery` | 7 / 3 / 4 | **EXISTS** |
| source policy の版管理 | `POLICIES`（`SPOL-SOFTWARE-0001` v1）+ `mk_source_policy` | 1 | **EXISTS** |
| entity → 正本の場所 | `ENTITY_REGISTRY`(host, path → entity, kind) | **4** | **PARTIAL**（4件しかない） |
| 取得アダプタ | `acquisition.ADAPTERS` | **6** | **EXISTS**（GitHub 4 / HTTP_STATIC / MANUAL） |
| 「取れなかった」の区別 | `TRANSPORT_STATUSES` / `CONTENT_STATUSES` | **12 / 7** | **EXISTS** |
| 本文を保存しない | `extract_fragment` / `content_hash` | — | **EXISTS** |
| 検索 PLAN | `pipeline.py:79` `SPLAN`（CREATE / UPDATE） | — | **EXISTS** |
| required と observed を分ける | `mk_leg_intent(required_source_kind)` / `policy_match` | — | **EXISTS** |
| 内部の knowledge routing | `self_grounding.QUERY_CLASS_DOMAINS` / `LEDGER_DOMAINS` | **4 / 3** | **PARTIAL**（台帳3本のみ） |
| LLM の安全方向 | 逐語「LLM は confirm/downgrade/unresolved のみ、elevate 不可」 | — | **EXISTS** |
| **本線への配線** | `twoder/` からの呼び手 | **0** | ★**UNWIRED** |
| **version_scope** | — | **0** | ★**MISSING** |
| **freshness / 知識の寿命** | — | **0** | ★**MISSING** |
| **retention / 知識キャッシュ** | — | **0** | ★**MISSING** |
| **外部を「探す」口**（web search） | `discovery_classes` は宣言のみ | **0** | ★**MISSING** |
| Knowledge Domain の登記先 | — | **0** | ★**MISSING**（§2.2 を見ること） |

## 1.2 §6 の語彙は新設しない —— 既存14語への写像（全件）

| 素案 §6 の候補 | 既存語 | 判定 |
|---|---|---|
| OFFICIAL_SPEC | `FORMAL_SPEC` | ○ |
| OFFICIAL_MANUAL | `OFFICIAL_DOCS` | ○ |
| OFFICIAL_REPOSITORY | `OFFICIAL_REPOSITORY` | ◎ 完全一致 |
| ACADEMIC_PRIMARY | `PRIMARY_RESEARCH` | ○ |
| PROJECT_ISSUE | `OFFICIAL_ISSUE` | ○ |
| COMMUNITY | `COMMUNITY_REPORT` | ○ |
| SECONDARY | `source_class` の `SECONDARY` | ○（軸が違う。kind ではなく class） |
| UNKNOWN | `UNKNOWN` | ◎ 完全一致 |
| VENDOR_SUPPORT | **該当なし** | ★1語だけ空白。`OPERATIONAL_REPORT` / `PRIVATE_GUIDE` で足りるか要判断 |

★既存にあって素案が挙げていない語も在る:
`OFFICIAL_RELEASE` / `REPRODUCIBLE_RUN` / `REPRODUCTION_RUN` / `INDEPENDENT_BENCHMARK` /
`TECHNICAL_REPORT` / `OPERATIONAL_REPORT` / `PRIVATE_GUIDE`。

★∴ **新設は最大1語（VENDOR_SUPPORT）。それも既存2語で足りる可能性がある。**

## 1.3 素案が想定していなかった既存の強み

★`coverage_requirements`（`SOFTWARE_TECHNICAL_V1`）は **問いの型ごとに必要な source 種別**を持つ:

- `compatibility_exists` → `OFFICIAL_DOCS` / `OFFICIAL_REPOSITORY` / `OFFICIAL_RELEASE` の **any_of**
- `operational_success` → `REPRODUCTION_RUN` / `REPRODUCIBLE_RUN`、または `OPERATIONAL_REPORT` を **独立2件**
- `not_found` → `OFFICIAL_DOCS` / `OFFICIAL_REPOSITORY` / `OFFICIAL_ISSUE` の **all_of**

★これは素案 §11「Knowledge Route」と §33「受入試験」の**両方の骨格が既に在る**ということ。
★特に `not_found` の `all_of` は「**無いと言う前に3か所見る**」を機械にしたもの
——「無いと書く前に探した範囲を書く」がコードに在る。

---

# 2. 素案からの修正（V1 で変えたところ）

## 2.1 ★Phase 2 を差し替える

素案 §32 Phase 2 は「Python Runtime / Import を1領域だけ pilot」。
**V1 では Phase 2 を「配線」に置き換える。**

理由（実測）: Knowledge Map を1つ作っても、**それを使う経路が本線に無い**。
`SPLAN` を作る `pipeline.py` を呼ぶ本線コードが 0件なので、
pilot を作っても **どこからも呼ばれない Map が1つ増えるだけ**になる。

★★Phase 2（V1）= **`egl` の取得機構を Domain 経由で1回だけ通す。**
`domain_esde` に口を足すのではなく、**既存 `to_domain` に操作名を1つ足して**
`pipeline` / `acquisition` を **1 leg だけ**走らせ、ETRACE に残る形にする。
★受入 = 「本線から呼ばれた証拠が1件でも出ること」。Knowledge Map の件数は問わない。

★Python Runtime / Import を pilot 領域にするのは **賛成**（素案の理由が実測に合っている
—— 今日だけで `operator.py` 遮蔽 / `sys.path` / `subprocess` / `cwd` を **3回**踏んだ）。
★但しそれは **Phase 3 以降**。

## 2.2 ★Knowledge Domain の「登記先」は無い —— 但し今は作らない

`DOMAINS` 16件（開発対象領域）とも `DOMAIN_OPERATIONS`（運用上の責任領域）とも**別の軸**。
`ENTITY_REGISTRY` は host/path の写像であって **知識領域の階層を持たない**。

★∴ 素案 §3-4 の階層（`Python → Runtime → Import system`）を入れる先は**無い**。

★**但し新台帳を作らない**（Taka 常設命令）。V1 の扱い:

1. Phase 2 は **階層を持たずに**通す（`ENTITY_REGISTRY` の1行だけで足りる）
2. 階層が**無いせいで通らなかった**という実測が出てから、置き場を設計する
3. ★それまで「Knowledge Domain」は**語の定義だけ**（GDW 裁定①と同じ扱い）

## 2.3 ★§7 Version / §8 Freshness は「無い」から始める

どちらも既存0件。∴ **素案の表（Version-bound / Slow / Fast）をそのまま実装しない。**

★V1 の順序:
1. **`source_version` を1つの leg に付けられるか**だけ試す（既存 `LegIntent` に欄を足さずに済むか調査）
2. 付けられたら、**同じ leg を2回取って content_hash が変わるか**を見る
   —— これが freshness の**最小の観測**（★寿命の分類表より先に、変化の検出）
3. 分類表（version-bound / slow / fast）は **変化が観測できてから**作る

★理由: 寿命の分類は**予想**であり、変化の観測は**実測**。
★「予想を固定する前に決定論で確定する」。

## 2.4 ★§22 の受入試験は今のままでは成立しない

素案 §33 は「A: 現在のRRI で検索 / B: Top-Down 経由」を比較する。

★**実測: 「現在のRRI」に一般的な外部検索の口が無い。**
`ADAPTERS` は GitHub 4 + HTTP_STATIC + MANUAL の6種で、
**URL を知っている先は取れるが、探すことができない**（`discovery_classes` はアダプタ0件）。

∴ **A が「無制限検索」にならない。** 比較の前提が崩れる。

★V1 の受入試験（差し替え）:

| # | 測るもの | A（現状） | B（Top-Down 経由） |
|---|---|---|---|
| 1 | **正本に到達できたか** | locator を人が渡さないと 0 | `ENTITY_REGISTRY` から locator が出る |
| 2 | 読んだ source 数 | — | — |
| 3 | `required` と `observed` の一致 | `policy_match` で判定 | 同じ |
| 4 | `not_found` を言うのに何か所見たか | — | `coverage_requirements` の all_of |
| 5 | 取れなかった時の理由 | `TRANSPORT`/`CONTENT` の12/7語 | 同じ |

★★**「賢くなった」ではなく「locator を機械が出せたか」で測る。**
★素案 §33 の「token量 / query回数」は**外部検索の口ができてから**。

## 2.5 ★§19 Knowledge Worker は今は置かない

素案 §19 は Worker 5種（Inventory / Structure / Source / Freshness / Retrieval）。

★V1: **0種から始める。** 理由 —— `acquisition` / `pipeline` / `source_policy` が
既に Inventory・Source・Retrieval に相当する働きをしている。
**Worker を新設すると、動いていない既存機構の隣に動かない新機構が並ぶ。**

★GDW 裁定②（Worker の門）はそのまま適用する:
Worker を置くなら `authority.POLICY` の行為名で拘束する。★新設は差分だけ。

★★併せて今日の実測を渡す —— **Worker を subprocess で起こすなら
`from twoder import ...` は `ModuleNotFoundError` になる**
（`sys.path[0]` は起こされた script の置き場）。`--check` はこれを捕まえない。
詳細は `ART-7308ecee62` §1.36 / §2.6。

## 2.6 ★§24-25 の「大量に作らない」は強化して残す

素案 §24 の候補（Python / Linux / systemd / Git / CUDA / NVIDIA / vLLM / Qwen / Claude /
HTTP / JSON / system services ＝ **12領域**）でも、V1 では**まだ多い**。

★V1: **1領域。** `ENTITY_REGISTRY` に既に在る **vLLM** から始めるのが最も安い
（★host/path の登録が済んでおり、`OFFICIAL_DOCS` と `OFFICIAL_REPOSITORY` の両方が在る）。

★Python Runtime / Import は **2番目**。理由: 実際の failure が豊富で Bottom-Up 接続が試せる
（素案 §32 の理由に賛成）が、**`ENTITY_REGISTRY` に docs.python.org が無い**ので
1行足す判断が要る = Phase 2 の「配線だけ」に混ぜない。

---

# 3. 素案のまま採る部分（★変えない）

- **§0 目的** —— 世界の情報を持つのではなく、探索空間を設計する
- **§1 二方向の循環** —— Bottom-Up と Top-Down は独立機能でなく循環する
- **§5 三分類**（INTERNAL_CANONICAL / EXTERNAL_CANONICAL / DISCOVERED）
  ★但し語の新設前に既存を見る（`source_class` の PRIMARY/SECONDARY/GENERATED と軸が違う）
- **§14 Bottom-Up → Top-Down の学習** —— ★今日の実測がそのまま例になっている
  （`subprocess` / `cwd` / `sys.path` / `operator.py` 遮蔽を **1日に3回**踏んだ
  = `Python → Runtime → Import Resolution` の昇格候補が**観測から出た**）
- **§20 Worker は「世界はこうだ」と確定しない** —— 既存の「LLM は elevate 不可」と同じ思想
- **§27 Knowledge Map 自身に ESDE を当てる** —— ★対等性/対称性/階層性/連動性は
  既存計器 `s_esde_evaluate`(ART-1a882c44e2) の軸をそのまま使える
- **§28 Map は腐る** —— ★これは今日 `ART-8810d0646e` で4件出した型と同じ
  （**古い値が現在の顔で出る**）。★Map にも同じ規律を当てる
- **§29-31 境界**（ESDE=構造 / Ledger=履歴 / RRI=実行 / General は中身を知らない）
- **§34 成功条件** —— 件数ではなく探索量と誤り率

---

# 4. Phase（V1・素案から差し替え）

| Phase | 内容 | 実装 | 受入 |
|---|---|---|---|
| **1** | 全件調査 | **0行**（★本書＝完了） | 分類表（§1.1）が埋まった |
| **2** | ★**配線** —— `to_domain` 経由で `acquisition` を **1 leg** 走らせる | 表に操作名1つ | ★**本線から呼ばれた証拠が1件**（ETRACE） |
| **3** | 1領域（**vLLM**）で locator → 取得 → `policy_match` を通す | 小 | `required` と `observed` が一致した記録1件 |
| **4** | 変化の検出（同じ leg を2回・`content_hash` 比較） | 小 | ★変化が**観測できた**（分類表はまだ作らない） |
| **5** | Bottom-Up → Top-Down（failure から領域を昇格候補にする） | 小 | 候補が**観測から**出た（人が書いていない） |

★Phase 2 が通らない限り 3 以降へ進まない。★**Knowledge Map の件数を成果にしない。**

---

# 5. 裁定が要る点（★Taka）

1. **Phase 2 を「配線」に差し替えてよいか。**
   素案の Phase 2（Python pilot）を先にやると、**呼ばれない Map が1つ増える**（§2.1 の実測）。
2. **`VENDOR_SUPPORT` を1語足すか、既存2語で足りるとするか。**（§1.2 —— 空白はこの1語だけ）
3. **外部を「探す」口（web search アダプタ）を作るかどうか。**
   ★無いままでも Phase 2-4 は通る（locator を知っている先だけ取る）。
   ★§22 の「external canonical first」を本当にやるなら要るが、**新しい外向きの口**なので私は決めない。
4. **`ENTITY_REGISTRY` に docs.python.org を足すか。**（Phase 3 の2番目に必要・1行）

★1〜4 のどれも**新台帳を作らない**。
