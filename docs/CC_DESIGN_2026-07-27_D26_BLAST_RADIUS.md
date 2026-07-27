# 設計/監査 → MGR（写: Taka / IMPL）: **D-26 — `approval_id` に nonce を足すのは小さい。token に運ばせる道は意図的に閉じている**

- `BUILD_ROLE: 参照`（事実のみ。設計判断は §3 に分けて書く）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-27_D25_RULING_NO_FIELD_ABUSE.md`

## 0. 裁定を受領
**`ts` に attempt を入れない。`conformance_probe` を書き換えない。** **どちらも本日の規律そのものであり、異議は無い。**

---

## 1. Q1 — `approval_id` の入力に attempt（nonce）を足す影響範囲【監査:CC-α】

```
再現: grep -rn "approval_id.*sha1\|sha1.*approval" --include=*.py twoder/
  twoder/authority.py:133 のみ    ← ★approval_id を計算するのはここ1箇所
再現: grep -n "def _load_grant" -A 8 twoder/approval_registry.py
  台帳を走査し approval_id の一致で GRANT を探す（★再計算して照合していない）
```
| 観点 | 事実 |
|---|---|
| **計算箇所** | **`authority.py:133` の1箇所だけ** |
| **検証が再計算するか** | **しない。** id で台帳を引き、保存済みの値と比べるだけ |
| **既存 GRANT 記録への影響** | **★無い。** 式を変えても、既に台帳に在る id はそのまま引ける |
| **呼び出し元** | **7箇所**（本番2 = `counterfactual_runner:54` / `command_surface:58`、テスト5） |
| **既定 `None` の optional 引数にした場合** | **★既存呼び出しは1つも変わらない**（`None` なら現行と同じ id） |

> **∴ Q1 は小さい。** **後方互換の optional 引数1つで足りる。**

## 2. Q2 — token 自体が attempt を運べるか【監査:CC-α】
```
再現: grep -n "def validate_by_token" -A 5 / "def _extract_approval_id" twoder/approval_registry.py
  「dict の中身は照合に使わない。approval_id が取れなければ拒否」
  「dict は approval_id フィールドのみ(中身の action_type 等は真正性に使わない=族C)」
```
**∴ 検証側は token から `approval_id` 文字列しか取らない。** **中身を読まないのは意図的な設計である**（自己申告の排除＝族C）。
> **∴ token に attempt を持たせても検証側は読まない。** **∴ この道は原理的に閉じている。** **開けるべきでもない。**

---

## 3. ★設計判断（事実と分けて書く）
**Q1 が小さく、Q2 が閉じている以上、選べるのは1つである。**

> **`authority.grant_approval` に `nonce=None` を足し、与えられた時だけ `approval_id` の hash 入力に含める。**
> **`mint_token` は `nonce=attempt` を渡し、`task_id` は素のまま、語彙は `LIVE_WORKER_MINIMAL` / `LIVE_WORKER_TASK` にする。**

**3つの制約がすべて立つ:**
| 制約 | 満たし方 |
|---|---|
| **C1** 検証は素の `task_id` | **満たす**（suffix を付けない） |
| **C2** 同一 `ts` で attempt だけ変えて id が異なる | **満たす**（nonce が hash に入る） |
| **C3** `approval_id` は4項目のみ | **★1項目増やす。** これが本件の本体である |

**★`ts` を汚さない。`conformance_probe` を書き換えない。既存の呼び出しも記録も壊さない。**

### 3-1. 正直に（過大にしない）
- **これは「4項目では足りなかった」という設計の訂正である。** **`approval_id` は「誰が・何を・いつ」だけで一意にできる、という前提が誤っていた。** **再試行という軸が抜けていた。**
- **`authority.py` を触る。** **MGR の当初の裁定（mint の1箇所だけ）を超える。** **∴ 裁定が要る。**
- **【未確認】** `authority.py` の他の利用者（`egl` / `dev-workcell` 側）を私は網羅していない。**上の7箇所は `grant_approval(` の grep 結果であり、間接呼び出しは追っていない。**

---

## 4. 「止まってよい」について（MGR §4）
**MGR は「1・2 のどちらも小さくないなら止まってよい」とした。**
**∴ 止まる条件には当たらない。** **Q1 は小さい。**
**∴ 私は「止まる」を選ばない。** **ただし `authority.py` を触る裁定は MGR が出すものであり、私は待つ。**

**★もし MGR が「範囲を広げない」を維持するなら、そのときは §4 の条件が成立する。**
**その場合の Gap 登録文（用意しておく）:**
> **`G-16` 追記: 「`approval_id` の入力が4項目（task_id / operation_class / action_type / ts）しかなく、再試行の軸が無い。∴ 素の `task_id` で検証しつつ attempt 単位で一意にすることが、`authority.py` を触らずには成立しない。最小修理では解けない。」**

---
*CC-α D-26。裁定（`ts` に attempt を入れない・probe を書き換えない）を受領、異議なし。★Q1=`approval_id` を計算するのは `authority.py:133` の1箇所だけで、検証は id で台帳を引くだけで再計算しない ∴ 式を変えても既存 GRANT 記録は無効化されない。呼び出し元は7箇所（本番2/テスト5）で、既定 `None` の optional 引数にすれば既存呼び出しは1つも変わらない ∴ **小さい**。★Q2=検証側は token から `approval_id` 文字列しか取らず、中身を読まないのは意図的な設計（自己申告の排除=族C）∴ token に attempt を運ばせる道は原理的に閉じており、開けるべきでもない。★設計判断=`grant_approval` に `nonce=None` を足し、与えられた時だけ hash 入力に含める。`mint_token` は `nonce=attempt` を渡し `task_id` は素・語彙は LIVE_WORKER_MINIMAL/LIVE_WORKER_TASK。これで C1/C2/C3 がすべて立ち、`ts` を汚さず probe も書き換えず既存も壊さない。正直に=これは「4項目では足りなかった」という設計の訂正であり、再試行という軸が抜けていた。`authority.py` を触るので MGR の当初裁定を超え、裁定が要る。【未確認】間接呼び出しは追っていない。★「止まってよい」の条件には当たらない（Q1 が小さい）が、MGR が範囲を広げないと決めるなら G-16 追記文を用意した。*
