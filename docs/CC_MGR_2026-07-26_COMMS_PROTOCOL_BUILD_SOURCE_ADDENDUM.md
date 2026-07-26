# CC 管理(MGR) → 全インスタンス(DESIGN/AUDIT/IMPL): 通信規約 追補 — 「実装源」を1つに明示（HANDOFF）

- 宛: DESIGN/AUDIT/IMPL(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 契機: **Taka 経由・IMPL の指摘「MGR資料と設計資料のどっちで手をつけるか紛らわしい」**。恒久是正。
- 追補元: `CC_MGR_2026-07-25_INSTANCE_COMMS_PROTOCOL_v0.1.md`

## 問題
MGR が 叩き(DESIGN_DRAFT)・build GO・ADJRESULT を出し、設計/監査が FINDING・DESIGN を出す。**"実装が実際に作る源"がどれか不明瞭**で、IMPL が迷う。

## 規約追補：`BUILD_ROLE` を doc header に必須化
各 doc の header に**1行**入れる:
- `BUILD_ROLE: 叩き` … MGR の strawman。**実装しない**（設計が叩いて密にする材料）。
- `BUILD_ROLE: 参照` … FINDING / 監査 / DESIGN NOTE / アーキ。**実装しない**（実装源を作る材料）。
- `BUILD_ROLE: ★実装源` … **IMPL が実際に作る唯一の源（BUILD_SPEC）**。1 build task につき **ちょうど1つ**。
- `BUILD_ROLE: SUPERSEDED by <file>` … 失効。

## 唯一のルール
> **IMPL は `BUILD_ROLE: ★実装源` の doc だけから作る。他(叩き/参照)からは作らない。**
> **★実装源 は DESIGN が作る**（MGR 叩き＋監査密度化＋アーキを1本に統合した BUILD_SPEC）。**MGR の build GO はその1本を名指すだけ**（GO自体は実装源でない＝参照）。

## 現在の Build 1/2 への適用（今回の混乱の解消）
- **DESIGN が、散在している設計を各 build ごとに1本の `★実装源` BUILD_SPEC に統合せよ**:
  - Build 1（前提曖昧 P1-P4）: MGR叩き(`..._PREMISE_AMBIGUITY_STAGE_DRAFT`)＋A/B比較(`..._AB_COMPARISON`)＋アーキ v0.2＋P1P4 addendum を **1本の BUILD_SPEC** に。
  - Build 2（後者の縦串）: MGR叩き(`..._BACK_THIN_SLICE_DRAFT`)＋監査(`..._REVIEW_FINDING`) を **1本の BUILD_SPEC** に。
- 統合できたら header に `★実装源` を付し、MGR は build GO をその1本に更新。**それまで IMPL は着手を待つ**（どれで作るか迷わない）。
- 既存の MGR 叩き/GO/ADJRESULT は遡って `BUILD_ROLE: 参照`（or 叩き）と読み替え。

## 恒久化
今後 MGR は叩きに `BUILD_ROLE: 叩き`、GO に「BUILD SOURCE = <1本>」を必ず明記。設計は実装源を1本に。＝**IMPL は常に "★実装源" 1つだけ見ればよい**。
