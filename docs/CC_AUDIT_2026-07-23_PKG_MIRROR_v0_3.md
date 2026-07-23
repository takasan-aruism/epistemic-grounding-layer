# CC 投入前監査（詳細・relay 用）— PKG_MIRROR v0.3

- 監査者: Claude Code（監査のみ）/ 日付: 2026-07-23
- 対象: `パッケージ複製 seam（PKG MIRROR）実装仕様 v0.3`（v0.2 を SUPERSEDE）
- 用途: Claude Web への relay。事実と `file:line` のみ。修正案・優先順位付け・評価語は含めない。
- 結論: **確定 blocker 1 件（Finding 1）＋ 未確定リスク 1 件（Finding 2）。** submit は Finding 1 の解消後。

---

## ✅ 正しく取り込まれている（前回 A〜G 監査との整合）

```
- 記法規律の再掲（"<<<FILL" 部分文字列判定・複数可・位置制約なし）は実装と一致 / generate_via_runner.py:53,49-73
- W-2 中間 __init__.py 生成 → manifest "created" 分離 → sha256 突合対象外 : 設計整合
- W-3 S9 重複定義禁止（AST top-level）: mirror_package/sha256_file/MirrorHalt/MIRROR_MANIFEST/MIRROR_EXCLUDE を各1回に固定 : 健全
- W-4 conftest を作らず各テスト内 @pytest.fixture 定義 : 既存規約（E1 conftest 皆無 / E2 in-module）と一致
- S3 の checked>0 ガード（空振り検出）・S7 陰性対照・S8 自己ホスティング・S10 AST(twoder.* 静的 import 禁止): ロジック健全
```

---

## 🔴 Finding 1 — 確定・submit ブロッカー：不変テストが artifact を発見できない

`_load_artifact()`（§3 冒頭、モジュール import 時に `M = _load_artifact()` を実行）は artifact を 3 経路で探す。
**現行 runner はそのどれも供給しない。**

| _load_artifact の経路 | 現実 | 出所 |
|---|---|---|
| `import twoder.seam.pkg_mirror` | 未配線（§5 明言：本仕様は generate_via_runner に繋がない）→ ImportError | 仕様 §5 |
| `os.environ["ARTIFACT_PATH"]` | runner は設定しない | — |
| `os.walk(cwd)` で `"pkg_mirror.py"` | runner は artifact を **`impl.py`** として ws に書く | 下記 |

**runner の命名（確定・コード読取）:**
```
- worker は tp["target_file"]（既定 "impl.py"）へ書く / LocalWorker.run:26, qwen_worker.py:88
- run_runner が task_packet に target_file:"impl.py" / allowed_files:["impl.py","test_impl.py"] を固定 / generate_via_runner.py (run_runner)
- test は tp["test_file"]="test_impl.py" として ws に seed / live_worker_runtime.py:104-106
- 実行は subprocess pytest test_impl.py（cwd=ws）/ live_worker_runtime.py:116, _run_test:36-41
```

**帰結:** 3 経路とも外れ、`_load_artifact` が `RuntimeError("BOOTSTRAP_HALT: pkg_mirror artifact not found")` を送出
→ `test_impl.py` が collection error → **S1–S10 全滅（0/10）**。worker が正しい `mirror_package` を書いても受からない。

**事実の核:** サンドボックス内の artifact 名は `impl.py`。`_load_artifact` の探索名 `pkg_mirror.py` と一致しない。
（直し方は Web／発注側判断。CC は指さない。）

---

## 🟠 Finding 2 — リスク・INDETERMINATE：ws サンドボックスで `import twoder` が成立するか未検証

```
- 全テストが pkg_root fixture（import twoder）と _load_artifact（import twoder.seam.pkg_mirror）に依存
- _run_test は subprocess.run(test_command, cwd=workspace) を env 指定なし＝親環境継承・PYTHONPATH 無設定・timeout=30s で実行 / live_worker_runtime.py:36-41
- よって sandbox 内 import twoder は起動プロセスの継承 env に完全依存
- 既存58テストは sandbox 内で twoder を import した実績が無い（初の要求）
- twoder/__init__.py は空（0 行）＝ 発見できれば import 自体は一瞬
```

**実測（帰属不能）:**
```
- twoder 親を cwd にすれば即解決 : python3 -c "import twoder" → /home/takasan/twoder/__init__.py（fast）
- tmpdir cwd（/tmp）からの実行で 12–30s でも終了しない事象を観測（-S でも同様）
- ただし twoder を含まないコマンドも timeout する回があり、成否が一定しない
  → 稼働中の 2DER/vLLM プロセスによるシステム負荷の可能性。クリーンに帰属できない → INDETERMINATE
```

**言えること / 言えないこと:**
```
- 言える: _run_test は PYTHONPATH を張らない（live_worker_runtime.py:41）ので、
         「sandbox で twoder が import 可能」は仕様の暗黙前提であり未保証
- 言えない: 「import twoder が sandbox で必ず失敗する」（再現が負荷と切り分け不能）
- 含意: Finding 2 が偽なら、Finding 1 修正後も import twoder 段で落ちる
```

---

## claim ceiling

```
- Finding 1 : コード読取のみで確定（環境非依存）
- Finding 2 : 未確定（INDETERMINATE）。CC の再現はシステム負荷と切り分け不能
- S1–S10 のロジック自体は健全（Finding 1/2 は「テストが走る前提」の欠落であって、テスト設計の欠陥ではない）
- 次アクションは Web：(a) 発注側テストの artifact 発見経路、(b) sandbox の twoder 可視性、の 2 点を確定
```
