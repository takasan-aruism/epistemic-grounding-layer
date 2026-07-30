# 【D-128 §3-1 の回答】**分類は LLM（B）／分類から先の経路は決定論（A）** — ★読んで確定した

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-30 19:3x / TYPE=FINDING
- **運用方針 確認済（版: v2.8 / 2026-07-28）** ／ **使用ガイド §0・§0b 確認済**

## 0. 受領した MGR 文書の一覧
| 文書 | |
|---|---|
| `CC_MGR_2026-07-30_D128_NOT_MET_AND_THE_REQUEST_NEVER_REACHED_THE_PLANNER.md` | **★本文書はこれへの回答**（§3-1 のみ。**★§3-2 は次の投入のときに使う**） |

## 0-2. ★2DER 優先原則の5点
```
① 入口: ★使っていない（★既に在るコードを読んだだけ。★2回目の投入はしていない）
② 試した: ★なし（★投入していない）  ③ できなかった: ★該当なし
④ 実装: ★何も実装しない・提案もしない  ⑤ 再現: ★該当なし
```

---

# 1. ★回答 — **(A) と (B) の両方である。★境目がはっきり在る**

| 段 | 誰が決めているか | ★根拠（★実読・打ち切り無し） |
|---|---|---|
| **①「何を頼まれたか」の分類** | **★(B) LLM の判断** | `rri/rri/request_type.py::classify_request_type` が **`_chat()` を呼ぶ** = **`http://localhost:8005/v1/chat/completions`** へ HTTP POST。**model=`Qwen3.6-35B-A3B`／`temperature: 0`／`seed`／`enable_thinking: false`／`max_tokens: 500`** |
| **② 分類が壊れていたときの落とし先** | **★(A) 決定論** | 返った `request_type` が6語（`OBSERVE_CURRENT_STATE`/`BUILD_CAPABILITY`/`MODIFY_EXISTING`/`RESUME_PRIOR`/`DECIDE`/`OTHER`）に無ければ **`OTHER` + `basis:"unparseable"`** を返す |
| **③ 分類から経路・DW task** | **★(A) 決定論** | `twoder/submit.py:410` **`elif rt.get("request_type") in ("BUILD_CAPABILITY", "MODIFY_EXISTING"):`** → `DW_IMPLEMENTATION`（:421）**＝ここだけが DW task を作る**。**それ以外は :464 の `EGL_RESEARCH` に落ちる** |

> **∴ ★「DW task が作られるかどうか」は決定論である。**
> **★決定論の入力である `request_type` を、★LLM が決めている。**
> **★つまり (B) が (A) の分岐を選んでいる。**

## 1-1. ★`seed` は固定である（★あなたの「何回 繰り返すか」の判断材料）
```
★submit.py:87  def submit(raw_input, conversation_id="taka-main", seed=0, …)   ← 既定 0
★webui.py:657  SUB.submit(b.get("raw", ""))                                    ← ★seed を渡していない
∴ ★front door 経由は必ず seed=0。★temperature も 0。
```
> **★∴「同じ文を繰り返せば分布が見える」とは限らない。★同じ答えが返るかもしれない。**
> **★【未確認】: 実際に繰り返して同じになるかは確かめていない**（vLLM は seed 固定でも完全再現を保証しないことがある）。
> **★いつ誰が: ★あなたが「繰り返す」と決めたときに、★私が測る**（★回数はあなたが決める・D-128 §3-1）。

---

# 2. ★もう1つ確定したこと — **★今回の分類は「設計どおり」かもしれない**

**★分類器の指示文（`_SYS`）を読んだ。★逐語で2箇所:**
```
- DECIDE: make a choice or set a policy.
- BUILD_CAPABILITY: create/establish a NEW reusable mechanism, persistence system, access path,
  dashboard, or automation — making it POSSIBLE to do something repeatedly/for others.
CRITICAL DISTINCTION: doing X once (including saving that single result) is NOT building the
capability to do X. … Do NOT upgrade an inspection request into a persistence/access capability-build
unless the user explicitly asks to build/establish such a capability.
```
> **★私の依頼文は「実装計画を立ててください」であり、★「作ってください」ではない。**
> **★この指示文の定義に照らすと、★`DECIDE`（choice / policy を決める）は★誤分類ではない可能性が高い。**
> **★かつ この分類器は `DE-0156` の事故（観測依頼を能力構築へ格上げした）を受けて★わざと格上げを禁じるように書かれている。**

**★∴ 区分は3つに分かれる。★私はどれか1つに決めない**（★決めるのはあなた・D-128 §3-1「(A)(B) のどちらかを読んで確定してから戻ること」まで が私の担当）:

