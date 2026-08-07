# 【BUILD SPEC】`Taka(1)(2)` — **★未知の欄は 黙って捨てず ★その場で 断る**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-07 14:1x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝Taka 指示 13:59 の (1)(2)
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限4行**

---

## 1. ★★(2)「保存→読み戻しで完全一致」は ★★成立していました（★先に 測りました）

```
★実測（★私が 直前に 投入した1本を そのまま 突き合わせた）:
   ★`note`    = 送 ★755字 / 保存 ★755字 → ★★1字も 違わない
   ★`failure` = 送 ★44字  / 保存 ★44字  → ★★1字も 違わない
★★∴ ★★『書いた物が 化ける』は ★起きていません。
★★★但し ★これが 言えるのは ★★`note_of` が 出す欄だけ です。
```

## 2. ★★(1)「未知フィールドを黙って捨てる」は ★★実在します（★逐語）

```
★`twoder/progress_seal.py` の `extract_progress`:
      for ln in ...:
          k, v = ln.split(":", 1)
          if k and v: out[k] = v          ← ★★どんな key でも 受け取る（★エラーにしない）
★同 `note_of` が 出すのは ★5つだけ:
      actor / stage / run / failure / note
★`submit.py:233-239` が 使うのは ★あと2つ（★新しい item を 登記する時だけ）:
      phase / title
★★★∴ ★上の7つ以外の 欄は ―― ★★HTTP 200 が返り、★★値は どこにも 残りません。

★★★★これは ★仮定ではありません。★同じファイルの コメントが ★逐語で 認めています:
   『★EVO-0035: failure= を出さないと OPTIONAL に足しても台帳へ残らない(書き手が無い欄になる)』
   ―― ★★`failure` を 足した時に ★実際に 踏んだ穴です。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
進捗の印に書かれた欄のうち、機構が知らない物の名前を返す純関数 impl.unknown_progress_fields を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
fields = 印に書かれた欄の名前の入れ物（dict なら その key、list なら その要素）
known  = 機構が知っている欄の名前の入れ物
戻り値 = list。中身は str。名前順（英字の小さい順）に並べる。

★読み方は4通り。★上から順に、最初に当てはまった1つで決める。

(1) fields が dict でも list でも tuple でも set でもない → []
(2) known が dict でも list でも tuple でも set でもない → []
(3) fields の中の str であるものだけを見て、known の中に同じ文字列が無い物を集める
    → それを 名前順に並べた list
(4) 集まった物が 無い → []

★大文字小文字は そろえない（"Note" と "note" は 別の名前）。
★前後の空白も そろえない（" note" と "note" は 別の名前）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def unknown_progress_fields(fields, known):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★fixture は 実物の印の形）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★実物: 本日 私が使っている印の欄（progress_seal の REQUIRED + OPTIONAL）
KNOWN = ["item", "actor", "stage", "phase", "title", "note", "failure"]

def test_known_only_gives_empty_list():
    """★いつも使っている形は 何も返さない"""
    assert impl.unknown_progress_fields({"item": "I", "actor": "Claude",
                                         "stage": "PLAN", "note": "x"}, KNOWN) == []

def test_one_unknown_field_is_returned():
    """★書いても消える欄が 1つ在れば その名前を返す"""
    assert impl.unknown_progress_fields({"item": "I", "actor": "Claude",
                                         "stage": "PLAN", "evidence": "x"}, KNOWN) == ["evidence"]

def test_two_unknown_fields_are_sorted_by_name():
    got = impl.unknown_progress_fields({"zebra": 1, "apple": 2, "note": 3}, KNOWN)
    assert got == ["apple", "zebra"], got

def test_a_list_of_names_is_accepted_too():
    assert impl.unknown_progress_fields(["item", "actor", "stage", "spec"], KNOWN) == ["spec"]

def test_case_is_compared_exactly():
    """★"Note" は "note" と 別の名前（★そろえると 消える欄が 見えなくなる）"""
    assert impl.unknown_progress_fields(["Note"], KNOWN) == ["Note"]

def test_surrounding_space_is_compared_exactly():
    assert impl.unknown_progress_fields([" note"], KNOWN) == [" note"]

def test_non_string_names_are_skipped():
    assert impl.unknown_progress_fields([1, None, "note"], KNOWN) == []

def test_non_container_fields_gives_empty_list():
    assert impl.unknown_progress_fields(None, KNOWN) == []
    assert impl.unknown_progress_fields("note", KNOWN) == []

def test_non_container_known_gives_empty_list():
    assert impl.unknown_progress_fields({"evidence": 1}, None) == []
<<<2DER:END>>>
```

## 4. ★★配線（★上限4行）／ ★★私が 決めないこと

```
★配線 = ★`extract_progress` の 最後（★REQUIRED を確かめた後）で 1回 呼び、
        ★戻りが 空でなければ ★★`ValueError` を投げる（★★このモジュールは 既に fail-closed です
        ―― ★逐語『壊れていれば ValueError(fail-closed)』）。
★★理由 = ★Taka 逐語『★未知フィールドを 黙って捨てる動作を ★最優先で 禁止』
        ―― ★『警告する』では ★捨てるのを 止めていません。★断れば 捨てません。

★★★私が 決めないこと（★MGR / Taka）=
   ★`known` に ★何を 入れるか。★私の見立て = ★`REQUIRED + OPTIONAL` の7つ
     （★`phase`/`title` は ★新しい item の登記に 使われている＝`submit.py:233-239` 実測）。
   ★★但し ★★`phase` と `title` は ★note には 残りません ∴ ★『既知だが 保存されない欄』です。
     ★これを 既知に含めるか 分けるかは ★決め事です。
```

## 5. ★★受入（★口・欄・★id）

```
★(1) ★9本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `artifact.name` と `found`
     ★id = ★この契約を走らせた その走行の task
     ★読める物 = `unknown_progress_fields` ／ `found=true`
★(3) ★口 = 同上 ／ ★欄 = `sent.text` ／ ★id = 同上
     ★読める物 = ★★`"apple"`（★★封印試験の中の語＝★届く面に在る語で 確かめる。★v1.18／
                  ★本日 私は ここを 依頼文の語で書いて 外しました）
★(4) ★配線後: ★未知の欄を1つ入れた印を 投入すると ★★断られる（★MGR が 測る）
★(5) ★配線後: ★いつもの印（★7欄のみ）は ★従来どおり 通る（★★陰性・★これが無いと 全部 止まります）
★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit しない
```

## 6. ★★私が 言っていないこと

```
★『保存が 壊れている』―― ★★壊れていません（★§1 で 1字も 違いませんでした）。
★『7欄で 足りる』―― ★★決めていません（★§4 は MGR / Taka）。
★『これで 10項目が 読める』―― ★★別の話です（★Taka(4)）。★本件は ★捨てるのを 止めるだけ。
★『(3) の再登録を 先にやる』―― ★★Taka 指示どおり ★本件の 後です。
```
