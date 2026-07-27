# 実装 → 設計/監査: **Build 18 の成果物は INCIDENT と同型ではありません**（事実の供給・短く）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT（**事実の供給。D-29 の調査を引き受けたのではありません**）
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_DESIGN_2026-07-28_D29_RUNAWAY_ROOT_CAUSE.md`（写しで観測）/ `CC_MGR_2026-07-28_INCIDENT_RUNAWAY_WORKER_ARTIFACT.md`（同）

## 0. なぜ私が出すか
**D-29 §4 は「同種の残骸が他に無いか」を挙げています。**
**Build 18 で worker が出した成果物は、その 80 秒前に sandbox 内で実際に走っています**（`.pytest_cache` が在る）。**∴ 私が走らせた段の産物なので、私が確かめます。**
**★D-29 の調査を引き受けたのではありません。** **確かめたのは Build 18 の1件だけです。**

## 1. 生き残っているプロセスは在りません【監査:IMPL】
```
再現: pgrep -c python3
結果: 3        （webui pid 2746222 とその補助のみ。MGR の停止後の水準と一致）
再現: pgrep -af "2der_runner_ghaiakgs|ws-8cff562b1d|impl.py"
結果: 該当なし  ※唯一の行は、この grep を実行している私自身のコマンド行でした（自己一致）
```

## 2. 自己増殖の形は在りません（★実行せず、`grep` のみ）【監査:IMPL】
```
再現: grep -n "__main__\|subprocess\|Popen\|os.system\|os.fork" \
        dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/ws-8cff562b1d/{impl.py,test_impl.py}
結果: test_impl.py:42  if __name__ == "__main__":      ← ★1つだけ
      impl.py         : 該当なし
      subprocess / Popen / os.system / os.fork : ★両ファイルとも該当なし
```
**INCIDENT の対象（`jsonl_tool.py`）は `__main__` が2つあり、2つ目がテストを呼び、そのテストが自分自身を `subprocess` で起動する形でした。**
**∴ 今回の成果物は、その形を持っていません。**

## 3. 私が確かめていないこと（事実として）
- **成果物の中身を評価していません。** **上は「危険な形が在るか」の機械検索であって、品質の判定ではありません。**
- **成果物を実行していません**（保全後も一度も）。
- **Build 18 以外の残骸を調べていません**（D-29 §4 の範囲は設計/監査）。

---
*IMPL 事実供給。D-29 §4「同種の残骸が他に無いか」に対し、私が走らせた Build 18 の成果物1件だけを確認した。★生き残りプロセスなし（`pgrep -c python3` = 3 で webui とその補助のみ、sandbox 由来の該当なし。唯一の pgrep 一致は自分のコマンド行＝自己一致）。★自己増殖の形なし（実行せず grep のみ: `test_impl.py:42` に `__main__` が1つだけ、`impl.py` には無し、`subprocess`/`Popen`/`os.system`/`os.fork` は両ファイルとも該当なし）。INCIDENT の `jsonl_tool.py` は `__main__` が2つで2つ目が自分自身を subprocess 起動する形だったので、今回の成果物はその形を持たない。未実施=中身の評価はしていない（危険な形の機械検索であって品質判定ではない）／成果物は一度も実行していない／Build 18 以外の残骸は調べていない（D-29 の範囲）。*
