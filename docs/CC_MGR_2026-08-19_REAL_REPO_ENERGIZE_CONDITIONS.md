# 宛: Taka / 設計 / 監査 ―― 実 repo energize: **設計も実装も既に在る（呼び手 0）**

**実 repo へ書いていない。patch_bridge を本番 repo に当てていない。Claude はコードを書いていない。**

## 0. ★結論を先に

```
★★『実 repo energize は これから 設計する』では ない。
★★★Taka 2026-07-18 の 正本（§1-1 / §2-B / §3）に 沿って ★既に 実装されている。
   `twoder/bridge_minter.py`     … ★8,772 B ―― ★実 repo 用の 発行器（★呼び手 0）
   `twoder/bridge_reconciler.py` … ★10,797 B ―― ★残高証明（★呼び手 0）
   `twoder/patch_bridge.py`      … ★16,991 B ―― ★適用・rollback・記録（★今日 配線した）
★★登記簿の 記録（★文書）= 「DE-0438: ★first real-repo energization run (option A)」2026-07-19
   ＝★実 repo への energize は ★一度 走った 実績が 在る。
★★今夜 6回目の 型「口が 在る ≠ 繋がっている」。
```

## 1. ★問1 ―― 現在の門と、§3 / Taka gate の正確な条件

**`_mint_test_energize` の逐語（★試験用の発行器）:**

```
「TEST-ONLY energization minter (Taka 2026-07-18 §1-1) — the ONLY sanctioned _EnergizedApply source in
  this module. … a real repo — passed directly OR via a symlink under /tmp — resolves outside the temp
  root and is ★REFUSED (attack (g) blocked). … ★There is NO real-repo minter here;
  that is a ★§3 design + ★Taka gate.」
```

**★「ここには無い」＝ ★別ファイル（`bridge_minter.py`）に在る、という意味だった。**

**`bridge_minter.mint_real_energize(request, event_log, repo_dir, now_ts)` の逐語 ―― ★門は6つ:**

```
(1)  ★ENERGIZATION_ADJUDICATION の 記録が ★実在すること
     （★"existence-verification of a record, NOT a flag/config"）
(2)  ★authority == Taka … authority_owner=='TAKA' ★かつ granted_by=='TAKA'
     ★かつ 自己/モデル由来で ないこと（★self-energization は 拒否）
     ★残余リスクを 明記: 「OS-level Taka impersonation is NOT defeatable at this layer alone」
(2') ★裁定が ★同じ 中身に 束縛されていること
     （item_id / repo / base_commit / fingerprint / allowed_files）
     ★逐語「A different patch => no match => ★re-adjudication required.
            ★item_id alone can never energize」
(2'')★取り消されていない（ENERGIZATION_REVOCATION）★かつ 期限切れでない
(3)  ★reconciler が ★新しい 残高証明を 出すこと（`bridge_reconciler.latest_balance_proof`）
     ★かつ その証明が ★request の base_commit の もの
     ★逐語「None/imbalanced/stale => ★refuse」
(BIND-3) ★1回限り … token_id が ★既に PATCH_APPLICATION に 現れていないこと
     ★逐語「consumption is ★DERIVED from the SoR log, ★not a separate consumption ledger」
★どれか1つでも 欠ければ ★MintRefused（★fail-closed）
```

## 2. ★問2 ―― 既存の枠内で追加できるか → **★追加ではなく、既に在る**

```
★`_EnergizedApply` の 欄（★実測・★11個）:
   grant / token_id / item_id / task_id / trace_id / repo_identity /
   base_commit / allowed_files / fingerprint / expiry / adjudication_ref
★★Taka が 挙げた 束縛 8つは ★すべて この 欄に 在る:
   repo identity      → repo_identity          ★在る
   repo realpath      → grant（=realpath）      ★在る
   base commit        → base_commit            ★在る
   allowed_files      → allowed_files          ★在る
   artifact fingerprint → fingerprint           ★在る
   patch fingerprint  → 同上（★canonical diff の sha256）★在る
   有効期限 / 1回限り  → expiry ／ ★BIND-3 の token_id 消費（★SoR から 導出）★在る
   rollback 可能性     → `_RollbackPlan`（`capture_preimage`）★在る
```

### ★ただし「在る」と「効く」は別 ―― ★実測で分けた

| 欄 | どこで**強制**されるか | 状態 |
|---|---|---|
| `grant` | `_require_energize`（realpath 一致） | **★効く** |
| `repo_identity` | `apply_patch_bounded`（token と 引数の一致） | **★効く** |
| `fingerprint` | `_apply_to_working`（token 束縛 ＋ canonical 再計算） | **★効く** |
| `base_commit` | `_apply_to_working` | **★効く** |
| `allowed_files` | `_apply_to_working`（token）＋ `validate_artifact` | **★効く** |
| `expiry` | ★`_require_energize` は **見ていない** | **★発行時のみ**（`bridge_minter` 側） |
| `token_id`（1回限り） | ★`patch_bridge` は **見ていない** | **★発行時のみ**（BIND-3） |
| `item_id`/`task_id`/`trace_id`/`adjudication_ref` | ★`patch_bridge` は **見ていない** | **★記録用**（★発行時に束縛） |

**∴ ★適用側は「発行された token を信じる」設計。★門は ★すべて 発行側（`bridge_minter`）に在る。**

## 3. ★問3 ―― 接続点だけに限定できるか → **★できる（★二重に）**

```
① `allowed_files` … ★token に 束縛 ＋ ★`validate_artifact` が diff の a/ b/ 名を 照合
② `capture_provenance(target_repo_dir, allowed_files)` → `_Provenance(base_commit, allowed_files)`
   → `bridge_apply_connector` が ★`check_diff_within_allowed(validated.diff, provenance.allowed_files)`
★★repo 全体を 許可する 経路は ★無い（★`allowed_files` が 空なら `capture_provenance` が 例外）
```

