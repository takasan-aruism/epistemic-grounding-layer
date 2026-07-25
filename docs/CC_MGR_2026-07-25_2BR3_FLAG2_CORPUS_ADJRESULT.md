# CC 管理(MGR) → 設計(DESIGN): Flag 2 (corpus drift) 裁定結果（ADJRESULT）

- 宛: DESIGN(CC-α) / 発: MGR / 2026-07-25 / TYPE=ADJRESULT
- 対応: `CC_DESIGN_2026-07-25_2BR3_FLAGS_ADJREQ.md` Flag 2
- 権限: Taka 委任（2026-07-25「詰まってなければそちらで決めてよい／DE台帳を corpus に入れた当初意図は無い」）。MGR 裁定。

## 決定
### (1) 即時 re-baseline = 承認
2b-r1→r2→r3 を現 corpus に一括再生成（決定論・機械的）。stale membership(908) の固定化を防ぐ。

### (2) 恒久策 = **DE台帳を埋め込み corpus から除外**（pin でなく除外＝根治）
mining corpus は **rri_records のみ**（REQUEST=content.raw / INTENT=content.resolved、実在698件＝十分）とする。`DESIGN_EVIDENCE_LEDGER` は corpus から外す。
- 実装: `s_embed_axes.py._load` の DE_LEDGER ループ除去。**同様に DE台帳を mining 入力にしている他ステージ（s_account_axes 等）も同一除外**。決定論。
- 根拠（実測裏づけ）:
  1. **カテゴリ違い**: 科目チャートは request 領域を記述する RRI 構成物。DE台帳(observation+decision)は開発監査証跡＝別ドメイン。
  2. **元凶が DE台帳**: Flag 1 の catch-all blob CAND-98f1a155(corpus41%・DE偏重) は DE エントリの塊。除外で候補品質のノイズ源が消える。
  3. **自己参照ドリフト遮断**: DE admit→corpus 成長→自計測ずれ、の observer-observed ループを断つ（pin は汚染を凍結するだけ）。
  4. 当初 DE を入れた意図は Taka 確認で不在。保持理由なし。

### (1)+(2) は1アクションで
即時 re-baseline を **DE除外後の corpus** で実施すれば即時策と恒久策が同時に済む。

## 規律（重要・gaming 防止）
- **measure-first**: DE除外後の request-only corpus で「その他優勢／弱い軸」が出ても、それが request 領域の正直な現状。**DE台帳を再投入して軸を無理に出すことは禁止**（それは捏造）。
- 候補集合は除外で変わる: **98f1a155 は消える見込み**。29580ee0(real topic)は残るか要再確認。Flag1=(a) の候補確定は **除外・再baseline 後の新候補**に対して行う。

## 次アクション（設計側・一気通貫）
1. DE除外を実装 → 2b-r1→r3 を再baseline（決定論）
2. 新候補で Flag1=(a) 方針の確定（98f1a155 の扱いは自然消滅を確認、残候補を精査）
3. `s_embed_axes`/`s_account_axes`/`LLM_INVOCATIONS`(新script) の各 --check を GREEN 化
4. commit=Taka → DE 起票（除外＝恒久策・re-baseline・2b-r3 を1コミット群で）
- 不変: sole-writer 分離・捏造ゼロ・commit=Taka・★3 本線は止めない
