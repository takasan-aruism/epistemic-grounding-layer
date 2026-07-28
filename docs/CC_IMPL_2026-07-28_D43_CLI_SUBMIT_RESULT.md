# 実装 → 設計/監査: **本番の run を引けました。親子も1本に繋がっています**（受入①②③ 実データ）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v2.2）**
- 権限: `CC_MGR_2026-07-28_D43_BUILT_RECEIVED_ONE_CLI_SUBMIT_GRANTED.md` §2 / `CC_DESIGN_2026-07-28_D43_RELAY_CLI_SUBMIT_APPROVED.md`
- 事前記録: `CC_IMPL_2026-07-28_D43_CLI_SUBMIT_TEXT.md`（**文面を投入前に固定した文書**）

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸）
### 経路
- [x] **CLI で1回投入し、本番の `ETR-` id を得た**
### 実測
- [x] **受入① `GET /api/resolve?id=ETR-…` が run の event 列を返した**
- [x] **受入② `…-0001` が単一 event を返した**
- [x] **受入③ ★本番の親子が root から1本に繋がった**

---

## 1. 投入（★1回だけ・事前に文書化した文面のまま）
```
文面（CC_IMPL_2026-07-28_D43_CLI_SUBMIT_TEXT.md §1 と同一・1文字も変えていません）:
  宛: 設計/監査(CC-α)
  2DER の front door を CLI から通したとき、DS・RRI・EGL のどこまで記録が残るかを知りたい。
  記録に残っている事実だけで、追跡が途切れる箇所を挙げてください。

結果: exit=0
  ★ETRACE_RUN_ID  = ETR-75b58cfddf27
  RRI_REQUEST_TYPE = OBSERVE_CURRENT_STATE
  DW_TASK_ID       = None
  boundary_failures = 2件
```

### 1-1. ★1回目の実行は投入に至っていません（自己申告・回数に数えません）
```
最初の実行: python3 -m twoder.submit … → ★ModuleNotFoundError: No module named 'twoder'
原因: 直前に `cd /home/takasan/twoder` した作業ディレクトリが残っていた（私の誤り）
∴ submit の処理は1行も走っておらず、DS/RRI にも記録は増えていません。
∴ 許可された1回は消費していないと判断し、正しいディレクトリから1回だけ投入しました。
★本日3回目の cwd 由来の誤りです（Build 14 / Build 21 と同型）。
```

## 2. 受入①（実データ）
```
再現: GET /api/resolve?id=ETR-75b58cfddf27
resolved = True / count=3 / truncated=False / total=3

  ETR-75b58cfddf27-0001   SUBMIT  ENTRY       parent=None
  ETR-75b58cfddf27-0002   DS      UTTERANCE   parent=ETR-75b58cfddf27-0001
  ETR-75b58cfddf27-0003   RRI     mint        parent=ETR-75b58cfddf27-0002
```
**★台帳を直読していません。** **2DER に id を渡して聞いた結果です。**

## 3. 受入②（実データ）
```
再現: GET /api/resolve?id=ETR-75b58cfddf27-0001
resolved=True / event_id=ETR-75b58cfddf27-0001 / component=SUBMIT / function=ENTRY
```
**∴ `rid.count("-")` による run / event の分岐が本番で効いています。**

## 4. ★受入③ 本番の親子（D-42 から未確認だったもの）
```
root（parent_event_id が None）の数 = 1
root から親子を辿った長さ = 3 / 全 event = 3
★1本に繋がった。孤立した event は0件。
```
**∴ 「記録関数だけが親を決める」形が、本番のプロセスでも成立しています。**
**★繋げる修正はしていません**（繋がったので不要でした）。

## 5. 予想と実際（事前記録 §3）
| 項目 | 予想 | **実際** | 判定 |
|---|---|---|---|
| `ETRACE_RUN_ID` が印字されるか | される | **された（`ETR-75b58cfddf27`）** | 当たり |
| `/api/resolve` が event 列を返すか | 返す | **返した（3件）** | 当たり |
| **本番の親子** | **繋がる方に賭ける** | **★繋がった** | **当たり** |
| event の件数 | **予想しない**（未確認と書いた） | **3件** | — |
| `request_type` | 予想しない | `OBSERVE_CURRENT_STATE` | — |

## 6. ★事実として残すこと（判定はしません）
- **今回の run は `SUBMIT → DS → RRI` の3件で終わっています。** **`EGL` と `DW` の event はありません。**
- **理由は調べていません。** **`DW_TASK_ID` が `None`（DW へ行かない routing）であることは応答から分かりますが、EGL の合流点③（`admit_design_evidence`）を通らなかったのかどうかは、私は確認していません。**
- **∴ 「CLI 経路が最後まで追える」とは書きません。** **書けるのは「CLI 経路が DS と RRI まで、1本の親子で追えた」ことです。**

## 7. 守った条件（MGR §2）
1. **1回だけ投入しました**（§1-1 の未実行分は投入に至っていません）。
2. **投入前に文面を文書に書きました**（`ART-61e13b85cc`）。
3. **受入①②③は満たせたので、2回目を投入していません。**
4. **親子は繋がったため、繋げる修正はしていません**（繋がらなければ事実を書く用意でした）。
- **本番コードを1行も変更していません**（本文書の作業では）。**commit していません。**

---
*IMPL BUILT（D-43 CLI 投入）。MGR 許可の CLI 投入を1回だけ実施し、事前記録の文面をそのまま使用。★1回目の実行は `cd /home/takasan/twoder` の残りで `ModuleNotFoundError` になり submit が1行も走っていないため回数に数えず、正しいディレクトリから1回投入した（本日3回目の cwd 由来の誤り＝Build 14/21 と同型・自己申告）。**`ETRACE_RUN_ID = ETR-75b58cfddf27` を取得**し、`GET /api/resolve` で**受入①**（run の event 列 3件・`truncated=False`）、**受入②**（`…-0001` が単一 event・`rid.count("-")` の分岐が本番で有効）、**★受入③（本番の親子が root 1つから3件すべて1本に繋がり孤立0件）**をすべて実データで満たした。台帳は直読せず 2DER に id を渡して聞いている。予想は3項目とも当たり（件数と `request_type` は予想しないと事前に書いた）。★事実として=今回の run は `SUBMIT → DS → RRI` の3件で終わり **EGL と DW の event が無い**。理由は調べていないので「CLI 経路が最後まで追える」とは書かず、「DS と RRI まで1本の親子で追えた」とだけ書く。条件（1回だけ／事前に文面を書く／満たせたので2回目を投入しない／繋がったので繋げる修正をしない）をすべて守った。本番コード無変更・commit なし。*
