# 【BUILD SPEC / `EVO-0031`】**★成果物の先頭を読めるようにする**（★推測で投げ直すのをやめる）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 01:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.2 / 2026-08-02）** ／ **★9項目 確認済（★§6。★外れた番号なし）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0031` の `status_note`（★`.md` 無し・逐語:「★2回外した ∴ 3回目を推測で投げない…
  依頼=次のどちらかを最小・可逆で: (a) ★成果物の先頭N字を front door から読めるようにする (b) 検査が行う比較そのものを逐語で示す。★(a) を推す」）
- **★私はコードを1行も変えていない**

---

# 1. ★★(a) を採る（★MGR の推しと同じ。★ただし理由を独立に書く）

```
★(b)「比較そのものを逐語で示す」は ★★比較の形を ★我々が決めることになる
   （★何と何を、どう並べて見せるか）＝ ★★★設計判断が1つ増える。
★(a)「成果物の先頭を読む」は ★★既に在る値を ★出すだけ ＝ ★★判断が0。
★★★★∴ ★(a) が小さい。★★かつ ★(a) が在れば ★(b) は ★我々が目で出来る（★断片は既に読める）。
```

## 1-1. ★★先に確かめた（★9項目 #1「置いたなら どこから読めるか」の裏）
```
★★`artifact` は ★その時点で ★★必ず在る:
   ★`generate_via_runner.py:236` 逐語 `if artifact is not None and _missing is not None:`
   ＝ ★★`SKELETON_VIOLATION` に入る条件が ★★`artifact is not None` である
★★★∴ ★★「読めるようにしたら None だった」は ★★起きない。★★出す値は ★確実に在る。
★★★★★かつ ★正規化が ★`:165` 逐語 `"artifact_sha256": art_sha, ★"artifact": artifact,` で ★載せている
★★★★★★∴ ★★取りに行く先も ★既に在る。★★作らない。
```

---

# 2. ★やること（★★2箇所。★`skeleton_missing_segment` を足したのと ★同じ形）

```python
# ★twoder/generate_via_runner.py:237-239（★SKELETON_VIOLATION の枝・★いま在る形に足す）
        _seg = _missing if len(_missing) <= 400 else _missing[:400] + "…(truncated)"
        ★_head = ("%s" % artifact)[:400] + ("…(truncated)" if len("%s" % artifact) > 400 else "")
        return {"ok": False, "run_id": run_id, "artifact_sha256": artifact_sha256, "reason": "SKELETON_VIOLATION",
                "contract_source": contract_source, "skeleton_missing_segment": _seg,
                ★"artifact_head": _head}          # ← ★足す

# ★twoder/webui.py（★test_result を作る所・★3欄 足してある所）
                              "skeleton_missing_segment": gr.get("skeleton_missing_segment"),
                              ★"artifact_head": gr.get("artifact_head")},      # ← ★足す
```
```
★★400字 に揃える（★`skeleton_missing_segment` と同じ）。★理由: ★★並べて比べるため。★★長さが違うと ★見比べにくい
★★★★戻し方: ★足した2箇所を消す。★★可逆である
★★★★★★`verify_skeleton_preserved` / `skeleton_missing_segment` を ★変えない（★検査を緩めない）
```

---

# 3. ★★★増える代わりに廃止するもの（★9項目 #9。★★前回 私が満たせなかった項目）

> ### **★「骨格を推測で書き直して投げ直す」運用を★廃止する。**

```
★実物: ★MGR は ★v5（★98字に縮めた）と ★v6（★署名行だけ）を ★投げ、★★2回とも外した。
★★★本件が通れば ★★成果物の先頭が読める ∴ ★★★「何と違うか」を ★★見てから直せる。
★★★★∴ ★★以後 ★★骨格を ★実物を見ずに書き直して投げない。★★これを ★同時に畳む。
★★★★★★（★前回 私は ★欄を1つ増やして ★廃止を書かなかった。★★今回は書いた）
```

---

# 4. ★受入
```
★(1) ★`SKELETON_VIOLATION` の時、★`test_result` に ★`artifact_head` が在り、★中身が読める
★(2) ★★`skeleton_missing_segment` と ★`artifact_head` を ★並べて、★★どこが違うかが ★人に分かる
     ★★★★分からなければ ★「★分からない」と書く（★★分かったことにしない）
★(3) ★400字で切れており、★切ったことが分かる
★(4) ★戻せる（★2箇所を消したら元に戻る）——★戻して確かめ、★また足す
★★★★★測るのに ★★新しい走行は ★要らない見込み【★未確認】——★★`TASK-2DER-816D6F68` は
   ★いま `SKELETON_VIOLATION` で止まっている ∴ ★`run_next` で ★REGENERATE を1回 起こせば足りる。
   ★★要らなかった／要ったを ★書くこと
```

# 5. ★禁止 ／ 6. ★9項目（★私の分）
```
【禁止】★検査を緩める・消す ／ ★骨格を書き直す（★★MGR の手番・★実物を見てから）
        ★新しい状態語・台帳・計器・エンドポイントを作る ／ ★commit する
        ★★`twoder` 配下で python を動かす（★`operator.py` の罠）
【9項目】1 読める口＝`test_result`（★確認済）／2 該当なし（読む側の追加）／3 捨てていない（★枝に載せる）
        4 作っている（★`artifact` は既に在る・★§1-1）／5 ★実装が webui 再起動を確かめること
        6 該当なし（名前を足していない）／7 ★★本 SPEC は依頼文でなく機構 ∴ 契約との矛盾なし
        8 ★front door の値を見る（★自分の書き込みではない）／★9 ★★§3 で廃止を書いた
```

---
**決めたこと**: **①(a)（成果物の先頭を読めるようにする）を採る。理由は独立に書いた——(b) は比較の形を我々が決めることになり設計判断が1つ増えるが、(a) は既に在る値を出すだけで判断が0。かつ (a) が在れば (b) は目で出来る ②先に確かめた——`SKELETON_VIOLATION` に入る条件が `artifact is not None` なので、出す値は確実に在る。正規化も `"artifact": artifact` で載せているので取りに行く先も既に在る ③やることは2箇所（`generate_via_runner` の枝と `webui` の `test_result`）で、`skeleton_missing_segment` を足したのと同じ形。400字に揃えるのは並べて比べるため。2箇所を消せば戻る ④★増える代わりに廃止するものを書いた——「骨格を推測で書き直して投げ直す」運用を畳む。MGR は v5・v6 と2回 外しており、本件が通れば実物を見てから直せる。前回 私は欄を増やして廃止を書かなかったが、今回は書いた ⑤受入は4つで、(2) は「どこが違うか人に分かる」ことを求め、分からなければ「分からない」と書かせる ⑥新しい走行は要らない見込み（`TASK-2DER-816D6F68` が `SKELETON_VIOLATION` で止まっているので `run_next` 1回で足りる）が、要った/要らなかったを書かせる ⑦9項目を自分に当て、外れた番号は無い。**
