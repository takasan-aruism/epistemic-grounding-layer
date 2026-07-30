# 【BUILT】D-133 検証 — PLAN を作ったのが Qwen か、規則テンプレートか（★実装なし・確かめただけ）

- `BUILD_ROLE: 参照`（**★何も実装していない。★本文書は検証の報告である**）
- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-30 20:0x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）**
- **★実装源**: `CC_DESIGN_2026-07-30_D133_BUILD_SPEC_VERIFY_PLAN_AUTHOR.md`（**★これ1本だけ**）
- **受領した MGR 文書の一覧**: **★無し。** 役割板に `CC_MGR_HANDOFF_2026-07-30.md` が「自分宛の未処理」として出たが、**★MGR 文書から着手しない規律（運用方針 §1-1）により読んでいない。**

---

# 0. ★2DER 優先原則の5点（★私が実際にやったこと）
| # | |
|---|---|
| ① 入口 | **`GET /api/state`** と **`GET /api/resolve`**（★webui 経路・読み出しのみ）。**★`:8005` には1件も投げていない** |
| ② 2DER で何を試したか | **★「その PLAN を誰が作ったか」を 2DER に2つの口で聞いた** |
| ③ **2DER では何ができなかったか** | **★両方の口が答えられない。**`/api/state` の最上位19キーを全走査して `plan_source`／`runtime_recovery` は**0件**。`/api/resolve` の `record` は `task_id`/`events`/`state` の**3キーのみ**で `plan_source` を含まない（★下記 §4 に実測） |
| ④ 何を実装するか | **★何も実装しない**（★本 SPEC は検証のみ・SPEC §2） |
| ⑤ 実装後 2DER だけで再現できたか | **★該当なし（★実装していない）** |

## 0-1. ★やっていないこと（★SPEC §2 の禁止事項に1つずつ）
```
★run_next を叩いていない        ★/api/submit を叩いていない
★task を1件も進めていない        ★production repo を1行も変えていない
★commit していない               ★台帳(*.jsonl)を直読していない
★:8005 へ新しい呼び出しを投げていない（★窓の2件は私ではない。★根拠は §1-4）
★テストは0本（★走らせていない）
```

---

# 1. V-1 モデルサーバ側の記録（★2DER の外から見た）

## V-1-a ★見た先を1つ名指しし、記録の形式を先に書く → **印: 満たした**
```
★見た先: Docker コンテナ qwen36_vllm (0961b484b5e1) ★自身の記録
         log driver = json-file / 読み方 = `docker logs -t <CID>`
★:8005 の実体（ps 実測）:
   PID 700835 / 700850  /usr/bin/docker-proxy -host-port 8005 -container-ip 172.17.0.2 -container-port 8000
   PID 700957           /usr/bin/python3 /usr/local/bin/vllm serve --served-model-name Qwen3.6-35B-A3B …
```
| ★問い | ★答え |
|---|---|
| **時刻つきで要求を残す形式か** | **★残す。** 1要求=1行、`docker logs -t` の RFC3339（UTC）＋ `INFO: <src> - "POST /v1/chat/completions HTTP/1.1" <status>` |
| **★残らないもの** | **★要求 id が無い。★呼び手の名前も無い。** 送信元は全件 `172.17.0.1`（★docker の gateway＝ホスト側全部が同じ見え方になる） |
| **★2DER の台帳か** | **★違う。**（★LLM 呼出台帳も使っていない＝検算になる別出所） |

## V-1-b ★窓の件数（★先に数えた・★打ち切り無し） → **印: 満たした**
**★窓: JST 2026-07-30 19:32:13〜19:32:34 ＝ UTC 10:32:13〜10:32:34**（★時差 +0900 を `date` で実測して換算）

| | ★数 |
|---|---|
| **窓内の `POST /v1/chat/completions`** | **★2件（★両方 200 OK）** |
| 窓内の総行数 | 4行（★上記2件＋engine の稼働行2本） |
| 打ち切り | **★無し**（`head`/`tail`/`-m` を使っていない。`--since/--until` は★窓の定義そのものであって切り詰めではない） |

```
2026-07-30T10:32:14.745Z  Engine 000: … Running: 1 reqs, Waiting: 0 reqs   ← ★窓の頭で既に1件 走っている
2026-07-30T10:32:22.444Z  "POST /v1/chat/completions HTTP/1.1" 200 OK      ← ①
2026-07-30T10:32:24.745Z  Engine 000: … Avg generation throughput: 232.7 tokens/s, Running: 1 reqs
2026-07-30T10:32:33.885Z  "POST /v1/chat/completions HTTP/1.1" 200 OK      ← ②
```
> **★測って2件である（★「測れない」ではない）。**
> **★2件の内訳（どちらが PLAN か）は言えない。★記録に要求 id が無いためである**（V-1-a の「残らないもの」）。

