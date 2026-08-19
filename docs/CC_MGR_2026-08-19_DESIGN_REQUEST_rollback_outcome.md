# 宛: DESIGN（監査 CC）―― 契約作成の依頼: **rollback の結果を正しく表す純関数1つ**

**依頼元: MGR ／ 2026-08-19 ／ Taka 指示「(b) を扱う」**
**MGR は判断ロジックを書きません。実 repo へ書いていません。実装していません。**

---

## 1. ★閉じたい欠陥（★1つだけ）

```
`patch_bridge.apply_patch_bounded`（★285-290行・実物）:
    except Exception:
        try:
            _restore_preimage(workspace_dir, plan, energize)
        except Exception:
            ★pass   # rollback needs the same energization; if absent, apply never wrote, so nothing to undo
        emit_patch_application(..., ★'ROLLED_BACK', ...)   # ★★戻せていなくても そう 書く
        raise

★★∴ ★復元に 失敗しても ★記録は `ROLLED_BACK`（★＝嘘）。
★★かつ ★例外が 起きなくても ★『本当に 戻ったか』を ★誰も 確かめていない。
```

## 2. ★四問の確認結果（★すべて実物）

### ① 握り潰しの場所 → **`patch_bridge.py:287-288`**（上記）

### ② `outcome` に rollback 失敗を表す語が既に在るか → **★無い**

```
★使われている 語は ★2つだけ:
   `patch_bridge`      … 'APPLIED' / 'ROLLED_BACK'
   `bridge_reconciler` … 'APPLIED' / 'ROLLED_BACK'（★`_fold_expected` が この2語だけ 見る）
★★第3の 語は ★存在しない。
```

### ③ 既存の口で「復元不能」を記録できるか → **★できる（★3つとも既存）**

```
★`twoder/intervention.py::record_intervention(*, trigger, reason, ts, idempotency_key, detected_by,
     severity='INFO', action_class='OBSERVE', status='OPEN', ★rollback_ref=None, evidence_refs=None, …)`
   逐語「Append ONE intervention to the DS stream (sole writer = ds.phase0).
        ★Idempotent on idempotency_key」
   ★★`rollback_ref` という 欄が ★既に 在る。

★`twoder/escalation_router.py::route(failure_signal, classification, human_conditions, …)`
   `HUMAN_CONDITIONS` に ★★'IRREVERSIBLE_CHANGE' が ★既に 在る
   ＝★『戻せなかった＝不可逆に なった』を ★既存の 語で 表せる。

★`twoder/human_escalation_packet.py::build_packet(...)`
   `REQUIRED_FIELDS = (decision_point, options, recommended_option, uncertainty, default_if_undecided)`
   逐語「★STRUCTURALLY forbids "please look at everything" dumps」
```

### ④ 後続を進めない fail-closed が既に在るか → **★在る（★`raise`）**

```
`apply_patch_bounded` は ★記録の 直後に ★`raise` する ∴ ★呼び手へ 例外が 伝わる。
★`bridge_apply_connector` は ★try で 包んでいない ∴ ★そのまま 上へ 抜ける。
★★∴ ★『進めない』は ★既に 効いている。★壊れているのは ★記録の 語だけ。
```

## 3. ★契約にしてほしいもの（★純関数 1本）

```
★判断が要るのは ★『この rollback は 成功したのか』の 1点。
★材料（★すべて 既に 手元に 在る）:
   ・復元を 試みたか
   ・復元中に 例外が 起きたか（★型の 名前だけ・★文字列）
   ・★復元後の disk の sha256
   ・preimage の sha256 ／ existed（★`_RollbackPlan.entries[i]`）
★返り（★形は DESIGN が 決める）:
   ・★記録に 書くべき 語（★'ROLLED_BACK' か ★それ以外か）
   ・★理由の 語
   ・★人へ 上げるべきか（★真偽）
★★副作用 0（★ファイル・git・記録を 触らない）／ ★決定論。
★★名前・引数・返り・第3の語の 綴りは ★DESIGN が 決める。
```

## 4. ★DESIGN に判断してほしい点（★MGR は決めない）

```
★(あ) 第3の 語を ★`PATCH_APPLICATION` の outcome に 入れるか
      ＋ ★記録が 1本に まとまる ／ ★新台帳 0
      − ★`bridge_reconciler._fold_expected` は ★2語しか 見ない ∴ ★未知の 語は
        ★expected を 動かさない（★= その file は ★『event 無し』扱い → ★dirty なら
        ★`orphans_git_without_event` に 出る）★= ★安全側だが ★意味は DESIGN が 決めるべき
★(い) 第3の 語を 入れず ★`intervention` だけに 残すか
      ＋ ★`PATCH_APPLICATION` の 語彙を 汚さない
      − ★2つの 記録を 突き合わせないと 分からない
★(う) 両方（★`intervention` ＋ ★`escalation_router` の IRREVERSIBLE_CHANGE）
```

## 5. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★A 成功 … 例外なし ＋ disk == preimage → ★'ROLLED_BACK'／上申しない
★★B 失敗（例外）… 復元で 例外 → ★'ROLLED_BACK' で ★ない ／ 理由 ／ ★上申する
★★C 失敗（黙って ずれた）… 例外は 無いが ★disk != preimage → ★'ROLLED_BACK' で ★ない
★existed=False … 元々 無かった file（★戻す＝消す）→ ★disk が None なら 成功
★空・None    … preimage が 無い ／ disk が 取れない
★決定論      … 同じ 入力で 同じ 出力
★★語を 作らない … ★'APPLIED' を ★絶対に 返さない
```

## 6. ★Hermetic の受入（★MGR が実走します）

```
★A rollback 成功 → ROLLED_BACK ／ 元 bytes 復元 ／ reconciler ★BALANCED
★B rollback を 意図的に 失敗させる → ★ROLLED_BACK で ない ／ 理由が 記録される ／
   ★fail-closed（★例外が 上へ 抜ける）／ ★後続の 適用・確定 なし
★★B の 起こし方（★MGR の 案・★DESIGN が 変えてよい）:
   `_restore_preimage` は ★`_require_energize` を 通る ∴ ★energize を 渡さずに 呼べば ★必ず 失敗する
   （★★これは ★今 まさに `except: pass` が 想定している 場面＝★逐語「if absent, apply never wrote」）
   ★★但し その 逐語は ★『apply が 書く前に 落ちた 場合』を 指す ∴
     ★『apply が 書いた 後に 復元が 落ちる』場面と ★混ざっている ―― ★★そこが この欠陥の 芯。
```

## 7. ★MGR が先に言っておくこと（★隠さない）

```
★① 配線（★`apply_patch_bounded` の 285-290行を 部品の 返りで 書き換える）は ★別途。
   ★契約経路では 既存ファイルを 変えられない（★今夜 8回 出た 型）。
★② `intervention.record_intervention` は ★`ds.phase0` が 唯一の 書き手 ∴
   ★`patch_bridge` から 直接 呼べるかは ★未確認（★MGR は 走らせていない）。
★③ connector / delegated energize / 実 repo 適用には ★進んでいない（★Taka 指示どおり）。
```

## 8. MGR がしていないこと

```
★判断ロジック 0行 ／ 実装 0 ／ 実 repo 書き込み 0 ／ 新台帳 0
★preimage / fingerprint / allowed_files / provenance の 意味を 変えていない
★第3の 語を 私が 決めていない ／ (あ)(い)(う) を 選んでいない
```
