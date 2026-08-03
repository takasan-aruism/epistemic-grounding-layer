# 【BUILD SPEC】`EVO-0054` — **★核は在る。★`merge_progress` を worker に出す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-03 17:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.10）** ／ **★9項目 確認済（★§7）** ／ 親: `ITEM-2DER-EVO-0035`
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★★v1.8 の宣言（★着手前・★実測）

> ### **★この単位の核は ★在る。★2DER 工程は 0 ではない。**

```
★核 = ★merge_progress(prev, progress)
   ★入力 prev     = 直前の記録 dict（★`status` を持つ・★値のみ）／★無ければ None
   ★入力 progress = 投入から抽出した進捗 dict（★`status` は ★在っても無くてもよい・★`actor`/`stage`/`note`/`next`）
   ★出力 = {"status": str, "status_kept": bool, "claims_turn": bool}
   ★規則 = ★`progress` に `status` が ★無ければ ★`prev` の `status` を ★そのまま返し `status_kept=True`
           ★在れば その値（★`STATUSES` の6語のいずれかの時だけ。★外なら ★★None を返して `status_kept=False`）
           ★`claims_turn` = ★`progress` に `next` が ★在る時だけ True
```

| 条件 | 3値 | ★逐語・実測 |
|---|---|---|
| (a) 入出力が値で閉じる | **★閉じる** | dict 2つ → dict 1つ。★台帳にも webui にも触れない |
| (b) 本番 import が要らない | **★要らない** | 判定に使うのは ★`status` の文字列と ★キーの有無だけ |
| (c) 封印試験が書ける | **★書ける** | ★§3 に逐語で置いた |

**★閉塞の逐語**
```
★`progress_seal.py:20` ★`REQUIRED = ("item", "status", "actor", "stage")` ＝ ★`status` を ★省けない
★`roadmap_registry.py:97-99` ★`if not e or status not in STATUSES: return None` ＝ ★省くと ★書けない
★∴ ★どの追記も ★必ず状態を主張する
```

## 2. ★分担
```
★worker : ★`merge_progress` ★1関数だけ（★純関数）
★Claude : ★配線のみ ＝ ★`progress_seal.REQUIRED` から `status` を外し、★`submit.py:228` で
          ★`merge_progress` の戻りを ★`set_status` に渡す。★`set_status` は ★`status=None` を受けない ∴
          ★呼び手が ★決めた値を渡す（★`set_status` 自体は ★触らない）
★★★Claude は ★`merge_progress` の中身を ★1文字も書かない
```

## 3. ★★契約（★そのまま封入できる形。★封入は MGR）

**★依頼文**
```
台帳へ追記する時の「状態と手番」を決める純関数 impl.merge_progress を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
prev     = 直前の記録 dict または None。"status" を持つことがある。
progress = 今回の投入 dict。"status" を持つことも持たないこともある。"next" も同じ。
戻り値 = {"status": str|None, "status_kept": bool, "claims_turn": bool}

・progress に "status" が無い（キーが無い / 値が None）→ prev の "status" をそのまま返し
  status_kept は True。prev が None または prev に status が無ければ status は None。
・progress に "status" が在る → その値が
  PROPOSED / PLANNED / IN_PROGRESS / DONE / DEFERRED / DROPPED の★いずれかの時だけ その値を返す。
  ★列挙外なら status は None（★推測しない・★prev で埋めない）。どちらも status_kept は False。
・claims_turn は progress に "next" が在り値が空でない時だけ True。それ以外は False。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def merge_progress(prev, progress):
<<<2DER:END>>>
```

**★封印試験（★8本・★v1.10 の対を守る）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def test_omitted_status_keeps_previous():
    """★本日(1)(2) の形: 記録だけ足したいのに DONE が戻された"""
    v = impl.merge_progress({"status": "DONE"}, {"actor": "Claude", "stage": "RECORD"})
    assert v["status"] == "DONE" and v["status_kept"] is True

def test_explicit_status_replaces():
    v = impl.merge_progress({"status": "DONE"}, {"status": "IN_PROGRESS"})
    assert v["status"] == "IN_PROGRESS" and v["status_kept"] is False

def test_all_six_statuses_are_accepted():
    """★列挙は全部 通ること(v1.10 の対・肯定側)"""
    for s in ("PROPOSED", "PLANNED", "IN_PROGRESS", "DONE", "DEFERRED", "DROPPED"):
        v = impl.merge_progress({"status": "DONE"}, {"status": s})
        assert v["status"] == s, (s, v)

