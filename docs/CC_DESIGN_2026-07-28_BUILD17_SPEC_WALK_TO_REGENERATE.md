# BUILD SPEC — Build 17: **既存の再試行経路を1段ずつ歩き、`READY_FOR_REGENERATE` で止まる**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-28_D28_APPROVED_WALK_THE_PATH.md`
- 対象: **`TASK-2DER-21F64D9D`**（現在 `READY_FOR_AUDIT`）。**`D6A93450` / `B9B4DA3B` に触らない**

## 0. ★D-28 の経路図を訂正する（私の誤り）
**私は「`AUDIT → DISPOSITION_REQUIRED → DISPOSE → READY_FOR_REGENERATE`」と書いた。**
**実際は分岐がある**（`dev-workcell/dw/workcell.py:119-123` 逐語）:
```python
if not findings and tests_ok:        state = "READY_FOR_UPPER_REVIEW"
elif not findings and not tests_ok:  state = "READY_FOR_REGENERATE"    # ★DISPOSE を経ない
else:                                state = "DISPOSITION_REQUIRED"
```
**コメント逐語**: 「**F5 は保持: test が passed=True でなく findings も無ければ、そのまま rework(dispose する finding が無い)**」

**本件は `test_result.status = FAILED` ＝ `tests_ok` は偽。**
> **∴ 監査が finding を0件返せば、`AUDIT` 1段で `READY_FOR_REGENERATE` に到達する。** **`DISPOSE` は要らない。**
> **∴ 「dispose 必須」は finding が在る場合の話である。** **私は片方の枝だけを見て道を描いていた。**

---

## 1. 手順（1段ずつ・最大3回）
```
繰り返す（run_next は最大3回）:
  ① derive_state を確認して記録する
  ② 状態が READY_FOR_REGENERATE  → ★止まる（目的地）
     状態が JUDGE_REQUIRED / BLOCKED / 予期しないもの → ★止めて上げる
     それ以外                     → run_next を1回だけ実行し、応答全文を記録
```
- **`run_until_barrier` を使わない。**
- **★各段の前に必ず `derive_state` を見る**（前回、状態を確認せずに撃つ SPEC を私が書いた）。
- **★`REGENERATE` を実行しない。** **`READY_FOR_REGENERATE` に**なったら**止まる。**
- **3回撃っても目的地に着かなければ、そこで止めて上げる。**

## 2. ★出すもの
1. **各段について**: 実行前の `derive_state` / `run_next` の応答全文 / 実行後の `derive_state` と events。
2. **`AUDIT` の結果**: **`findings` の件数と中身を逐語**（**要約しない**）。**`n_findings` だけでなく、在るなら中身も。**
3. **監査の出力を採点しない**（MGR §3-3）。**そのまま貼る。**
4. **`DISPOSE` が自動で処理された場合、何が起きたかを記録する**（MGR §3-4）。**黙って通さない。**
5. §3 の予想と実際の表。**外れに「外れた」と書く。**
6. **`/tmp/2der_runner_*` の数は投入前後で数えるが、`/tmp` を消さない。**
7. 本番無変更・**commit しない**・冒頭に「運用方針 確認済（版: v1.9）」・定型見出し。

## 3. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| `AUDIT` は dispatch される | **`true`**（`INDEPENDENT_AUDITOR` は機械 actor・`claude_barrier=False`） |
| **`findings` の件数** | **★0件に賭ける**（**監査対象の成果物が存在しない**ため。`diff=null`） |
| **`AUDIT` 後の状態** | **★`READY_FOR_REGENERATE` に賭ける**（0件 ＋ `tests_ok` 偽 → §0 の第2分岐） |
| **必要な `run_next` の回数** | **★1回** |
| `DISPOSE` | **経由しない** |

**★外れたら「外れた」と書く。** **特に findings が1件以上返った場合、`DISPOSITION_REQUIRED` へ行くので2段になる。** **その場合も1段ずつ。**

## 4. やってはいけないこと
1. **`REGENERATE` を実行しない**（本 build は到達まで）。
2. **`run_until_barrier` を使わない。**
3. **監査の出力を採点・修正しない。**
4. **新しい task を作らない。** **他の2 task に触らない。**
5. **手で findings や disposition を書かない。**
6. **オラクルを開封しない。**
7. **本番コードを変更しない。**
8. **`/tmp` を消さない**（`G-17`・Taka の資源）。
9. **`CC_REGISTER.jsonl` に試験行を書かない。**
10. **`twoder/runs/*.trace.json` を読まない。**

## 5. 定型見出し（そのまま）
```
## 到達経路
- [ ] (A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て届いた。

## プロセス鮮度（実行時）
- webui pid / 起動時刻 / ソース mtime:
- [ ] 起動がソースより新しい / [ ] 古い（→ 止めた）

## 歩いた段（実行した順に・撃つ前の状態を必ず書く）
- 1段目: 前=____ / 操作=____ / 後=____
- 2段目: …

## 結果の区分（1つに丸）
- [ ] REACHED_REGENERATE（READY_FOR_REGENERATE に到達して止まった）
- [ ] NEEDS_DISPOSE（findings が在り DISPOSITION_REQUIRED になった）
- [ ] STOPPED_UNEXPECTED（予期しない状態で止めた）
- [ ] BLOCKED（gate に拒否された）
```

## 6. 位置づけ
- **到達しても「作れるようになった」と書かない。** **再生成の入口に着いただけである。**
- **1回の観測で常態を判定しない。**

---
*BUILD SPEC v1.0（★実装源）。Build 17=既存の再試行経路を1段ずつ歩き `READY_FOR_REGENERATE` で止まる。★D-28 の経路図を訂正——`workcell.py:119-123` に分岐があり、**findings が0件で tests_ok が偽なら `AUDIT` 1段で直接 `READY_FOR_REGENERATE` に到達する**（DISPOSE を経ない。逐語「dispose する finding が無い」）。「dispose 必須」は finding が在る場合の話で、私は片方の枝だけを見て道を描いていた。手順=最大3回、各段の前に必ず `derive_state` を確認し、目的地か予期しない状態なら止まる。`run_until_barrier` 不使用・`REGENERATE` は実行しない。出すもの=各段の前後の状態と応答全文／★findings の件数と中身を逐語（採点しない）／DISPOSE が自動処理されたら何が起きたかを記録。予想を固定=AUDIT は dispatch される／**findings は0件に賭ける**（監査対象が存在しないため）／**AUDIT 後は READY_FOR_REGENERATE に賭ける**／必要な run_next は1回／DISPOSE は経由しない。禁止=REGENERATE を実行しない・新 task を作らない・手で findings を書かない・オラクル非開封・`/tmp` を消さない・本番無変更。区分4択。到達しても「作れるようになった」と書かない。*
