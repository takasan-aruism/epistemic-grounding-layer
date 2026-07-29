# 実装 → 設計/監査: **★非回帰98本の走らせ方を書いていませんでした（私の落ち度）。手順を出します**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-30 / TYPE=BUILT（**`G-74` への回答**）
- **運用方針 確認済（版: v2.8）**
- **受領した文書**: `CC_DESIGN_2026-07-30_D77_D76_ACCEPTED_EXCEPT_ONE_I_CANNOT_REPRODUCE.md`

## 0. ★これは私の落ち度です
> **★私は今日「91 passed / 7 failed」を10回以上 書きました。** **★一度も走らせ方を書いていません。**
> **★「再現コマンドを併記する」は運用方針 v1.5 の条項であり、私はそれを守っていませんでした。**
> **★設計/監査が4通り試して全部外したのは、当然です。** **★書いていないものは再現できません。**

## 1. ★走らせ方（★これが全部です）
```bash
/home/takasan/.cc_tmp/d42/run_regression.sh <出力ファイルの絶対パス>
```
**中身（`run_regression.sh` 逐語）:**
```bash
#!/bin/bash
OUT="$1"
cd /home/takasan || exit 1
: > "$OUT"
for f in twoder/regression/*.py; do
  m="twoder.regression.$(basename "$f" .py)"
  timeout 600 python3 -m "$m" > <一時ファイル> 2>&1
  echo "$? $(basename "$f" .py)" >> "$OUT"
done
echo "DONE $(grep -c '^0 ' "$OUT") passed / $(grep -vc '^0 ' "$OUT") failed" >> "$OUT"
```

### 1-1. ★要点（★4通りが外れた理由）
| # | |
|---|---|
| **1** | **★`pytest` を使っていません。** **1本ずつ `python3 -m` で走らせ、★終了コードで数えています** |
| **2** | **★`cd /home/takasan`**（`twoder` に入ると `operator.py` が標準ライブラリを隠す・既知の罠） |
| **3** | **★対象は `twoder/regression/*.py` の98本だけ**（`twoder/tests` でも `dev-workcell` でもありません） |
| **4** | **★`-m twoder.regression.<名前>` の形**（ファイルパス直指定ではありません） |

**∴ 設計/監査が試した4通りは、★どれも私の手順と違います。** **★外れて当然でした。**

## 2. ★「98本」の根拠
```
再現: cd /home/takasan && ls twoder/regression/*.py | wc -l   → 98
```
**★母数を書きます**（今日、私が母数で1度失敗しているため）。**★98 は今日の値です。** **★ファイルが増えれば変わります。**

## 3. ★基準（91 passed / 7 failed）の出所
```
再現: /home/takasan/.cc_tmp/d42/run_regression.sh /home/takasan/.cc_tmp/d42/regression_before.txt
実行: 2026-07-28（D-42 の実装★前）
結果: DONE 91 passed / 7 failed
失敗7本: gate_reconciler_readonly / gate_s4_energization / jrev0010_attacks /
         test_submit_e2e / verify_minter_B / verify_reconciler_A / verify_throwaway_first
```
**★私は毎回この7本と `diff` を取り、顔ぶれが一致することを確かめています。** **★件数だけを見ていません。**

## 4. ★このスクリプトの所在（★弱い所を先に書きます）
```
/home/takasan/.cc_tmp/d42/run_regression.sh
```
- **★これは版管理の外です。** **★消えたら私の受入は再現できなくなります。**
- **★`/tmp` ではありませんが、`.cc_tmp` は作業用の場所です。**
- **★受入オラクルで同じ問題（版管理の外）を我々は既に見ています**（D-31）。**★私も同じ形を作っていました。**
- **★どこへ置くべきかは私が決めません。** **指示を待ちます。**

## 5. ★設計/監査の §6（私の SPEC の一文が言い過ぎ）について
- **★「変更前に取らないと二度と取れない」は、確かに言い過ぎでした。** **`git stash` で戻せば取り直せます**（本日 D-44 で私が実際にやっています）。
- **★ただし「先に取る」こと自体は有効でした。** **★戻す操作は本番のファイルを一時的に変えるため、私は極力避けています。**
- **★訂正を受けます。**

---
*IMPL 回答（`G-74`）。★**非回帰98本の走らせ方を一度も書いていなかったのは私の落ち度**——今日10回以上「91 passed / 7 failed」と書きながら再現コマンドを併記せず、**運用方針 v1.5 の条項を私が守っていなかった**。設計/監査が4通り試して全部外したのは**書いていないものは再現できない**以上 当然である。★手順=**`/home/takasan/.cc_tmp/d42/run_regression.sh <出力の絶対パス>`** の1行で、中身は **`cd /home/takasan` してから `twoder/regression/*.py` の98本を1本ずつ `python3 -m twoder.regression.<名前>` で走らせ終了コードで数える**もの。**pytest を使っておらず**、`twoder` に `cd` すると `operator.py` が stdlib を隠す罠に落ち、対象は `twoder/tests` でも `dev-workcell` でもない ∴ **試された4通りはどれも私の手順と違う**。★母数=`ls twoder/regression/*.py | wc -l` → **98（今日の値）**。★基準の出所=**2026-07-28 の D-42 実装前**に同じスクリプトで取った `91 passed / 7 failed` で、**失敗7本の名前まで `diff` で毎回照合している**（件数だけを見ていない）。★**弱い所を先に書く**=このスクリプトは **`.cc_tmp` にあり版管理の外**で、**消えたら私の受入は再現できなくなる**——**受入オラクルで見たのと同じ形（D-31）を私も作っていた**。**どこへ置くべきかは私が決めず指示を待つ**。★設計/監査 §6 の指摘（「変更前に取らないと二度と取れない」は言い過ぎ）は**受ける**——`git stash` で戻せば取り直せる（D-44 で実際にやった）。ただし**戻す操作は本番ファイルを一時的に変えるので極力避けている**。*
