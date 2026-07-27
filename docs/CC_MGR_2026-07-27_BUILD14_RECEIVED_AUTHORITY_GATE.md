# CC 管理(MGR) → 設計/監査(CC-α): **Build 14 受領 — ★契約の壁は越えた。次は権限の壁**（HANDOFF）

- `BUILD_ROLE: 参照` / **宛: DESIGN/AUDIT(CC-α)** / 写: Taka / 発: MGR / 2026-07-27 / TYPE=HANDOFF
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD14_GENERATE_BUILT.md`（**未監査**）

## 1. ★契約の壁は越えた（事実）
| | Build 12（契約なし） | **Build 14（契約つき）** |
|---|---|---|
| 失敗理由 | `SPEC_INCOMPLETE_NO_CONTRACT` | **★別の理由に変わった**（下記） |
| sandbox | **作られなかった**（56→56） | **作られた**（56→57・`/tmp/2der_runner_tx15qmh2`） |
| 成果物 | 無し | **無し（sandbox は空・0ファイル）** |

**∴ 契約を渡したことで、`GENERATE` は次の段まで進んだ。** **Build 12 の詰まりは解けた。**
**過大にしない**: **成果物は出ていない。** **1段先の壁に当たっただけである。**

## 2. ★新しい壁は「権限」である（逐語）
```
action_type mismatch (ledger=USE_VLLM_INFERENCE, need=LIVE_WORKER_MINIMAL);
task_id mismatch (ledger=TASK-2DER-21F64D9D#attempt-1, run=TASK-2DER-21F64D9D);
operation_class LIVE_WORKER_TASK outside approved scope
```
**3つの不一致が1文字列に連結されている。** **性質が違うので分けて扱うこと:**
| # | 内容 | MGR の見立て（**裁定ではない**） |
|---|---|---|
| **(1)** | `action_type` が `USE_VLLM_INFERENCE` だが `LIVE_WORKER_MINIMAL` が要る | **承認の範囲の問題**に見える |
| **(2)** | `task_id` が `…#attempt-1` と `…`（接尾辞の有無）で食い違う | **★内部の不整合に見える。** 権限の話ではない可能性 |
| **(3)** | `operation_class LIVE_WORKER_TASK` が承認範囲外 | **承認の範囲の問題**に見える |

## 3. 依頼（D-25・これ1つ）
> **★この承認は、誰が・どこに・どうやって与えるものか。**
- **確かめること**: 承認を保持しているのは何か（`AUTHP:` / `AUTHD:` の id 族が `ids.resolve` に在るのは既知）／`action_type` と `operation_class` の値はどこで定義されるか／**付与は自動か、人手か。**
- **★もし人手（Taka の承認）が要るなら、それは MGR が Taka へ上げる案件である**（上げてよい4類型の (ii)/(iii)）。**設計は「要る／要らない」を事実で示すところまで。**
- **★(2) の `task_id` 不一致は、権限とは別に切り分けること。** **同じ文字列に入っているからといって同じ原因とは限らない。**
- **【未確認】を消さない。** **「動く」と書くなら再現コマンドを併記。**

## 4. 禁止（今この場で）
1. **★権限を迂回しない。** **承認の範囲を自分で広げない。** **これは run-gate と同じ種類の安全機構である。**
2. **★手で成果物を書かない。**
3. **`#attempt-1` を推測で合わせない。** **由来を確かめてから。**
4. **再投入しない。** **同じ依頼文で2回目を打つなら、回数と理由を先に MGR へ。**

## 5. 併せて受領（作法）
- **鮮度確認の初回で相対パスを使い「4ファイルとも存在しない」と出たが、絶対パスで取り直し、誤った出力を根拠にしていない。** **自分の観測の誤りを、使う前に捕まえている。**
- **`contract_source` キーが payload に無い**ことを、実装源が名指ししていた項目として報告した。**「無い」を書いている。**

---
*MGR。Build 14 受領（未監査）。★契約の壁は越えた=Build 12 の `SPEC_INCOMPLETE_NO_CONTRACT` が別の理由に変わり、sandbox も作られた（56→57）。ただし中身は0ファイルで成果物は無い——1段先の壁に当たっただけ。★新しい壁は権限=`action_type mismatch (USE_VLLM_INFERENCE vs LIVE_WORKER_MINIMAL)` / `task_id mismatch (#attempt-1 の有無)` / `operation_class LIVE_WORKER_TASK outside approved scope` の3つが1文字列に連結。性質が違うので分けて扱う（(2) は内部の不整合に見え権限の話ではない可能性）。D-25=この承認は誰がどこにどうやって与えるものか（AUTHP:/AUTHD: の id 族／値の定義場所／付与は自動か人手か）。★人手（Taka の承認）が要るなら MGR が上げる案件であり、設計は「要る／要らない」を事実で示すところまで。禁止=権限を迂回しない・承認範囲を自分で広げない（run-gate と同種の安全機構）／手で成果物を書かない／`#attempt-1` を推測で合わせない／再投入しない。作法=鮮度確認の初回の誤出力を使う前に自分で捕まえた／`contract_source` が無いことを「無い」と書いた。*
