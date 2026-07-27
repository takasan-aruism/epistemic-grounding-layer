# BUILD SPEC — Build 20: **オラクルを安全に走らせる経路を作る（U1〜U3）。★オラクルは開封しない**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-28_BUILD19_RECEIVED_UNFREEZE_NOT_YET.md` §3（解凍条件 U1〜U3）

## 0. ★これは何で、何ではないか
| | |
|---|---|
| **これは** | **オラクルを「掃除の効く形」で走らせる経路を作り、ダミーで動くことを実測する** |
| **これではない** | **★オラクルを Build 18 の成果物に当てない。** **開封しない。** **賭けの決着をしない**（それは設計/監査が、解凍後に行う） |
| **理由** | **オラクルの中身と結果は設計/監査が保持する。** **IMPL が実物に当てると、held-out の意味が消える** |

---

## 1. 作るもの（1ファイル・小さい）
**`twoder/run_oracle_guarded.py`**（名前は変えてよい。**`twoder/` に1本**）
```
run(artifact_dir, oracle_path, target_file) -> dict

  U1: artifact_precheck を artifact_dir に当てる
      → safe_to_run が False なら、ここで止める（実行しない）
      → 戻り {"ran": False, "precheck": {...}, "reason": "PRECHECK_BLOCKED"}
  U2: safe_to_run が True なら、
      live_worker_runtime._run_test(workspace=artifact_dir,
                                    test_command=["python3", oracle_path, target_file])
      ★新しい実行系を作らない。A で直した _run_test をそのまま使う
  U3: 戻り値の pg_cleanup をそのまま載せ、
      さらに ★独立に残存プロセスを数えた値も載せる（_run_test の自己申告だけに依らない）
      → 戻り {"ran": True, "precheck": {...}, "test_result": {...}, "survivors_independent": int}
```
- **標準ライブラリのみ。LLM を呼ばない。**
- **`artifact_precheck` と `live_worker_runtime` を変更しない。** **呼ぶだけ。**
- **★オラクルの中身を変えない。** **読まない。**

### 1-1. ★先に知っておくべき制約（私が読んだ事実）
```
live_worker_runtime._run_test:  res["stdout"] = r.stdout[-500:]   ← ★末尾500字に切られる
```
**∴ オラクルの出力は切れる可能性がある。**
- **∴ 合否の判定は `exit`（終了コード）で行う。** **オラクルは MUST が1件でも落ちれば非0で終わる。**
- **★出力が切れた場合は「切れた」と書く。** **回避策をこの build で作らない。** **必要なら次の build で扱う。**

---

## 2. 受入（★ダミーで実測する。実物に当てない）
1. **ダミーを2つ作る**（一時ディレクトリ。**`/tmp` 直下を汚さない**）:
   - **D1（安全）**: `answer(rid, resolve_fn, known_prefixes)` を持つ最小の実装。**`__main__` 1つ・`subprocess` 無し。**
   - **D2（危険）**: **`__main__` を2つ持つ**か **`subprocess` を含む**もの。**★自分自身を起動する形にしない**（INCIDENT を再現しない）。
2. **D2 に対して `ran: False` / `reason: PRECHECK_BLOCKED` になること。** **`precheck.hits` を貼る。**
3. **D1 に対して実行され、`test_result` と `pg_cleanup` と `survivors_independent` が返ること。** **全部貼る。**
4. **★`survivors_independent` が 0 であること。** **0 でなければ、そう書いて止める。**
5. **D1 に対するオラクルの `exit` を貼る。** **★オラクルの出力内容（どの検査が通った/落ちた）を BUILT に貼らない。** **`exit` と、切れたかどうかだけ。**
   - **理由**: **D1 は私が作ったダミーではなく IMPL が作るものなので、その結果は held-out の秘匿に影響しない。** **しかし習慣として、オラクルの出力を BUILT に流さない形を先に作る。**
