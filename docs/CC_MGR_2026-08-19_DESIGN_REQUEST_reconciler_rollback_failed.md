# 宛: DESIGN（監査 CC）―― 契約作成の依頼: **未解消の `ROLLBACK_FAILED` が在る間 BALANCED を出さない**

**依頼元: MGR ／ 2026-08-19 ／ Taka 指示（判定3 の是正・★1箇所だけ）**
**MGR は判断ロジックを書きません。実 repo へ書いていません。実装していません。**

---

## 1. ★閉じたい欠陥（★実走で確認済み）

```
APPLIED → rollback 失敗 → ROLLBACK_FAILED → on-disk は ★適用後の bytes の まま
→ `_fold_expected` が ★ROLLBACK_FAILED を 無視（★2語しか 見ない）
→ 直前の APPLIED の 期待値が 残る → ★disk と 一致 → ★★BALANCED

★★危険: この BALANCED は `bridge_minter` の ★門(3) の 材料
   逐語「(3) the reconciler proves a FRESH balance … ★None/imbalanced/stale => ★refuse」
   ＝★rollback に 失敗して 不可逆に なった 直後でも ★次の energize が 止まらない。
```

## 2. ★既存欄で表せるか → **★表せる（★新しい状態語を作らずに済む）**

**`ReconResult`（★実物・10欄）:**

```python
balanced: bool
★orphans_event_without_git: tuple   # (filename, expected_fp): event says APPLIED, disk doesn't match
orphans_git_without_event: tuple    # filename: dirty in git, no matching APPLIED event
baseline: bool ／ head ／ checked_files ／ applies_seen ／
repo_identity ／ repo_realpath ／ unbound_events_seen
```

```
★`balanced = not ew_git and not gw_event`（★実物）
★∴ ★`orphans_event_without_git` に 1件でも 入れば ★balanced は ★自動で False
★かつ `emit_reconciliation` は ★この欄を そのまま proof の payload に 載せる（★195行）
   ＝★★理由が 門(3)の 材料に そのまま 届く
★★∴ ★新しい 欄も 新しい 状態語も ★要らない 見込み（★但し 意味づけは DESIGN が 決める）
```

## 3. ★append-only で後から解消できるか → **★できる（★2重に）**

**`latest_balance_proof` の逐語:**

```
「Fresh iff the latest RECONCILIATION_* event is RECONCILIATION_BALANCED
  ★AND ★no PATCH_APPLICATION appears AFTER it
  (clock-free freshness cap = ★zero unreconciled applies since the proof).
  ★Absent/imbalanced/stale -> fresh=False -> ★minter fails closed.」
```

```
★① 後から ★正常な ROLLED_BACK を append すると ★それは PATCH_APPLICATION
   → ★古い proof の 後に 来る ∴ ★proof が ★stale に なる → ★fresh=False（★門(3) は 落ちる）
★② 新しく reconcile を 回すと `_fold_expected` は ★順に 畳む（★後の 語が 勝つ）
   → ★ROLLED_BACK が 最後なら ★expected=None（clean vs HEAD）として 評価される
★★∴ ★『戻せた』を 記録すれば ★C の 異常は 解消できる。★取り消し記録は 要らない。
★★＝ append-only の 意味と 矛盾しない。
```

## 4. ★契約にしてほしいもの（★純関数 1本）

```
★判断が要るのは ★『この file は 未解消の ROLLBACK_FAILED を 抱えているか』の 1点。
★材料（★既に 記録に 在る）:
   ・その file に 関わる PATCH_APPLICATION の ★outcome の 並び（★順序つき）
     例: ['APPLIED'] ／ ['APPLIED','ROLLED_BACK'] ／ ['APPLIED','ROLLBACK_FAILED'] ／
         ['APPLIED','ROLLBACK_FAILED','ROLLED_BACK']
★返り（★形は DESIGN が 決める）:
   ・★未解消か（真偽）／ ★理由の 語
★★副作用 0（★ファイル・git・記録を 触らない）／ ★決定論。
★★名前・引数・返りは ★DESIGN が 決める。
```

## 5. ★DESIGN に判断してほしい点（★MGR は決めない）

```
★(あ) 未解消の file を ★`orphans_event_without_git` に 入れる
      ＋ ★既存欄・★balanced が 自動で False ／ ★proof の payload に 載る
      − ★欄の コメントは 逐語「event says APPLIED, ★disk doesn't match」＝★意味が 少し ずれる
        （★今回は ★disk は 一致している が ★戻せていない）
★(い) 新しい 欄を 1つ 足す（例: `unresolved_rollback_failures`）
      ＋ ★意味が 正確
      − ★`ReconResult` と proof payload の 形が 変わる（★★新台帳では ない）
★(う) 別の 形
★★どれを 採っても ★『balanced=False に なる』ことは ★満たしてほしい。
```

## 6. ★Hermetic の受入（★MGR が実走します）

```
★A APPLIED のみ                    → disk 一致 → ★BALANCED
★B APPLIED → ROLLED_BACK           → 復元 → ★BALANCED
★★C APPLIED → ROLLBACK_FAILED      → disk は 適用後の まま
     → ★BALANCED では ない ／ ★理由が 判定結果に 残る
     → ★門(3) が 拒否する 材料に なる（★`latest_balance_proof` が fresh=False）
★D（★MGR から 追加）C の 後に ★正常な ROLLED_BACK を append → ★BALANCED に 戻る
   （★★append-only で 解消できることの 実証）
```

## 7. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★空・None … outcome の 並びが 空 ／ 未知の 語が 混ざる
★順序    … APPLIED→FAILED→ROLLED_BACK（★解消）／ APPLIED→ROLLED_BACK→FAILED（★再び 未解消）
★複数    … 同じ file に FAILED が 2回 ／ 別の file と 混在
★大小    … file 1本 ／ 複数本
★決定論  … 同じ 入力で 同じ 出力
★★語を 作らない … ★'APPLIED' と 'ROLLED_BACK' の 意味を 変えない
```

## 8. ★MGR が先に言っておくこと（★隠さない）

```
★① 配線（`_fold_expected` / `reconcile` から 呼ぶ）は ★別途（★今夜 9回目の 型）。
★② `emit_reconciliation` / `latest_balance_proof` の 形は ★触らない 方が 影響が 小さい
   （★MGR の 観察・★決定ではない）。
★③ ★`_fold_expected` は ★file 単位で 畳む ∴ ★『どの file が 未解消か』が 自然な 粒度。
★④ connector 本線接続・delegated energize・実 repo 適用には ★進んでいない。
```

## 9. MGR がしていないこと

```
★判断ロジック 0行 ／ 実装 0 ／ 実 repo 書き込み 0 ／ 新台帳 0
★APPLIED / ROLLED_BACK / patch fingerprint / post_apply_sha256 / preimage / provenance の
  意味を 1つも 変えていない
★暴走 TASK TASK-2DER-32EDB6C4 は BLOCKED の まま 触っていない
```
