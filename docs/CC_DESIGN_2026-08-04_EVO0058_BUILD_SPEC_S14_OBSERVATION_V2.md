# 【BUILD SPEC v2】`EVO-0058` 段2（S14）— **★emit を artifact 確定の後へ移す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 19:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1 との関係**: ★差し替えない・追記しない。**★本書が実装源**。★観測の中身は **v1 と同じ**（★移すだけ）
- **★v1.8 の宣言**: **★核は無い・2DER 工程 0**（★v1 と同じ）
- **★私の予告**: ★Claude の配線 **6〜10行**（★v1 と同じ・★増やさない）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★私の誤り（★実物で確かめた）

```
★v1 は ★`res = _REAL_RUNNER(...)` の ★直後（:134 の後）に emit を置いた。
★★その位置では ★`res.get("artifact")` しか見えない ―― ★★`workspace` から ★ファイルを読むのは ★:164-170。
★逐語（`generate_via_runner.py:164-170`）:
     artifact = res.get("artifact")
     if artifact is None and res.get("workspace"):    # production: workspace の成果物を読む
         try:  ... artifact = f.read()
         except OSError: artifact = None
★★★∴ ★v1 の位置の `artifact_len` は ★★本番経路では ★常に `None` になる ＝ ★★観測にならない。
★★★★★MGR の裁定(A)は ★正しい。★私の置き場所が ★誤っていた。
```

## 2. やること（★1箇所・★移すだけ）

**★`artifact` が確定した後**（`generate_via_runner.py:171` の `art_sha = ...` の**直前**）:

```python
    try:                                                     # S14(EVO-0058): 区間の観測(★既存 etrace を呼ぶだけ)
        from ds import etrace as _ET
        _ET.emit("RUNNER", "run_minimal_slice",
                 {"target_file": task_packet.get("target_file"),
                  "skeleton_len": len(task_packet.get("skeleton") or ""),
                  "tests_len": len(task_packet.get("test_body") or "")},
                 {"status": status, "classification": classification,
                  "artifact_len": (len(artifact) if isinstance(artifact, str) else None),
                  "workspace": bool(res.get("workspace"))},
                 "OK" if res.get("ok") else "FAILED",
                 task_id=task_packet.get("task_id"), fail_open=True)
    except Exception:
        pass
```

```
★★v1 との差は ★★位置だけ（★`status` / `classification` / `artifact` が ★確定済みの変数として使える）
★★★★行数は ★増えない。★観測の中身も ★変えない
★★★★★★(B)（★workspace のファイルを別途 調べる）は ★採らない ―― ★同じ値を2経路で調べる形を ★自分で作らない
```

## 3. ★★これで区別できること（★裁定の目的）

| 実際に起きたこと | `artifact_len` | `workspace` |
|---|---|---|
| ★成果物が在る | ★正の数（例 935） | True |
| ★ファイルは在るが ★空 | **★0** | True |
| ★ファイルが ★無い（OSError） | **★None** | True |
| ★workspace 自体が無い | ★None | **False** |

```
★★本日の事故（★0字）が ★★どの行だったかが ★次から分かる ＝ ★本件の目的
```

## 4. 受入（★v1 の §3 を引き継ぐ・★1つ足す）
```
★(1) 1回 走らせ ★`GET /api/etrace?run_id=…` に ★`component: "RUNNER"` が出る
★(2) ★`artifact_len` が ★逐語で読める（★成功時＝正の数）
★(3) ★空で落ちた時に ★`0` / `None` / `workspace:False` で ★§3 の表のどれかに ★当たる
     ★★再現できなければ ★『再現できなかった』と書いて ★止まる（★捏造しない）
★(4) `result` が OK/FAILED で入る ／★(5) Claude の配線行数（★2DER の実績に数えない）
★(6) 戻せる ／★(7) 61本を走らせない
★★★(8) ★★★成功した走行で ★`artifact_len` が ★★`None` でないことを ★必ず確かめる
     ＝ ★★v1 の誤り（★本番経路で常に None）を ★踏んでいないことの ★確認
★★★★★予告を投入前に書く: ★行数 ／ ★(2) で出ると思う `artifact_len`
```

## 5. ★★これでも分からないこと（★v1 から不変）
```
★『生成が途中で切れた』は ★★分からない ―― ★`artifact_len` は ★結果の長さであって ★worker の raw ではない。
★★∴ ★本件で分かるのは ★§3 の ★4通りまで。★raw を残すのは ★別の区間 ＝ ★次に選ぶなら そこ（★本件では作らない）
```

## 6. 禁止（★v1 を引き継ぐ）
```
★(B) を採る（★workspace を別途 調べる＝★読む口を2つ作る）／ ★S11 / S15 を同時に触る
★`artifact` の本文を emit に載せる ／ ★`fail_open` を外す ／ ★空の失敗を捏造して再現する
★『切れたことが見えるようになった』と書く ／ ★新しい台帳・計器を作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
