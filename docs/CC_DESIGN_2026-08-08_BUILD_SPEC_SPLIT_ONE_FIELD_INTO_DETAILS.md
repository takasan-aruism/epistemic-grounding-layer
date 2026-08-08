# 【BUILD SPEC＋訂正】★19件のうち **1件で通す** ／ ★併せて **MGR の前提を1つ 訂正**（★上限は 32 に ならない）

- **宛: 実装(IMPL)** ／ 写: MGR / Taka / 監視 ／ 発: 設計・監査(CC-α) ／ 2026-08-08 18:10 ／ TYPE=BUILD SPEC＋訂正
- **開発者規律 確認済（版: v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ **効く先＝1と3と4**
- **★新台帳0 ／ ★新エンドポイント0 ／ ★合格済の核（`trace_entry_v2`）に 1文字も 触らない**

---

## 0. ★★先に 訂正（★私の分母の 読み方が 粗かった）

MGR の裁定理由(1) は逐語で こうです。

> 『★形を直せば★機械が「在る/無い」を答えられる＝★★いま実物を検査できるのは13件だけ・**上限が32件まで上がる**』

```
★★これは 成り立ちません。★理由 = ★19件は ★★1つの形では ありません。
★私が 決定論で 分け直した（★契約 `trace_entry_v2` の出力＋★欄の中身の 形だけで 分けた・LLM 0回）:

  ★形A ★★7件 = ★「/」で 名前が 複数 入っている（★分ければ 鍵に なりうる）
      C-CC-REGISTER(6語) C-ETRACE(5語) C-ARTIFACT-REGISTRY(3語)
      C-RRI-PREFLIGHT(2語) C-DW-DISPATCH(2語) C-BUILD-PLANNER(2語)
      C-QWEN-WORKER(★file 欄が 2本)
  ★形B ★★4件 = ★鍵に 注記や 省略が 付いている（★落とせば 鍵に なりうる・★但し 落とし方が 形Aと 別）
      EP-RESOLVE-ETR『resolve(ETR-*)』 EP-OPERATOR『dispatch_once caller (line 151)』
      C-EGL-ACCOUNTS『…s_embed_axes.py, s_account_axes.py, …』(★2本目以降は ★前置きが 落ちている)
      C-EGL-EXECARCH（★同じ）
  ★形C ★★8件 = ★★欄に 入っているのが ★そもそも 鍵ではない（★★新しい情報が 要る＝146件と 同じ手当て）
      EP-CLI-MODULE『__main__ via -m twoder.submit』 EP-CLI-DIRECT『python3 twoder/submit.py』
      EP-WEBUI-SUBMIT『POST /api/submit』 EP-WEBUI-RUNNEXT『POST /api/run_next』
      EP-WEBUI-RESOLVE『GET /api/resolve』 EP-COMMAND-RUN『PAGE / openByRun』
      C-DS-SELECT（★file 欄が『-』） C-RRI-AXES-SOURCE『4軸のうち context_anchoring のみ』
  ★★7+4+8 = ★19 ＝ 一致。

★★∴ ★『手当てが1種類で済む』は ★★成り立ちません（★少なくとも 3種類）。
★★∴ ★上限は ★32 では なく ★★13 + 7 = ★★最大でも 20（★形A が 全部 当たった場合）。
   ―― ★形B の4件は ★別の手当て ／ ★形C の8件は ★★146件と 同じ手当て（★情報を 足す話）。
★★★★但し ★MGR の裁定そのもの（★19件を先に・★1件で通す）は ★変えません。
   ★理由 = ★形A は ★★欄の形だけで 片が付く 唯一の群 ∴ ★『欄の形の手当て』を 実演する 場所として 正しい。
```

**★私の非**: 前便で私は 19件を「欄の形の話」と **一括りに** 書きました。**中で3つに割れます**。
一括りにしたまま進めば、**形B・形C を「直したのに当たらない」と読み違える**所でした。

## 1. ★★選ぶ規則（★答えを 見る前に 書く・★これが MGR の心配への 答え）

MGR は こう書いています ―― 『(a)19件から1件を★設計が選ぶ(★私は選ばない=★都合のよい1件を選べてしまう)』。

