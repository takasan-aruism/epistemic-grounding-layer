# 【BUILD SPEC v2】★差し戻しを受ける ―― **送れる形にした**（★骨格に目印・★試験に `assert`）

- **宛: 実装(IMPL)** ／ 写: MGR / Taka / 監視 ／ 発: 設計・監査(CC-α) ／ 2026-08-08 18:25 ／ TYPE=BUILD SPEC（★v1 を差し替えず **新しい名前**で置く）
- **開発者規律 確認済（版: v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ **効く先＝1と3と4**
- **★新台帳0 ／ ★新エンドポイント0 ／ ★合格済の `trace_entry_v2` に 1文字も 触らない**

---

## 0. ★★私の非（★MGR の差し戻しは 正しい）

```
★★v1 の §4 は ★試験の ★名前だけ で、★★`assert` が 0本 でした。
   ―― ★★worker に 届く3面のうち ★『封印試験』は ★★中身が 規則です。
      ★名前だけ 送っても ★★通す条件が 1つも 無い ∴ ★★何も 検査されない。
★★v1 の §3 の骨格は ★```python の囲みだけ で ★目印が 付いていませんでした ∴ ★切り出せない。
★★★∴ ★私は「規律 v1.18(★worker に届く面は3つだけ)」を ★★知っていながら
   ★★『送れる形』に していませんでした。★★知っている と ★送れる は 別です。
★★★★併せて ―― ★MGR が 18:13 の記録で 757字に 切られた件について:
   ★★台帳の本文に ★契約の目印を 書くと ★封印が それを 拾います。
   ★★∴ ★本書では ★目印の文字列は ★★下の2つの箱の中に しか 書きません（★本文では 書きません）。
   ★★★台帳へ書く時も 同じです（★私の記録にも 目印は 書きません）。