6. **`artifact_precheck` / `live_worker_runtime` / オラクル本体を1行も変えていないこと**（`git status` で示す）。
7. **★Build 18 の保全物に当てないこと。** **当てていないことを明記する。**
8. **非回帰**: `twoder/regression/test_live_worker_runtime.py`。**実行して貼る。**
9. **commit しない。** 冒頭に「運用方針 確認済（版: v1.9）」。**定型見出し＋2軸の結果欄。**

---

## 3. 予想を先に書く（MGR 指定: 「U2 の形にしたとき既存のオラクルが動くか」）
| 項目 | DESIGN の予想 |
|---|---|
| **U2 の形でオラクルが動くか** | **★動く。** オラクルは `sys.argv[1]` を受け `os.path.abspath` で解決する標準的な CLI であり、cwd に依存しない |
| **オラクルの出力が500字で切れるか** | **★切れる方に賭ける**（オラクルは十数行を印字する） |
| `exit` の値（D1 に対して） | **【未確認】**——**D1 は IMPL が作るので、私は中身を知らない。予想しない** |
| D2 の precheck | **`safe_to_run: False`** |
| `survivors_independent` | **0** |
| 非回帰 | **PASS** |

**★外れたら「外れた」と書く。**

---

## 4. やってはいけないこと
1. **★オラクルを Build 18 の保全物に当てない。** **開封しない。**
2. **★オラクルの出力内容を BUILT に貼らない**（`exit` と切れたかどうかのみ）。
3. **オラクル本体・`artifact_precheck`・`live_worker_runtime` を変更しない。**
4. **新しい実行系を作らない**（`_run_test` を使う）。
5. **検査項目を増やさない。**
6. **`/tmp` のサブディレクトリを消さない**（証拠）。**ダミーは `/tmp` 直下に置かない。**
7. **INCIDENT を再現する形のダミーを作らない**（自分自身を起動しない）。
8. **本番コードの他の箇所を触らない。**

## 5. BUILT の定型見出し（2軸）
```
## 到達経路
- [ ] (A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸・両方に丸）
### 経路
- [ ] 作った / [ ] 途中で止めた（理由: ____）
### 実測
- [ ] D2 で PRECHECK_BLOCKED を確認 / [ ] しなかった（理由: ____）
- [ ] D1 で実行され survivors_independent = 0 を確認 / [ ] 0 でなかった（→ 止めた）
- [ ] Build 18 保全物には当てていない
```

## 6. 位置づけ
- **★これで「オラクルが安全に開ける」とは書かない。** **書けるのは「ダミーに対して、掃除の効く形で走り、残存が0だった」ことだけである。**
- **解凍と開封は、MGR の裁定と設計/監査の作業である。**

---
*BUILD SPEC v1.0（★実装源）。Build 20=オラクルを掃除の効く形で走らせる経路を作り、★ダミーで実測する。**オラクルを Build 18 の保全物に当てない・開封しない・出力内容を BUILT に貼らない**（held-out の秘匿と、その習慣を先に作るため）。作るのは `twoder/run_oracle_guarded.py` 1本——U1 `artifact_precheck` を当て False なら実行しない／U2 **新しい実行系を作らず A で直した `live_worker_runtime._run_test` をそのまま使う**／U3 `pg_cleanup` に加えて★独立に数えた残存も載せる（自己申告だけに依らない）。★先に知っておく制約=`_run_test` は stdout を末尾500字に切るので合否は `exit` で判定し、切れたら「切れた」と書き回避策を作らない。受入=D1(安全)/D2(危険・★自分自身を起動しない)のダミー2つで、D2 が `PRECHECK_BLOCKED`、D1 で実行され `survivors_independent=0`、オラクル出力は貼らず `exit` と切れたかのみ、3ファイルを1行も変えていないこと、Build 18 保全物に当てていない明記、非回帰。予想=U2 の形でオラクルは動く（`sys.argv[1]` を `abspath` で解決する CLI）／出力は切れる方に賭ける／D1 の exit は D1 の中身を知らないので予想しない／D2 は False／残存0／非回帰 PASS。★これで「安全に開ける」とは書かない。書けるのは「ダミーに対して掃除の効く形で走り残存が0だった」ことだけ。*
