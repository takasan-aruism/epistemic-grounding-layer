# 宛: 設計 / 監査 ―― ③「G が Domain を選ぶ」実測と、完了監査の依頼

## 1. 着手前の実測（G→D 入口4つ）

| 問い | 実測 |
|---|---|
| 何を見て呼び先を決めているか | **何も見ていない**。`dw_state` を見るのは `tick` の巡回判断だけで、呼び先は `from twoder.domain_dw import ...` で**固定** |
| DW／経路表のどちらに属するか | DW 4（`contract_with_precheck` / `submit_next_contract` / `receive_finished` / `record_stages`）／ 経路表 1（`precheck_names`、G からは見えず `domain_dw` 内） |
| Domain が増えた時に G 修正が必要になる箇所 | **名指し import 4本すべて** |

機械で全列挙（`ast` + 正規表現）。手で数えた範囲を母数にしていない。

## 2. 入れた物（最小1本）

- **判定**: `twoder/get_domain.py` ―― **2DER が書いた**（`TASK-2DER-673B1D3E`、CREATED→COMPLETE、機械が置いて commit）。私は1行も書いていない。
- **配線**: `manager_v0.to_domain(operation, *a, **k)` と表 `DOMAIN_OPERATIONS` / `DOMAIN_MODULES`。`contract_with_precheck` **1本だけ**を名指しから委譲へ。
- 万能 router は作っていない（`to_domain` は 8行）。Domain 内部は書いていない。新しい業務責務は足していない。

## 3. 完了後の実測（Taka の3問）

| 問い | 実測 |
|---|---|
| ① G が名指しする Domain 呼び出し | **4 → 3** |
| ② 新 Domain 追加時に G 変更が必要か | **関数は 0行**。実際に Domain を1つ足して委譲が通ることを確認（表に2行）。既存 Domain は壊れず（同じ plan で骨格 578B 一致・verdict=GO） |
| ③ G の責務が近づいたか | **部分的**。「渡す」は表に移った。「全体を見る／統合／上申」は未着手 |

副次: どこにも属さない操作は `NO_DOMAIN` を語で返し、**呼ばない**。

## 4. 足場負債（隠さず出す）

1. `route_table` Domain の**実体が `domain_dw` の中に在る**。表の上でだけ独立している。
2. 残り3本（`submit_next_contract` / `receive_finished` / `record_stages`）は名指しのまま。Taka 指示の「最小1本」に従った。
3. `precheck_names` の名前検査は依然 `serves_segment` が空で**効いていない**（骨格の説明文に機械が明記）。

## 5. 監査への依頼

**「Domain Manager 設計は完了したか」を再判定してほしい。** 特に次の3点を疑ってほしい。

- **③は「近づいた」と言えるか**。名指し 4→3 は 1/4 であり、責務の移動ではなく1件の付け替えに過ぎない、という読みは成立するか。
- **`to_domain` は門として効いているか**。表に2つの Domain が在るが、実体は同じモジュールを指す。**選択が働いていることの証拠**は fake Domain の1件だけで足りるか。
- **完了条件そのもの**。②WorkUnit の completion / required_tests 文言（**まだ私の言葉**）を残したまま「設計完了」と呼べるか。

**私（MGR）の見立て**: ③は**未完**。②を先に閉じるべきだと考えるが、判定は監査に委ねる。
