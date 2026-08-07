# 【BUILD SPEC】`①` — **★実物へ辿れない記述を 機械が 挙げる（★文書→実物 の向き）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 01:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝Taka「設計図が自分で答える」
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新しい欄0 ／ ★Claude の配線 ★上限6行**

---

## 1. ★★私の数を1つ 直す（★鍵を厳しくした）

```
★私は 01:1x に ★『実物へ辿れない記述 = ★127件』と 出しました。
★★あれは ★緩い鍵です（★`steps` を 辿れる側に 数えていた ―― ★`steps` は ★散文であって id では ありません）。
★★★鍵を 厳しくして 数え直した（★全数・★178記述）:
     ★辿れる = ★`file` を持つ、または ★`component`/`from`/`to` が ★他の記述の id と 一致する
     ★★結果 = ★辿れる 48 ／ ★★辿れない ★★130
★★★★∴ ★★数は 鍵で 動く（★本日 何度も 出た形）∴ ★★契約に 鍵を 書き込みます。
```

## 2. ★★なぜ これが 効くのか

```
★実測（★区分ごと）:
     ★★gaps 0/98 ／ canonical_stores 0/7 ／ unknowns 0/7 ／ write_paths 0/6 ／
       planned_extensions 0/5 ／ read_paths 0/4 ／ execution_flows 0/2 ／ llm_invocations 5/6
     ★components 23/23 ／ entrypoints 8/8 ／ edges 11/11 ／ state_machines 1/1
★★∴ ★『実物を持つ側』は ★もう 揃っている。★持たないのは ★★主張と 予定と 穴の側 です。
★★★これが ★『Gap 98 が 2週間 動かない』の 機械側の 理由 ――
   ★★誰も 辿れないから ★誰も 動けない。★★人の怠慢では ありません。
★★★★この向き（★文書→実物）は ★既存の検査に 在りません
   （★`conformance_probe` も ★C-TOTALITY も ★コード→文書 の向き）∴ ★重複しません。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
設計図の資料から、実物へ辿れない記述の id を挙げる純関数 impl.untraceable_entries を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
doc = dict。値が list の欄だけを見る。list の中の dict だけを見る。
戻り値 = list。中身は str。名前順（英字の小さい順）に並べる。

★先に「在る id」を集める:
   doc の中の すべての list の中の dict について、"id" が str なら それを集める。これを ids とする。

★1つの記述が「辿れる」とは、次のどちらかである:
   (あ) "file" が str であり、前後の空白を除くと 1文字以上ある
   (い) "component" / "from" / "to" のどれかの値が str であり、その値が ids の中に在る

★戻すのは、"id" が str であり、かつ「辿れる」に当てはまらない記述の "id"。

・doc が dict でない → []
・"id" を持たない記述は 数えない（戻り値にも入れない）
・大文字小文字は そろえない（"File" は "file" と 別の名前）
```

**★骨格**
```
<<<2DER:SKELETON>>>
def untraceable_entries(doc):
    # <<<FILL: この行を 実装で 置き換える（★この行は 残さない）>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★fixture は 実物の形）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★実物の形(egl/docs/2DER_EXECUTION_ARCHITECTURE.json より・逐語の欄名)
COMP = {"id": "C-DS-RECORD", "repo": "ds", "file": "ds/ds/phase0.py", "symbol": "record_utterance"}
GAP  = {"id": "G-02", "summary": "勘定科目の自動設定が EGL 登録経路に繋がっていない",
        "kind": "gap", "status": "OPEN"}
EDGE = {"id": "E-SUBMIT-DS", "from": "EP-WEBUI-SUBMIT", "to": "C-DS-RECORD", "mechanism": "call"}
EP   = {"id": "EP-WEBUI-SUBMIT", "repo": "twoder", "file": "twoder/webui.py"}

def test_entry_with_file_is_traceable():
    """★実物の場所を持つ記述は 挙げない"""
    assert impl.untraceable_entries({"components": [COMP]}) == []

def test_gap_without_any_key_is_listed():
    """★実測: gaps は 98件とも 鍵を持たない"""
    assert impl.untraceable_entries({"gaps": [GAP]}) == ["G-02"]

def test_edge_pointing_at_an_existing_id_is_traceable():
    """★他の記述を指していれば 辿れる"""
    doc = {"components": [COMP], "entrypoints": [EP], "edges": [EDGE]}
    assert impl.untraceable_entries(doc) == []

def test_edge_pointing_at_a_missing_id_is_listed():
    """★指した先が 資料に無ければ 辿れない"""
    doc = {"edges": [{"id": "E-X", "from": "NOT-THERE", "to": "ALSO-NOT-THERE"}]}
    assert impl.untraceable_entries(doc) == ["E-X"]

def test_result_is_sorted_by_name():
    doc = {"gaps": [{"id": "G-09"}, {"id": "G-02"}]}
    assert impl.untraceable_entries(doc) == ["G-02", "G-09"]

def test_empty_file_is_not_a_key():
    assert impl.untraceable_entries({"gaps": [{"id": "G-03", "file": "   "}]}) == ["G-03"]

def test_entry_without_id_is_not_listed():
    assert impl.untraceable_entries({"gaps": [{"summary": "名前が無い"}]}) == []

def test_uppercase_field_name_is_not_accepted():
    """★"File" は "file" と 別の名前（★そろえると 辿れない物が 隠れる）"""
    assert impl.untraceable_entries({"gaps": [{"id": "G-04", "File": "x.py"}]}) == ["G-04"]

def test_non_dict_gives_empty_list():
    for x in (None, [], "doc", 3):
        assert impl.untraceable_entries(x) == [], x
<<<2DER:END>>>
```

## 4. ★★配線（★上限6行）／ ★★増やさないこと

```
★資料を 読み込んで ★この関数へ 渡し、★結果を 台帳へ 1行 書く（★件数と ★最初の数件の id）。
★★新しい台帳を 作らない（★Taka 常設命令）。★★新しい欄を 資料に 足さない（★本件は ★読むだけ）。
★★★『鍵を 持たせる』作業は ★本件に 入れない ―― ★★まず ★何件 持っていないかを ★機械が 言えるようにする。
   ★★持たせるのは ★次（★1件ずつ・★全件に 遡らない＝Taka「全件直す、的な動きは不要」）。
```

## 5. ★★受入（★口・欄・★id）

```
★(1) ★9本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `artifact.name` と `found`
     ★id = ★この契約を走らせた その走行（★報告に 書く）
★(3) ★★実物の資料に 通すと ★★130件 が 出ること（★§1 の 厳しい鍵で 私が 数えた値）
     ★口 = 台帳の1行 ／ ★欄 = 件数 ／ ★id = その走行の run_id
★★(4) ★★陰性 = ★★`components`（23件）が ★1件も 出ないこと
     ―― ★出たら ★鍵の判定が 壊れています（★あの23件は ★全件 `file` を 持っています）
★(5) ★Claude の配線行数（★上限6行）／ ★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit は 2DER
```

## 6. ★★私が 言っていないこと

```
★『130件が 直る』―― ★★挙げるだけです。★直すのは 次。
★『127 が 誤りだった』―― ★★鍵が 緩かった、です（★§1）。★どちらも 同じ資料を 見ています。
★『これで 設計図が 自分を検査する』―― ★★向きが1本 出来るだけ。
   ★★『実際に動くか』は ★既存（`conformance_probe`）に 繋いでから ―― ★駆動役の後です。
★『Gap 98 が 動く』―― ★★動きません。★★なぜ動かないかが ★機械で 言えるようになるだけです。
```
