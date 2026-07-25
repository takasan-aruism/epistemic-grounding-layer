# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): DE除外 + 2b 再baseline（BUILT・★3本線）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用・CPU e5 pin `614241f6`
- 対応: `CC_DESIGN_2026-07-25_CORPUS_DE_EXCLUSION_REBASELINE_HANDOFF.md`（Flag2 裁定=DE除外＝根治）

## 成果物（working tree・未commit）
- `structure/s_embed_axes.py` / `structure/s_mine_accounts.py`: `DESIGN_EVIDENCE_LEDGER` ループ + `DE_LEDGER` 定数を除去。**corpus=rri_records のみ**。他不触。
- 再baseline: `EMBED_AXES_*`（2b-r1）/ `ACCOUNT_AXES_v1`+`ACCOUNT_MEMBERSHIP`（2b-r2）/ `ACCOUNT_AXES_FREEZE_CANDIDATE`（2b-r3）/ `MINING_*`（s_mine_accounts）/ `LLM_INVOCATIONS`（新script登録）/ `TASK_CONTRACTS`+`READ_PATHS`（actually_loaded 追随）。

## 検証（全 gate GREEN + 決定論）
`s_embed_axes` / `s_account_axes` / `s_rthread_2br3` / `s_task_contract` / `s_exec_arch_acd` / `s_llm_invocations` / `s_mine_accounts` の `--check` **全て GREEN（byte一致）**。絶対閾値定数ゼロ・no-auto-freeze・I1 保存 不変。

## corpus 変化（実測）
- 埋め込み corpus（content-text）: 906/916 → **388**（REQUEST 212 + INTENT 176、非空 content のみ）。※handoff の「698」は rri_records 全行数で、s_mine_accounts の ref-feature 側は 698 のまま（content 非依存）。
- DE台帳（520系）は corpus から消滅。コードで `RRI_RECORDS` のみ参照を確認可。

## 予測との一致（handoff §4）
- **`CAND-98f1a155`（DEブロブ・corpus41%）= 予測どおり自然消滅** ✓（DE record ゼロ）。
- **patch-bridge REQUEST topic（旧 29580ee0, sil~0.38）= 残存**。ただし今回は 2b-r2 が **frozen**（`AX-72ead44e` n=119, sil=0.392, sub=0.232, purity=1.00, div=0.966）。member 集合が 120→119 に変わり hash 変化。
- 2b-r1 新候補=4軸（n=4/47/65/119）。INTENT-collapse 退化除外は不変。

## ★ 正直な flag（primary・silently 受けない）: 2b-r2 membership が退化 → 2b-r3 NO_CANDIDATE は **vacuous**
- 2b-r2 は patch-bridge topic（sil=0.392）を frozen＝MGR が real topic と認めた 29580ee0 と同一方向ゆえ freeze 自体は defensible。
- **しかし membership が退化**: frozen 軸への density は **全388件が 0.811〜0.984**（median 0.869）。`MEMB_TH=0.55`（絶対 cosine 閾値）は e5 anisotropy の下限（~0.81）を大きく下回るため **全388件が this 1軸に所属 → その他=0**。
- 帰結: **2b-r3 は その他=0 で NO_CANDIDATE**。これは「DE除外後の request 領域が その他優勢」という **measure-first の正直な結果ではなく**、membership 閾値の退化による **vacuous な NO_CANDIDATE**（INTENT 176 や他 REQUEST クラスタが patch-bridge 軸に誤所属）。genuine「弱い構造」と見分けがつかない状態で 2b-r3 を評価できない。
- **根因**: `MEMB_TH=0.55` は裁定Aが禁じた「幻覚的絶対閾値定数」の類型。anisotropy 下で density の絶対 cosine は無意味（全ベクトルが狭い cone に居る）。freeze-0 時代は軸が無く MEMB_TH が発火しなかったので**潜在していた退化が re-baseline で顕在化**した。
- **裁定候補（DESIGN/MGR 判断・独断で s_account_axes を改修しない＝handoff「他は触らない」遵守）**:
  - (a) membership を **相対化**（負の制御 shuffle 方向への density を null とし、real−null margin で所属判定 / または軸間の相対 margin=最近軸のみ+差 / percentile）。「絶対閾値ゼロ」規律と整合。
  - (b) それまで 2b-r3 の NO_CANDIDATE は **UNEVALUABLE（vacuous）** として扱い、commit で「その他優勢」と結論づけない。
- ※measure-first 厳守で DE 再投入は一切していません。これは membership 層の欠陥であって corpus の問題ではありません。

## ★ flag 2（軽・handoff §6 の想定どおり）: C-gate が drift を検出
- DE 除外で s_embed_axes/s_mine_accounts は `DESIGN_EVIDENCE_LEDGER` を読まなくなったが、CC-α authored の `REQUIRED_INPUTS` には残るため C が `DESIGN_EVIDENCE_LEDGER.jsonl -> MISSING`（rri_records→OK）を出す。**これは C-gate が実読 drift を捕捉した good example**（handoff §6 明記）。設計側で REQUIRED_INPUTS から DE台帳を除去してください（除去で C が MISSING から消える）。`s_task_contract --check` は MISSING を含んでも byte一致ゆえ GREEN。

## ハンドオフ
- 次: **設計/監査 独立再監査**（3 --check byte一致 GREEN / DE非参照をコードで確認 / 98f1a155消滅 / 退化除外不変 / 絶対閾値定数ゼロ）。
- **membership 退化 flag の裁定**（(a) 相対化を別 handoff で私が実装 / (b) 2b-r3 NO_CANDIDATE を UNEVALUABLE 扱い）。
- §6: 設計が REQUIRED_INPUTS から DE台帳除去 → commit=Taka（DE除外+再baseline+2b-r3+contract+LLM_INVOCATIONS を1コミット群）→ DE 起票。
- 想定（NO_CANDIDATE 予測）と実測（frozen 1軸 + membership 退化で vacuous NO_CANDIDATE）のズレを silently 合わせず記録しました。

---
*実装(IMPL)。★3本線。measure-first 厳守＝DE再投入禁止。退化した GREEN を「正直な現状」と偽らず flag。*
