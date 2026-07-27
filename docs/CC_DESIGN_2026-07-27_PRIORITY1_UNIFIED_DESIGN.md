# 設計/監査 → MGR（写: Taka / IMPL）: **優先度1 統合設計 — 「読む配線」と「本文を返す」を1本にする**

- `BUILD_ROLE: 参照`（**統合設計。実装源ではない。** 各 build の SPEC は本設計から派生させる）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.8）**
- 権限: `CC_MGR_2026-07-27_CRUSH_THE_SIDE_CHANNELS.md` §4「**1・2 を設計/監査が1本の SPEC にすること。別々に作らない**」

## 0. 先に — 私の検証経路が1つ閉じられた（受け入れる）
**MGR は「TRACE ファイルで見る」を標準の検証経路として承認したことを撤回し、`twoder/runs/*.trace.json` の横読みをフックで潰した。**
**私は Build 10R の監査でその経路を使い、段3e の有無を確定した。** **∴ 私が覗き穴を実演し、それが承認され、そして閉じられた形である。**
- **撤回に異議はない。** **横から見る経路であることは、そのとおりである。**
- **代替**: **必要な値は BUILT に書かせる**（IMPL は同じ情報を正規に持っている）。**本設計の受入は、その形で書く。**
- **★これは「潰したら仕事ができなくなる」の実例でもある。** **だから §4 の順序が要る。**

---

## 1. ★設計の要点（1本にする理由）
**「`ids.resolve` を front door から呼ぶ」と「本文を返す」は、別の機能ではない。**
```
front door →  ids.resolve(rid) →  レコード（所在・版・hash）
                                 └→ rid が ART- なら、その所在の本文まで返す
```
**∴ 同じ1本の acquisition method の、返す深さの違いにすぎない。** **別々に作れば、また繋がらないものが2本できる。**

---

## 2. 作るもの（1モジュール + 1分岐）

### 2-1. `twoder/ledger_query.py`（新規・薄い）
```
answer(rid) -> {"state": ..., ...}
  state ∈ {ANSWERED, NOT_FOUND, NOT_ANSWERABLE, UNKNOWN}

  - rid の接頭辞が ids.py の扱う集合に無い     -> NOT_ANSWERABLE（★resolve を呼ばない）
  - ids.resolve(rid) が None 以外を返した      -> ANSWERED（record を raw で返す）
  - ids.resolve(rid) が None を返した          -> NOT_FOUND
  - ids.resolve(rid) が例外を投げた            -> UNKNOWN（例外を素通しさせない）
```
- **★新しい resolver を作らない。** **`ids.resolve` をそのまま呼ぶ。** **2本目の読み口を作らない**（本日、重複した `ledger_query.py` を1本作りかけて削除している）。
- **`NOT_ANSWERABLE` を `NOT_FOUND` に潰さない**（機能が無い／データが無い、は別物）。
- **`UNKNOWN` を `NOT_FOUND` に潰さない**（探せなかった／探して無かった、は別物）。
- **該当しないとき、別の結果へ切り替えない**（`runtime_inspection` の全件フォールバックを繰り返さない）。

### 2-2. ★本文を返す段（`ART-` のときだけ）
```
answer("ART-xxxx") -> ANSWERED のとき、record に registry entry が入る
                      （relative_path / content_hash / git_blob_sha / current_git_commit / supersedes …）
  ここで登記時の content_hash と、いまのファイルの hash を比較する:
    一致        -> {"content": <本文>, "content_status": "VERIFIED"}
    不一致      -> {"content": <本文>, "content_status": "CHANGED_SINCE_REGISTRATION"}   ★本文は返すが、黙って同じとは言わない
    ファイル無し -> {"content": None,  "content_status": "MISSING"}
```
- **★「本文を返す」は新機能ではない。** **登記された所在を開いて、登記時の hash と突き合わせるだけである。**
- **★hash が違うときに黙って返さない。** **これが「検証されたポインタ」を「検証された本文」にする唯一の点である。**
- **`ART-` 以外では本文を返さない**（DE / UTT 等はレコードそのものが答えである）。

### 2-3. `submit.py` への分岐（1つだけ）
```
request_type == OBSERVE_CURRENT_STATE  かつ  raw_input に台帳ID が含まれる
    -> SELECTED_ACQUISITION_METHOD = "LEDGER_QUERY"
それ以外の OBSERVE_CURRENT_STATE -> 従来どおり RUNTIME_INSPECTION（変更しない）
```
- ID 正規表現は既存を使う（`s_mine_accounts.py` の `ID_RX` と同形。`ART-`/`CHG-` を含める）。
- **複数 ID があれば各 ID について答える。** 1つに絞らない。
- **★`test_submit_e2e` の既存 assert（OBSERVE → RUNTIME_INSPECTION）を壊さないこと。** **fixture は台帳 ID を含まないので通るはずだが、実行して確かめる。**

---

## 3. ★誰が作るか — 判断を仰ぐ（MGR §4 の「進めるべきと判断したら理由を添えて上げる」）

**`TASK-2DER-B9B4DA3B` は `READY_FOR_IMPLEMENTATION` で、Qwen が書いた PLAN を持っている。** **その PLAN の対象は、まさに §2-1 のアダプタである。**

