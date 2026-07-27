# 実装 → 設計/監査: Build 20 — **掃除の効く実行経路を作り、ダミーで実測しました**（★受入⑤は本物のオラクルの所在が分からず未実施）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-28_BUILD20_SPEC_SAFE_ORACLE_PATH.md` v1.0
- **受領した文書**: 上記 / `CC_MGR_2026-07-28_BUILD20_APPROVED.md`（写しで観測）

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸・両方に丸）
### 経路
- [x] **作った**（`twoder/run_oracle_guarded.py`）/ [ ] 途中で止めた
### 実測
- [x] **D2 で `PRECHECK_BLOCKED` を確認**
- [x] **D1 で実行され `survivors_independent = 0` を確認**（★ただし §2 の訂正あり）
- [x] **Build 18 保全物には当てていない**

---

## 0. ★先に、実装源が前提にしていたものが手元に無い件【監査:IMPL】
**実装源は `run(artifact_dir, oracle_path, target_file)` を求めています。** **しかし `oracle_path` が実装源に書かれていません。**
**中身を開かずに探しました:**
```
再現: find egl twoder dev-workcell ds rri -type f \( -name "*.py" -o -name "*.txt" -o -name "*.json" \) \
        -not -path "*/.git/*" -size -200k | while read f; do
        [ "$(sha256sum "$f" | cut -c1-7)" = "77af566" ] && echo "★一致: $f"; done
結果: 出力なし（＝ sha256 が `77af566…` で始まるファイルは、この5リポジトリに存在しません）

再現: sha256sum twoder/reference_oracle.py     → 5799c6c4…（`77af566…` ではありません）
再現: grep -c "sys.argv" twoder/reference_oracle.py → 0
```
- **∴ `twoder/reference_oracle.py` は、実装源 §3 が描いた「`sys.argv[1]` を受ける CLI」ではありません。**
- **∴ 受入オラクルは、私の手の届く範囲のファイルとして存在しません**（**設計/監査が保持している、という記述と整合します**）。
- **∴ 受入⑤の「本物のオラクルを D1 に当てて `exit` を貼る」は実施できません。** **代わりに、★私が書いたダミーのオラクルで経路を実測しました。** **これは held-out の受入オラクルではありません。**
- **★中身は1文字も見ていません。** **ファイル名と sha256 とヒット件数しか見ていません。**

---

## 1. 作ったもの（`twoder/run_oracle_guarded.py`・新規1本）
```
run(artifact_dir, oracle_path, target_file, timeout=60)
  U1  artifact_precheck を artifact_dir に当てる
      safe_to_run が False → {"ran": False, "precheck": …, "reason": "PRECHECK_BLOCKED"}（★実行しない）
  U2  True のときだけ live_worker_runtime._run_test(artifact_dir, ["python3", oracle_path, target_file])
      ★新しい実行系を作っていません。Build 19(A) で直した _run_test をそのまま呼びます
  U3  _run_test の pg_cleanup をそのまま載せ、★独立に数えた残存数も載せる
      {"ran": True, "precheck": …, "test_result": …, "survivors_independent": int, "survivor_pids": [...]}
```
- **標準ライブラリのみ。LLM を呼びません。**
- **`artifact_precheck` と `live_worker_runtime` を1行も変えていません。呼ぶだけです。**
- **オラクルの中身を読んでいません・変えていません。**

## 2. ★計器の誤りを1つ出します（本日3回目の「自己一致」・`G-23`）【監査:IMPL】
**最初の実測で `survivors_independent = 1`（pid 3136727）と出ました。** **これは誤りでした。**
```
確認: ps -p 3136727  → ★既に存在しない（一瞬で消えるもの＝残存プロセスではない）
原因: 探す文字列に "impl.py" のような短い名前を使っていた。
      その文字列は、私がこの実測を起動した ★自分のシェルの命令行にも入っていた。
```
**∴ 数えていたのは、残った孫ではなく自分の呼び出し元でした。**
**対処（`run_oracle_guarded.py` の中だけ・他は触っていません）:**
1. **探す文字列を絶対パスに限定する**（短い名前では他人の命令行に容易に一致するため）
2. **自分自身と先祖プロセスを除外する**（`/proc` の `ppid` を辿る）

**取り直した値が下の §3 です。** **誤った値（1）を根拠にしていません。**
**★実装源が `survivors_independent` を「`_run_test` の自己申告だけに依らない独立の計測」として求めたのは正しく、そしてその独立の計測自体が `G-23` を踏みました。**

## 3. 実測（★取り直した後の値）
### 3-1. D2（危険なダミー・`__main__` が2つ。★自分自身を起動しない形）
```
ran = False / reason = PRECHECK_BLOCKED
precheck.hits =
  P1  line 5  if __name__ == "__main__":
  P1  line 9  if __name__ == "__main__":
```
**∴ 実行されていません。**

### 3-2. D1（安全なダミー・`__main__` 1つ・`subprocess` 無し）
```
ran = True
test_result: passed=True / exit=0 / timed_out=None
pg_cleanup   = {'attempted': True, 'survivors_before': 0, 'survivors_after': 0}
★survivors_independent = 0 / pids = []
stdout が500字で切れたか: False（長さ 16）
```
- **`exit` は 0 でした。** **★オラクル（私のダミー）の出力内容は貼っていません**（実装源 §4-2 の習慣を、ダミーに対しても守っています）。
- **`survivors_before` が 0 なのは、ダミーが掃除の前に自分で終了していたためです**（孫を作らないダミーなので当然です）。**Build 19 で孫を作る形では `survivors_before = 2` が観測されています。**

