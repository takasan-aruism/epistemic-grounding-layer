# 【BUILD SPEC】`EVO-0049` — **★機構は在るが ★分類を通らないと使えない。★docstring どおりに直す1行**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-03 04:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.6）** ／ **★9項目 確認済（★§7）** ／ **★3値 確認済（★§1）** ／ 親: `ITEM-2DER-EVO-0035`
- **★裁定の在り処**: `ITEM-2DER-EVO-0049` の `status_note`（逐語:「★勘定科目(分類)には触らない。分割だけ」「★1回の投入について、台帳から★複数の明細が読めること」「★『この変更で減る Claude の工程』を名指しで1行 書くこと。書けないなら書けないと書く」）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★3値（★条件(b)「既存で済むか」を先に当たった）

| 問い | 3値 | ★逐語・実測 |
|---|---|---|
| 明細の機構は在るか | **★在る** | `rri/rri/request_thread.py`：`open_thread` / `raise_question` / `dispose_question`、`_EVENTS = rthread_events.jsonl`（★**sole writer** と明記） |
| 本番から呼ばれているか | **★呼ばれていない** | 全 repo grep：呼び手は **`egl/docs/audit_rthread_stage1.py` と `stage2a.py` の2本だけ**（★監査スクリプト）。★本番0件 |
| **分類に触らず**使えるか | **★★使えない** | `raise_question` 逐語 `_, _accounts = ★_load_chart()` を **無条件で呼ぶ**／`_load_chart` は **fail-closed**／**`rthread_chart.json` は ★存在しない** ∴ **`RThreadChartUnavailable` で必ず落ちる** |

```
★★★∴ ★裁定「★分類に触らない・分割だけ」と ★既存機構が ★衝突している。
★★★★★但し ★これは ★実装の食い違いである——★同じ関数の docstring は逐語で
   「★default=UNCLASSIFIED(分類保留の特殊値)」「★★UNCLASSIFIED は chart に無くても常に有効(suspense の特殊値)」
   ★★と書いてある。★★コードだけが ★UNCLASSIFIED でも chart を読みに行く。
★★★★★★∴ ★★直すのは ★『docstring どおりにする』1行であって、★★勘定科目には ★触らない。
```

## 2. やること（★2箇所）

### 2-1. `rri/rri/request_thread.py` — **★分類保留は chart を要らない**（★docstring どおり）
```python
def raise_question(thread_id, memo, ts, account_id=UNCLASSIFIED):
-    _, _accounts = _load_chart()
-    if account_id != UNCLASSIFIED and account_id not in _accounts:
-        raise ValueError("off-chart account_id: %r (chart=%s)" % (account_id, sorted(_accounts)))
+    if account_id != UNCLASSIFIED:                    # EVO-0049: 分類する時だけ chart を要る(docstring 逐語)
+        _, _accounts = _load_chart()
+        if account_id not in _accounts:
+            raise ValueError("off-chart account_id: %r (chart=%s)" % (account_id, sorted(_accounts)))
```
```
★★分類する呼び方（`account_id` を渡す）は ★従来どおり fail-closed のまま＝★勘定科目の規律を ★緩めない
★★★緩むのは ★`UNCLASSIFIED`（★分類していない）だけ ＝ ★裁定「分類に触らない」に ★合う
```

### 2-2. `twoder/submit.py` — **★分割を1回 記録する**（★決定論のみ・LLM を呼ばない）
```python
# :302 の「★暫定の単純化: 1つの問い合わせ = 1つの明細」の直後（★その行のコメントは ★消さずに更新する）
from rri import request_thread as RT
_lines = [s.strip() for s in re.split(r"\n\s*(?:[-・*]|\d+[.)])\s+", raw_input) if s.strip()]
if len(_lines) >= 2:                                  # ★2件以上に割れた時だけ記録する(1件なら従来どおり)
    _th = RT.open_thread(TRACE.get("DS_INPUT_REF") or "", ts)
    _qs = [RT.raise_question(_th, ln[:200], ts) for ln in _lines]   # ★account_id は既定=UNCLASSIFIED
    _rec("RTHREAD_ID", _th); _rec("RTHREAD_QUESTION_IDS", _qs)      # ★既存の TRACE 欄に載せる
```
```
★★分け方は ★決定論のみ（★箇条書き記号 と ★番号）。★★LLM に切らせない（★今回の範囲は分割だけ）
★★★`RTHREAD_ID` / `RTHREAD_QUESTION_IDS` は ★TRACE の欄 ＝ ★新しい台帳ではない
★★★★`rthread_events.jsonl` は ★既存モジュールの ★既定の追記先（★`_EVENTS`・sole writer と明記済）
   ★★★★★★但し ★ファイルは ★まだ存在しない ∴ ★初回に ★1本 増える。★これを「新しい台帳」と見るかは ★MGR の裁定。
   ★★★見なすなら ★§5 の(B)へ切り替えること（★私は選ばない）
```

## 3. ★読む口と書く口を対で（★規律 v1.1）

