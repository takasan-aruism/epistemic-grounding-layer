# 【監査＋判定案】押しても流れない — **★ただし「壊れている」ではない。★planner は呼ばれ、理由を返して断った**

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-31 02:0x / TYPE=FINDING
- **運用方針 確認済（版: v2.8）** ／ **受領**: `CC_IMPL_2026-07-31_D146_PRESS_ONCE_BUILT.md`
- **2DER 優先原則**: ①読み出しの口のみ ②「新しい観測が生まれたか」を決定論で確認 ③該当なし ④実装しない ⑤該当なし ／ **`:8005` 未使用**

---

# 1. ★私の独立測定（★BUILT を読む前に取った。★全一致）

| # | 私が押す前に固定した基準 | ★押した後（★私の実測 01:51:53） | IMPL |
|---|---|---|---|
| 1 | `ARUN-00966` 未生成 | **★`resolved=false`（★増えていない）** | 一致 |
| 2 | `OBS-00967` 未生成 | **★`resolved=false`（★増えていない）** | 一致 |
| 3 | task = `CREATED`/`CREATE`/`PLAN`/`CLAUDE` | **★全項目 同じ（★変化なし）** | 一致 |
| 4 | `tasks` 157 | **★157（★増えていない）** | 一致 |
| 5 | — | **`implementation_packet_ref` が無い ＝ ★PLAN は記録されていない** | 一致 |

> **★E-3 は決定論で判定した。★「たぶん走った」を書く余地が無い形にしてあった。**

---

# 2. ★今回いちばんの収穫（★IMPL が見つけた。★私も根拠を取り直した）

```
planner_outcome = {"recorded": false, "stage": "provenance", "plan": null,
  "reason": ["missing required provenance field: trace_id",
             "missing required resolvable id: rri_request_id",
             "missing required resolvable id: rri_intent_id"]}
```
| ★確かめたこと | ★結果 |
|---|---|
| **`planner_outcome` が `null` でない** | **★`BUILD_PLANNER` は実際に呼ばれた。★呼ばれた上で断った** |
| **失敗理由が捨てられていない** | **★`CLAUDE_BARRIER` の一語に潰されず、★3件の理由が応答に載っている** |
| **`:8005` が0件だったこと** | **★設計どおり。**〔READ(CC-α): `build_planner.py:153` **"Provenance is verified BEFORE any LLM call (fail-closed)"**／`:166` が provenance 段で return〕**★推測ではなく、★コードと実測が一致した** |

> ### **★これは運用方針 §5-3「★失敗を、正常に見える別の結果に置き換えない。★理由を捨てない」が実際に効いた形である。**
> **★理由が捨てられていたら、我々は今ごろ「なぜか PLAN が動かない」を推測で埋めていた。**

## 2-1. ★私の過去の誤りの裏取りにもなっている（★書いておく）
```
★D-131 で私は「planner_outcome が null ＝ テンプレートが作った証拠」と誤って書き、自分で訂正した。
★今回、★失敗したときは null ではなく★理由入りで返ることが実測で確かめられた。
∴ ★あのときの訂正（「null は両方の成功経路で返る。証拠にならない」）は★正しかった。
```

---

# 3. ★原因（★IMPL の見立てを、私がコードで確かめた）

| # | ★確かめたこと | 根拠 |
|---|---|---|
| 1 | **BUILD 経路は provenance を持つ** | `submit.py:435-437` が `IR.mint("REQUEST"…)` / `IR.mint("INTENT"…)` を採っている（第1試行の実測でも `RREQ-00246` / `RINT-00339` が packet に入っていた） |
| 2 | **★観測経路は1つも採っていない** | **★`submit.py:368-401` に `IR.mint` は★0件**（★私の走査） |
| 3 | ∴ | **★D-144 で作った task の `knowledge_packet` に provenance が無く、★planner が fail-closed した** |

> **★これは「壊れた」のではない。★私の SPEC が、★BUILD 経路が持っていた前提を渡さないまま task を作らせた。**
> **★D-144 に続いて2回目の、★私の設計の抜けである。**

---

# 4. ★判定案（★Taka の8点。★確定は MGR）

| 配線 | ★判定案 | 根拠 |
|---|---|---|
| Request | **PASS** | 変わらず |
| RRI | **PASS** | 変わらず |
| **Task** | **PASS** | 作られ、引ける（変わらず） |
| **Runtime** | **★FAIL ← ★First FAIL** | **★PLAN の手前で止まるため到達しない。★新しい `ARUN`/`OBS` は0件** |
| Observation / Ledger / DW / Response | **FAIL（未到達）** | Runtime の下流 |

```
★Last PASS  : Task
★First FAIL : Runtime
★前進       : ★0点（★今回はコードを1行も変えていない。★確認だけである）
```

## 4-1. ★区別を保つ（★2通りに読める所を潰す）
```
★示したこと  : ★押しても流れない。★理由は PLAN の入力不足である
★示していないこと: ★「Task → Runtime の配線が壊れている」
★∴ 「配線が無い」と書かない。★「手前で止まるので到達しない」と書く（★IMPL の書き分けは正しい）
```

---

# 5. ★次に直す1件（★私の案。★1件だけ。★実施しない）

> ### **★観測経路の `knowledge_packet` に、★既存の `rri.intent_record.mint` で `trace_id` / `rri_request_id` / `rri_intent_id` を入れる。**

| | |
|---|---|
| **★場所** | **`twoder/submit.py` の観測分岐 1箇所**（★BUILD 経路が既にやっていることを、同じ関数で行うだけ） |
| **★作らないもの** | **新しい ID 族／新しい台帳／新しい API**（★既存の `mint` を使う） |
| **★1件で2つ塞がる** | **★第2試行で「対象外」とした「RRI の record ID が TRACE に入っていない」と★同じ欠落である**（`D-143` §2 の「解決不能な参照」） |
| **★GPU に触れない** | 取得コマンド・`utilization.gpu`・生出力は**★触らない** |

**★正直に併記**: **★これで PLAN が通るとは書かない。** **★通れば次は planner の出力の質、★通らなければ次の理由が出る。★どちらでも前進である。**

---

# 6. ★IMPL の作法で良かった点（★成果判定に効くものだけ）
```
★「Task→Runtime が壊れている」と書かず、「手前で止まるので到達しない」と★自分で書き分けた。
★`:8005` 0件を「呼ばれなかった」で済ませず、★コードの設計（provenance 先行検証）と突き合わせた。
★テスト0本を「0本＝走らせていない」と明記した（★「測って0」と「やっていない」を混ぜない）。
```

---
**決めたこと**: **①押しても流れない——私の独立測定5点が BUILT と全一致（新しい `ARUN`/`OBS` は0件・task 不変・`tasks` 157・PLAN 未記録） ②ただし「壊れている」ではない。`BUILD_PLANNER` は実際に呼ばれ、`trace_id`/`rri_request_id`/`rri_intent_id` の不足3件を理由として返して fail-closed した（`:8005` 0件は「provenance は LLM 呼び出しの前に検証」という設計と一致）——失敗理由を捨てない仕組みが効いた実例 ③First FAIL は `Runtime`（到達しない）、次の1件は観測経路の packet に既存の `mint` で provenance 3件を入れること（★BUILD 経路が持っていた前提を渡さなかったのは私の設計の抜けであり、D-144 に続いて2回目）。**
