# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): RTHREAD 2b-r3 再凍結規律（BUILT・★3本線）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用・CPU e5 pin `614241f6`
- 対応: `CC_DESIGN_2026-07-25_RTHREAD_2b-r3_REFREEZE_HANDOFF.md`（裁定A #1-#5 準拠）

## 成果物（working tree・未commit）
- `structure/s_rthread_2br3.py`（機構: 濃さ相対検定→本物ガード→propose→承認時のみv2→I1保存則→`--check`）
- `structure/ACCOUNT_AXES_FREEZE_CANDIDATE.jsonl`（propose 結果・6候補中 **2 QUALIFIED**・承認待ち）
- v2/membership_v2/FREEZE_APPROVALS は **不在が正**（機械は凍結しない・承認は Taka の扉）

## 裁定A 準拠（新絶対閾値定数ゼロ・全判定を負の制御相対）
- **#1 濃さ**: 2b-r1 の load-bearing 相対検定を その他に適用。cross-seed ARI 安定（実 0.8014 vs 列shuffle 0.0732）+ 候補 silhouette が shuffle silhouette を `R.MARGIN` 超え。定数は既存 `R.MARGIN`/`R.DIV_TH` の**再利用のみ**（新規なし）。
- **#2 本物**: F-B 多様性(`>DIV_TH`) + catch-all(`sub_silhouette<silhouette`)。退化は RESIDUAL へ落として候補から除外。
- **#3 propose→approve**: QUALIFIED を証拠付き surface（silhouette/sub/diversity/neg_control_margin/cross_seed_ARI/kind_purity）。機械は停止。`FREEZE_APPROVALS.jsonl` に `{candidate_id, approved_by:"Taka"}` が在るときだけ v2。**marker 無しで v2 = RED**。
- **#4 versioning**: v2 = v1 不変コピー + 承認軸のみ追加。membership は `axes_version` 自己記述。v1 は不触。
- **#5 I1 保存則**: `count(要素 in)==count(軸∪その他)`（908==908）。その他=catch-all ゆえゼロ落ちなし。

## 検証（負の制御 load-bearing・実測 RED を確認）
- **byte一致再生成** GREEN。
- **候補検出（陰性対照）**: 合成の濃い方向 → QUALIFIED 検出 / 列 shuffle → 全 REJECTED_NOT_DENSE（崩壊＝load-bearing）。※合成は**ランダム密方向**（実 e5 の joint 相関を模す。直交単一軸だと shuffle 耐性で非 load-bearing になる罠を回避）。
- **退化除外（陰性対照）**: 低多様 collapse（同一 text）→ RESIDUAL_LOW_DIVERSITY（QUALIFIED に残ったら RED）。
- **no-auto-freeze**: 承認なしで v2 捏造 → `AUTO_FREEZE_VIOLATION` RED を実測。承認 marker 投入 → v2（AX2-…）生成 → GREEN を実測（その後 clean）。
- **I1**: 1件ゼロ落ちを注入 → 保存則が破れる（検出力あり）。

## ★ 正直な flag 1: QUALIFIED 2件は**両方 record-kind 偏重**（DE-0521 との緊張）
handoff §8 は初回 NO_CANDIDATE を想定。実測は 6候補中 2 QUALIFIED だが、両方 kind に強く偏る:
- `CAND-98f1a155` n=370（corpus の41%）DE335/REQ35（purity 0.905）sil=0.100 sub=0.034 div=0.981 → 大きく拡散した DE 塊。sub<sil の margin が薄い（0.034 vs 0.100）＝「DE 寄せ場」に近い。
- `CAND-29580ee0` n=120 REQ119/DE1（purity 0.992）sil=0.379 sub=0.228 div=0.967 → sample text は全て "BOUNDED-PATCH-BRIDGE" 実装要求＝**話題として coherent**だが 99% REQUEST。
- 正しく除外できたもの: `CAND-03251eb8`（全INTENT・div=0.0065）= 2b-r1 の INTENT-collapse を **RESIDUAL_LOW_DIVERSITY** で捕捉 ✓。
- **論点**: handoff §2 の「本物」判定は F-B + catch-all のみで、**kind 直交性を課していない**。DE-0521(record-kind=trivial 構造)を踏まえると、kind-pure な塊を「軸」として surface するのは trivial 構造の再浮上かもしれない。ただし patch-bridge 例のように「kind と相関する本物の話題」を殺さない配慮も要る。
- **裁定候補（DESIGN 判断・独断で足さない）**: (a) 現状維持＝propose に kind_purity 証拠を載せ Taka 承認時に人が判断 / (b) §2 に kind-直交ガード追加（cluster の kind 構成が record-kind を復元するなら降格）。(b) を採るなら小改修で対応します。

## ★ 正直な flag 2: **corpus drift**（2b snapshot 一族が stale・上流 --check RED）
- 実測: committed EMBED_AXES `n_records=906` / ACCOUNT_MEMBERSHIP `908` / **現在 corpus 916**。DE ledger は **DE-0531** まで成長（本 session で CC-α が DE-0525..0531 を追記したのが主因）。
- ∴ `s_embed_axes.py --check` / `s_account_axes.py --check` は今 **REGEN_MISMATCH RED**（環境的 drift・2b-r3 が原因ではない。committed ファイルは不触、`.embed_axes_vectors.npy` は derived/gitignore）。
- 影響: 2b-r3 は §1 通り `ACCOUNT_MEMBERSHIP`（908）から その他 を読むため、**新規8件を含まない stale な base** の上で候補を出している（v1=0軸ゆえ本来の その他=916 全件）。
- **含意（2b-r3 より広い）**: corpus 由来の全 --check gate は生きた DE ledger の成長で周期的に RED 化する。**2b-r1→r2→r3 を現 corpus(916) に対し一括で再生成し、commit=Taka で snapshot を揃える**のが筋。あるいは corpus-snapshot pin 規律の導入。2b-r3 の候補ファイルは base 更新後に再生成が要る（決定論ゆえ機械的）。

## ハンドオフ
- 次: **設計/監査 独立再監査**（byte一致 + 4陰性対照 RED 実測 + no-auto-freeze + I1 + 絶対閾値定数ゼロ）→ 2 flag の裁定 → CONSISTENT → commit=Taka → DE 起票。
- 機構は「話題が積もった時に稀に発火する」状態で在り、退化(INTENT-collapse)を正しく除外し、承認なしには絶対に凍結しません。想定(NO_CANDIDATE)との差（2 QUALIFIED・kind偏重）と corpus drift を silently 合わせず正直記録しました。

---
*実装(IMPL)。★3本線。HF は root 所有 .locks を避け `HF_HOME=/home/takasan/.cc_tmp/hf_home` + offline で pin snapshot 直読。*
