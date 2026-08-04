# 【BUILD SPEC】`EVO-0049` — **★段0 と段3 を worker に。★門は明細ごとに回す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 07:1x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.11）** ／ **★9項目 確認済（★§8）** ／ 親: `ITEM-2DER-EVO-0035` ／ 方針: `ITEM-2DER-EVO-0057`（Taka 裁定）
- **★v1.8 の宣言**: **★核は在る・2件**（★Taka の裁定で確定済＝段0 と段3）
- **★私の予告**: ★worker の行数は **書かない**（★MGR と同じ理由＝本日4回連続で外した）／★**2件とも純関数で出る**／★Claude の配線 **8〜16行**
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★既存資産（★作り直さない・★実物を確かめた）

```
★`preflight_gate.PG.detect(text, failure_hits=…)` は ★テキスト1本を受ける（`submit.py:288` 逐語 `pg = PG.detect(raw_input, failure_hits=_fh)`）
★★∴ ★明細ごとに ★そのまま回せる（★門を作り直さない・★引数の形も変えない）
★`decision` は ★CLARIFY_FIRST / HOLD_AS_WEAK_CLAIM / STRONGLY_DISCOURAGE_DW / ALLOW_WITH_WARNING / ALLOW（★Taka 裁定の逐語と一致）
★`request_thread` は ★明細=`raise_question` / 揺れ=`OPEN_GAP` / 聞き返し=`present_gaps`・`human_replied`（★既に在る）
```

## 2. ★★新規は3つだけ（★Taka の逐語）

| # | 何を | 誰が |
|---|---|---|
| (a) | 明細に分ける器 | **★worker（★段0＝候補の列挙）** |
| (b) | 明細ごとに門を回す配線 | **★Claude（★`PG.detect` を回すだけ）** |
| (c) | 保存則の検査 | **★worker（★段3）** |

## 3. ★★契約①（★段0・★割らない＝候補を列挙するだけ）

**★依頼文**
```
長い依頼文の「切れ目の候補」を列挙する純関数 impl.segment_candidates を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
text = 依頼文の原文（str）
戻り値 = {"text_len": int, "candidates": [ {"start": int, "end": int, "kind": str}, ... ]}

・★原文を1文字も変えない。★戻り値に原文の写しを入れない（★位置だけ返す）。
・candidates は ★start/end の半開区間 [start, end) で、★text[start:end] が その断片。
・kind は "PARAGRAPH" / "BULLET" / "SENTENCE" の★3語のいずれか。★他の語を作らない。
・切れ目の見つけ方（★この順で重ねる。★重複した範囲は 後から出たものを ★捨てる）:
    ① 空行（\n\n 以上）で区切れる範囲 → "PARAGRAPH"
    ② 行頭が - ・ * または 数字+. または 数字+) の行 → "BULLET"
    ③ 。！？ の直後で区切れる範囲 → "SENTENCE"
・★候補は ★text 全体を覆う（★欠落を作らない）。★端の空白だけの範囲は ★捨てない（★kind は直近の種類）。
・★1つも見つからなければ candidates は [{"start":0,"end":len(text),"kind":"PARAGRAPH"}] の1件。
・text が空文字なら candidates は []。text_len は常に len(text)。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def segment_candidates(text):
<<<2DER:END>>>
```

**★封印試験（★fixture は ★rri_records の実物から取る・★手書き禁止）**
```
★★実装が ★最初にやること: ★`GET /api/etrace?run_id=…` の ★`ENTRY` の `raw_input`（★実物の依頼文）を ★1本 取り、
   ★その先頭 300 字を ★fixture にする。★★手で作らない（★2026-08-03 の事故＝手書き fixture が実形式と違った）。
★★試験の本数は ★実装が決めてよいが、★★次の7つの意図を ★1つずつ 別の関数にすること（★1つに2つの意図を入れない）:
   ① 空文字 → candidates == []
   ② 切れ目が無い文 → 1件・kind == "PARAGRAPH"
   ③ 実物の依頼文 → ★2件以上に割れる
   ④ ★★保存則: すべての候補の (end-start) の和 == text_len（★欠落0）
   ⑤ ★★重複0: 候補を start 順に並べると ★前の end == 次の start
   ⑥ kind が ★3語の外に出ない
   ⑦ ★★原文が壊れない: "".join(text[c["start"]:c["end"]] for c in candidates) == text
```

## 4. ★★契約②（★段3・★保存則の検査）

**★依頼文**
```
明細が原文を過不足なく覆っているかを検査する純関数 impl.check_conservation を作ってください。
（★本番モジュールを import しない・標準ライブラリのみ・骨格は1文字も変えない・試験は import impl）

■ 規則（これだけ）
text_len = 原文の長さ（int）
spans = [ {"start": int, "end": int}, ... ]（★順不同でよい）
戻り値 = {"ok": bool, "covered": int, "missing": [[int,int],...], "overlap": [[int,int],...]}

・covered = 重複を除いて覆われた文字数。
・missing = 覆われていない範囲を start 順に。★無ければ []。
・overlap = 2回以上 覆われた範囲を start 順に。★無ければ []。
・ok は ★missing == [] かつ overlap == [] の時だけ True。
・spans が空で text_len が 0 なら ok は True（covered 0・missing []・overlap []）。
・★start >= end の span は ★無視する（★エラーにしない・★covered に数えない）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def check_conservation(text_len, spans):
<<<2DER:END>>>
```