```
★★∴ ★私は「1件」を 名指しで 選ばず、★★先に 規則を 書いて、★規則が 決めた1件を 使います。

  ★規則 = ★★形A のうち、★★入っている名前の数が いちばん多い 1件。
  ★★当てはまる物 = ★★`C-CC-REGISTER`（★6語 ／ ★2位は C-ETRACE の5語 ∴ ★同点なし）。
  ★★★私は ★この6語が 実物に 在るかを ★★まだ 1度も 引いていません（★『後』の値を 知らずに 選びました）。
```

## 2. ★★直す前の 3値（★逐語・★私が 引いた値）

```
id     = C-CC-REGISTER          （★区分 components[20]）
file   = "egl/docs/cc_register.py"
symbol = "record_doc / record_done / pending / counts / doc_id_for / normalize_path"
★★trace_entry_v2 の 戻り =
   verdict  = "UNTRACEABLE"
   file     = "egl/docs/cc_register.py"
   symbol   = "record_doc / record_done / pending / counts / doc_id_for / normalize_path"
   missing  = "symbol_not_an_identifier"
   searched = []            ★★＝ ★1つも 見ていない（★『無い』とは 言っていない）
```

**★陰性に使う1件（★同じく 先に 書く）**

```
id     = EP-WEBUI-SUBMIT       （★区分 entrypoints[2] ／ ★形C）
file   = "twoder/webui.py" ／ symbol = "POST /api/submit"
★★これも 機械には ★『/ で区切られた 3つの名前』に 見えます（★`POST` `api` `submit` は ★全部 識別子の形）。
   ―― ★★∴ ★★核は これも 分けます。★★分けた結果が どうなるかが ★陰性の 中身です（★§6(3)）。
```

## 3. ★★作る物（★1つだけ・★新しい核 1本）

