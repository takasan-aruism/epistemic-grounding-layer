# 【BUILD SPEC】`EVO-0058` — **★前回 落ちた試験の名前だけを ★次の生成へ渡す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 08:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035` ／ 依頼: MGR 08:3x（★条件 (a)〜(d) を ★そのまま受ける）
- **★v1.8 の宣言**: **★核は無い・★2DER 工程 0**（★既存の記録を ★読んで ★つなぐだけ。★判断が無い）
- **★私の予告**: ★Claude **10〜16行** ／ ★worker **0件** ／ ★走行 **1回**（★同一 task の REGENERATE）
- **★新機構0・★新台帳0・★新エンドポイント0**（★`_read_events` と ★既存の `test_result` を読むだけ）

---

## 1. ★★増分は ★実測した（★条件(d)）

```
★実測（★捨て実装で ★本物の欠陥を再現し ★pytest -q の ★実出力から取った）:
   ★取れた `FAILED ` 行 = ★2行
   | FAILED test_impl.py::test_bounded_actor_is_returned_but_not_known - Assertion...
   | FAILED test_impl.py::test_bounded_actor_also_follows_the_route - AssertionErr...
   ★足す字数 = ★★175字（★見出し込み）／ ★requirement 7520字 → ★7695字 ＝ ★★+2.3%
★★★最悪でも ★上限が在る: ★5行 × 200字 + 見出し ＝ ★約1030字（★+14%）―― ★§3 の刈り込みで ★保証する
```

**★★正直に言う（★これで届かないもの）**
```
★`pytest -q` の要約行は ★assert の中身を ★自分で省略する（★逐語 `- Assertion...`）
★★∴ ★worker に届くのは ★★実質 ★試験の名前だけ。★assert の値は ★届かない。
★★★名前は ★規則を名指ししている（例: `bounded_actor_also_follows_the_route`）∴ ★無意味ではない。
★★★★中身も要ると分かったら ★別の1件（★`-q` をやめる／★tail を伸ばす）＝ ★本件では ★変えない。
```

## 2. ★取り出す場所（★既に記録されている・★新しく作らない）

```
★`live_worker_runtime.py:79-80` 逐語 = `res = {"passed":…, "exit":…, "stdout": (out or "")[-500:], "stderr": …}`
★`workcell.py:382-390` 逐語 = `record_generate` が ★`test_result` を ★GENERATE の payload に積む
★★∴ ★前回の失敗は ★★DW に ★既に在る。★取り出すのは ★`_read_events(task_id)` の ★逆順1件目。
★★★`stdout` は ★元から ★500字で切られている ∴ ★取れるのは ★要約行の付近だけ（★これが ★上限の実体）
```

## 3. 変更（★`twoder/generate_via_runner.py` の ★`run_runner`・★requirement を組む ★直前）

```python
    _prev = ""                                               # EVO-0058: 前回 落ちた試験の名前だけを次へ渡す
    try:
        from dw import workcell as W
        for _e in reversed(W._read_events(task_id) or []):
            if _e.get("phase") not in ("GENERATE", "REGENERATE"):
                continue
            _tr = (_e.get("payload") or {}).get("test_result") or {}
            if _tr.get("passed"):                            # ★前回が通っていたら 1文字も足さない
                break
            _ls = [l[:200] for l in (_tr.get("stdout") or "").splitlines()
                   if l.startswith("FAILED ")][:5]           # ★名前と要約だけ・★5行まで
            if _ls:
                _prev = "\n### 前回 落ちた試験:\n" + "\n".join(_ls)
            break                                            # ★直近の1件だけ見る
    except Exception:
        _prev = ""                                           # ★読めなければ 1文字も足さない
```

**★requirement の末尾に `_prev` を足す（★他は1文字も変えない）**
```python
                        "同梱の immutable_tests を全て通すコードを impl.py として書け。"
                        "\n### skeleton:\n%s\n### immutable_tests:\n%s" % (skeleton, immutable_tests)) + _prev,
```

```
★★条件(c)の担保 = ★前回が無い／前回が通っている／読めない → ★`_prev` は ★空文字
   ∴ ★★初回の入力は ★1文字も変わらない（★受入(1) で ★byte で確かめる）
★★★条件(b)の担保 = ★入れるのは ★`FAILED ` で始まる行だけ ―― ★diff も ★stderr も ★成果物本文も ★入れない
```

## 4. ★★これが何を変えるか（★先に言う）

```
★★『再抽選』が ★『前回を見た生成』に変わる ―― ★これが ★本件の狙い（★MGR/Taka の依頼）
★★★同時に ★★『同一入力を2回』という ★比較手順は ★2回目に ★使えなくなる（★入力が違うため）
   ∴ ★★REGENERATE の2回目を ★1回目と ★並べて ★版の優劣を論じない（★規律 v1.14 と ★同じ向き）
★★★★『直るようになった』とは ★書かない ―― ★★試験の名前が ★届くようになっただけである
★★★★★rework は ★2回で ★JUDGE_REQUIRED へ昇格する（`workcell.py:41`）∴ ★見られるのは ★最大2回
```

## 5. 受入

```
★(1) ★★初回の requirement が ★★7520字のまま（★byte で確かめ、★逐語で書く）
★(2) ★1回 落ちた後の REGENERATE で ★requirement が ★★+175字 前後になる（★実測値を ★逐語で書く）
     ★★★私の実測と ★違ってよい ―― ★違ったら ★『違った』と ★数字を書く（★合わせに行かない）
★(3) ★足された行が ★★`FAILED ` で始まる行だけであること（★逐語で全行を書く）
★(4) ★前回が ★通っている task では ★★0字（★1文字も足さない）
★(5) ★★同一 task の中で ★REGENERATE が ★1回 走る（★新規 task を立てない）
★(6) ★Claude の行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★(10) ★通過本数が ★変わっても ★★『直った』と書かない（★§4・★1走行）
★★★★★予告を投入前に書く: ★行数 ／ ★(2) の増分字数
```

## 6. 禁止

```
★`stdout` 全文 ／ ★`stderr` ／ ★`diff` ／ ★成果物本文を ★入れる（★`FAILED ` 行だけ）
★5行を超えて入れる ／ ★1行200字を超えて入れる（★上限を外さない）
★初回の入力を ★1文字でも変える（★§3・受入(1)）
★どの行を入れるかを ★LLM に選ばせる（★決定論で刈る）
★新規 task を立てて ★『同一 task で回した』と書く
★★『直るようになった』『輪が閉じた』と書く（★§4）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
