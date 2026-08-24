# 設計: General が軽量に読める Domain 共通観測形式 v0.1

- **出所**: Taka 指示 2026-08-24 逐語「優先順位ロジックはまだ実装しない。まず5 Domainについて、Generalが軽量に読める共通観測形式を既存値だけで作れるか設計する。」
- **担当**: Claude Code (MGR / General Manager)
- **これは設計である。実装0行。** 新しい業務state 0 / 新しい priority 語彙 0 / 新台帳 0 / 新ID族 0。
- **前提資料**: `CC_MGR_2026-08-24_DOMAIN_SUMMARY_COMMON_FORM_SURVEY_v0.1.md` (ART-37a3175c06)
- **測ったHEAD**: twoder 925749c / egl 0f12a22

---

## 0. 結論（先に3行）

1. **作れる。** ただし **General が値を作ってはいけない**。General は「Domain が既に作って置いた観測」を**読むだけ**にする。これで条件6・7が構造的に満たされる。
2. **5軸のうち、いま実際に埋まるのは 6/25 マス。残り19マスは `null` + 理由**。推測で埋めない。
3. **Domain 間依存の自動記帳は、いま 0本しか作れない。** 条件9「blocking理由から決定論で証明できるものだけ」を満たす材料が無い（**blocking 欄を持つのは esde だけで、しかも理由の欄が無い**）。

---

## 1. 共通観測形式（欄は6つ）

```
{
  "domain":   <既存: /api/domains の name>,
  "observed": true | false,
  "why":      <observed=false の時だけ。既存の逐語をそのまま写す>,
  "as_of":    <既存: include_gate の as_of。作られた時刻>,
  "age_sec":  <既存: include_gate の age_sec>,
  "axes": {
    "state":            {"value": …, "source": "<Domain の既存欄名>"} | null,
    "needs":            {"value": …, "source": …} | null,
    "blocking":         {"value": …, "source": …} | null,
    "escalation":       {"value": …, "source": …} | null,
    "next_eligibility": {"value": …, "source": …} | null
  }
}
```

### 条件との対応（1つずつ）

| 条件 | どう満たすか |
|---|---|
| 新しい業務stateを作らない | 5軸の名前は **Taka の指示文の語をそのまま**使う。`observed` は**業務stateではなく観測メタ**（観測できたか否か）。値そのものは Domain の既存欄を**写すだけ**で、語を作らない |
| 値が無いものは推測しない | 軸は `null`。埋めない。`why` に理由を1行 |
| dw / route_table は「未観測」と明示 | `observed:false` ＋ `why` に `/api/domains` の**逐語**「状態を返す口が無い（`twoder.domain_dw` に `*_summary` が在りません）」をそのまま。**新しい説明文を作らない** |
| Domain固有の意味解釈はDomain側 | **5軸を埋めるのは Domain**。General は `undisposed_rate` を「needs」だと解釈しない。`source` に Domain の欄名を書かせるので、**誰がどう写したかが後から引ける** |
| Generalは共通形式だけ読む | General は `axes` の外を読まない。Domain 固有欄（`writer_counts` / `axis_names` / `runtime_control` 等）は共通形式に載せない |
| 1回の取得が60秒周期を妨げない | **§2 で構造的に保証する** |
| 重いsummaryを直接呼ばない | **§2**。General は `ledger_summary` / `esde_summary` を1度も呼ばない |
| Domain間依存は既存 ITEM.depends_on | **§4** |
| 自動記帳は blocking理由から決定論で証明できるものだけ | **§5**。いまは 0本 |

---

## 2. 軽さをどう保証するか（条件6・7の本体）

### 2-1. 実測（この設計の出発点）

| Domain | 状態取得の実測 | 出所 |
|---|---|---|
| sysops | **0.0秒** | `/api/domains` の `state.sec` |
| esde | **21.71秒** | 同 |
| ledger | **165.52秒**（cold build）／ `heavy_sec` 71.4 | 同 `state.gate.build_sec` |
| dw | — | 口が無い |
| route_table | — | 口が無い |
| **合計（`/api/domains` 1回）** | **187.29秒** | 同 `elapsed_sec` |

> **★60秒周期に対して 187秒。3周ぶん食う。** ∴ 「General が読むたびに作る」形はどう調整しても成立しない。

### 2-2. 設計：General は作らない。読むだけ。

```
Domain（自分の間隔で・別プロセスで作る）        General（60秒周期・読むだけ）
  include_gate.isolated_or(spec, build)   ──→   最後に置かれた観測を読む
        ↓ 作った物を置く                              ↓
   as_of / age_sec を必ず添える              observed / age_sec を見るだけ
```