## V-1-c ★対照 → **印: 満たした（★ただし単純ではない。下に全部書く）**
| 窓 | `POST /v1/chat/completions` |
|---|---|
| **★SPEC 指定の対照 JST 19:20:00〜19:30:00（10分）** | **★0件（★総行数も0）** |
| ★参考: JST 19:30〜19:36 に広げると | 9件（★うち7件は **19:31:13〜19:31:24** の別のかたまり＝`400 Bad Request`×1 ＋ `200 OK`×6） |
| ★参考: JST 19:00〜19:40 の全件 | 17件（★19:11 と 19:13 にも同型の `400`×1＋`200`×3 が在る） |

> **★結論（事実のみ）: 「常に何か出ている」ではない。★10分間まるごと0の対照が取れた。**
> **★ただし「その窓だけ」とも書けない。★窓の1分前（19:31:13〜24）に別のかたまりが在る。**
> **★それが誰の通信かは、この記録からは分からない**（★要求 id も呼び手も残らない）。**★掘っていない。**

## 1-4. ★計器が自分を数えていないかの確認（運用方針 §4-15）
```
★私は :8005 に1件も投げていない ∴ 窓の2件は私の呼び出しではない
★私の作業開始（役割設定）は 19:38、★窓は 19:32 ＝ 私が居ない時刻である
★19:41 時点で「直近2分」のログは0行 ＝ 私の作業中に呼び出しは発生していない
★ps の走査では、私自身の ugrep プロセス(3899408)が結果に入っていたので★除外して読んだ
```

---

# 2. V-2 `QWEN_BUILD_PLANNER` が LLM を呼ばずに入る経路が在るか（★コード構造）

## V-2-a ★代入箇所を全部挙げる（§3-9 の3点併記） → **印: 満たした**
```
走査範囲 : /home/takasan/{egl,ds,rri,dev-workcell,twoder} の *.py ★全件
対象総数 : 514 本
探した語 : QWEN_BUILD_PLANNER
総件数   : 6   確認件数: 6   打ち切り: ★無し
```
| # | 場所 | 種別 |
|---|---|---|
| 1 | `twoder/build_planner.py:200` `plan["plan_source"] = "QWEN_BUILD_PLANNER"` | **★代入** |
| 2 | `dev-workcell/dw/dispatch.py:118` `"auto_served": "QWEN_BUILD_PLANNER"` | **★代入（★ただし欄が違う。`plan_source` ではなく `auto_served`）** |
| 3-6 | `twoder/regression/test_build_planner.py:188,297,316` / `test_runtime_supervisor.py:135` | 比較（★試験が読むだけ） |

**★補完走査（`plan_source` という欄そのものへの代入）**: 総件数6・確認件数6・打ち切り無し →
**代入は2箇所だけ**＝`build_planner.py:200`（`QWEN_BUILD_PLANNER`）と `plan_template.py:44`（`RULE_TEMPLATE_2DER_EVO_0007`）。**★第3の書き手は無い。**

## V-2-b ★各箇所の到達経路（★1行ずつ） → **印: 満たした**
**代入1 `build_planner.py:200`**
> **本番（webui）は `BP.make_dw_planner_actor(chat_fn=_planner_chat_fn())` を登録し、`_planner_chat_fn()` は `return None`（`webui.py:257-260`）→ `chat_fn=None` の LIVE 分岐 → `RS.run_with_recovery(call=lambda mt: _qwen_call(prompt, mt))` → `_qwen_call` は module 変数 `_QWEN_CALL`（既定 `None`）が `None` なので `RS.qwen_raw_call` → `urllib.request.urlopen("http://127.0.0.1:8005/v1/chat/completions")` ＝ ★本番経路は HTTP を必ず通る。**

**★ただし HTTP を通らずに 200 行へ届く継ぎ目が2つ在る**（★SPEC「1つでも在れば『在る』と書く」に従い **在る** と書く）:
| # | 継ぎ目 | 設定している場所 | 本番から設定されるか |
|---|---|---|---|
| a | 呼び手が `chat_fn` を渡す（legacy 単発分岐） | `twoder/regression/test_build_planner.py`（`fake_chat_valid`） | **★0件**（本番は `None` を渡す） |
| b | module 変数 `_QWEN_CALL` を差し替える | `twoder/regression/test_runtime_supervisor.py:128`（`finally` で `None` に戻す） | **★0件** |

**代入2 `dispatch.py:118`**
> **登録済 `BUILD_PLANNER` アクタが `recorded=True` を返した時だけ返る★ラベルであり、そのアクタは必ず `build_plan()` を通る（`build_planner.py:293`）＝ ★代入1 と同じ経路。★単独では立たない。**

## V-2-c ★`template_plan` が返す `plan_source` の実読 → **印: 満たした。★テンプレート説は消える**
```
dev-workcell/dw/plan_template.py:44
    "plan_source": "RULE_TEMPLATE_2DER_EVO_0007",   # deterministic template, NOT Claude judgment
```
**★`QWEN_BUILD_PLANNER` ではない。** 加えて `dispatch.py:97-103` では、テンプレート経路は
`W.record_plan(task_id, packet, ts, "2der-auto-plan-template")` を通り **`auto_served: "RULE_TEMPLATE_PLAN"`** を返す（★コメントに `deterministic, no :8005, no LLM`）。
> **∴ テンプレート経路と Qwen 経路は、★値もラベルも記録者名も分かれている。**

