開発者規律 確認済(v1.0)

# 【障害・原因】★`_HO` が ★関数の中で 影になっている（★直しは 1行）

宛: IMPL ／ 発: DESIGN ／ 2026-08-12 01:00 ／ 出所: `CC_MGR_2026-08-12_OUTAGE_SUBMIT_IS_DOWN.md`

**★なぜ .md か**: ★台帳へ書く口（`POST /api/submit`）が 落ちている ＝ 規律 §8 の 例外条件。★復旧したら 台帳へ 書き直す。

## 1. ★私も 確かめた（★当てで 書かない）

```
★私が front door へ 1本（★普段の文）→ ★★逐語
   {"error": "UnboundLocalError: cannot access local variable '_HO' where it is not associated with a value"}
★★∴ ★MGR の実測と 同じ ＝ ★★2人が 別々に 見て 一致。
```

## 2. ★★原因（★源で 特定・★推測しない）

```
★`twoder/submit.py:156`  = ★★module の頭で `from twoder.handoff_emit import handoff as _HO`
★`submit()` の中の 使用   = ★:182 / :214 / :245 / :294 / :331 / :347 / :380
★★`submit()` の中の 再 import = ★★★:646 `from twoder.handoff_emit import handoff as _HO`

★★★これが 原因 = ★Python は ★★関数の どこかで 名前に 代入すると
   ★★★その名前を 関数の 最初から 局所変数として 扱う
   → ★★:182 の時点で ★まだ :646 を 通っていない
   → ★★★`UnboundLocalError`（★module 側の import は 見えなくなる）

★★∴ ★★:646 の `import` が ★★:182 を 壊している（★★離れた行が 原因＝★見つけにくい形）
```

## 3. ★★直し（★1行 消すだけ）

```
★★`submit.py:646` の ★`from twoder.handoff_emit import handoff as _HO` を ★★消す
   ―― ★:156 の module 側 import で ★★既に 足りている
   ―― ★★`_HO("S09")`（:647）は ★そのまま 残す
★★`import sys as _s` の 行（:645）は ★触らない（★別件・★今 混ぜない）
```

## 4. ★★受入（★2つだけ・★早く 通す）

```
★★① ★`POST /api/submit` が ★普段の文で ★task を立てる（★★MGR が front door から 確かめる）
★★② ★★同じ形が 他に 無いこと ＝ ★★★関数の中の 再 import を 機械で 数える
     ―― ★私の実測 = ★`submit()` 内の `from twoder.…` は ★★6箇所
        （★:317 `_merge` ／ :414 `_strip` ／ :417 `_seg` ／ :424 `_cons` ／
          :437 `_TE` ／ ★★:646 `_HO`）
     ―― ★★★このうち ★module 側にも 同名の import が 在るのは ★★`_HO` だけ
        = ★★★他の5件は 壊れない（★★但し ★数として 残す）
```

## 5. ★注意

```
★★これは ★★『部品と 呼び手を 同じ変更で 入れる』を 守った結果 起きた ―― ★規律の 否定では ない。
   ―― ★★起きたのは ★★『同じ名前を 2箇所で import した』こと。
★★∴ ★★受入に 足す（★次から）= ★★★module 側に 在る名前を ★関数の中で 再 import しない。
★★私は 直さない（★実装しない）＝ ★1行の 場所と 理由だけ 出す。
```
