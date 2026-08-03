# 【BUILD SPEC】`EVO-0050` — **★測るだけ。★比較対象が v1/v2 でずれる（先に言う）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 05:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.11）** ／ **★9項目 確認済（★§7）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は在るが小さい**（★集計だけ・MGR の宣言と一致）
- **★私の予告**: ★worker **12〜20行**／★Claude の配線 **0〜6行**／★再測の `n_frozen_axes` は **予告しない**（★測る対象そのもの）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★★先に言う: **比較対象がずれている**（★実測）

```
★私が 70.6% / n_frozen_axes=2 を読んだのは ★`ACCOUNT_AXES_v2.json`
★★しかし ★再生成 prog `s_account_axes.py:24-25` の出力先は 逐語:
      OUT_AXES = ".../ACCOUNT_AXES_★v1.json"
      OUT_MEMB = ".../ACCOUNT_MEMBERSHIP.jsonl"
★★★∴ ★prog を走らせても ★v2 は ★作り直されない。
★`v2` の note 逐語=「★v2 = v1 不変コピー + ★Taka 承認済み新軸 1本(2b-r3)。★v1 は不変」
★★★★∴ ★★v2 は ★人が1本 足したもので、★prog では再現できない。
★★★★★∴ ★『2本 → 再測で何本か』を ★同じ土俵で比べるには ★★v1 と v1 を比べる必要がある。
```

**★実装が最初にやること（★1手）**: **★`v1` の現在値を読む**（`n_frozen_axes` / `membership_other_count` / `membership_real_assigned` / `membership_shuffle_assigned`）。**★これが 7/25 の基準である。**★`v2` の 2本 / 70.6% は **★v1 + 人の1本**なので、**★そのまま比較に使わない**。

## 2. ★再測の手段（★書かない口が既に在る）

```
★`s_account_axes.py --check` は ★★書かない（逐語 `:203` 以降が --check 分岐、★:230-231 の write は ★その後）
★★`--check` は ★GREEN 行に ★必要な数字を ★全部 出す（逐語）:
   "frozen=%d ... membership real_assigned=%d その他=%d shuffle_assigned=%d"
★★★∴ ★再測は ★`--check` を1回 走らせるだけ。★`--apply`(引数なし実行)は ★★走らせない
★★★★★陰性対照も ★--check が ★自分で判定する（★`MEMBERSHIP_NEG_CONTROL_FAILED` の分岐が在る）
   ＝ ★受入(5) は ★新しく作らない・★既存の判定を ★そのまま出す
```

## 3. ★worker が書く核（★集計だけ・★小さいと宣言済）

**★依頼文**
```
軸の再測結果を比べる純関数 impl.axis_delta を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
before = {"n_frozen_axes": int, "real_assigned": int, "other_count": int, "shuffle_assigned": int}
after  = 同じ形
戻り値 = {"axes_delta": int, "other_ratio_before": float|None, "other_ratio_after": float|None,
          "other_ratio_delta": float|None, "verdict": str, "neg_control_ok": bool}

・axes_delta = after["n_frozen_axes"] - before["n_frozen_axes"]
・other_ratio = other_count / (other_count + real_assigned)。★分母が 0 なら None。
  ★割合は 0.0〜1.0 の小数で返す（★百分率にしない）。
・other_ratio_delta = after の割合 - before の割合。★どちらかが None なら None。
・verdict は AXES_INCREASED / AXES_DECREASED / OTHER_DECREASED / OTHER_INCREASED / UNCHANGED の★5語。
  ★順番は この順で、★最初に当たったもの:
    ① axes_delta > 0            → "AXES_INCREASED"
    ② axes_delta < 0            → "AXES_DECREASED"
    ③ other_ratio_delta < 0     → "OTHER_DECREASED"
    ④ other_ratio_delta > 0     → "OTHER_INCREASED"
    ⑤ それ以外（None を含む）    → "UNCHANGED"
・neg_control_ok = after["shuffle_assigned"] < after["real_assigned"] の時だけ True。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def axis_delta(before, after):
<<<2DER:END>>>
```

**★封印試験（★7本・★意図ごとに1行＝本日4回目の同型への対処）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

B = {"n_frozen_axes": 2, "real_assigned": 114, "other_count": 274, "shuffle_assigned": 1}

def test_unchanged_when_identical():
    v = impl.axis_delta(B, dict(B))
    assert v["axes_delta"] == 0
    assert v["verdict"] == "UNCHANGED"

def test_axes_increase_wins_over_other():
    a = {"n_frozen_axes": 3, "real_assigned": 100, "other_count": 300, "shuffle_assigned": 1}
    assert impl.axis_delta(B, a)["verdict"] == "AXES_INCREASED"

def test_axes_decrease_is_reported():
    a = {"n_frozen_axes": 1, "real_assigned": 114, "other_count": 274, "shuffle_assigned": 1}
    assert impl.axis_delta(B, a)["verdict"] == "AXES_DECREASED"

def test_other_decreased_when_axes_same():
    a = {"n_frozen_axes": 2, "real_assigned": 200, "other_count": 200, "shuffle_assigned": 1}
    assert impl.axis_delta(B, a)["verdict"] == "OTHER_DECREASED"