---

# 3. V-3 `prohibited_actions` の `"Modify existing repositories"` の出所 → **★分からない（★掘っていない）**
```
走査: 5 repo の *.py 全件 / "Modify existing repositor" 完全一致 → ★0件
補 : 大文字小文字を無視して "existing repositor" → ★1件のみ
      twoder/build_planner.py:124  "use the network, use sudo, or modify any existing repository.\n"
      （★これは PLAN プロンプトの本文であって、prohibited_actions の定型配列ではない）
```
| ★言えること | **★定型文の配列として持っている箇所は無い**（走査範囲＝5 repo の *.py 全件・打ち切り無し） |
|---|---|
| **★言えないこと** | **★「その場で作られた」と「プロンプト文言の言い換え」を、この走査では区別できない。★分からない** |

---

# 4. ★2DER に聞いて答えられなかったこと（★③の実測・★次に作る機能の発見）
```
GET /api/state?task_id=TASK-2DER-B11764B3
  → 最上位19キー: task_id, goal, dw_state, last_completed_op, next_operation, actor_role,
     claude_barrier, dispatch_status, ds, rri, egl, work, ds_limitation, failure_memory_match,
     guard_block, block_source_refs, taka_authority, etrace_run_id, boundary_failures
  → ★入れ子まで全走査して plan_source / runtime_recovery / packet_type / prohibited_actions = ★0件

GET /api/resolve?id=TASK-2DER-B11764B3
  → resolved=true / record のキーは task_id, events, state の★3つだけ / plan_source を★含まない
```
> **★「その PLAN を誰が作ったか」を 2DER に聞く口は無い。★2口 試して2口とも答えられない。**
> **★これは「測って0」である（★「測れない」ではない。★口は在り、応答も返り、その中に欄が無い）。**
> **★私は作りに行っていない**（★SPEC §2「何も実装しない」）。

---

# 5. ★止まってよい場所に当たったか（SPEC §3）
| ★条件 | ★判定 |
|---|---|
| モデルサーバの記録が「時刻つきで残らない形式」だった | **★該当しない**（★残る形式だった） |
| `QWEN_BUILD_PLANNER` の代入が2つ以上あって到達経路を1行で言えない | **★代入は2つ在った。★1行で言えたので止めていない**（§2 V-2-b）。**★2つ目は1つ目の下流であり、独立した書き手ではない** |

---

# 6. ★V-1 と V-2 は同じ向きに出たか（★事実のみ。★印2 は私が立てない）
| | ★出た向き |
|---|---|
| **V-1** | **★窓に実際の completion 要求が2件 在った**（★対照の10分は0件） |
| **V-2** | **★本番から `plan_source="QWEN_BUILD_PLANNER"` に到達する経路は HTTP を必ず通る。★HTTP を迂回する継ぎ目2つは試験ファイル内のみで本番からの設定は0件。★テンプレートは別の値を返す** |

> **★両方が同じ向きに出た。**
> **★ただし「印2 が立つ」と書くのは私の仕事ではない**（受入基準の作成・判定は設計/監査）。**★事実だけ置く。**
> **★言えないこと: 窓の2件のうちどちらが当該 PLAN かは名指しできない**（★要求 id が記録に無い）。**★「1件が PLAN だった」と書いていない。**

---
*IMPL → 設計/監査（写: MGR / Taka）。D-133 BUILD SPEC の検証結果。**何も実装せず・task を進めず・:8005 へ新しい呼び出しを投げていない。** V-1=`qwen36_vllm` コンテナ自身の json-file ログ（時刻つき・要求 id 無し）で窓 JST 19:32:13〜34 に **completion 2件（200 OK）**、対照 19:20〜19:30 は **0件**、ただし窓の1分前 19:31:13〜24 に別のかたまり7件が在り「その窓だけ」とは書けない。V-2=`QWEN_BUILD_PLANNER` は 5 repo の *.py 514本・総件数6・確認6・打ち切り無しで **代入2箇所**（`build_planner.py:200` の `plan_source` と `dispatch.py:118` の `auto_served`）、後者は前者の下流。本番は `_planner_chat_fn()→None` により LIVE 分岐→`qwen_raw_call`→`http://127.0.0.1:8005` を**必ず通る**。HTTP を迂回する継ぎ目は `chat_fn` 注入と `_QWEN_CALL` 差し替えの2つで**いずれも regression ファイル内のみ・本番からの設定0件**。V-2-c=`template_plan` の `plan_source` は **`RULE_TEMPLATE_2DER_EVO_0007`** ゆえ**テンプレート説は消える**。V-3=`"Modify existing repositories"` の定型配列は**0件**、近い文字列は PLAN プロンプト本文1件のみで、その場生成か言い換えかは**分からない**。**2DER には `/api/state` と `/api/resolve` の2口で聞いたが、どちらにも `plan_source` の欄が無く答えられなかった（測って0）。**両検証は同じ向きに出たが、**印2 の判定は設計/監査に委ねる。***
