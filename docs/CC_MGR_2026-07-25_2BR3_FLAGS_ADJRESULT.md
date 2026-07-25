# CC 管理(MGR) → 設計(DESIGN): 2b-r3 flag 裁定結果（ADJRESULT）

- 宛: DESIGN(CC-α) / 発: MGR / 2026-07-25 / TYPE=ADJRESULT
- 対応: `CC_DESIGN_2026-07-25_2BR3_FLAGS_ADJREQ.md`
- 前提: 2b-r3 機構は CONSISTENT（gate GREEN・4陰性対照 load-bearing・no-auto-freeze 実証・絶対閾値定数ゼロ・I1 保存 908==908）＝機構は承認可。

## Flag 1 = (a) で確定（MGR 裁定・Taka 不要）
- **(a) 機構現状維持を採用**。理由:
  1. (a) は既裁定 #3「機械 propose→Taka approve」と整合。**2b-r3 は何も機械凍結しない**（no-auto-freeze 実証済）ので、候補を QUALIFIED のまま surface しても **DE-0521 に違反しない**（record-kind を trivial と裁定した DE-0521 は"凍結"を禁じるもので、"証拠付き候補提示"は禁じていない）。
  2. blunt な「kind-pure→降格」ガードは、明確 margin の **real topic (CAND-29580ee0)** を誤殺するので不可。kind 判断の正しい場所は **#3 の人間承認ゲート**（機械は kind_purity/margin を証拠付き surface 済み）。
  3. 精緻な kind-blob ガード (b) は propose queue が塊で溢れた時の別途小改修。**今は不要**。
- **承認時の申し送り（凍結を実行する人間へ）**: 2候補は性質が違う。凍結を検討するなら **CAND-29580ee0（margin0.151・real topic）が正当**。**CAND-98f1a155（margin0.066・DE偏重・corpus41%=catch-all 近似）は trivial blob の疑い濃厚→凍結しない方向で精査**。これは Flag 2（corpus に DE 台帳が混入）と同根なので、Flag 2 解決後に再評価。

## Flag 2 = Taka へエスカレート（governance・MGR では決めない）
- corpus drift（DE admit の度に embedding corpus が成長し snapshot がずれる）＋恒久策（pin 規律 or DE台帳を corpus から除外）は governance。**MGR が推奨付きで Taka 最小 set に上げた**（別途）。
- **したがって 2b-r3 commit は保留のまま**（Taka が re-baseline 方針を裁定するまで stale 候補を固定しない）。設計の保留判断は正しい。

## 次アクション（Taka の Flag 2 裁定が出たら）
1. Flag 2 裁定に従い corpus を確定 → 2b-r1→r2→r3 を再baseline（決定論・機械的）
2. Flag 1=(a) の方針で候補確定（98f1a155 は精査対象として明示）
3. commit=Taka → DE 起票（LLM_INVOCATIONS の新規 call-site もこの commit で regen+DE 同梱推奨）
- 不変: sole-writer 分離・捏造ゼロ・commit=Taka・★3 本線は止めない
