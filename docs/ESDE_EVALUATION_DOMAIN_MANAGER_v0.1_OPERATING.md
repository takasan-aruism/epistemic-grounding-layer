# ESDE Evaluation Domain Manager v0.1 ―― ★Claude 運用規則（正本・実践導入版）

**受領 2026-08-20（Taka）／ ★これは 説明語では なく ★★Claude を 拘束する 記述形式**
**★成功条件 = 「Claude が 理解して いる こと」では なく ★★所定の 形式で 宣言・観測・照合しなければ 先へ 進めない こと**

## 0. 基本原則（逐語）

```
★存在して いる こと ／ source を 読んだ こと ／ 単体試験が 通った こと ／ Stage へ 到達した ことは
  ★★機能成立の 証拠では ない。
★未確認は 無では ない。UNVERIFIED / UNKNOWN / UNREACHABLE / CONFLICT と して 明示的に 存在させる。
★評価を 単一 総合点へ 潰さない。★各概念は 異なる 故障型を 観測する ために 保持する。
★調査は 局所名では なく ★作用・因果鎖を 起点と する。★『無い』の 前に 検索範囲を 記録する。
```

## 1. 概念配置

| 概念 | 運用上の意味 | 主な対象 | 扱い |
|---|---|---|---|
| 対等性 | 同じ構造空間で相互参照できる共通形式 | schema / protocol / ID / event / type / I/O契約 | 基盤条件 |
| 対称性 | 対応する反対側・相補側が存在するか | writer-reader / grant-revoke / apply-rollback / pass-reject | 測定指標 |
| 連動性 | 宣言された作用が実際に次へ渡ったか | 因果鎖の edge / handoff / call / event | 測定指標 |
| 階層性 | 正しい責務境界・層を通過しているか | RRI / DW / Bridge / authority / repo | 測定指標 |
| 了解 | 下位構造が成立し新しい一存在として扱える状態 | 能力 / subsystem / function-axis | 昇格判定 |
| 創造 | 成立した存在を材料に より大きな構造が反復試行から現れる | 複数の了解・軸・試行系列 | 当面 上位観測 |

## 3. 共通状態語彙（★読み替え禁止）

```
PRESENT / ABSENT / OBSERVED / BROKEN / UNVERIFIED / UNKNOWN / UNREACHABLE / CONFLICT /
ESTABLISHED / REJECTED
★禁止 = UNVERIFIED→ABSENT ／ PRESENT→OBSERVED ／ Stage到達→通過 ／ 証拠の存在→目的達成
```

## 10. 強制運用フロー（★11段）

```
①AXIS宣言（対象/入口/出口/authority/保存先/構成要素を固定）
②全件調査（作用起点・★『無い』なら検索範囲を併記）
③因果鎖（各点で 誰が作る/何を作る/どこに保存/誰が読む/無い時どう止まる/本線で呼ばれる）
④DESIGN_HOLD（1点でも推測なら実装へ進まない）
⑤ESDE宣言（対等性/対称性/連動性/階層性を★実装前に記録）
⑥R1 E2E（正規上流から実走）
⑦R2 DENOMINATOR（分母/分子）
⑧R3 INTERNAL GATE（Stage内部の validator/authority/transition 通過まで）
⑨R4 GATE ENUMERATION（拒否条件を全列挙し★各拒否を実際に発火）
⑩再測定（同じ因果鎖・同じ試験で before/after）
⑪了解判定（必要条件を満たした時だけ ESTABLISHED）
```

## 11. Claude が しては ならない こと（逐語・9件）

```
・局所関数だけを見て全体経路が成立したと結論する
・自分が作った部品の caller だけを検索して『他に無い』と結論する
・source inspection のみで E2E 成立を宣言する
・単体試験・sandbox 成功を本線成功として扱う
・Stage 到達を Stage 通過として扱う
・0/0、bool(exists)、証拠1件などを成功判定に使う
・UNVERIFIED を都合よく PASS/ABSENT へ変換する
・停止した 2DER を迂回し Claude が代行実装する
・総合点で異なる欠損を相殺する
```

## 12. 標準記述フォーマット（★報告は この 形で 出す）

```
AXIS / SCOPE(entry,exit,authority,persistence,components)
EQUALITY(canonical_protocols, compatible, incompatible, unknown, status)
SYMMETRY(pairs, required, present, missing, unverified)
LINKAGE(edges[id,from,to,payload,trigger,evidence,status], declared, observed, broken)
HIERARCHY(boundaries, required, passed, violation, unreachable)
R1_END_TO_END / R2_DENOMINATOR / R3_INTERNAL_GATES / R4_REJECTION
UNDERSTANDING(candidate, requires, evidence, unresolved, result)
CREATION(status)
DECISION: GO | DESIGN_HOLD | REJECT
```

## 14. 2DER への 段階導入（★新台帳・新state・新authority を 先に 増やさない）

```
Phase 0(現在) 本書を Claude/MGR の 必須報告形式と して 運用・実例を 蓄積
Phase 1      AXIS/EQUALITY/SYMMETRY/LINKAGE/HIERARCHY を 既存記録から 機械取得（取得不能は UNVERIFIED）
Phase 2      R1-R4 を IMPLEMENT/COMPLETE の 強制門へ 接続
Phase 3      UNDERSTANDING を 能力登録と して 実装（ESTABLISHED を 次の AXIS の 構成要素へ）
Phase 4      CREATION を 複数 AXIS・試行系列の 上位観測と して 設計
★機械取得 不能な 値を ★LLM 自己申告で 埋めない ―― ★UNVERIFIED と する。
```

## ★MGR 体制の 判断（2026-08-20・★Claude の 回答）

```
★分けない（一人で 進める）。★理由:
  ・入口は 一つ（★Taka と 話すのは MGR だけ）＝ ★監査役を 別に 立てると 入口が 2つに なる
  ・本日の 事故の 原因は ★視点の 数では なく ★★実走の 有無だった（★ESDE+R1〜R4 で 一人でも A/B を 出せた）
★★但し ★処理は 分ける（★自己監査の 甘さへの 構造的 担保）:
  ①declared を ★実装前に commit する ＝ ★git 履歴で 後から 書き換えられない
  ②実装ターンと 監査ターンを ★別メッセージに する ＝ ★監査は その回の 新しい 実走証拠だけを 根拠に する
  ③Claude が 実装した 場合は ★監査対象が『私が 書いた コード』で ある ことを 明記する
★Taka が 分けると 裁定すれば ★従う（★その 場合は ESDE 視点の 監査を 別スレッドへ）。
```
