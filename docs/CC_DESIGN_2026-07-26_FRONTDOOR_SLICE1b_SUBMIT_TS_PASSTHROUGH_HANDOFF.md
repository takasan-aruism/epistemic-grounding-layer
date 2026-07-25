# 設計/監査 → 実装: submit に optional ts pass-through（front-door slice1b）HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / repo=**twoder**(+egl 参照) / 決定論
- 正本: `CC_MGR_2026-07-26_FRONTDOOR_SLICE1_TS_SOURCE_ADJRESULT.md`（ts=(a) 採用）+ DE-0538（同値実証）+ 本 handoff
- **注意**: これは **2DER コア `twoder/submit.py`（front door）に初めて手を入れる**変更。最小・後方互換・cross-repo。**commit=Taka**（Taka awareness 事項）。

## 0. 規律
- 最小・**後方互換**（optional 引数・未指定時は既存挙動＝ハードコード ts）。submit の「no Date.now＝replay 決定論」は **submit が時刻を"生成"せず"受領"する**ことで保つ（MGR 裁定の要旨）。
- ledger-row-neutral の核を維持：submit 経由でも実 ts を渡せば直叩きと byte 同値。sole-writer=egl.de_admission 不変。★3 本線は止めない。

## 1. 依頼（最小）
1. `twoder/submit.py`:
   - `submit(raw_input, conversation_id="taka-main", seed=0, admission_payload=None, ledger_path=None, formal_candidates=None, **ts=None**)` に optional `ts` を追加。
   - 本体先頭の `ts = "2026-07-11T08:00:00"`（submit.py:88）を **`ts = ts or "2026-07-11T08:00:00"`** に（未指定時は既定＝既存 caller 無影響）。
   - この `ts` は既に DE-admission fast path が `admit_design_evidence(admission_payload, ts=ts, ledger_path=...)` に渡している（下流不変）。DS thread event 等も同じ `ts` を使う（front door の時刻整合）。
2. `egl/structure/de_submit_route.py`:
   - `admit_via_submit(candidate, ts=None, ledger_path=None)` が **`ts` を submit へ実注入**（現状 API 対称性で受けるだけ→実配線）。ts 未指定時は candidate 側の運用に合わせ**実時刻を生成して渡す**（呼び手が実時刻を与える＝de_admission 直叩きと同じ実時刻源）。

## 2. 同値ハーネス更新（実 ts で byte 同値）
- `s_de_route_equiv.py`: 従来の「同一 ts を明示注入して比較」に加え、**実時刻 ts を submit に渡した時も直叩き(同 ts)と ledger 行 byte 同値**を確認。ts 未指定時に submit が既定ハードコード値へ fallback することも確認（後方互換）。

## 3. 受入（設計が独立再検証）
- `s_de_route_equiv.py --check` GREEN：実 ts 注入で submit 経由 == 直叩き（byte 同値）。ts 未指定 submit が既定値で従来動作。
- **後方互換**: ts を渡さない既存 submit caller（通常の問い合わせ経路）の挙動・trace が不変（既定 ts）。
- sole-writer=egl.de_admission 不変・実 ledger 不汚染（hermetic）・全 gate GREEN。
- twoder repo の diff が submit.py の最小 optional 引数追加に限定（scope creep なし）。

## 4. 完了後 / switch
- `CC_IMPL_2026-07-26_FRONTDOOR_SLICE1b_SUBMIT_TS_PASSTHROUGH_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → **commit=Taka（twoder + egl 両 repo・各 push）** → DE。
- その後 **slice1c=switch**: DE 記録ルーチンを `admit_via_submit`（実 ts）へ切替（別 DE）。**直叩き閉塞はさらに後の別スライス**（MGR/Taka）。
- 想定と実測がズレたら silently 合わせず記録。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。2DERコア front doorへの最小・後方互換変更・ts は受領のみ(生成でない)・cross-repo commit=Taka。★3 本線・止めない。*
