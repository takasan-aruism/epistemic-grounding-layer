# 設計/監査 → MGR（写: Taka / IMPL）: **D-29 — `process_kill_cleanup` は宣言だけで実装が無い。`/tmp` の1000万件（G-17）もこれで説明が付く**

- `BUILD_ROLE: 参照`（**調査のみ。修正していない**・MGR §3-5）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-28_INCIDENT_RUNAWAY_WORKER_ARTIFACT.md`

## 0. 答え（先に4つ）
1. **`process_kill_cleanup` は宣言だけである。実装は無い。**
2. **生き残る経路は「テストの timeout が直接の子しか殺さない」こと。**
3. **自己増殖の仕組みは Taka の特定どおり。** **`__main__` が2つあり、どの起動経路でもテストが走る。**
4. **★`G-17`（`/tmp` の約1000万エントリ）の主因は、これで説明が付く。**

---

## 1. `process_kill_cleanup` は何をしているか【監査:CC-α・実測】
```
再現: grep -rn "process_kill_cleanup" --include=*.py twoder/
  live_worker_scaffold.py:18  REQUIRED_SANDBOX_FIELDS = (… "process_kill_cleanup" …)   ← 項目名の一覧
  live_worker_scaffold.py:21  _MUST_BE_TRUE = (… "process_kill_cleanup" …)             ← True であることの検査
  live_worker_scaffold.py:35  {"process_kill_cleanup": True, …}                        ← True を入れた辞書
```
**∴ 3箇所とも「宣言」である。** **プロセスを殺すコードはどこにも無い。**
> **∴ `_MUST_BE_TRUE` が検査しているのは「サンドボックス仕様が True と自己申告しているか」であって、「実際に掃除されるか」ではない。**
> **★本日の主題（`DECLARED` を `LIVE` と読まない）の、最も高価な実例である。** **しかも自己申告の排除を掲げている系の中に在った。**

## 2. 生き残る経路【監査:CC-α】
```
live_worker_runtime.py:42  subprocess.run(test_command, cwd=workspace, …, timeout=30)
```
**`timeout` は起動した直接の子を殺す。** **その子が更に起動した孫以降には届かない。**
**∴ テストが自分自身を subprocess で起動していれば、孫は timeout の外で生き続ける。**

## 3. 自己増殖の仕組み（Taka の特定を実測で確認）【監査:CC-α】
```
対象: /tmp/refora_vgsranp1/ref_yvas4ez5/jsonl_tool.py（2026-07-15 作成）
再現: grep -n "__main__" jsonl_tool.py   → 46行目 と 165行目（★2つある）
      165行目以降: if __name__ == '__main__': / run_test()
      run_test() 内: tool_path = …/jsonl_tool.py を subprocess で起動
```
**∴ どの経路で起動しても、2つ目の `__main__` が `run_test()` を呼ぶ。**
**∴ `run_test()` が自分自身を起動する。** **∴ その子でもまた2つ目の `__main__` が走る。** **∴ 無限に増える。**

## 4. ★`G-17` との接続（強い状況証拠）【監査:CC-α】
```
再現: grep -n "NamedTemporaryFile" test_jsonl_tool.py
  tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)   ← ★3箇所以上・delete=False
再現: ls -U /tmp | head -2000 | grep -c "\.jsonl$"   → 2000（サンプル2000件すべてが .jsonl）
```
**∴ 1回の起動ごとに `.jsonl` の一時ファイルが複数、`delete=False` で残る。**
**∴ 530 プロセス × 5日間 → `/tmp` の約1000万件と整合する。**
> **★`G-17` の「作っている主体は未特定」は、これで説明が付く。**
> **【未確認】**: **全1000万件がこの1件由来かは数えていない。** **サンプル2000件が全て `.jsonl` であること、テストが `.jsonl` を `delete=False` で作ることの2点からの推定である。** **断定しない。**

## 5. 同種の残骸（MGR §3-4）【監査:CC-α】
```
再現: ls -d /tmp/refora_*/ref_*/ | wc -l                     → 13
再現: find /tmp -maxdepth 3 -name "jsonl_tool.py" -size +0   → 3件以上
  /tmp/refora_vgsranp1/ref_yvas4ez5/jsonl_tool.py
  /tmp/refora_kwcnoe3f/ref_44t4bb87/jsonl_tool.py
  /tmp/dw_beta_i5ggirnz/ws-e0f16b5b4e/jsonl_tool.py     ← ★refora 以外の経路にも在る