def test_unknown_status_is_rejected():
    """★列挙外は弾くこと(v1.10 の対・否定側)。★prev で埋めない"""
    v = impl.merge_progress({"status": "DONE"}, {"status": "FINISHED"})
    assert v["status"] is None and v["status_kept"] is False

def test_none_value_counts_as_omitted():
    v = impl.merge_progress({"status": "DEFERRED"}, {"status": None})
    assert v["status"] == "DEFERRED" and v["status_kept"] is True

def test_no_prev_gives_none():
    v = impl.merge_progress(None, {"actor": "MGR", "stage": "RECORD"})
    assert v["status"] is None and v["status_kept"] is True

def test_claims_turn_only_when_next_present():
    """★本日(3)(4) の形: 手番を主張するつもりが無い追記が 手番を奪った"""
    a = impl.merge_progress({"status": "DONE"}, {"actor": "Claude", "stage": "RECORD"})
    b = impl.merge_progress({"status": "DONE"}, {"next": "MGR"})
    assert a["claims_turn"] is False and b["claims_turn"] is True

def test_empty_next_does_not_claim():
    v = impl.merge_progress({"status": "DONE"}, {"next": ""})
    assert v["claims_turn"] is False
<<<2DER:END>>>
```

## 4. ★読む口と書く口（★対で名指し・規律 v1.1）

```
★書く口 : ★`roadmap_registry.set_status`（★既存・★触らない）／★呼び手 `submit.py:228`
★読む口 : ★`GET /api/resolve` の ★`record.status` と ★`effective`（★`EVO-0052` で入れた）
★★★`claims_turn` が False の時は ★`note_of` に ★`next=` を ★書かない ∴ ★手番は ★前の note が持ち続ける
   ＝ ★`effective` の「末尾から最初に取れた next=」と ★噛み合う（★読む側と書く側が同じ規則になる）
```

## 5. ★★受入（★今日の4件を試験にする＝規律 v1.9）

```
★(1) ★worker が `merge_progress` を書く（★台帳の実行記録で確認・★自己申告でない）
★(2) ★封印試験 ★8本 全通
★(3) ★★★本日(3)(4) の形が ★再現できないこと（★裁定の指定）:
     ★`status` と `next` を書かない追記を1件 投入 → ★`GET /api/resolve` で
     ★★`record.status` が ★前のまま ／ ★`effective.next` が ★前の手番のまま
     ★★★★これを ★実データで1回 示す（★作文でない）
★(4) ★本日(1)(2) の形: ★`DONE` の item に記録だけ足しても ★`DONE` のまま
★(5) ★sha256 一致 ／ ★(6) ★行数を分ける（worker N ／ Claude M）／ ★(7) ★戻せる ／ ★(8) ★61本を走らせない
★★★★(9) ★出せなかったら『出せなかった』と書いて止まる
★★★★★予告を投入前に書く: ★worker の行数 ／ ★Claude の配線の行数 ／ ★(3) で見えるはずの値
```

## 6. ★★先に言う（★これでも直らないこと）

```
★`set_status` は ★`status=None` を受けない（`roadmap_registry.py:98` 逐語）。★本件では ★触らない。
★∴ ★「省ける」ようになるのは ★★front door の投入の側だけ で、★`set_status` を直接 呼ぶ経路は ★変わらない。
★★★今日の4件は ★全て front door 経由 ∴ ★4件とも塞がる見込み。★但し ★他経路は ★塞がらない【★未確認】
```

## 7. ★9項目（私の分）
```
1 置いたなら読めるか＝★受入(3) は ★`/api/resolve` で見る
2 読めるなら書けるか＝★§4 で ★書く口と読む口を ★対で名指しした
3 理由を捨てない＝★★§6 に ★直らない範囲を先に書いた
4 作っていないのでは＝★`prev` は ★`resolve` が既に返す ∴ ★新しい記録を作らない
5 走ったか＝★受入(1)(3) は ★実投入で測る／6 名前＝★`status` / `next`（★既存語）
★7 依頼と試験の矛盾＝★★列挙(6語)を ★肯定側1本＋否定側1本の ★対で置いた（★v1.10・★3回の再発への対処）
8 計器が自分を数えないか＝★受入(3) は ★台帳の値（★私の申告ではない）
★9 増える代わりに廃止＝★★「記録を足すために ★状態を書き直す」運用を畳む。
   ★★但し ★§6 のとおり ★他経路が残る ∴ ★「全部 塞いだ」と ★書かない
```

## 8. 禁止
```
★Claude が `merge_progress` の中身を書く ／ ★`set_status` を触る ／ ★`STATUSES` を増やす
★列挙外の status を ★`prev` で埋める（★「分からない」を消す）／ ★勘定科目に触る
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
