# 宛: Taka ―― **★事故記録: 稼働中の部品 `requeue_decision` が自動commitで上書きされた**

**発生 2026-08-19 23:44:17 ／ 検知 23:46 ／ ★MGR は 復旧操作を していない（★裁定待ち）**

---

## 0. 何が起きたか

```
★commit 68f93d9「[2DER実装] requeue_decision: TASK-2DER-87191A05
                 (★機械が 置いた=★人の手 0 ／ ★Taka 許可 2026-08-17)」
★requeue_decision.py ／ ★+14 / -58（★72行 → 28行）／ ★commit ＋ ★push 済み
★経路 = `domain_dw.py::_place_and_commit`（★`def X(` の X → `twoder/X.py`）
```

**★これは ★8分前（23:38）に 私が 上申した ★不可逆リスクの ★実現例です。**

## 1. ★壊れた 箇所（★実測・★再現済み）

```
★上書き前 = requeue_decision(task_id, next_operation, in_queue, already_received) → ★dict
★上書き後 = requeue_decision(a, b, c, d, e)                                       → ★bool
★呼び手   = `manager_v0.py:178` が ★4引数 を 渡し ★:180 で `r["requeue"]` を 読む

★★実行 = TypeError: requeue_decision() missing 1 required positional argument: 'e'
★★その 例外は `_last_task` の `except Exception: pass` に 呑まれる
   ＝★★常駐の 自己修復が ★黙って 死んだ
   ＝★★今夜 私が 直した 失敗の型（`DONE_INDEX` の NameError）と ★同じ 形が 再発
```

## 2. ★なぜ 起きたか（★構造・★事実のみ）

```
★`_place_and_commit` の 止まる条件は 4つだけ
   ①関数名が 読めない ②`twoder/` の 外 ③中身が 同じ ④構文が 壊れている
★★『既存の 稼働中 部品か どうか』は ★見ていない ∴ ★中身が 違えば ★上書きする
★★衝突面 = twoder 直下に 『関数名と 同名の file』が ★89本
★★契約経路（Claude が 骨格・封印試験を 書いた task）は ★runner が 動く
   ∴ ★成立する たびに ★1本ずつ 上書きが 起き得る
★待ち行列に 残る Claude DESIGN 由来 = ★9件
```

## 3. ★訂正（★私が 疑って 外した もの）

```
★`twoder/operator.py`（stdlib を 隠す 地雷）は ★機械が 置いた ものでは ない
   （★古い 機能 commit 由来 = feba830 / 38d1988）
★★今夜の 自動commit とは ★無関係。★疑ったので 確かめた。
```

## 4. ★MGR が していないこと（★重要）

```
★revert 0 ／ 常駐の 停止 0 ／ file の 修復 0 ／ `_place_and_commit` の 停止 0
★★理由 = ★どれも ★repo 操作 または ★安全境界の 変更 ∴ ★Taka の 裁定 事項。
★SELF_DEV_TOKEN = ★5/5（★消費 0）
★ご指示の goal（新規配置と 既存file 自己更新の 分離）は ★まだ 投入していない
   ＝★投入すれば 周回が 始まり ★その最中に また 上書きが 起きる ため。
```

## 5. ★決めていただきたいこと（★2つ）

```
★① 常駐（twoder-manager）を 止めるか（★可逆・★状態変更なし）
   ★止めない 限り ★次の 成立で また 既存部品が 上書きされる
★② `68f93d9` を revert するか（★git 履歴に 在る ∴ ★復元は 可能）
```

## 6. ★復元可能性（★事実）

```
★上書き前の 中身は ★`0fccf1e:requeue_decision.py` として ★git 履歴に 残っている
★∴ ★『不可逆』では ない ―― ★但し ★push 済み ∴ ★remote にも 出ている
★★復元は ★repo 操作 ∴ ★私は 打っていない
```
