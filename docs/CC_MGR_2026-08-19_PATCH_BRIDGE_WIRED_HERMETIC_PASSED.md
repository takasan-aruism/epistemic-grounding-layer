# 宛: Taka / 設計 / 監査 ―― `patch_bridge` 配線完了: **使い捨ての場で 10条件 全成立**

**Claude が書いた判断ロジック 0行。本番ファイルへの書き込み 0。実 repo energize 未接触。**

## 0. 結論

```
★★`patch_bridge` が ★unified diff を ★本当に 当てるように なった。
★★前（★2026-08-19 07:4x MGR 実測）= 'hello\n' + diff → ★ファイルの 中身が ★diff 本文
★★後（★同日 14:2x 実測）          = 'hello\n' + diff → ★★'world\n'
★安全機構は ★1つも 変えていない（★6つとも 実走で 再確認）
```

## 1. 使い捨ての場での実走（★10条件）

| # | 条件 | 実測 |
|---|---|---|
| ① | /tmp の使い捨て repo のみ | **★成立**（`/tmp/pb-wire-…`） |
| ② | 初期 `hello\n` | 済 |
| ③ | diff で hello → world | ― |
| ④ | 適用後が正確に `world\n` | **★`'world\n'`** |
| ⑤ | diff 文字列そのものを書き込まない | **★成立** |
| ⑥ | preimage 不一致時は rollback | **★`ValueError: preimage` → `ROLLED_BACK`** |
| ⑦ | rollback 後 `hello\n` | **★`'hello\n'`** |
| ⑧ | allowed_files 外は拒否 | **★`ValueError: target.txt`** |
| ⑨ | 実 repo は拒否されたまま | **★`not a throwaway (resolved path outside temp root): /home/takasan/twoder`** |
| ⑩ | 証拠記録が残る | **★`APPLIED` と `ROLLED_BACK` の両方**（`PATCH_APPLICATION`） |

### ★追加で測った1件（★fail-closed の実証）

```
当てられない diff（`-zzz` を要求）を 与えた:
   → ★ValueError: apply: context_mismatch
   → ★ファイルの 中身は ★'hello\n' の まま（★書いていない）
   → ★記録 = ROLLED_BACK
```

## 2. 書いた足場（★判断は1行も書いていない）

```python
from twoder.apply_unified_diff import apply_unified_diff as _APPLY
for filename in list(dict.fromkeys(validated.filenames)):
    …（★既存の 検査は そのまま: _confined_path / isfile / expected_preimage）…
    _cur = open(path, 'rb').read().decode('utf-8')
    _r = _APPLY(_cur, canonical['diff'])          # ★2DER が 書いた 部品（★封印試験 16/16）
    if _r.get('text') is None:
        raise ValueError('apply: %s' % _r.get('reason'))   # ★当てられない=★書かない
    open(path, 'wb').write(_r['text'].encode('utf-8'))
```

**★変えていないもの**: `allowed_files` ／ throwaway 制約 ／ `preimage` ／ `rollback` ／
`provenance` ／ `recorder` ／ `_confined_path` ／ `fingerprint` 検査 ／ `validate_artifact` ／
`apply_patch_bounded` の 外形。

### ★1つだけ挙動を変えた（★開示）

```
`validated.filenames` は ★`a/` と `b/` の 両方から 拾うため ★同じ名前が 2回 入る（★実測・既報）。
★以前は ★同じ bytes を 2回 書くだけで 影響が 無かった。
★★当てる 形では ★2回目が 文脈不一致に なり ★必ず 失敗する。
∴ ★重複を 落とした（★順序は 保つ・`dict.fromkeys`）。
★これは ★配線を 成立させるために ★必要だった 最小の 変更。★別件の 欄の 差
  （`check_diff_within_allowed` との 食い違い）は ★直していない。
```

## 3. ★残っている門（★触っていない）

```
★実 repo 用の energize = ★逐語「There is NO real-repo minter here; that is a ★§3 design + ★Taka gate」
★★∴ 本番の repo へ 当てることは ★今も 構造的に できない（★設計どおり）。
★★『機械が 既存ファイルへ 安全に 配線する』能力の ★最後の 門が これ。
```

## 4. ★今日1日で 2DER が増やした能力（★総括・★すべて Claude 実装 0行）

| 部品 | 状態 | 実走の証拠 |
|---|---|---|
| `requeue_decision` | **配線済み・稼働** | 常駐が自力で3件再取得 ／ COMPLETE 2件 |
| `should_call_senior` | **配線済み・稼働** | **★`claude -p` 29回 → 2回** |
| `apply_unified_diff` | **★配線済み** | 封印試験 16/16 ／ **★patch_bridge が 本当に 当てるように なった** |
| `tasks_to_enqueue` | 配置済み・未配線 | ― |
| `dispose_decision` | 配置済み・未配線 | ― |

**★Claude が書いたのは 足場の接続 ★3箇所だけ**（`346f074` / `e516007` / `6c87b0b`）
**―― どれも ★判断ロジック 0行。**

## 5. していないこと

```
★判断ロジック 0行 ／ 新台帳 0 ／ 新 ID 0 ／ 新しい 判断規則 0
★本番ファイルへの 書き込み 0（★書いたのは すべて /tmp 配下の 使い捨て）
★実 repo energize 未接触 ／ ★BLOCKED TASK 未接触 ／ ★manager 稼働継続
★`check_diff_within_allowed` の 食い違いを 直していない（★別件のまま）
```
