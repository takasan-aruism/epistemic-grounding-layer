# 【BUILD SPEC】E2E 検査 — **証拠回収の手順（★何を証拠にするかを、走らせる前に決める）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-30 22:3x / TYPE=BUILD_SPEC
- **運用方針 確認済（版: v2.8）**
- **★正典**: `TAKA_2026-07-30_PHASE4_E2E_INSPECTION_ORDER.md`（逐語）／**裁定**: `CC_MGR_2026-07-30_D137_…md`
- **★これは何に対して発火するのか**: **★正典の依頼文1件を投入した、その1回の実行だけ。**

## ★2DER 優先原則の5点（本 SPEC について）
```
① 入口 : ★(a) HTTP。POST /api/submit → POST /api/run_next
② 試す : ★正典の依頼文をそのまま1回
③ できなかったこと: ★検査結果として書く（★これを取るのが目的である）
④ 実装 : ★何も実装しない・提案もしない（★停止したら最小修正候補を1件だけ、実施せずに書く）
⑤ 再現 : ★該当なし
```

---

# 1. ★投入（★1回だけ）

## 1-1. 依頼文は**打ち直さない**
```bash
cd /home/takasan
python3 - <<'PY' > /tmp/claude-1000/-home-takasan/e2e_req.json
import json,re,hashlib,sys
s=open('/home/takasan/egl/docs/TAKA_2026-07-30_PHASE4_E2E_INSPECTION_ORDER.md',encoding='utf-8').read()
raw=re.search(r'#### 検査課題.*?```\n(.*?)\n```', s, re.S).group(1)
assert '\n' not in raw
sys.stderr.write("字数 %d / sha1 %s\n%s\n" % (len(raw), hashlib.sha1(raw.encode()).hexdigest(), raw))
print(json.dumps({"raw": raw}, ensure_ascii=False))
PY
```
**★字数と sha1 を BUILT に書く**（★1文字も変えていないことの示し方）。**★ファイルとしてスクリプトを作らない**（D-137 §1-3）。

## 1-2. ★投入と、その直後にやること（★順番を守る。★今日これで印が1つ立った）
```
① POST /api/submit             ← ★応答を全文 保存する（-o /dev/null を使わない）
② ★直後に GET /api/receipt     ← ★他の口を1つも叩く前に。★これをしないと入口を示せない
③ 以後、下表の順に回収
```
**★投入は1回。★再投入しない。★止まっても直さない**（D-137 §1-4）。

---

# 2. ★工程ごとの証拠（★走らせる前に固定した。★後から変えない）

| # | 正典の工程 | ★実装上の名称 | ★証拠を取る口（★既存のみ） | ★何が取れたら PROVEN か |
|---|---|---|---|---|
| 1 | 受付 | `submit()` / HTTP 入口 | `POST /api/submit` 応答 ＋ **★直後の** `GET /api/receipt` | `task_id` が返り、`receipt.last_recv_at` が**★投入時刻と一致** |
| 2 | ID 発行 | `DW_TASK_ID` | `GET /api/resolve?id=<task_id>` | `resolved: true` と `state` が返る |
| 3 | RRI | `RRI_REQUEST_TYPE` / `RRI_RESOLVED_INTENT` | `submit` 応答の `request_type` ＋ `GET /api/state?task_id=` の `rri` | **★呼ばれた証拠**（値が在る）と**★後工程へ渡った証拠**（`acquisition_method` が決まっている） |
| 4 | 計画 | `PLAN` | `GET /api/claude_packet?task_id=` の **`implementation_packet_ref`** | **★`plan_source` を必ず書く**（`QWEN_BUILD_PLANNER` か `RULE_TEMPLATE_2DER_EVO_0007` か）＋ **`runtime_recovery`**（`attempts`/`outcome`） |
| 5 | 実行命令生成 | 計画内の `steps` / `test_command` | 同上 | 命令が**★投入文に無い**ことを、★文字列の完全一致で確かめる |
| 6 | 実環境での取得 | `GENERATE`（`CODING_WORKER`＝`QWEN_LIVECODER`） | `claude_packet` の **`worker_run_ref`** | **★実際に打たれた command / 対象 host か container** が特定できる |
| 7 | 出力取得 | 同上 | `claude_packet` の **`test_result`** ＋ 生出力 | **★GPU 識別/使用率/VRAM 総量/VRAM 使用量/実行中プロセス**の5つが**★実測値として**在る。**★1つでも空なら「取得不能」と書く。★空を成功にしない** |
| 8 | 検証 | `AUDIT`（`INDEPENDENT_AUDITOR`＝`QWEN_AUDITOR`） | `claude_packet` の **`findings`** ＋ `GET /api/state` の `dw_state` | **★検証主体と検証結果**が記録されている。**★出力をそのまま採用していたら不成立** |
| 9 | 記録 | Event Trace / 各台帳 | `GET /api/state` の `etrace_run_id` → **`GET /api/resolve?id=ETR-…`** ／ `UTT-` / `DE-` / `ART-` | **★1つの task_id から、入力→RRI→計画→実行→生出力→検証→DW入力→最終結果 のどこまで辿れたかを★1つずつ ○/× で書く** |
| 10 | DW 要約 | **★該当する既存の口を、設計は名指せない** | `claude_packet` ／ `GET /api/state` ／ `GET /api/control` を叩いて**★在るか確かめる** | **★引けなければ「引けない」と書く。★`UNKNOWN` の材料である。★作りに行かない** |
| 11 | ユーザ返答 | **★同上（名指せない）** | 同上 | **★同上** |

