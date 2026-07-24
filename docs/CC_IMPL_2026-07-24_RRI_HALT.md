# 実装担当 → 設計担当: RRI_IMPL_SPEC v0.1 について halt（フロー矛盾＋成果物3未投下）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `RRI_IMPL_SPEC_v0.1.md`

## halt 理由（着手していない）

1. **フロー矛盾（要 Taka 裁定）**: 本 spec は line 6 / 182 で **実装者=Qwen（raw_input→submit）** と明記。これは ANCHOR §1-1（実装＝本 CC インスタンス／submit→Qwen は置換）と食い違う。**RRI が新フロー（実装インスタンス）か旧フロー（Qwen submit）か**が未確定。spec 自身の「矛盾規則: halt」に従い停止。
2. **成果物3 未投下**: 実装対象の骨格＋不変テスト（T14–18/25/36–40）が egl/docs に無い。現状は設計 spec（v0.1）のみ。spec も「骨格＋不変テストは成果物3で発注側が固定」と明記。実装可能な artifact がまだ無い。
3. 対象は別 repo `rri/rri/request_thread.py`（新規モジュール・repo dir 在り）。twoder ではない。

## 必要な確定
- (a) RRI の実装フロー裁定（実装インスタンス or Qwen）。
- (b) (a)=実装インスタンスなら 成果物3（骨格＋不変テスト）の投下。

## 待機
実装インスタンスは着手せず待機。(a)=実装インスタンス＋(b) 投下なら Monitor `b0718vzrg` が拾って新フローで実装する。(a)=Qwen なら RRI は本インスタンスの対象外。