def test_other_increased_when_axes_same():
    a = {"n_frozen_axes": 2, "real_assigned": 50, "other_count": 350, "shuffle_assigned": 1}
    assert impl.axis_delta(B, a)["verdict"] == "OTHER_INCREASED"

def test_ratio_is_fraction_not_percent():
    v = impl.axis_delta(B, dict(B))
    assert v["other_ratio_before"] is not None
    assert 0.70 < v["other_ratio_before"] < 0.71

def test_zero_denominator_gives_none_not_zero():
    z = {"n_frozen_axes": 2, "real_assigned": 0, "other_count": 0, "shuffle_assigned": 0}
    v = impl.axis_delta(B, z)
    assert v["other_ratio_after"] is None
    assert v["other_ratio_delta"] is None

def test_neg_control_flag():
    ok = impl.axis_delta(B, {"n_frozen_axes": 2, "real_assigned": 114, "other_count": 274, "shuffle_assigned": 1})
    ng = impl.axis_delta(B, {"n_frozen_axes": 2, "real_assigned": 5, "other_count": 274, "shuffle_assigned": 90})
    assert ok["neg_control_ok"] is True
    assert ng["neg_control_ok"] is False
<<<2DER:END>>>
```

## 4. ★Claude の配線（★0〜6行と予告）

```
★配線は ★要らないかもしれない=★本件は ★『測って台帳に書く』作業であり、★front door の口を増やさない。
★★成果物は ★`twoder/axis_delta.py` へ ★無改変で置く（★sha256 で照合）。
★★★呼び出しは ★実装が ★1回だけ手で行い（★--check の出力を入れる）、★結果を ★台帳の note に書く。
★★★★★∴ ★配線 0行も ★在りうる。★0 なら ★0 と書く（★水増ししない）
```

## 5. 受入
```
★(1) ★worker が `axis_delta` を書く（★Claude は本文0行・★実行記録で確認）／★(2) ★8本 全通
★(3) ★★`--check` を ★1回 走らせる（★`--apply` は ★走らせない）。★GREEN/RED を ★逐語で持ち帰る
★(4) ★★`v1` の現在値を ★before に、★`--check` の再測値を ★after に入れて ★`axis_delta` を1回 呼ぶ
     ★★結果（★`axes_delta` / `other_ratio_*` / `verdict` / `neg_control_ok`）を ★逐語で書く
★(5) ★★母数と打ち切りの有無（★corpus の行数＝★2062 を実測で確かめ直す）
★(6) ★★`v2`(2本 / 70.6%) は ★★人が1本 足したものなので ★比較に使っていない、と ★明記する
★(7) ★Claude の配線行数（★0 なら 0）／★(8) ★戻せる ／★(9) ★61本を走らせない
★★★★(10) ★`--check` が ★RED を返したら ★★『RED だった』と書いて ★止まる（★直しに行かない・★別単位）
★★★★★予告を投入前に書く: ★worker の行数 ／ ★`--check` の所要時間の見込み
```

## 6. ★★これで分からないこと（★先に言う）
```
★`--check` は ★`v1` を再生成して ★byte 一致を見る ∴ ★corpus が増えていれば ★★REGEN_MISMATCH で RED になりうる。
★★★その RED は ★欠陥ではなく ★★『corpus が変わった』の印である ―― ★但し ★区別は ★出力文字列でしか付かない。
★★★★★∴ ★受入(3) で ★RED の ★行を丸ごと持ち帰らせる（★要約させない）。★判定は MGR。
★★『軸が増えた』『その他が減った』とは ★先に書かない（★裁定の逐語）。
```

## 7. ★9項目（私の分）
```
1 置いたなら読めるか＝★結果は ★台帳の note（★front door から読める）
2 読めるなら書けるか＝★書く口は ★`--apply` だが ★本件では ★走らせない（★§2 で明記）
3 理由を捨てない＝★★§6 で ★RED の意味を ★先に書き、★行を丸ごと持ち帰らせる
4 作っていないのでは＝★★`--check` は ★既に必要な数字を全部 出す ∴ ★新しい計測を作らない
5 走ったか＝★受入(3)(4) は ★実際に走らせて測る／6 名前＝★既存欄（`n_frozen_axes` 等）
★7 依頼と試験の矛盾＝★★依頼文に書いた5語・順番・割合の形（小数）を ★★全部 試験で縛った（v1.11）
   ★★★意図ごとに1行にした（★本日4回目の同型＝1つの assert に2つの意図を入れない）
8 計器が自分を数えないか＝★陰性対照は ★`--check` が ★自分で判定する（★私が別に作らない）
★9 増える代わりに廃止＝★★「7/25 の数字を ★記憶から引く」運用を畳む（★本日 MGR が実際に踏んだ）
```

## 8. 禁止
```
★`--apply`(引数なし実行)を走らせる ／ ★`ACCOUNT_AXES_v2.json` を ★比較の基準に使う
★勘定科目そのものを書き換える（★測るだけ）／ ★RED を直しに行く（★別単位）
★割合を百分率で返す（★小数）／ ★分母0で 0.0 を返す（★None）
★Claude が `axis_delta` の中身を書く ／ ★新しい台帳・エンドポイントを作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
