# 【BUILD SPEC】`EVO-0052` — **★worker が書く純関数1つ。★Claude は配線だけ**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-03 10:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.8）** ／ **★9項目 確認済（★§7）** ／ **★3値 確認済（★§1）** ／ 親: `ITEM-2DER-EVO-0035`
- **★裁定の在り処**: `ITEM-2DER-EVO-0052` の `status_note`（逐語:「★worker が effective_state を書き、Claude は配線だけ」「★worker に出せなかったら『出せなかった』と書いて★止まる」）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★3値（★核が在るか＝v1.8 の宣言）

| 条件 | 3値 | ★逐語・実測 |
|---|---|---|
| (a) 入出力が値で閉じる | **★閉じる** | 入力＝`history(rid)` の戻り（`roadmap_registry.py:90` 逐語「全エントリを古い順に返す」）＝ **dict の list**。出力＝dict |
| (b) 本番 import が要らない | **★要らない** | 判定に使うのは `status` と `status_note` の**文字列だけ**。台帳にも webui にも触れない |
| (c) 封印試験が書ける | **★書ける** | ★§3 に**逐語で置いた**（`import impl` / `<<<FILL` つき） |
| 原因 | **★確定** | `roadmap_registry.py:81-86` 逐語「**Latest entry**」＝ **最後の1件を丸ごと採る** ∴ 追記が必ず上書きする |

```
★★∴ ★この単位の 2DER 工程は ★0 ではない（★v1.8 の宣言＝MGR の note と一致）。
```

## 2. ★分担（★これが本件の主目的）

```
★worker が書く : ★`effective_state(entries)` ★1関数だけ（★純関数・★本番 import なし）
★Claude が書く : ★配線のみ ＝ ★`webui.resolve_view` から呼んで ★応答に1欄 足す
★★★★Claude は ★`effective_state` の中身を ★1文字も書かない（★書いたら ★行数を分けて申告する）
```

## 3. ★★契約（★そのまま封印できる形。★封印は人＝MGR/Taka）

**★依頼文（★骨格の前に置く本文）**
```
台帳の履歴から「いまの本当の状態」を決める純関数 impl.effective_state を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
entries = 同じ id の履歴を「古い順」に並べた list。各要素は dict で、
  "status"      … 文字列 または None（欄が無い場合も None とみなす）
  "status_note" … 文字列 または None
戻り値 = {"status": str|None, "next": str|None,
          "status_source_index": int|None, "next_source_index": int|None}
・status … ★末尾から前へ見て、最初に見つかった None でない status。その添字を status_source_index に。
・next   … ★末尾から前へ見て、最初に status_note から取り出せた next の値。その添字を next_source_index に。
・next の取り出しは ★`next=` の直後が DESIGN / IMPL / MGR / TAKA / NONE のいずれかの時だけ。
  ★`note=` の直後、または ★文字列の先頭、のどちらかに在るものだけを採る（★文中の next= は採らない）。
・見つからなければ その欄は None（★空文字にしない・★推測しない）。
・entries が空なら 4欄すべて None。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def effective_state(entries):
<<<2DER:END>>>
```

**★封印試験（★7本・★今夜3回 踏んだ形を含む）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def test_empty_gives_all_none():
    v = impl.effective_state([])
    assert v == {"status": None, "next": None,
                 "status_source_index": None, "next_source_index": None}

def test_last_non_none_status_wins():
    v = impl.effective_state([{"status": "PROPOSED", "status_note": None},
                              {"status": "DONE", "status_note": None}])
    assert v["status"] == "DONE" and v["status_source_index"] == 1

def test_note_only_append_does_not_clobber_done():
    """★今夜3回 踏んだ形: DONE の後に status を省いた追記が来ても DONE のまま"""
    v = impl.effective_state([{"status": "DONE", "status_note": "actor=MGR"},
                              {"status": None, "status_note": "actor=Claude note=測定だけ"}])
    assert v["status"] == "DONE" and v["status_source_index"] == 0

def test_next_is_taken_from_latest_note():
    v = impl.effective_state([{"status": "DONE", "status_note": "note=next=MGR x"},
                              {"status": None, "status_note": "note=next=DESIGN y"}])
    assert v["next"] == "DESIGN" and v["next_source_index"] == 1

def test_next_at_string_head_is_taken():
    v = impl.effective_state([{"status": None, "status_note": "next=IMPL やること"}])
    assert v["next"] == "IMPL"

def test_next_in_the_middle_is_not_taken():
    """★本文中の next= は手番ではない(実測: 『/ next=NONE。』『例 next=DESIGN /』)"""
    v = impl.effective_state([{"status": "DONE", "status_note": "note=完了した / next=NONE。以上"}])
    assert v["next"] is None