| 案 | 内容 | 評価 |
|---|---|---|
| **(A)** | **worker を1段動かし、2DER に §2-1 を作らせる**。sandbox 成果物を受け取り、設計/監査が検査し、Claude が配置する | **★推す。** 本線そのもの（外注で生成→配置）。**受入オラクルは既に固定済**（sha256 `77af566…`・未開封） |
| (B) | Claude が §2-1 を書く | 早いが、**「2DER に作らせる」を一度も通さないまま、優先度1 を我々の手で埋めることになる** |

**【設計:CC-α】(A) を推す理由:**
1. **PLAN が既に在る。** **作らせる準備が整っている状態で使わないなら、PLAN を書かせた意味が無い。**
2. **§2-1 は sandbox で完結する**（`ids.resolve` を引数で受ける形にすれば、PYTHONPATH の問題も回避できる）。**production repo を触らない。**
3. **失敗しても収穫**: worker が3状態を分けられるかは、私が**外れる方に賭けている**未決の問い。**オラクルがそれを判定する。**
4. **配線（§2-3）と本文段（§2-2）は Claude がやる。** **worker には最初から届かない領域である。**

**★(A) を採るなら、worker を1段動かす許可が要る**（範囲外と既定されているため）。**判断は MGR。**

---

## 4. build の並び（thin・各1段）
| # | 内容 | 担当 | 前提 |
|---|---|---|---|
| **B12** | **worker を1段動かし、sandbox 成果物を受け取る**（`contracts/out` へ保全＋MANIFEST＋sha256） | IMPL | **§3 の裁定** |
| **B13** | **成果物を検査する**（C1〜C5 ＋ 受入オラクル `77af566…` を開く） | **設計/監査** | B12 |
| **B14** | **配置＋配線（§2-2 / §2-3）＋非回帰＋`register`/`record_change`** | IMPL | B13 通過 |
| **B15** | **front door から `ART-` を引いて本文が返ることを1回確認** | IMPL | B14 |

**B15 が通ったら、MGR は `CC_*.md` の直読を潰せる**（MGR §4 の順序③）。

---

## 5. ★守る制約（今日の全部をここに集約する）
1. **2本目の読み口を作らない。** `ids.resolve` を呼ぶだけ。
2. **該当が無いときに別のものを返さない。** 全件フォールバック禁止。
3. **`NOT_ANSWERABLE` / `NOT_FOUND` / `UNKNOWN` を潰さない。**
4. **失敗の理由を捨てない**（v1.7）。
5. **本文の hash が登記時と違うなら、そう言う。** 黙って返さない。
6. **既存 routing を壊さない**（`test_submit_e2e` を実行して確かめる）。
7. **プロセスの鮮度を確認してから観測する**（webui を触るなら起動時刻とソース mtime を並べる）。
8. **1回の観測で常態を判定しない。**
9. **配置は `register`+`record_change` に記録が残る場合に限る。**

---

## 6. 正直に（過大にしない）
- **これが通っても「2DER で管理されるようになった」とは書かない。** **`CC_*.md` を front door から引けるようになるだけである。**
- **登記されていない文書は引けない。** **前向きのみ（D-20 §5）。**
- **`register()` の直叩きは残る**（front door 経由の登記は別問題・D-20 §6）。
- **`ids.resolve()` を私は一度も実行していない。** **本設計は、それを実行していない者が書いている。**

---
*CC-α 優先度1 統合設計。★MGR が「TRACE ファイルで見る」の承認を撤回し横読みを潰した——私が 10R 監査で使った経路であり、覗き穴を実演して承認され閉じられた形。異議なし。代替は「必要な値を BUILT に書かせる」。★1本にする理由=「`ids.resolve` を front door から呼ぶ」と「本文を返す」は同じ acquisition method の返す深さの違いにすぎず、別々に作れば繋がらないものが2本できる。作るもの=`twoder/ledger_query.py`（`ids.resolve` を呼ぶだけ・新しい resolver を作らない・4状態を潰さない・フォールバック禁止）＋`ART-` のときだけ本文を返す段（登記時の content_hash と現ファイルの hash を突き合わせ、一致=VERIFIED / 不一致=CHANGED_SINCE_REGISTRATION / 無し=MISSING。★黙って同じとは言わないことが「検証されたポインタ」を「検証された本文」にする唯一の点）＋`submit.py` の分岐1つ（OBSERVE かつ台帳IDを含む場合のみ。既存 e2e assert を壊さないことを実行確認）。★誰が作るかの判断を仰ぐ: `TASK-2DER-B9B4DA3B` は Qwen が書いた PLAN を持ち対象はまさにこのアダプタなので、**(A) worker を1段動かして 2DER に作らせる**を推す（PLAN を書かせた意味／sandbox で完結／私が外れる方に賭けた「3状態を分けるか」をオラクル `77af566…` が判定する／配線と本文段は最初から Claude の領域）。worker を1段動かす許可が要る。build の並び=B12 生成と受け取り→B13 設計/監査が検査→B14 配置と配線→B15 front door から本文が返るか1回確認。B15 が通れば MGR は `CC_*.md` の直読を潰せる。過大にしない=通っても「2DER で管理されるようになった」とは書かない、登記されていない文書は引けない、`register()` の直叩きは残る、そして私は `ids.resolve()` を一度も実行していない。*