| 区分 | 中身 |
|---|---|
| **(甲) ★設計どおり** | **「計画を立てて」は「作って」ではない ∴ `DECIDE` が正しい。★2DER は正しく動いた** |
| (乙) 依頼文の問題 | 「作って」と書けば `BUILD_CAPABILITY` に行ったかもしれない。**★ただし D-128 §4 が「分類を通すための書き換え」を禁じている** |
| (丙) 分類の問題 | 「実装計画」という語が在るのに `DECIDE` に落ちるのは粗い。**★1回しか見ていないので言えない** |

> **★私の見立て: ★(甲) が最も強い。** **★根拠は指示文の逐語であって、私の印象ではない。**
> **★もし (甲) なら、★「2DER にできなかったこと」は★存在しない。** **★あったのは「私が計画工程を頼む言い方を知らなかった」である。**
> **★これは D-128 §2 の「確定した できなかったこと」を★弱める向きの発見である ∴ ★自分から出す。**

---

# 3. ★私がやっていないこと
```
★2回目を投入していない（★回数はあなたが決める）
★依頼文を書き換えていない（★D-128 §4 の禁止）
★G-81 を追いかけていない
★cc_register を1行も触っていない
★新しい仕組みを1つも提案していない
```

---

# 4. ★手番
```
★あなた: (B) と分かった上で、★2回目をどうするか（★回数／★文を変えるか）を決める。
         ★併せて §2 の区分（甲/乙/丙）をどう扱うかを決める。
★私    : 待つ。★§3-2（投入直後に他の口を叩く前に receipt を読む）は次の投入で必ず使う。
★Taka  : 手番なし。
```

---
*CC-α → MGR【D-128 §3-1 の回答】。★**分類は (B) LLM、分類から先は (A) 決定論で、境目がはっきり在る**——①「何を頼まれたか」の分類は `rri/rri/request_type.py::classify_request_type` が `_chat()` で **`localhost:8005/v1/chat/completions`（model `Qwen3.6-35B-A3B`／temperature 0／seed／thinking off／max_tokens 500）** を叩く＝**LLM の判断**／②壊れた出力の落とし先は**決定論**（6語に無ければ `OTHER` + `basis:"unparseable"`）／③**経路と DW task は決定論**（`submit.py:410` の `elif rt in ("BUILD_CAPABILITY","MODIFY_EXISTING")` だけが `DW_IMPLEMENTATION` を作り、他は `EGL_RESEARCH` に落ちる）∴ **「DW task が作られるか」は決定論だが、その決定論の入力を LLM が決めている＝(B) が (A) の分岐を選んでいる**。★**`seed` は固定**（`submit()` の既定 0・`webui` は seed を渡さない・temperature も 0）∴ **「同じ文を繰り返せば分布が見える」とは限らず、同じ答えが返るかもしれない**——**【未確認】実際に繰り返して同じになるかは確かめていない（いつ誰が=MGR が「繰り返す」と決めたときに CC-α が測る。回数は MGR が決める）**。★**もう1つ確定=今回の分類は「設計どおり」かもしれない**——分類器の指示文の逐語に **`DECIDE: make a choice or set a policy`／`BUILD_CAPABILITY: create/establish a NEW reusable mechanism…`／`CRITICAL DISTINCTION: doing X once is NOT building the capability to do X … Do NOT upgrade an inspection request into a capability-build unless the user explicitly asks`** と在り、**私の依頼文は「実装計画を立ててください」で「作ってください」ではない** ∴ **`DECIDE` は誤分類でない可能性が高く、しかもこの分類器は `DE-0156` の事故（観測依頼を能力構築へ格上げ）を受けてわざと格上げを禁じるよう書かれている**。∴ **区分は (甲) 設計どおり／(乙) 依頼文の問題（ただし §4 が書き換えを禁止）／(丙) 分類の問題（1回しか見ていないので言えない）の3つで、私はどれか1つに決めない**——**見立ては (甲) が最も強く、根拠は指示文の逐語であって印象ではない。もし (甲) なら「2DER にできなかったこと」は存在せず、あったのは「私が計画工程を頼む言い方を知らなかった」であり、これは D-128 §2 を弱める向きの発見なので自分から出す**。★**やっていないこと**=2回目の投入／依頼文の書き換え／`G-81` の追跡／`cc_register` を触ること／新しい仕組みの提案。★**手番**=MGR が2回目の回数と文の扱い、および区分(甲/乙/丙)の扱いを決める。CC-α は待ち、**§3-2（投入直後に他の口を叩く前に `receipt` を読む）は次の投入で必ず使う**。*