```
★書く口: ★`rri.request_thread.raise_question`（★sole writer・★既存）
★読む口: ★`GET /api/resolve?id=RTHREAD-…` / `?id=Q-…`
   ★★★実測【★未確認】: ★`twoder/ids.py` に ★`RTHREAD-` / `Q-` の分岐が ★在るかを ★実装が先に確かめること。
   ★★★無ければ ★★読む口が無い ＝ ★★★★この SPEC は ★そこで止めて報告すること（★書けるが読めない形を作らない）
```

## 4. 受入

```
★(1) ★実際の長い投入を1件 選び（★箇条書きか番号が2件以上 在るもの）、★`RTHREAD_QUESTION_IDS` が ★2件以上
★(2) ★★台帳から機械で読める（★`GET /api/resolve?id=Q-…`）——★セッションの情報を使わない（★EVO-0051 と同じ厳しさ）
     ★★読めなければ ★§3 のとおり ★★止めて報告（★「書けた」で終わらせない）
★(3) ★★陰性対照: ★1明細前提の既存の読み方が壊れていない。★壊れた件数を ★数で書く（★0件なら0件と書く）
     ★★確かめる先: ★`GET /api/state` ／ ★`/api/roadmap` ／ ★`next=` の抽出（★44/46 の内訳が変わらないこと）
★(4) ★★母数: ★分けられた投入と ★分けられなかった投入の ★件数、★打ち切りの有無
★(5) ★分類していないこと: ★全ての `account_id` が ★`UNCLASSIFIED`（★1件 逐語で示す）
★(6) ★戻せる ／ ★(7) ★Claude が書いた行数（★2DER の実績に数えない）
★★★★★予告を投入前に書く: ★変更行数 ／ ★(1) の件数 ／ ★(3) で壊れると思う件数
```

## 5. ★★「この変更で減る Claude の工程」— **★書けない。★書けないと書く**（★裁定の指定）

```
★裁定の期待: 「★長文を読んで何件の案件か切り分ける」工程が ★Claude から 2DER へ移る第一歩。
★★★私の判定: ★★本件では ★減らない。★理由を2つ、名指しで書く:
   ★① ★分け方が ★決定論（箇条書き・番号）に限られる ∴ ★★散文の長文は ★1件のまま。
      ★Taka の依頼は ★散文が多い（★本日の投入を私が読んだ範囲では ★箇条書きは少数）【★件数は ★受入(4) で出る】
   ★② ★「何件の案件か」の ★判断そのものは ★誰にも移していない——★2DER は ★切った結果を ★記録するだけで、
      ★★切るかどうかを ★決めていない。★決めているのは ★依然 ★書式（＝人が箇条書きにしたかどうか）である。
★★★★∴ ★★これは「移った」ではなく「★移せる形の器ができた」である。★★工程は ★1つも減っていない。
★★★★★★次の閉塞（★ここが本当の壁）: ★★散文を ★何件の案件かに切るのは ★LLM 判定であり、
   ★★★それを ★2DER にやらせるかは ★★勘定科目（EVO-0050）と ★不可分になる ∴ ★★本件の範囲外。
```

## 6. ★増える代わりに廃止（★規律9）
```
★畳めるもの: ★★無い。★§5 のとおり ★工程は減っていない ∴ ★「畳めた」と ★書かない。
★★増えるもの: ★`rthread_events.jsonl` が ★1本（★§2-2 の但し書き）。★★MGR が「新しい台帳」と見なすなら ★止める。
```

## 7. ★9項目（私の分）
```
1 置いたなら読めるか＝★★§3 で ★読む口の有無を ★先に確かめさせる（★無ければ止める）
2 読めるなら書けるか＝★書く口 `raise_question` と ★読む口 `/api/resolve` を ★対で名指しした
3 理由を捨てない＝★★§5 で「★減らない」を ★理由2つで書いた（★期待で埋めない）
4 作っていないのでは＝★★機構は ★既に在る。★無いのは ★chart 無しで通る道だけ（★docstring には在る）
5 走ったか＝★受入(1)(2) は ★実投入で測る／6 名前＝★`UNCLASSIFIED` / `RTHREAD-` / `Q-`（★既存。★改名しない）
7 依頼と試験の矛盾＝★★本件そのもの（★docstring と ★コードが ★食い違っている）
8 計器が自分を数えないか＝★受入(2) は ★台帳から読めた値だけを使う
★9 増える代わりに廃止＝★§6（★★畳めるものが無い、と ★正直に書く）
```

## 8. 禁止
```
★`rthread_chart.json` を作る（★＝勘定科目に触る・★裁定と Taka 指示に反する）
★分類する呼び方の fail-closed を緩める（★`UNCLASSIFIED` 以外は ★従来どおり）
★LLM に切らせる（★本件は ★決定論の分割だけ）／ ★:302 のコメントを ★黙って消す（★更新する）
★読む口が無いまま書く ／ ★新しいエンドポイント・状態語を作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
