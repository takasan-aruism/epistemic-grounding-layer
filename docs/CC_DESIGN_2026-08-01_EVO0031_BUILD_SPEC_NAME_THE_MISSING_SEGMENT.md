# 【BUILD SPEC / `EVO-0031`】**★見つからなかった断片を★名指しする**（★bool → ★理由つき）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 23:1x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.1 / 2026-08-01）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0031` の `status_note`（★`.md` 無し・逐語:「★我々が骨格を推測して直すのは禁止…
  依頼=BUILD SPEC を最小・可逆で: 骨格の検査が落ちた時、★どの断片が見つからなかったかを返し test_result から読めるようにする」）
- **★増える管理対象 0** ／ **★私はコードを1行も変えていない**

---

# 1. ★★これは C型（★最初から作っていない）を潰す1件である

```
★A型（★片側だけ在る）と ★B型（★渡す所で捨てる）は ★★繋げば出る。
★★★C型は ★★中で作る所から要る ∴ ★★★★今回だけは ★「値を作る」変更になる。★★そう書いておく。
★★★★★ただし ★新しい状態語も台帳も計器も ★作らない。★★既存の返り値に ★欄を足すだけである。
```

---

# 2. ★やること（★★2箇所。★どちらも可逆）

## 2-1. ★検査が「どの断片か」を返せるようにする（`twoder/generate_via_runner.py`）
```python
# ★:69-80 の verify_skeleton_preserved は ★そのまま残す（★呼び出し元が他に在るかもしれない）
#   ★★実装が先に確かめること: ★`verify_skeleton_preserved` の呼び出し元を ★全数 走査し、
#   ★★★1箇所だけなら ★下の関数に置き換えてよい。★2箇所以上なら ★足す形にする。★どちらにしたか報告する。

def skeleton_missing_segment(skeleton, artifact):
    """骨格の固定区間のうち ★最初に見つからなかったものを返す。★全部 在れば None。★LLM を通さない。"""
    if not isinstance(artifact, str):
        return "(artifact is not a string)"
    pos = 0
    for seg in _skeleton_fixed_segments(skeleton):
        idx = artifact.find(seg, pos)
        if idx < 0:
            return seg          # ★★見つからなかった断片 そのもの
        pos = idx + len(seg)
    return None
```

## 2-2. ★その値を `test_result` まで運ぶ
```python
# ★generate_via_runner.py:219-220（★SKELETON_VIOLATION を返す枝）
    artifact = res.get("artifact")
    ★_missing = skeleton_missing_segment(skeleton, artifact)
    if artifact is not None and ★_missing is not None:
        return {"ok": False, "run_id": run_id, "artifact_sha256": artifact_sha256,
                "reason": "SKELETON_VIOLATION", "contract_source": contract_source,
                ★"skeleton_missing_segment": _missing}      # ← ★足す

# ★twoder/webui.py:327-329（★test_result を作る所・★EVO-0031 で 2欄 足した所）
                              "runner_exit": gr.get("runner_exit"),
                              "runner_stdout_tail": gr.get("runner_stdout_tail"),
                              ★"skeleton_missing_segment": gr.get("skeleton_missing_segment")},  # ← ★足す
```
```
★★★★戻し方: ★足した3箇所（関数1・返り値1・test_result 1）を消す。★★可逆である。
★★★★★★`verify_skeleton_preserved` を ★消さない・★緩めない（★検査の強さを変えない）
```

---

# 3. ★★長さの上限を決めておく（★先に書く・★私の判断）
```
★★断片は ★骨格 全文になりうる（★`<<<FILL` が無い契約では ★固定区間が1つ ＝ ★全文）。
   ★★★実測: ★私が S-3 に書いた skeleton には ★`<<<FILL` が ★0件 ∴ ★★全文が1断片である。
★★★★∴ ★そのまま載せると ★`test_result` が ★数千字になりうる。
★★★★★★∴ ★★先頭 ★400字 で切る。★切ったことが分かる形にする（例: 末尾に `…(truncated)`）。
   ★★★★★★★★理由: ★★「どこが」を知るには ★先頭で足りる（★`find` は ★先頭から一致を見る）。
   ★★★★★全文が要るなら ★★別の口を作る話になる ∴ ★今回やらない（★規律9）。
```

---

# 4. ★受入（★裁定の逐語＋★§3）
```
★(1) ★`SKELETON_VIOLATION` の時、★`GET /api/claude_packet` の ★`test_result` に
     ★`skeleton_missing_segment` が★在り、★中身が読める
★(2) ★★`TASK-2DER-0E5E8675`（★いま SKELETON_VIOLATION で止まっている）で ★逐語を持ち帰る
     ★★★★ただし ★★★過去の走行は ★測り直せない（★捨てた値は台帳に無い）∴ ★★新しい走行が要る
     ★★★★★★走行の作り方は ★あなたが決めてよい（★`run_next` で REGENERATE を起こす／★再投入）。★どちらか書く
★(3) ★400字で切れており、★切ったことが分かる
★(4) ★戻せる（★3箇所を消したら ★元に戻る）——★戻して確かめ、★また足す
★★★★★予告を投入前に書く: ★(1)〜(4) の予想 ／ ★変更行数 ／ ★`verify_skeleton_preserved` の呼び出し元の件数
```

---

# 5. ★★禁止（★★1つ 強く書く）
```
★★★★骨格を ★推測で直さない（★裁定の逐語:「★我々が骨格を推測して直すのは禁止」）
   ★★私は ★前回 「★`<<<FILL` が無いのが原因かもしれない」と書いた。★★★これは ★推定である。
   ★★★★★★★この SPEC で ★それを直さない。★★読めるようにするだけである。★直すのは ★MGR の手番。
★他: ★`verify_skeleton_preserved` を消す・緩める ／ ★新しい状態語・台帳・計器・エンドポイントを作る
     ★契約を書き直す ／ ★commit する ／ ★★`twoder` 配下で python を動かす（★`operator.py` の罠）
```

# 6. ★報告
```
1 ★変更行数（★Claude が書く例外 ∴ ★2DER の実績に数えない）
2 ★受入 (1)〜(4) ／ 3 ★予告の当否 ／ 4 ★`verify_skeleton_preserved` の呼び出し元は何件で どちらにしたか
5 ★★`skeleton_missing_segment` の ★逐語（★400字まで）／ 6 ★どの方法で新しい走行を作ったか
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①これは C型（最初から作っていない）を潰す1件で、今回だけは「値を作る」変更になる。ただし新しい状態語も台帳も計器も作らず、既存の返り値に欄を足すだけである ②2箇所——`skeleton_missing_segment` を足して最初に見つからなかった断片そのものを返し、`SKELETON_VIOLATION` の枝と `test_result` まで運ぶ。`verify_skeleton_preserved` は消さず緩めず、呼び出し元を全数 走査して1箇所なら置換・2箇所以上なら並置とし、どちらにしたか報告させる ③長さの上限を先に決めた——`<<<FILL` の無い契約では固定区間が1つ＝骨格 全文なので、そのまま載せると数千字になりうる。先頭400字で切り、切ったことが分かる形にする。全文が要るなら別の口の話なので今回やらない ④受入は4つ。過去の走行は測り直せないので新しい走行が要り、その作り方は実装が決めてよいがどちらか書かせる ⑤★骨格を推測で直すことを強く禁じた。私が前回 書いた「`<<<FILL` が無いのが原因かもしれない」は推定であり、この SPEC ではそれを直さず、読めるようにするだけである。直すのは MGR の手番。**
