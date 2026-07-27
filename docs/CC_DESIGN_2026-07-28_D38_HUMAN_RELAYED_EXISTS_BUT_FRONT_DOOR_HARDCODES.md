# 設計/監査 → MGR（写: Taka / IMPL）: **D-38 — 口は在る。`HUMAN_RELAYED` は「Claude が Taka の言葉を代理投入する」ためにこそ設計されている。★front door が `MACHINE_SUBMIT` を直書きしている**

- `BUILD_ROLE: 参照`（調査のみ。**投入していない・1行も直していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **受領した文書**: `CC_MGR_2026-07-28_D37_PREMISE_FAILS_TAKA_UTTERANCE_NEVER_ENTERED.md`

## 0. 答え（D-38-1）
> **★在る。** **しかも本件のためにこそ設計されている。**
> **★通れないのは、front door が `origin="MACHINE_SUBMIT"` を直書きしているからである。**

---

## 1. DS 側は、この場合を想定して作られていた【監査:CC-α】
```
再現: grep -n "def record_utterance" -A 14 ds/ds/phase0.py

def record_utterance(speaker, raw_text, conversation_id, timestamp, preceding_utterance_ref=None,
                     ts_source="UNSPECIFIED", origin="UNSPECIFIED", relayed_by=None, authored_by=None):
```
**docstring 逐語:**
> 「`origin`: 発話の出所。**HUMAN_DIRECT / HUMAN_RELAYED / MACHINE_SUBMIT / MACHINE_CODEGEN / UNSPECIFIED**。
> **★呼び手が申告する。推測しない。申告が無ければ UNSPECIFIED**（Build 4 PART 2 §7）。
> **HUMAN_RELAYED の時は `relayed_by`(誰が投入したか)と `authored_by`(誰が書いたか)を併記する
> ——「直接打った」と偽らないため。** 前向きのみ。過去レコードは遡って埋めない。」

> **∴ `HUMAN_RELAYED` ＋ `relayed_by=Claude` ＋ `authored_by=Taka` は、まさに本件の形である。**
> **∴ 「誰が書いたか」と「誰が入れたか」を分けて残す設計が、既に在る。**
> **★「直接打ったと偽らないため」という一文まで書かれている。** **我々はその機構を使わないまま、`MACHINE_SUBMIT` で1日投入し続けた。**

## 2. ★front door が塞いでいる【監査:CC-α】
```
再現: sed -n '85p' twoder/submit.py
  def submit(raw_input, conversation_id="taka-main", seed=0, admission_payload=None,
             ledger_path=None, formal_candidates=None, ts=None)      ← ★origin/authored_by の引数が無い

再現: sed -n '99,101p' twoder/submit.py
  utt = phase0.record_utterance("USER", raw_input, conversation_id, ts,
                                preceding_utterance_ref=…, ts_source=ts_source,
                                origin="MACHINE_SUBMIT")              ← ★直書き

再現: sed -n '536p' twoder/webui.py
  tr = SUB.submit(b.get("raw", ""))                                   ← ★raw しか渡さない
```
| 層 | 状態 |
|---|---|
| `ds.phase0.record_utterance` | **5種の `origin` と `relayed_by`/`authored_by` を受け取れる** |
| **`twoder.submit`** | **★引数を持たず `MACHINE_SUBMIT` を直書き** |
| `webui /api/submit` | **★`raw` しか渡さない** |

> **∴ 「呼び手が申告する。推測しない」という DS の規律が、front door で潰されている。**
> **∴ front door は、常に「機械が入れた」と申告する。** **人間が書いた文でも。**

## 3. ★これは本日の型の、いちばん深い1件である
| 本日の型 | 本件 |
|---|---|
| 機能は在るが、その場所で使われていない | **`HUMAN_RELAYED` は在るが、front door から使えない** |
| 宣言と実際が違う | **`speaker=USER` と記録しながら `origin=MACHINE_SUBMIT`** |
| 探した範囲に無いものを「無い」と書く | — |

**∴ 台帳の `speaker=USER` は、「人間が言った」を意味していない。**
**∴ MGR が §2 で見た「`speaker=USER` だが `origin=MACHINE_SUBMIT`」は、front door の直書きの結果である。**

**★そして重い含意**: **「全案件を台帳経由で管理する」は、この1行を直すまで成立しない。**
**逆に言えば、成立しない理由は、いま1箇所に特定された。**

## 4. 私は直さない（範囲を守る）
- **★1行も直していない。投入もしていない**（Taka の指示どおり・調査のみ）。
- **直すなら `submit()` に `origin` / `relayed_by` / `authored_by` を通し、`webui` から渡せるようにする。** **既定は現行のまま（`MACHINE_SUBMIT`）にすれば、既存の呼び出しは1つも変わらない。**
- **★ただしこれは「膨らませる」に当たらないかを MGR が判断すべきである。** **私は事実と、直す場合の最小形だけを出す。**

## 5. Gap Register（登録する。JSON にも同時に入れる）
| id | 内容 | 状態 |
|---|---|---|
| **`G-30`** | **`ds.phase0.record_utterance` は `HUMAN_RELAYED`/`relayed_by`/`authored_by` を受け取れるが、`twoder.submit` が引数を持たず `origin="MACHINE_SUBMIT"` を直書きしている。** ∴ front door から人間の発話を「人間が書いた」として記録できない。**「呼び手が申告する。推測しない」という DS の規律が front door で潰れている** | OPEN |

## 6. 残（★期限と担当を書く・`G-29` の規律）
| 未確認 | 誰が | いつ |
|---|---|---|
| `/api/ingest` が発話の取り込み口になり得るか | **CC-α** | **次の作業で読む**（`webui.py:602`） |
| 他に発話を入れる口が在るか（`command_surface` 等） | **CC-α** | 同上 |

---
*CC-α D-38。★口は在る——`ds.phase0.record_utterance` は `origin` に `HUMAN_DIRECT/HUMAN_RELAYED/MACHINE_SUBMIT/MACHINE_CODEGEN/UNSPECIFIED` を受け取り、`HUMAN_RELAYED` のときは `relayed_by`(誰が入れたか)と `authored_by`(誰が書いたか)を併記すると docstring に明記されている。**「直接打ったと偽らないため」という一文まで在り、まさに「Claude が Taka の言葉を代理投入する」本件のために設計されている。** ★通れない理由は front door が塞いでいること——`twoder.submit` は `origin`/`authored_by` の引数を持たず `origin="MACHINE_SUBMIT"` を直書きし、`webui /api/submit` は `raw` しか渡さない ∴ DS の「呼び手が申告する。推測しない」という規律が front door で潰され、front door は人間が書いた文でも常に「機械が入れた」と申告する。∴ 台帳の `speaker=USER` は「人間が言った」を意味していない。★「全案件を台帳経由で管理する」はこの1箇所を直すまで成立しないが、逆に成立しない理由が1箇所に特定された。私は1行も直さず投入もしていない（Taka 指示どおり調査のみ）。直す場合の最小形＝`submit()` に3引数を通し既定を現行のままにすれば既存呼び出しは変わらないが、膨張に当たるかの判断は MGR。`G-30` を登録し、残る未確認（`/api/ingest` が発話の取り込み口になり得るか等）には★誰が・いつを書いた（`G-29` の規律）。*
