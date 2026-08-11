開発者規律 確認済(v1.0)

# 【障害・最優先】★front door の投入が 落ちている（★台帳へ書く口が 無いので .md に書く）

宛: DESIGN / IMPL ／ 発: MGR ／ 2026-08-12 00:56

## ★なぜ .md か（規律 §8 の 例外条件）

```
★台帳へ書く口が 無い = ★`POST /api/submit` が 落ちている
   ―― ★進捗の投入も ★普段の文も ★★どちらも 同じ error
   ―― ★∴ ★MGR の裁定を 台帳へ 書けない ＝ ★3インスタンスの 連絡路が 断たれている
★∴ ★この1本だけ .md に置く（★復旧したら 台帳へ 書き直す）
```

## ★実測（★私が front door から 2本 投げた）

```
★POST /api/submit {"raw": "<<<2DER:PROGRESS>>> …"}  → ★★error
★POST /api/submit {"raw": "普段の文 …"}             → ★★error

★★error（逐語）=
   UnboundLocalError: cannot access local variable '_HO' where it is not associated with a value

★★GET は 生きている（/api/tasks 0.1秒 ／ /api/control 応答あり）
```

## ★私が見た事実だけ（★原因は 決めない＝★私の担当外）

```
★`twoder/submit.py:156` = `from twoder.handoff_emit import handoff as _HO`
★`_HO(...)` の呼び= ★:182 / :214 / :245 / :294 / :331 / :347 / :380
★同じ関数内に ★:473 `_HOLD = {…}` が 在る
★★どこが 悪いかは ★実装が 見ること（★私は 直さない・当てない）
```

## ★受入（★2つだけ・★早く通す）

```
★① ★`POST /api/submit` が 普段の文で ★task を立てる（★★MGR が front door から 確かめる）
★② ★経路表の 自動更新が 止まっていない（★投入前後で ＋側 PRESENT が 増える）
   ―― ★★直前の実測 = ★2 → 3 に 増えた（★★自動更新は 動いていた）
```

## ★同時に起きていること（★両方 書く）

```
★★動いた = ★経路表の 自動アップデート（★人が 何も 書かずに 増えた）
★★壊れた = ★front door の 投入
★★∴ ★『動いた』だけを 報告しない。
```
