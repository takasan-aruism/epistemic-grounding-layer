# CC 管理(MGR) → 設計/監査(CC-α): slice1 ts 源 裁定（ADJRESULT）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=ADJRESULT
- 対応: `CC_DESIGN_2026-07-26_FRONTDOOR_SLICE1_TS_SOURCE_ADJREQ.md`
- 権限: MGR 裁定（既存不変量維持の設計整合判断）。cross-repo commit は commit=Taka。

## 前提評価
slice1 同値実証 = 良好（byte同値 4/4・hermetic 534→534・sole-writer=de_admission 不変・front-door provenance 生成 & ledger-row-neutral）。**設計が ts 実差異を検知し、committed submit を独断改修せず上程したのは正しい規律。**

## 判断① ts 源 = **(a) 採用**（optional ts 引数を submit に追加・pass-through）
- 理由: 本移行の**核＝ledger-row-neutral（台帳出力を変えない）**。(b) 固定 ts は `admitted_at` を実時刻→2026-07-11 に**後退させる実差異**＝移行の目的に反する。却下。
- (a) が正しい設計: **de_admission は既に `ts` を引数で受ける**(caller 提供)。submit も同型で **ts を受けて pass-through**すれば、submit の「no Date.now＝replay 決定論」を保ったまま（submit は時刻を"生成"せず"受領"）実時刻を維持できる。＝現行台帳の実時刻運用と整合。
- **submit 改修は最小・後方互換**（optional 引数・未指定時は既定のハードコード値＝既存 caller 無影響）。cross-repo（twoder repo）ゆえ **commit=Taka**（Taka に awareness: これが移行で 2DER コア=front door に初めて手を入れる点）。

## 判断② proof を先に commit（bundle しない）
- slice1 proof（`de_submit_route.py` + `s_de_route_equiv.py`・**挙動非変更の同値実証 tooling**）を**先に単独 commit=Taka**。
- 理由: proof は完了済・behavior-neutral＝**同値の記録として switch のタイミングに依らず独立に立つ**。ts修正+switch は submit 改修を含む別リスク＝**別コミット群**にする方が history がクリーン・review/revert 容易。
- 順序: ①proof commit → ②IMPL が submit に optional ts 追加 → ③再監査 → ④DE 記録ルーチンを `admit_via_submit` へ **switch**（switch も別 DE）。

## 不変（厳守）
- **直叩きは未閉塞のまま**（この段は enforcement しない・並行運用）。switch は「同値＋ts整合」を証明してから。
- byte同値・hermetic・sole-writer 分離・measure-first・★3 本線は止めない。

## 次アクション
proof commit（Taka）→ submit ts pass-through の小 handoff を IMPL へ → 再監査 → switch。切替可否の最終確認が要れば MGR 経由で最小 set を Taka へ。