**★封印試験（★意図ごとに1本）**
```
① 完全被覆 → ok True / missing [] / overlap []
② 欠落あり → ok False / missing に その範囲
③ 重複あり → ok False / overlap に その範囲
④ 欠落と重複が同時 → ok False / 両方 出る
⑤ 空(0, []) → ok True
⑥ start>=end の span を混ぜても ★結果が変わらない
⑦ spans が ★順不同でも 同じ結果
```

## 5. ★Claude が書く配線（★(b) のみ・★8〜16行と予告）

```python
# twoder/submit.py の 分割記録ブロック — ★段0 の候補で割り、★明細ごとに門を回す
from twoder.segment_candidates import segment_candidates as _seg
from twoder.check_conservation import check_conservation as _cons
_c = _seg(_split_src)
_spans = _c["candidates"]
_cons_r = _cons(_c["text_len"], _spans)                      # ★段3
_gates = [PG.detect(_split_src[s["start"]:s["end"]], failure_hits=_fh) for s in _spans]   # ★段1(明細ごと)
_rec("SPLIT_CONSERVATION", _cons_r)
_rec("SPLIT_GATES", [{"start": s["start"], "end": s["end"], "kind": s["kind"],
                      "decision": g["decision"], "triggered": g["triggered"]}
                     for s, g in zip(_spans, _gates)])
```
```
★★門は ★作り直さない=★`PG.detect` を ★そのまま呼ぶ（★引数の形も変えない）
★★★★`raise_question` に渡すのは ★従来どおり（★本件では ★明細の作り方を変えない＝★段2 は ★次の単位）
★★★★★★記録は ★TRACE の欄に足すだけ（★新しい台帳を作らない）
```

## 6. ★★対照（★先に固定・★Taka 指定をそのまま）

```
★陰性 = ★段落だけで機械的に割ったものと ★候補が ★変わらないなら ★★『不活性』と書く（★DE-0558）
★陽性 = ★わざと2用件を1文に詰めた入力（★実物から作らず ★★実物に無ければ『無い』と書く）が ★割れるか
★再現 = ★3シードで収束するか（★段0 は決定論 ∴ ★3回 呼んで ★同一であることを示す）
★保存則 = ★欠落0・重複0（★段3 が機械で出す）
★★★★★4つとも ★結果を書く。★差が出なければ ★『差が出なかった』と書く（★それも収穫）
```

## 7. 受入
```
★(1) ★worker が ★2件（段0・段3）を書く（★Claude は本文0行・★実行記録で確認）
★(2) ★封印試験 全通（★fixture が ★実物由来であることを ★逐語で示す＝どの run_id から取ったか）
★(3) ★★保存則が ★機械で出る（★`check_conservation` の戻りを ★逐語で）
★(4) ★★門の判定が ★明細ごとに出る（★`SPLIT_GATES` に ★明細数と同じだけ ★decision が並ぶ）
     ★★★これが Taka の (2)『割っただけは弱い』への ★担保である
★(5) ★★4つの対照の結果を ★全部 書く（★陰性で差が出なければ ★『不活性』と書く）
★(6) ★Claude の配線行数 ／ ★(7) ★戻せる ／ ★(8) ★61本を走らせない
★★★★(9) ★出せなかったら『出せなかった』と書いて止まる
★★★★★★『理解できるようになった』と ★書かない（★裁定の逐語）
```

## 8. ★9項目（私の分）
```
1 置いたなら読めるか＝★`SPLIT_CONSERVATION` / `SPLIT_GATES` は ★`/api/state` の TRACE 欄で読める
2 読めるなら書けるか＝★書く口は ★既存の `_rec`（★新しい台帳を作らない）
3 理由を捨てない＝★★門の `decision` を ★明細ごとに ★全部 残す（★1つに丸めない）
4 作っていないのでは＝★★門も明細の器も ★既に在る。★無いのは ★候補の列挙と ★保存則の検査だけ
5 走ったか＝★受入(3)(4) は ★実投入で測る／6 名前＝★既存語（`decision` / `triggered`）
★7 依頼と試験の矛盾＝★依頼文に書いた ★3語・順番・保存則を ★全部 試験で縛った（v1.11）／★意図ごとに1本
8 計器が自分を数えないか＝★fixture は ★実物から取る（★私が作らない）
★9 増える代わりに廃止＝★★「1問い合わせ＝1明細」の暫定（`submit.py:302`）を畳む。
   ★★但し ★段2（分岐）と ★4軸の測定は ★本件に入れない ∴ ★「理解できる」とは ★書かない
```

## 9. 禁止
```
★`preflight_gate` / `request_thread` / `request_resolution` を作り直す・改造する
★段0 で ★割る（★候補を列挙するだけ）／ ★原文を書き換える・写しを戻り値に入れる
★4軸の LLM 測定を入れる（★後回し・裁定の逐語）／ ★段2 の分岐を実装する（★次の単位）
★fixture を手で書く（★実物から取る）／ ★1つの assert に2つの意図を入れる
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