def test_missing_keys_are_treated_as_none():
    v = impl.effective_state([{}, {"status": "IN_PROGRESS"}])
    assert v["status"] == "IN_PROGRESS" and v["next"] is None
<<<2DER:END>>>
```

## 4. ★Claude が書く配線（★これだけ・★行数を申告する）

```python
# twoder/webui.py の resolve_view — ★history は既に取れている(EVO-0022) ∴ 呼ぶだけ
    if hist:
        from twoder import effective_state as ES        # ★置いた成果物(§5)
        eff = ES.effective_state(hist)
    else:
        eff = None
    return {"id": rid, "resolved": rec is not None, "record": rec, "history": hist,
            ★"effective": eff, "read_only": True}
```
```
★`record` を ★変えない（★既存の読み手を壊さない）。★足すのは ★`effective` の1欄だけ
★★★★書く側（`set_status` が status を省けない件）は ★★本件では直さない——★§6 に理由を書く
```

## 5. ★成果物の置き方（★S-3 と同じ形。★実績が分かれるように）

```
★worker の成果物(impl.py の本文)を ★`twoder/effective_state.py` へ ★1文字も変えずに置く
★★sha256 を控え、★受入(3) で ★`artifact_sha256` と ★一致することを示す（★S-3 で通した形）
```

## 6. ★★本件で直らないこと（★先に言う）

```
★★`set_status` は ★`status` を省けないまま である（`roadmap_registry.py:97-99` 逐語
   `if not e or status not in STATUSES: return None`）。★書く側は ★本件では触らない。
★∴ ★実際の台帳には ★依然 上書きが記録される。★直るのは ★★「読む時に本当の状態が言えること」だけ。
★★★「上書きが止まった」と ★書かない。★止まるのは ★書く側を直す次の単位である。
★★★★★受入(2) の「機械的に止まる」は ★★封印試験の中で止まること を指す（★§3 の3本目）。
   ★台帳側で止まったと ★読み替えない。
```

## 7. 受入

```
★(1) ★★worker が `effective_state` を書く。★台帳の実行記録に ★2DER の走行が残ること
     （★`GET /api/state` の `dw_state` が ★GENERATE 以降へ進む・★自己申告でない）
★(2) ★封印試験 ★7本 全通（★特に3本目=DONE の上書きが落ちること）
★(3) ★置いた本文の sha256 が ★`artifact_sha256` と一致（★Claude が書き直していない証拠）
★(4) ★★行数を分けて書く: ★worker の本文 N行 ／ ★Claude の配線 M行
★(5) ★`GET /api/resolve?id=ITEM-2DER-EVO-0052` に ★`effective` が出る。★`record` は不変
★(6) ★戻せる ／ ★(7) ★61本を走らせない（★走らせた名前を書く）
★★★★(8) ★★worker に出せなかったら ★『出せなかった』と書いて ★止まる（★裁定の逐語）。
     ★その時は ★何が出せなかったか（★契約が通らない／planner が拒否した／runner が落ちた）を ★逐語で書く
★★★★★予告を投入前に書く: ★worker の行数の見込み ／ ★Claude の配線の行数
```

## 8. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/resolve` の `effective`（★受入(5)）
2 読めるなら書けるか＝★書く側は ★本件では触らない（★§6 で明示）
3 理由を捨てない＝★★§6 で「直らないこと」を先に書いた
4 作っていないのでは＝★入力の `history` は ★既に在る（EVO-0022）∴ ★新しい記録を作らない
5 走ったか＝★受入(1) が ★実行記録での確認／6 名前＝★`status` / `status_note` / `next`（★既存語）
7 依頼と試験の矛盾＝★★§3 の依頼文と試験を ★同じ規則で書いた（★`next=` の位置の縛りを ★両方に書いた）
8 計器が自分を数えないか＝★受入(1) は ★台帳の実行記録（★私の申告ではない）
★9 増える代わりに廃止＝★★「DONE かどうかを人が note を読んで判断する」運用を畳む。
   ★★但し ★§6 のとおり ★書く側が残る ∴ ★★「畳めた」と ★書かない
```

## 9. 禁止
```
★Claude が `effective_state` の中身を書く（★書いたら行数を分けて申告し、★2DER の実績に数えない）
★`record` の形を変える ／ ★`set_status` を触る（★本件の範囲外）／ ★勘定科目に触る
★新しい台帳・新しいエンドポイントを作る ／ ★封印試験を緩める・書き換える
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