## 2-1. ★`run_next` の扱い（★D-137 §1-1）
```
★task_id を必ず付ける（付けないと refused になる。★今日 実測）
★押した回数・各回の時刻・各回の返り値を★全部 書く
★工程「実行」の actor に 2DER を入れない（★押したのは人である）
★2DER が自分で次へ進んだ事実が在れば、★そのときだけ別行で書く
```

## 2-2. ★先に言っておく（★出ても失敗ではない）
```
★DW の並びに ★Claude 側の関門が2つ在る（実読・dispatch.py:29-37）:
   DISPOSITION_REQUIRED → DISPOSE (MANAGER=CLAUDE)  ／  READY_FOR_UPPER_REVIEW → UPPER_REVIEW (CLAUDE_SENIOR=CLAUDE)
★ここに当たったら、★そこが停止点である。★押さない。★正典 B（最初の停止点の確定）で完了である。
★「あと1段で動く」と書かない。
```

---

# 3. ★やってはいけないこと
```
★nvidia-smi など GPU を自分で測らない（D-137 §1-2。★広く読む）
★取得方法を補完しない・コマンドを選ばない・整形しない・要約を書き足さない
★スクリプトをファイルとして作らない（★コマンドを打つのは可）
★止まったら直さない・迂回しない・再投入しない（★自動 retry が既存仕様で動いた場合のみ、回数と各試行結果を書く）
★production repo を変えない・commit しない・台帳を直読しない
★判定を確定しない（★判定案も出さなくてよい。★事実だけ置く）
```

# 4. ★報告の形（★正典の形式をそのまま使う）
```
★まず表: 順番 / 工程 / 判定 / actor / 主な証拠ID / 備考
★判定は正典の6区分だけ: PROVEN / OBSERVED_UNATTRIBUTED / WIRED_UNPROVEN / FAILED / NOT_REACHED / UNKNOWN
★「概ね成功」「ほぼ動いた」を書かない
★続けて: 最終結果 ／ 2DER が担当した工程 ／ 人・Claude が担当した工程（★開始操作を省略しない）
          ／ 台帳と Event Trace の評価 ／ 停止原因 ／ ★次の最小修正候補は1件だけ（★実施しない）
★宛: 設計/監査(CC-α)。TYPE=BUILT。★:8005 を使ったら1行 書く
```

# 5. ★止まってよい場所（★2通りに読めたら止めて聞く）
```
★Claude 側の関門に当たった → ★そこで終了。★押さない
★取得値の一部だけが空 → ★「取得不能」と書いて続けてよい（★空を成功にしない）
★口が在るのか無いのか判断が割れる → ★止めて設計へ聞く
```

---
**決めたこと**: **①依頼文は正典から機械で抜き、投入は1回、投入直後に他の口を叩く前に `receipt` を読む ②工程1〜9 の証拠の口を走らせる前に固定した（計画は `plan_source` と `runtime_recovery` を必ず書く／取得は5項目、空を成功にしない） ③工程10・11 は既存の口を設計が名指せないので「引けなければ引けないと書く」＝作りに行かない。**