```

**v1 の §0〜§2（★19件を 3つの形に割った件・★1件の 選び方・★直す前の3値）は そのまま 生きています。**
**MGR は それを 受けています ∴ ここでは 繰り返しません。** 対象は **`C-CC-REGISTER`（6語）** です。

## 1. ★★作る物（★1つだけ）

```
★置き場   = /home/takasan/twoder/split_symbol_details.py（★worker の中では impl.py）
★関数名   = split_symbol_details ／ ★署名 = split_symbol_details(entry)
★行数     = ★★上限 60 行（★docstring を除く）
★禁止     = ★file を 読まない（★`open(` `Path(` `os.` を 1つも 書かない）／★import を 足さない
★理由     = ★合格済の `trace_entry` と 同じ作法（★中身は 呼び手が 渡す・★核は 判定だけ）
```

## 2. ★★骨格（★下の箱を そのまま 送る）

<<<2DER:SKELETON>>>
def split_symbol_details(entry):
    """1つの記述の symbol 欄に名前が複数入っている時、名前1つずつの記述に分ける。

    entry は設計図の1つの記述(dict)。戻り値は list。
    要素は元の記述を写した dict で、symbol が1つの名前に置き換わっている。

    読み方は4通り。上から順に、最初に当てはまった1つで決める。
      1. entry が dict でない
         -> 空の list を返す
      2. entry.get("symbol") が str でない、または前後の空白を除くと空
         -> 空の list を返す
      3. entry["symbol"] を "/" で切り、片ごとに前後の空白を除き、
         前後の空白を除くと空になった片を落とす。残った片が 1個以下
         -> 空の list を返す
      4. 上のどれでもない場合、残った片の数だけ dict を返す。
         i 番目(0から数える)の dict は entry を写した上で、次の3つを入れる。
           symbol       = i 番目の片
           detail_index = i
           detail_of    = entry.get("id")

    元の entry は変わらないままにする。呼び手が後で元の entry を読んでも
    symbol は元の文字列のままで、detail_index は入っていない。
    片の順番は元の並び順のまま。大文字小文字はそろえない。
    """
<<<2DER:END>>>

## 3. ★★封印試験（★11本・★下の箱を そのまま 送る）

<<<2DER:IMMUTABLE_TESTS>>>
from impl import split_symbol_details


def _entry():
    return {"id": "C-CC-REGISTER",
            "file": "egl/docs/cc_register.py",
            "symbol": "record_doc / record_done / pending / counts / doc_id_for / normalize_path"}


def test_dict以外を渡すと空のlistを返す():
    """dict でない物には明細が無い。空の list を返す。"""
    assert split_symbol_details("record_doc / record_done") == []
    assert split_symbol_details(None) == []
    assert split_symbol_details(["record_doc", "record_done"]) == []


def test_symbolが文字列でない時は空のlistを返す():
    """symbol が str でない記述、symbol が無い記述は分けない。"""
    assert split_symbol_details({"id": "X", "symbol": None}) == []
    assert split_symbol_details({"id": "X", "symbol": 3}) == []
    assert split_symbol_details({"id": "X"}) == []


def test_symbolが空白だけの時は空のlistを返す():
    """前後の空白を除くと空になる symbol は分けない。"""
    assert split_symbol_details({"id": "X", "symbol": ""}) == []
    assert split_symbol_details({"id": "X", "symbol": "   "}) == []


def test_名前が1つだけの時は空のlistを返す():
    """分ける物が1つだけの記述は、そのままにする。"""
    assert split_symbol_details({"id": "X", "symbol": "record_doc"}) == []
    assert split_symbol_details({"id": "X", "symbol": "  record_doc  "}) == []


def test_6つの名前を6つの記述に分ける():
    """スラッシュで区切られた6語は6件になる。並び順は元のまま。"""
    out = split_symbol_details(_entry())
    assert len(out) == 6
    assert [d["symbol"] for d in out] == [
        "record_doc", "record_done", "pending", "counts", "doc_id_for", "normalize_path"]


def test_分けた記述のsymbolは前後の空白が落ちている():
    """片の前後に空白が付いていても、symbol には空白を残さない。"""
    out = split_symbol_details({"id": "X", "symbol": "  open_run /  emit  "})
    assert [d["symbol"] for d in out] == ["open_run", "emit"]


def test_分けた記述は元の記述のfileとidをそのまま持つ():
    """symbol 以外の欄は写したままにする。"""
    out = split_symbol_details(_entry())
    assert len(out) == 6
    for d in out:
        assert d["file"] == "egl/docs/cc_register.py"
        assert d["id"] == "C-CC-REGISTER"


def test_detail_indexは0から順に入る():
    """明細の番号は 0 から始まり、1つずつ増える。"""
    out = split_symbol_details(_entry())
    assert [d["detail_index"] for d in out] == [0, 1, 2, 3, 4, 5]


def test_detail_ofには元のidが入る():
    """どの記述から分かれたかを、明細の側が持つ。id が無い記述では None。"""
    out = split_symbol_details(_entry())
    assert [d["detail_of"] for d in out] == ["C-CC-REGISTER"] * 6
    out2 = split_symbol_details({"symbol": "alpha / beta"})
    assert [d["detail_of"] for d in out2] == [None, None]


def test_呼んだ後も元の記述は変わらない():
    """元の記述は読むだけにする。呼び手が後で読んでも元の値のまま。"""
    e = _entry()
    split_symbol_details(e)
    assert e["symbol"] == "record_doc / record_done / pending / counts / doc_id_for / normalize_path"
    assert "detail_index" not in e
    assert "detail_of" not in e


def test_空の片は落ちて数に入らない():
    """スラッシュが続いてできた空の片は数に入れない。残りが1個以下なら空の list。"""
    out = split_symbol_details({"id": "X", "symbol": "alpha // beta /"})
    assert [d["symbol"] for d in out] == ["alpha", "beta"]
    assert split_symbol_details({"id": "X", "symbol": "alpha //"}) == []
<<<2DER:END>>>

## 4. ★★直し方（★設計図は 私も MGR も 直接 書かない）

```
★(1) ★核が 6明細を 作る（★値を 決めるのは 機械＝★空白と 区切りだけで 決まる）。
★(2) ★配線（★Claude が 書く・★★上限 10 行）=
      ★`egl/docs/2DER_EXECUTION_ARCHITECTURE.json` の `components` から
      ★`id == "C-CC-REGISTER"` の 1件を 取り、★核に 通し、★戻った 6件で ★その1件を 置き換えて 書き戻す。
      ―― ★★書く中身は ★核の 戻り値そのもの（★私が 手で 書いた文字を 入れない）。
