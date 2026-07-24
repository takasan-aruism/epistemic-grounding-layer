# 実装担当 → 設計/監査担当: RTHREAD 2b-r2 axis-freeze（BUILT・結論 0 frozen / その他優勢）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-25
- 対応: `CC_DESIGN_2026-07-25_RTHREAD_2b-r2_AXIS_FREEZE_HANDOFF.md`
- repo=egl。CPU のみ・LLM/:8005/GPU 不使用・決定論。埋め込みは 2b-r1 の pin（e5 @ `614241f6`）を継承。

## 成果物（working tree・未commit）

- `egl/structure/s_account_axes.py`（catch-all 裁定＋凍結＋membership＋`--check`）
- `egl/structure/ACCOUNT_AXES_v1.json`（**n_frozen_axes=0**・per-axis 裁定記録）
- `egl/structure/ACCOUNT_MEMBERSHIP.jsonl`（908要素・全て その他/UNCLASSIFIED）

## 結論: `n_frozen_axes = 0`（その他優勢＝redesign plan §2 が明記した正当な初期状態）

§2 の catch-all 裁定（silhouette vs sub_silhouette、`sub >= sil → CATCH_ALL`）を全 TOPIC 軸に適用:

| 軸 | silhouette | sub_silhouette | margin(sub-sil) | verdict |
|---|---|---|---|---|
| 1 | 0.079 | 0.112 | +0.033 | CATCH_ALL |
| 2 | 0.021 | 0.119 | +0.098 | CATCH_ALL |
| 3 | 0.045 | 0.151 | +0.107 | CATCH_ALL |

- **全3軸が CATCH_ALL（内部で割れる方が他軸との分離より強い）→ 凍結対象 0。** 全908要素が その他。
- これは redesign plan §2(ii)「拡散・軸ほぼ無し → その他優勢 = 正当な初期状態（実運用で話題が積もると結晶、を後で=2b-r3）」に一致。**軸を捏造せず凍結しない。**

## 検証

- **負の制御 load-bearing**: 列 shuffle で mean silhouette 0.232 → **-0.004（≈chance）**に崩壊（崩れる＝計器が空振りでない）。
- **byte一致再生成**: `--check` GREEN（pin+cache、freeze 不変、drift 無し）。
- **membership**: 多重所属可・全軸閾値(cosine>=0.55)未満→その他 を実データで実証（現状 frozen=0 ゆえ全て その他）。**density は observed のみ・gate/branch/transition に一切入れない（T26・コード上 density は projection 出力だけ）**。

## ★ CC-α 想定との差（正直な報告・裁定を仰ぐ＝r1 と同規律）

- handoff §0 は「凍結候補=TOPIC 3軸、catch-all 裁定で 3 か 2」を想定。**実測は 0**（全 CATCH_ALL）。
- 原因（精査）: **r1 の安定性 ARI 0.885 は主に INTENT-collapse クラスタ（RESIDUAL 済）由来**で、実 TOPIC 軸の silhouette は 0.02–0.08 と低い（e5 の強い異方性）。低 silhouette 領域で sub≈sil のため、**軸1 の CATCH_ALL は margin +0.033＝境界で脆い**（軸2,3 は +0.10 で明確）。
- **裁定候補**: (a) この 0-frozen（その他優勢）を正当な初期状態として受容（plan §2(ii)・私の推奨＝measure-first に忠実）／(b) 異方性で silhouette 判別力が弱い点を踏まえ、catch-all 規則を separation の別指標（例: 中心角・whitening 後 silhouette）へ精緻化して再測定。**私は規則を勝手に緩めず handoff の `sub>=sil` を忠実実装**しました。

## ハンドオフ

- 次: **CC 独立再監査 → CONSISTENT → commit=Taka → DE 起票**（「意味埋め込みでも決定論 coherence 検定では凍結可能な軸は出ない＝その他優勢」＝ Taka モデルの measure-first 到達）。
- (b) の指標精緻化を望むなら別スライスで。現状は **その他優勢**で決着（過剰主張より正直な NO）。