- **General が build を起動しない。** 鮮度切れなら「古い」と分かる形で返り、**待たない**。
- ∴ General の1回の取得は **辞書引きの費用のみ**。**60秒周期を構造的に妨げない。**
- **重い summary を直接呼ばない**（条件7）— 呼ぶのは Domain 側だけ。

### 2-3. 使う既存機構（新規0）

| 要る性質 | 既存で在るもの | 状態 |
|---|---|---|
| 重い計算を別プロセスへ | `twoder/include_gate.py` の `run_isolated` / `isolated_or` | **在る**。front door が5箇所で使用中 |
| 重なりを止める・鮮度を持つ | 同 `compute(key, build, fresh_sec)` | **在る**。`as_of` / `cached` / `age_sec` / `build_sec` を返す |
| Domain が自分の間隔で落とす | `domain_sysops._interval_wait` / `domain_ledger._LAST` | **在る**。sysops は W1/W2/W4 を 1800/1800/3600秒で自分で落としている |

### 2-4. ★足りない1点（実装前に必ず要る）

**`include_gate` に「作らずに読むだけ」の口が無い。** `compute(key, build, …)` は鮮度切れなら**必ず build する**。

- 既存の `stats(key)` はメタだけで**値を返さない**。
- ∴ General が「読むだけ」を守るには、**値を返す read-only の1関数**が要る（新台帳0・新state0・新語0。既存モジュールに関数を1つ）。
- **これは実装であり、本書では実装しない。**

### 2-5. ★未解決：置き場（2候補。測っていないので選ばない）

**`include_gate._SLOTS` はプロセスローカルである**（実測: `_SLOTS = {}` はモジュール変数）。**General（`manager_v0`）と front door（`webui`）は別プロセス** ∴ 一方が温めた値をもう一方は見られない。

| 候補 | 新台帳 | 費用 | 状態 |
|---|---|---|---|
| (i) 各プロセスのメモリ | 0 | 読みは無料 | **共有されない**。General が自分で作る＝§2-2 に反する |
| (ii) ETRACE（既存・追記式・全 Domain が既に `_emit` 済） | 0 | **未測** | 読む費用を測っていない ∴ **推測しない** |

> **★実装前に (ii) の読み費用を測ること。** 測る前に選ぶと、§2-2 の保証が空手形になる。

---

## 3. 5軸を誰がどう埋めるか（既存値だけで・Domain 側が写す）

**General は1つも解釈しない。** 下表は「Domain が自分の既存欄からどう写せるか」であり、**Domain 側の宿題**である。

| Domain | state | needs | blocking | escalation | next_eligibility |
|---|---|---|---|---|---|
| **dw** | `null` | `null` | `null` | `null` | `null` — **observed:false**（口が無い） |
| **route_table** | `null` | `null` | `null` | `null` | `null` — **observed:false**（口が無い） |
| **esde** | `state`（既存欄・値 `"ACTIVE"`） | `backlog` / `unresolved_metrics` | `blocking`（既存欄） | `human_decision_waiting` | **`null`**（値が無い。General 側の `ESDE_INTERVAL`/`_ESDE_LAST` は**プロセス内変数**で再起動で消える ∴ 出所にしない） |
| **ledger** | **`null`**（値が無い） | `rates.undisposed_rate` / `rates.unassigned_rate` / `dispose_candidates` | **`null`**（値が無い） | **`null`**（`dispose_note` は散文 ∴ 写せない） | **`null`**（`ledger_tree_stale.next_in` は**別操作** ∴ Domain が summary 側へ写すなら可） |
| **sysops** | **`null`**（値が無い） | `★未達`（**日本語の自由文3件** ∴ 型が揃わない） | **`null`** | **`null`**（`sysops_runtime_escalations` は**別操作**） | `last_run_age_sec` + `intervals_sec` |

**埋まるのは 6/25 マス（24%）。残り19マスは `null` + 理由。**

### 3-1. 19の欠けを2つに分ける（★同じ「欠け」にしない）

| 種類 | 件数 | 中身 | 直し方 |
|---|---|---|---|
| **値が実在するが summary に出ていない** | **4** | ledger の `next_eligibility`（`ledger_tree_stale.next_in`）／ ledger の `escalation`（散文で在る）／ sysops の `escalation`（別操作に在る）／ sysops の `needs` の型 | **Domain 側が summary へ写すだけ**。新語0 |
| **値そのものが無い** | **15** | dw 5 / route_table 5 ／ esde の `next_eligibility` ／ ledger の `state`・`blocking` ／ sysops の `state`・`blocking` | ★**新しい業務stateを作らずには埋まらない** ∴ **今回は埋めない。`null` のまま出す** |