```
★置き場   = /home/takasan/twoder/split_symbol_details.py
★関数名   = split_symbol_details
★署名     = split_symbol_details(entry)
★行数     = ★★上限 60 行（★docstring を除く）
★禁止     = ★file を 読まない（★`open(` `Path(` `os.` を 1つも 書かない）／★他の module を import しない
★理由     = ★合格済の `trace_entry` と 同じ作法（★中身は 呼び手が 渡す・★核は 判定だけ）
```

**★骨格（★`<<<FILL>>>` を 置かない形＝★本日 1件で 通った形）**

```python
def split_symbol_details(entry):
    """1つの記述の symbol 欄に名前が複数入っている時、名前1つずつの記述に分ける。

    entry は設計図の1つの記述(dict)。戻り値は list。
    要素は元の記述を写した dict で、symbol が1つの名前に置き換わっている。

    読み方は4通り。上から順に、最初に当てはまった1つで決める。
      1. entry が dict でない
         -> 空の list を返す
      2. entry["symbol"] が str でない、または前後の空白を除くと空
         -> 空の list を返す
      3. entry["symbol"] を "/" で切り、片ごとに前後の空白を除き、空になった片を落とす。
         残った片が 1個以下
         -> 空の list を返す
      4. 上のどれでもない場合、残った片の数だけ dict を返す。
         i 番目(0から数える)の dict は entry を写した上で、次の3つを入れる。
           symbol       = i 番目の片
           detail_index = i
           detail_of    = entry.get("id")
         元の entry は変えない。呼び手が元の entry を後で読んでも symbol は元のまま。

    片の順番は元の並び順のまま。大文字小文字はそろえない。
    """
```

**★worker に 届くのは 3面だけ（★規律 v1.18）** ∴ 上の読み方は **docstring の中に 置いてあります**。
**この .md の本文は worker に 1文字も 届きません**。実装は **骨格と 試験を そのまま 渡してください**。

## 4. ★★封印試験（★11本・★規則は 名前の側にも 置く）

```
test_dict_ではない物を渡すと空のlistを返す
test_symbol_が文字列ではない時は空のlistを返す
test_symbol_が空白だけの時は空のlistを返す
test_名前が1つだけの時は空のlistを返す
test_スラッシュで区切られた6つの名前を6つの記述に分ける
test_分けた記述のsymbolは前後の空白が落ちている
test_分けた記述は元の記述のfileとidをそのまま持つ
test_分けた記述のdetail_indexは0から順に入る
test_分けた記述のdetail_ofには元のidが入る
test_呼んだ後も元の記述のsymbolは元のまま
test_空の片は落ちて数に入らない
```

各試験の docstring に **その1本が何を守るか**を1文で書いてください（★名前と docstring は worker に届きます）。

## 5. ★★直し方（★設計図は 私も MGR も 直接 書かない）

```
★(1) ★核が 6明細を 作る（★値を 決めるのは 機械＝★空白と「/」だけで 決まる）。
★(2) ★配線（★Claude が 書く・★★上限 10 行）=
      ★設計図 `egl/docs/2DER_EXECUTION_ARCHITECTURE.json` の `components` から
      ★`id == "C-CC-REGISTER"` の 1件を 取り、★核に 通し、★戻った 6件で ★その1件を 置き換えて 書き戻す。
      ―― ★★書く中身は ★核の 戻り値そのもの（★私が 手で 書いた文字を 入れない）。
★(3) ★2DER の口で 登記と commit（★git を 直に 叩かない）=
      ★`artifact_registry.register(...)` ／ ★`record_change(...)` ／ ★`commit_one(...)`
      ―― ★`commit_one` は ★置いた 1本だけを add する 作り ∴ ★2本 置くなら ★2回 呼ぶ。
★★★★LLM の呼び出し = ★★値を 決める呼び出しは 0回。
   ★核を 作る worker の 呼び出しは ★★別に 数えて 報告してください(★『0回』と 混ぜない)。
★★★★合計件数は 変わります = ★★178 → 183（★components 23 → 28）。
   ―― ★これは ★★ずれでは なく ★明細化そのもの（★EVO-0049 と 同じ形）。★先に 書いておきます。
```

## 6. ★★受入（★口・欄・id・逐語・陰性）

```
★(1) ★口 = ★核を 走らせた出力 ／ ★id = ★`C-CC-REGISTER`
     ★欄 = ★`verdict` / `file` / `symbol` / `missing` / `searched`
     ★読める物 = ★★6明細 それぞれの 3値。
     ★★『在る』(PRESENT)が 出た明細は ★★file と symbol を ★逐語で 出すこと。
     ★★『無い』(ABSENT)が 出た明細も ★★file と symbol を ★逐語で 出すこと
        ―― ★理由 = ★★それが Taka の言う『★本当にその機能があるのか』の 答えそのもの。
★(2) ★★合計 = ★★183（★内訳の 3値の 合計が 183 と 一致すること）。
     ★★`C-CC-REGISTER` は ★もう 出てこないこと（★1件が 6件に 置き換わった＝★残っていたら 二重）。
★(3) ★★陰性 = ★★`EP-WEBUI-SUBMIT`（★形C）を ★同じ核に 通した結果を ★併せて 出すこと。
     ★★★設計図は 直さない（★通すだけ・★読むだけ）。
     ★読める物 = ★3明細（`POST` `api` `submit`）の 3値。
     ★★★どちらでも 結果です=
        ★全部 ABSENT なら → ★★『欄の形を 直しても、★鍵でない物は 在るに ならない』＝★機械は 嘘を つかない。
        ★1つでも PRESENT なら → ★★その file と symbol を 逐語で 出すこと。
          ―― ★★これは 失敗では なく ★★『機械が 嘘を つく所が もう1つ 見つかった』という 結果です。
             ★見つけたら ★そこで 止めて ★設計へ 返してください（★直さない）。
★(4) ★★合格済の `trace_entry_v2.py` の 中身が ★1文字も 変わっていないこと（★sha を 前後で 出す）。
★(5) ★戻せる ＝ ★口 `GET /api/resolve?id=CHG-****`
     ★欄 = ★`after_commit`（★null ではない）／ ★`revert_scope.complete` = ★true
     ★★その commit に ★置いた その1本以外の file が 入っていないこと（★`git show --stat` の 逐語）。
★(6) ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限 10 行（★実数を 報告する）。
★(7) ★★答えられなかった物は ★『答えられなかった』と 書く（★規律3）。
     ―― ★★特に ★設計図を 2DER の口で 書き戻せなかった場合は ★★『どの口が 無いのか』を 1行 書く。
        ★★それが 次に作る機能です（★私は 今 それを 作れと 言っていません）。
```

## 7. ★★言っていないこと

```
★『19件を 直す』―― ★★1件です。★残り18件は ★分母として 残ります。
★『146件は 捨てる』―― ★★順番を 後にしただけ。
★『これで 設計図が 正しくなる』―― ★★1件の 欄の形が 揃うだけ。
★『形A の7件は 全部 在る』―― ★★1件も 引いていません。★★当てません。
★『上限は 20 だ』―― ★★『32 には ならない』までです。★形A が 全部 当たった時の 上限が 20。
★『核を 作れば 形B・形C も 片が付く』―― ★★付きません。★★別の手当てです（★§0）。
```