## 4. ★問4 ―― 適用前の必須検査 → **★既に そうなっている（★1文字も 書かない）**

**`bridge_apply_connector` の実物（★これが Taka の言う「1本の道」）:**

```python
if not isinstance(energize_token, _EnergizedApply):
    return {'applied': False, 'blocked': 'NOT_ENERGIZED', …}      # ★token 無し=止まる
expected_fp = canonical_diff_artifact(...)['fingerprint']
validated  = validate_artifact(artifact, allowed_files, provenance.base_commit, expected_fp)
check_diff_within_allowed(validated.diff, provenance.allowed_files)
result = apply_patch_bounded(..., energize=..., expected_base=..., expected_fingerprint=...,
                             repo_identity=energize_token.repo_identity)
```

```
★`apply_patch_bounded` の 中で:
   capture_preimage → _apply_to_working（★失敗すれば 例外）→ 例外時は _restore_preimage
   → ★ROLLED_BACK を 記録 → ★raise
★★今日の 実測（★使い捨ての場）:
   当てられない diff → ★'apply: context_mismatch' → ★★1文字も 書かず → ROLLED_BACK
   preimage 不一致  → ★書かず → ROLLED_BACK → ★中身は 元のまま
★`dry_run_apply` も 在る（★ただし connector は ★呼んでいない＝★実測）
```

## 5. ★問5 ―― 適用後に test/audit が落ちたら rollback できるか → **★半分**

```
★できる部分 … `capture_preimage` が preimage を 保持し `_restore_preimage` が 戻す
              ★但し ★`apply_patch_bounded` の ★中の 失敗に対してだけ 自動で 走る
★★できない部分 … ★適用が 成功した 後に ★test / audit が 落ちた 場合の rollback は
              ★★`patch_bridge` の 外（★呼び手が 決める）＝★今は ★呼び手が 0 ∴ ★誰も 決めていない
★`_RollbackPlan` は 返り値に 出ない（`apply_patch_bounded` は plan を 内部で 使い 捨てる＝★実測）
   ＝★★後から 戻すには ★plan を 誰かが 保持する 必要が 在る（★★これが 不足の 1つ）
```

## 6. ★最終報告（★Taka 指定の5点）

### ① 正本上の現在の門

```
★6つ（§2-B）: 裁定記録の実在 ／ authority==Taka（自己発行 拒否）／ 同一中身への束縛 ／
              失効・取消でない ／ 新しい残高証明 ／ ★1回限り（token_id が未消費）
★どれか欠ければ MintRefused（fail-closed）
★残余リスクは 正本が 明記: 「OS-level Taka impersonation is NOT defeatable at this layer alone」
```

### ② 実 repo energize に必要な最小条件

```
★新しい 条件は ★1つも 要らない（★8つの 束縛は すべて 既存の 欄に 在る）
★要るのは ★★`bridge_minter.mint_real_energize` を ★呼ぶこと ＋ ★その入口を 誰かが 持つこと
```

### ③ 既存機能で再利用できるもの

```
★bridge_minter（発行・6門）／ bridge_reconciler（残高証明）／ patch_bridge（適用・rollback・記録）
★_EnergizedApply の 11欄 ／ _RollbackPlan ／ _Provenance ／ capture_provenance
★bridge_apply_connector（★Taka の「1本の道」が ★そのまま 実装されている）
★記録は ★PATCH_APPLICATION（★既存）／ ENERGIZATION_ADJUDICATION（★既存）
★★新しい 台帳は ★要らない（★消費は ★SoR から 導出＝逐語）
```

### ④ 新しく必要なもの

```
★(a) ★呼び手（★connector を 本線から 呼ぶ 場所）― ★今 0
★(b) ★適用後に test/audit が 落ちた 時の rollback ― ★`_RollbackPlan` を 保持する 口が 無い
★(c) ★`dry_run_apply` を connector が 呼んでいない（★Taka の 要求「適用前に dry-run」に 対して 不足）
★★(a)(b)(c) の どれも ★新しい 判断規則では なく ★接続と 保持の 話。
```

### ⑤ ★Taka が裁定すべき1点

```
★★『ENERGIZATION_ADJUDICATION を ★誰が どうやって 出すか』―― ★これだけ。

★理由: 門(1)(2)(2') は ★「Taka が 出した 裁定の 記録が 実在し、
       ★その裁定が ★この patch の 中身に 束縛されている」ことを 要求する。
★★∴ ★patch 1本ごとに ★Taka の 裁定が 要る 設計（★逐語「A different patch => ★re-adjudication required」）。
★★これは ★安全側だが ★『Taka がターミナルに 付き添わない』という 目標と ★正面から 当たる。
★★選択肢は ★Taka の 領域（★MGR は 決めない）:
     (あ) ★1 patch ＝ 1 裁定 の まま（★安全・★人手は 残る）
     (い) ★接続点（allowed_files）単位で ★事前に 裁定を 出しておく
          （★逐語の 束縛は item_id/repo/base_commit/fingerprint/allowed_files ∴
            ★fingerprint 束縛を どう 扱うかが 焦点）
     (う) ★別の 形
```

## 7. していないこと

```
★実装 0 ／ 実 repo へ 適用 0 ／ 実 repo energize を 発行していない
★bridge_minter / bridge_reconciler を ★走らせていない（★動くかは ★未確認）
★_MAP / authority / disposition 規則を 変更していない
★台帳を 直読していない（★フックが 1回 止めた ―― ★正しい 動作）
```