> **★これが条件1と条件2を同時に守る唯一の形である。** 15マスは「まだ無い」と言い続ける。

---

## 4. Domain 間依存（条件8）

**使うのは既存の2つだけ。新しい dependency 台帳は作らない。**

| 要る物 | 既存 | 実測 |
|---|---|---|
| 依存の欄 | `ITEM.depends_on`（`roadmap_registry`） | ITEM 一意 170件中 **72件（42.4%）**が非空＝**生きている** |
| Domain ↔ ITEM の鍵 | `/api/domains` の `note.item_id` | dw:EVO-0073 / esde:EVO-0099 / ledger:EVO-0103 / sysops:EVO-0102 ／ **route_table:なし** |

**読み方**: `Domain A → Domain B` は「A の item_id の `depends_on` に B の item_id が在る」で定義する。**新しい語も欄も作らない。**

**現在値**: **辺 0本**（4つの item の `depends_on` は4件とも空）。∴ 共通観測に載る依存も **いまは0本**。**0本を「依存が無い」と読ませない** — `route_table` は item_id 自体が無いので**そもそも引けない**（分母の外）。

---

## 5. 依存の自動記帳（条件9）— いまは 0本しか作れない

条件は「**blocking 理由から決定論で証明できるものだけ**」。

**証明に要る鎖**: `blocking = true` → **その理由** → 理由が**他 Domain の item を名指し** → その id が resolve できる → **`depends_on` に1行追記**。

**実測でこの鎖は最初の2段で切れている。**

| 段 | 在るか |
|---|---|
| ① `blocking` 欄 | **1/5 のみ**（esde の `blocking:false`） |
| ② blocking の**理由**の欄 | **0/5** — ★どの Domain も持っていない |
| ③ 理由が他 Domain を名指し | ②が無いので**評価不能** |
| ④ id が resolve できる | 同上 |

> **★∴ いま自動記帳できる依存は 0本。** これは「機構が無い」ではなく「**②の欄が無い**」。
> **★順序**: まず `blocking` に**理由の欄**を持たせる（Domain 側）。それが揃うまで、**依存は人が書く**か、**書かない**。
> **★推測で書かない** — 共起や名前の一致から依存を起こすのは計器ではなく推測器になる。

---

## 6. 実装前に必ず測ること（測る前に実装しない）

1. **§2-5 (ii) ETRACE から観測を読む費用**。§2-2 の保証はこれが安いことに乗っている。
2. **`include_gate` の read-only 読み出しが本当に O(1) か**（ロック待ちが無いか）。
3. **各 Domain の観測生成を別プロセスへ出した時の実測**（`isolated_or` の `sec` と `isolated` 印）。ledger 165.52秒が別プロセスで何秒になるか。

---

## 7. 完了条件（「ファイルができた」で判定しない）

1. 5 Domain すべてが共通形式で返る（**うち2つは `observed:false` で返る**のが正しい状態）
2. General の1回の取得が **1秒未満**（実測で示す。60秒周期を妨げないこと）
3. General が `ledger_summary` / `esde_summary` を **1度も呼んでいない**（呼び手を機械で数えて0）
4. `null` の19マスに**理由が付いている**（0件と書かない）
5. 新しい業務state・priority語彙・台帳・ID族が **0**（機械で数えられる）
6. 依存は `ITEM.depends_on` からのみ読む（新しい dependency 台帳が0）
7. 自動記帳した依存は **blocking 理由から決定論で証明できたものだけ**（いまは 0本＝**0本で正しい**）

**★7 の「0本」を失敗と数えない。** 材料が無いのに辺を作ったら、それが失敗である。

---

## 8. この設計でやっていないこと（隠さない）

- **実装0行。** `include_gate` の read-only 口も、Domain 側の写しも、書いていない。
- **ETRACE の読み費用を測っていない** ∴ 置き場を選んでいない（§2-5）。
- **`/api/domains` の 187.29秒は1回の測定**（`cached:false`）。温まった時の値は測っていない。
- **dw / route_table の状態は測っていない**（口が無い）。0件ではない。
- 優先順位規則は**1文字も設計していない**（Taka 指示: 5 Domain すべてから共通観測が取れてから）。
