# 宛: Taka ―― 判定 **B: 委任という概念だけが不足**（材料は全部在る・実装 0）

**実装していない。実 repo へ書いていない。`bridge_minter` を走らせていない。**

## 0. 判定

```
★★B. 委任という 概念だけ 不足している。
★材料（★scope つき・★期限つき・★1回限りの Taka 承認トークン）は ★既に 在り 動いている。
★★足りないのは ★『Taka が 委任した 相手が 出した 裁定』を ★受け取る 分岐 1つだけ。
★★ただし ★A では ない ―― ★`bridge_minter` は ★委任を 一切 見ない（★下記 §1）。
★★C でも ない ―― ★正本が 禁じているのは ★「patch ごとの Taka」では なく
   ★★「機械が 自分で 自分を energize すること」（★下記 §5）。
```

## 1. ★問1 ―― `granted_by == TAKA` はどこまで必須か

**`bridge_minter.py:92-100` の実物（★3つとも ★裁定記録の欄を 直接 見る）:**

```python
if str(ap.get('authority_owner','')).upper() != 'TAKA': raise MintRefused('authority_owner != TAKA')
if str(ap.get('granted_by','')).upper()     != 'TAKA': raise MintRefused('granted_by != TAKA')
attribution = str(ap.get('attribution','')).upper()
if attribution != 'TAKA':                              # ★FAIL-CLOSED ALLOWLIST (JREV-0010)
    raise MintRefused('attribution must be TAKA (present + allow-listed), got %r' % ...)
if attribution in _FORBIDDEN_ATTRIB:                   # ★defence in depth
    raise MintRefused('self-/model-attributed adjudication refused: %r' % ...)

_FORBIDDEN_ATTRIB = frozenset({'SELF','LLM','CLAUDE','AGENT','AUTO','MODEL', …})
```

```
★★『TAKA 以外は すべて 拒否』の ★許可名簿方式（★1語だけ 通す）。
★★∴ ★2DER が 出した 裁定は ★attribution が 'TAKA' でない 限り ★構造的に 通らない。
★★委任を 見る 欄・分岐は ★1つも 無い（★`approval_id` も `delegat` も 参照していない）。
```

## 2. ★問2 ―― authority に事前委任の仕組みが在るか → **★在る**

**`twoder/authority.py` の実物:**

```python
grant_approval(action_type, task_id, operation_class, approved_by, ts, approved_scope, expiry, nonce)
   逐語「Mint a ★SINGLE-USE, task+operation-scoped approval token — ★NOT a reusable bare boolean.
         Bound to a specific task_id + operation_class with an approval_id;
         ★consumable exactly once (durably, via the DS event stream).」
validate_approval(token, action_type, task_id, operation_class, ts)
   逐語「Reject a ★bare boolean / mismatched / expired / already-consumed token.」
   実装が 見る もの: action_type 一致 ／ ★task_id 一致 ／
        ★operation_class が token の operation_class か ★approved_scope の 中 ／
        ★expiry 超過でない ／ ★single_use なら 未消費
consume_approval(token, ts) … 「Burn a single-use token by recording a CONSUMED event」
```

**★これは まさに「Taka が 事前に 範囲と 期限を 決めて 委任し、機械が 1回だけ 使う」形。**
**★しかも ★DS の event stream に 消費が 残る（★別台帳を 作っていない）。**

## 3. ★問3 ―― repo_identity / allowed_files / ceiling / expiry に束縛できるか

| 束縛 | 既存で持てるか |
|---|---|
| `expiry` | **★在る**（`grant_approval` の引数・`validate_approval` が検査） |
| 範囲 | **★在る**（`approved_scope`・`operation_class`） |
| authority ceiling | **★在る**（`item_ceiling(item_id)` / `gate_for_item`） |
| `repo_identity` / `allowed_files` | **★欄としては 無い** ―― ★但し `approved_scope` は ★自由な一覧 ∴ ★入れられる |
| 単一使用 | **★在る**（`single_use` ＋ `approval_consumed`） |

**★∴ ★新しい 欄を 作らずに 束縛できる（★`approved_scope` に 何を 入れるかは ★設計の 判断）。**

## 4. ★問4 ―― 委任範囲内で 2DER が adjudication を出しても6門を保てるか

```
★保てる 門（★5つ）:
 (1)  記録の実在      … ★2DER が 書いても 記録は 実在する（★形は 同じ）
 (2') 同一中身への束縛 … ★fingerprint / repo / base_commit / allowed_files を そのまま 入れる
                        ★実装は `ap.get('allowed_files') != request['allowed_files']` 等で 突き合わせる
 (2'')取消・失効       … ★ENERGIZATION_REVOCATION は 発行者を 問わない
 (3)  新しい残高証明   … ★`bridge_reconciler` は 発行者を 問わない
 (BIND-3) 1回限り     … ★token_id の 消費は ★SoR から 導出 ∴ 発行者を 問わない

★★保てない 門（★1つ）:
 (2)  authority == Taka … ★attribution が 'TAKA' 以外なら ★必ず 拒否
      ＝★★ここだけが ★委任を 受け付けない
```

**★∴ 6門のうち ★5門は そのまま。★変えるべきは ★門(2) の1つだけ。**

## 5. ★問5 ―― rollback を自動経路の必須条件にできるか → **★半分**