```
**∴ `reference_oracle` 経路（`refora_`）だけでなく、`dw_beta_` 配下にも同じ成果物が在る。**
**∴ `/tmp` 以外は未調査。** **【未確認】**

## 6. ★もう1つの含意（私の資料の記述に関わる）
**この成果物は 2026-07-15 に作られている。** **∴ 過去に生成経路がコードを出したことがある。**
**∴ 私が資料に書いた `C-QWEN-WORKER: WIRED_UNPROVEN` は「本日の観測では到達0件」の意味であって、「一度も出したことが無い」ではない。**
- **【未確認】** **この成果物がどの経路（`reference_oracle` / DW worker）で作られたかを、私は特定していない。**
- **∴ 資料の status を今は動かさない。** **特定できてから直す。** **推測で昇格させない。**

---

## 7. Gap Register への登録（MGR §3-3）
| id | 内容 | 種別 | 状態 |
|---|---|---|---|
| **G-20** | **`process_kill_cleanup` / `host_filesystem_unreachable` 等のサンドボックス保証は、仕様辞書の自己申告を検査しているだけで、実装が無い。** `_MUST_BE_TRUE` は「True と書いてあるか」しか見ない | **`CONTRADICTED`**（宣言と実際が矛盾） | OPEN |
| **G-21** | **`_run_test` の `timeout` は直接の子しか殺さない。** 生成コードが自分を subprocess 起動すると、孫以降が timeout の外で生き残る | gap | OPEN |
| **G-22** | **生成コードの決定論検査に「`__main__` が複数ある」「テストが自分自身を起動する」を見る項目が無い**（`verify_skeleton_preserved` は骨格の保存しか見ない） | gap | OPEN |
| **G-17 更新** | **主因の候補が特定された**（本文書 §4）。**断定はしない** | — | — |

## 8. やっていないこと（MGR §3-5）
- **修正を始めていない。** **1行も直していない。**
- **削除していない**（MGR が慎重に実施中）。
- **`/tmp` を消していない。**

---
*CC-α D-29。★①`process_kill_cleanup` は宣言だけで実装が無い——3箇所とも項目名の一覧・True であることの検査・True を入れた辞書であり、プロセスを殺すコードは無い。`_MUST_BE_TRUE` が見ているのは「仕様辞書が True と自己申告しているか」であって実際に掃除されるかではない。**自己申告の排除を掲げている系の中に、自己申告だけの保証が在った**。②生き残る経路=`live_worker_runtime.py:42` の `subprocess.run(..., timeout=30)` は直接の子しか殺さず孫以降に届かない。③自己増殖=`jsonl_tool.py` に `__main__` が2つ（46行目と165行目）あり、2つ目が `run_test()` を呼び、`run_test()` が自分自身を subprocess 起動する（Taka の特定を実測で確認）。★④`G-17` との接続=テストが `.jsonl` を `delete=False` で3箇所以上作り、`/tmp` のサンプル2000件が全て `.jsonl` ∴ 530プロセス×5日で約1000万件と整合する（全件がこの1件由来かは数えていないので断定しない）。⑤同種の残骸=`refora_*/ref_*` が13ディレクトリ、`jsonl_tool.py` の実体が3件以上、`dw_beta_` 配下にも在る。`/tmp` 以外は未調査。★⑥含意=この成果物は 07-15 作成なので過去に生成経路がコードを出したことがある。私の資料の `C-QWEN-WORKER: WIRED_UNPROVEN` は「本日の観測では到達0件」の意味であり、どの経路で作られたか未特定なので status を今は動かさない（推測で昇格させない）。Gap は G-20(CONTRADICTED: サンドボックス保証が自己申告のみ)/G-21(timeout が孫に届かない)/G-22(生成コードに `__main__` 重複と自己起動を見る検査が無い)を登録。修正は1行もしていない。*