### 3-3. 出力の切れ（実装源 §1-1）
- **今回は切れていません**（16 字）。**私のダミーが短いためです。**
- **★実装源は「切れる方に賭ける」と予想していましたが、それは本物のオラクル（十数行を印字する）についての予想です。** **私のダミーではその予想を検証できません。** **★当たり外れの判定をしません。**

## 4. 受入の対応表
| # | 受入 | 結果 |
|---|---|---|
| ① | ダミー2つ（`/tmp` 直下に置かない） | **`~/.cc_tmp/b20_…` に作成** |
| ② | D2 が `PRECHECK_BLOCKED` | **確認（hits 掲載）** |
| ③ | D1 で `test_result` / `pg_cleanup` / `survivors_independent` | **全部掲載** |
| ④ | `survivors_independent` が 0 | **★0**（取り直した値。§2 の訂正つき） |
| ⑤ | D1 に対する**本物のオラクル**の `exit` | **★未実施。** **所在が分からない**（§0）。**ダミーで代替し、そう明記** |
| ⑥ | 3ファイルを1行も変えていない | **`git status --porcelain` で確認**（§5） |
| ⑦ | Build 18 保全物に当てていない | **当てていません**（§5） |
| ⑧ | 非回帰 `test_live_worker_runtime.py` | **15/15 passed** |

## 5. 触ったファイル / 触っていないこと
```
再現: cd /home/takasan/twoder && git status --porcelain
結果: （空）
再現: git log --oneline -3 -- run_oracle_guarded.py artifact_precheck.py live_worker_runtime.py
  3fde617 D-30 受領。★列挙の網羅を確認せよ / G-24 を「改善」で直さない
  9019b2e Build 19: 宣言を実装に変える1件目(…)
```
- **★私が本 build で作った `run_oracle_guarded.py` は、私が報告する前に MGR の commit `3fde617` に入っていました。** **事実として記録します**（**私は commit していません**）。**現在の作業ツリーと commit の内容は一致しています**（`git status` が空）。
- **`artifact_precheck.py` / `live_worker_runtime.py` は本 build で1行も変えていません**（差分なし）。**オラクル本体も触っていません**（そもそも所在不明）。
- **Build 18 の保全物**:
```
再現: find dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen -newermt "2026-07-28 02:30"
結果: 出力なし（＝本 build 中に1件も触れていません）
```

## 6. 予想と実際（実装源 §3）
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| U2 の形でオラクルが動くか | 動く | **本物では未実施**（所在不明）。**私のダミーは動いた** | **★判定不能** |
| 出力が500字で切れるか | 切れる | **私のダミーでは切れない（16字）** | **★判定不能**（本物で測っていない） |
| D1 の `exit` | 予想しない | **0**（私のダミーに対して） | — |
| D2 の precheck | `safe_to_run: False` | **`False`** | **当たり** |
| `survivors_independent` | 0 | **0**（★取り直した後） | **当たり** |
| 非回帰 | PASS | **15/15 PASS** | **当たり** |

## 7. 守った禁止事項
- **★オラクルを Build 18 の保全物に当てていません。開封していません。所在も中身も見ていません。**
- **オラクル（ダミーを含む）の出力内容を貼っていません**（`exit` と切れたかどうかのみ）。
- **`artifact_precheck` / `live_worker_runtime` を変更していません。新しい実行系を作っていません。**
- **検査項目を増やしていません。**
- **`/tmp` のサブディレクトリを消していません。ダミーを `/tmp` 直下に置いていません**（`~/.cc_tmp` 配下）。
- **自分自身を起動する形のダミーを作っていません。**
- **本番コードの他の箇所を触っていません。**
- **commit していません。**

## 8. 位置づけ（実装源 §6）
- **「オラクルが安全に開ける」とは書きません。** **書けるのは「私が作ったダミーに対して、掃除の効く形で走り、残存が0だった」ことだけです。**
- **本物のオラクルでは1度も走らせていません。**

---
*IMPL BUILT（Build 20）。`twoder/run_oracle_guarded.py` を新規1本（U1 precheck→False なら実行しない／U2 **新しい実行系を作らず Build 19(A) の `_run_test` をそのまま呼ぶ**／U3 `pg_cleanup` に加え独立計測の残存数）。★実装源が前提にした `oracle_path` が実装源に書かれておらず、中身を開かずに sha256 で探しても5リポジトリに `77af566…` は存在せず、`twoder/reference_oracle.py` は `sys.argv` を持たない ∴ **受入⑤（本物のオラクルの exit）は未実施**とし、私が書いたダミーのオラクルで経路を実測した（held-out ではない）。実測=D2 は `PRECHECK_BLOCKED`（P1 2件）、D1 は `ran:True` / `exit:0` / `pg_cleanup={'attempted':True,'survivors_before':0,'survivors_after':0}` / **`survivors_independent = 0`**。★計器の誤りを申告（本日3回目の自己一致・`G-23`）=最初 `survivors_independent=1` と出たが、その pid は既に存在せず、原因は探す文字列 `impl.py` が自分の呼び出し元シェルの命令行に一致していたこと。対処として自作ファイルの中だけで「絶対パスのみを探す」「自分と先祖を除外する」を入れ、取り直した値だけを根拠にしている。★独立の計測を求めた実装源の判断は正しく、その独立の計測自体が G-23 を踏んだ。予想=D2 False・残存0・非回帰 PASS は当たり、「U2 でオラクルが動くか」「出力が500字で切れるか」は**本物で測っていないので判定不能**（ダミーでは動き、16字で切れなかった）。非回帰 15/15 PASS。★私が作った `run_oracle_guarded.py` は報告前に MGR の commit `3fde617` に入っていた（事実として記録・私は commit していない）。Build 18 保全物は本 build 中に1件も触れていない（`-newermt` で確認）。「オラクルが安全に開ける」とは書かない。*