```
★できる … `capture_preimage` / `_restore_preimage` は 既に 在り、★適用中の 失敗では 自動で 走る
          （★今日 使い捨ての場で 実測: preimage 不一致・文脈不一致 とも ROLLED_BACK ＋ 復元）
★★できない … ★適用が 成功した 後に ★test / audit が 落ちた 場合:
          ★`apply_patch_bounded` は `_RollbackPlan` を ★返さない（★内部で 使い捨て）
          ∴ ★後から 戻すには ★plan を 誰かが 保持する 必要が 在る（★★不足の1つ・既報）
★∴ 「必須条件にできるか」= ★★『plan を 返す/保持する』1点が 埋まれば できる。
```

## 6. ★最終報告（★Taka 指定の2点だけ）

### ① ★毎 patch で Taka が必要な理由

```
★★理由は ★2つ。★どちらも 正本の 逐語。

★理由A（★論理的に 不可避）―― ★fingerprint 束縛
   逐語「the adjudication binds the SAME per-patch content as the request
         (item_id/repo/base_commit/★fingerprint/allowed_files).
         ★A different patch => no match => ★re-adjudication required.
         ★item_id alone can never energize」
   ★fingerprint は ★patch が 出来て 初めて 決まる
   ∴ ★★『patch を 見る前に その patch の 裁定を 出す』ことは ★原理的に できない。
   ★★＝ Taka が 事前に 裁定を 積んでおく 方式は ★成立しない。

★理由B（★意図的な 防御）―― ★自己 energize の 禁止
   逐語「attribution is NOT self-/model-authored (★self-energization refused)」
   `_FORBIDDEN_ATTRIB = {'SELF','LLM','CLAUDE','AGENT','AUTO','MODEL', …}`
   ★★機械が 自分の 書き込みを 自分で 承認する 経路を ★名簿で 塞いでいる。
   ★残余リスクも 正本が 明記:「OS-level Taka impersonation is NOT defeatable at this layer alone」
```

**★∴「毎 patch」なのは ★fingerprint 束縛の 帰結であって、★Taka を 呼びたいからでは ない。**

### ② ★安全性を落とさず Taka を通常経路から外せる最小変更

```
★★1つだけ ―― ★門(2) に ★「委任の 連鎖」を 見る 分岐を 足す。

   現在:  attribution == 'TAKA' でなければ ★拒否
   最小:  attribution == 'TAKA'                                        … ★従来どおり 通す
          ★または attribution == '2DER' ★かつ 次を ★すべて 満たす:
            ・裁定が ★Taka の approval token を 名指ししている（`approval_id`）
            ・`authority.validate_approval(token, …)` が ★ok（★★既存関数・★新規0）
                → action_type 一致 ／ ★expiry 内 ／ ★未消費（single_use）
                → `approved_scope` に ★repo_identity と ★allowed_files が 含まれる
            ・その token を ★`consume_approval` で ★焼く（★★1回限りが ★二重に 効く:
              ★token の 消費 ＋ ★BIND-3 の token_id 消費）

★★これで 落ちないもの:
   ★fingerprint 束縛 … ★そのまま（★2DER は 実際の patch を 見てから 裁定を 書く）
   ★1回限り性       … ★二重に なる（★むしろ 強くなる）
   ★allowed_files   … ★token の scope で ★Taka が 先に 縛る（★repo 全体は 渡らない）
   ★自己 energize 禁止 … ★★機械単独では 発行できない
                        ＝★『Taka が 先に 範囲を 切った 中でだけ』機械が 出せる
   ★残高証明・取消・記録の実在 … ★手を 触れない

★★増えるもの: ★分岐 1つ（`bridge_minter` の 門(2)）
★★増えないもの: ★新台帳 0 ／ 新 ID 0 ／ 新しい 判断規則 0 ／ repo 全体の 許可 0 ／
               ★shell 実行権 0 ／ ★fingerprint 束縛を 外さない ／ ★allowed_files だけの 自由 patch に しない

★★別途 要る（★既報・★この変更とは 独立）:
   ・connector の 呼び手（★今 0）
   ・`_RollbackPlan` を 返す/保持する（★test/audit 失敗後の rollback を 必須にするため）
   ・connector が `dry_run_apply` を 呼ぶ
```

### ★★これは Taka の裁定事項（★MGR は決めない）

```
★門(2) は ★正本の 安全境界そのもの ∴ ★上申条件① と ⑧ に 当たる。
★★争点は 1つ:「★Taka が 先に 範囲(repo・allowed_files・期限)を 切って 委任した 中で、
   ★2DER が ★実際の patch を 見て 裁定を 出す」ことを ★自己 energize と 呼ぶか 呼ばないか。
★MGR の 見立て（★決定ではない）: ★呼ばない ―― ★範囲は Taka が 先に 切り、
   ★機械は その中で しか 動けず、★消費は 記録に 残り、★取消も 効く。
★★但し これは ★価値判断 ∴ ★Taka が 決める。
```

## 7. していないこと

```
★実装 0 ／ 実 repo へ 書き込み 0 ／ bridge_minter / bridge_reconciler を 走らせていない
★fingerprint 束縛を 外す 案を 採っていない ／ allowed_files だけの 自由 patch を 作っていない
★repo 全体の 許可を 作っていない ／ _MAP / authority / disposition 規則を 変更していない
```