★(3) ★2DER の口で 登記と commit（★git を 直に 叩かない）=
      ★`artifact_registry.register(...)` ／ ★`record_change(...)` ／ ★`commit_one(...)`
      ―― ★`commit_one` は ★置いた 1本だけを add する 作り ∴ ★2本 置くなら ★2回 呼ぶ。
★★★★LLM = ★値を 決める呼び出しは 0回 ／ ★核を 作る worker の 回数は ★別に 数えて 報告する。
★★★★合計件数は 変わる = ★★178 → 183（★`components` 23 → 28）＝★明細化そのもの。★先に 書いておく。
```

## 5. ★★受入（★口・欄・id・逐語・陰性）

```
★(1) ★口 = ★核を 走らせた出力 ／ ★id = ★`C-CC-REGISTER`
     ★欄 = ★`verdict` / `file` / `symbol` / `missing` / `searched`（★`trace_entry_v2` の 戻り）
     ★読める物 = ★★6明細 それぞれの 3値。
     ★★PRESENT も ABSENT も ★★file と symbol を ★逐語で 出すこと
        ―― ★それが Taka の言う『★本当にその機能があるのか』の 答えそのもの。
★(2) ★★合計 = ★★183（★3値の 合計が 183 と 一致）／ ★`C-CC-REGISTER` が ★もう 出てこないこと。
★(3) ★★陰性 = ★`EP-WEBUI-SUBMIT`（★形C ／ `twoder/webui.py` ／ `POST /api/submit`）を
     ★★同じ核に 通した結果を 併せて 出す（★★設計図は 直さない・★読むだけ）。
     ★読める物 = ★3明細（`POST` `api` `submit`）の 3値。
     ★全部 ABSENT なら → ★『欄の形を 直しても、★鍵でない物は 在るに ならない』。
     ★1つでも PRESENT なら → ★★その file と symbol を 逐語で 出し、★★そこで 止めて 設計へ 返す
        ―― ★失敗では ありません。★『機械が 嘘を つく所が もう1つ 見つかった』という 結果です。
★(4) ★★`trace_entry_v2.py` の sha を ★前後で 出し、★変わっていないこと。
★(5) ★戻せる = ★口 `GET /api/resolve?id=CHG-****` ／ ★欄 `after_commit`(★null でない)・
     ★`revert_scope.complete` = true ／ ★★その commit に 他の file が 入っていないこと(★`git show --stat` 逐語)。
★(6) ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限 10 行（★実数を 報告）。
★(7) ★答えられなかった物は ★『答えられなかった』と 書く（★規律3）。
     ★特に ★設計図を 2DER の口で 書き戻せなかった時は ★『どの口が 無いのか』を 1行。
```

## 6. ★★言っていないこと

```
★『v1 は 間違いだった』―― ★★§0〜§2 は 生きています。★★送れる形に なっていなかった、が 非です。
★『19件を 直す』―― ★★1件です。★『146件は 捨てる』―― ★★順番を 後にしただけ。
★『形A の7件は 全部 在る』―― ★★1件も 引いていません。★★当てません。
★『これで 設計図が 正しくなる』―― ★★1件の 欄の形が 揃うだけ。
```
