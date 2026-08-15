開発者規律 確認済(v1.0)

# 【是正指示・★Taka】★2DER GNW 構成 ―― ★★単一 Manager の 高機能化を 進めない

宛: MGR ／ 発: DESIGN（監視兼務）／ 2026-08-16 03:0x ／ 台帳: ★MGR が 決める（★本線＝EVO-0058 との 関係も MGR 判断）

## 0. ★★先に ―― ★★私（監視）の 非

```
★★私は 12時間 ★`manager_v0` を ★『Manager』1つとして 数え続けた。
★★『★これは Domain の 1つでは ないか』という 問いを ★★一度も 立てていない。
★★∴ ★★『常時起動 Manager が 動いた／責務が 2つ 減った』という 私の 報告は
   ★★★層を 取り違えた 報告(★D の話を G の話として 出した)。
★★Taka が ★逐語で 3回 訊いて 初めて 出た(★『どの Manager を 指している？』)。
```

## 1. ★Taka 逐語（★全文・★歪めない・★切り詰め0）

> **2DER GNW構成への是正指示**
>
> **現在の manager_v0 を中心とした構成を、単一Managerの高機能化として進めないこと。**
>
> **2DERが目指しているManager構成は、原則として General Manager → Domain Managers → Workers の三層構造である。**
>
> **現在確認されている領域候補は少なくとも、DW / RRI / 経路表 / 2DER(Towder) である。ただし、これをそのまま確定一覧とはしない。既存資料・台帳・実コードから、現在存在する責務領域を先に調査し、Domain Managerの母集団を確定すること。**
>
> **1. 最初に「現在のManager機能」を分解する ―― manager_v0 の各機能について、①General Managerの仕事 ②Domain Managerの仕事 ③Workerの仕事 ④どこにも属さない／判断不能 のどれかに分類する。★名前ではなく、実際に何を読んで、何を判断し、何を動かしているかで分類すること。★特に manager_v0 が現在行っている全領域の押し出しを、そのままGeneral Managerの職責とみなしてはならない。**
>
> **2. General Managerを「何でもやるManager」にしない ―― General Managerの基本職責は、全体状態を見る → 注意を向けるべきDomainを決める → Domain Managerへ渡す → Domainから返った状態を統合する → 必要なら人へ裁定を上げる とする。原則としてGeneral Manager自身は、DW内部の案件処理／RRI内部の調査処理／経路表の更新・経路判定／個別Workerの実行 を直接担当しない。★General ManagerがDomain固有処理を持ち始めた場合、それを「便利だから追加」とせず、職責越境として検出できるようにする。**
>
> **3. Domain Managerは各領域の状態を管理する ―― 各Domain Managerは自分の領域について、現在何があるか／何が動いているか／何が止まっているか／次に何をする必要があるか／自分で処理できるか／上位判断が必要か を答えられる状態にする。Workerはその下で具体的作業を行う。したがって、General → Domain → Worker の各境界について、★入力・出力・権限・状態・停止条件・上申条件 を明示する。**
>
> **4. 経路表Domainを先行実例として扱う ―― twoder-route-worker.service が既に独立しているため、ここをGNW分離の最初の実例として調査する。★ただし「serviceが分かれているからDomain Managerである」とは判定しない。現在のroute-workerが、Domain Managerなのか／Workerなのか／両方を混在させているのか を職責から判定する。★経路表には将来的に「人体図鑑＋機能表」を管理する領域責任があるため、単なる経路更新WorkerとDomain Managerは区別すること。**
>
> **5. DW・RRIについて既存実装を優先して調査する ―― ★新しいManagerを先に作らない。DW、RRIには既に独立した責務・状態・処理系が存在するため、現在どこまでDomain Manager相当の機能を持っているかを調査する。★特にDWには既にPLAN / GENERATE / AUDIT / UPPER_REVIEW / DISPOSE等の役割分離が存在するため、これを壊して外側から巨大Managerを被せない。「足りないDomain Manager機能」だけを特定する。**
>
> **6. 常駐化とGNW構成を分けて考える ―― 「常時動くManagerが必要」と「一つのManagerが全部を見る」は別である。常駐するGeneral Managerが必要でも、Domain内部の処理をGeneralへ集約する理由にはならない。★むしろ常駐Generalは軽く保ち、必要なDomainだけを起こし、Domainが必要なWorkerを動かし、仕事が終われば休止する方向を基本とする。**
>
> **7. 今回は実装より先に構造を確定する ―― まず以下を1枚の表として出すこと。**
> **領域 | General / Domain / Worker | 現在の実体 | 現在の職責 | 本来の職責 | 越境している職責 | 不足している職責 | 常駐の必要性 | 上位/下位との入出力**
> **そのうえで、現在構成 → GNW目標構成 の差分を出す。★この段階では新しいManager、新台帳、新しい口を作らない。既存部品の再配置・職責分離だけでどこまで到達できるかを先に確定する。**
>
> **完了条件 ―― 今回の完了は「GNWを実装した」ではない。**
> **1. General Managerの職責が確定した**
> **2. Domain Managerの母集団が実態から列挙された**
> **3. 各DomainとWorkerの境界が確定した**
> **4. manager_v0 が現在吸収している越境職責が全件出た**
> **5. 既存実装を流用できる部分と新規実装が必要な部分が分離された**
> **6. 次に実装する最小の1件が特定された**

## 2. ★Taka 逐語（★直前の 会話・★前提として 必要）

> **G は General、D は Domain、W は Worker なので、あなたが言っているのは DW の Domain Manager ということだね。★現状 General Manager は存在しない。General Manager と言っているのが、以前「Manager機能を移管しないとね」と言っていたもの**

> **Domain Manager は複数いる。DW、RRI、経路表、Towder かな？ 他にはわからんけど。★いまやっている GNW 構成はそんな感じの話よ？ ★ちゃんとそれに向かって進んでる？**

## 3. ★★私が 実測した 現状（★2026-08-16 03:0x・★source と systemd から 直接）

```
★★常駐している もの = ★★3つだけ
   ★`twoder-manager.service`     = `twoder/manager_v0.py`（★611行）
   ★`twoder-route-worker.service`= `twoder/route_worker.py`（★297行）
   ★`twoder-webui.service`       = front door

★★Taka の 挙げた 領域候補と 突き合わせ:
   ★DW      = ★専任の 常駐 ★無し（★`dev-workcell/dw/dispatch.py` は 在るが ★呼ばれる部品）
   ★RRI     = ★★無し
   ★経路表  = ★在る（route-worker）★★但し Domain Manager か Worker かは ★未判定
   ★2DER    = ★`manager_v0`（★★但し 全領域を 押している）
   ★★General = ★★★無し（★Taka 逐語で 確認）

★★★∴ ★`manager_v0` は ★名前上は 1つの Domain のはず が
   ★★★実質 General の 位置に 座り ★全領域を 押している。
★★★∴ ★私が 昨日 出した『611行に 増えた＝D が 太った』は ★★症状の 記述
   ―― ★★★原因は ★『G が 無いので G の仕事が D に 流れ込んでいる』。
```

## 4. ★★これは 新規の 話では ない（★★既存資料を 先に 引く・★Taka §5）

```
★★『Manager機能を 移管しないとね』は ★以前から 在る ∴ ★★★過去資料に 当たる
★★私が いま 確かめた 範囲 = ★`egl/docs` に `GDW` / `G_D_W` の 名を持つ 文書は ★★0件
   ★★但し ★『G-D-W / Work Relay 仕様』は ★2026-08-15 14:2x に ★MGR が 数で 検証している
      （逐語=★『17欄中6在る・並列実績0・★★DW Manager は既存』）
   ★★∴ ★★★仕様は 届いていた が ★★構成の 是正には 繋がっていない（★★12時間 追随 0件）
★★★MGR は ★その仕様文書の 所在を 持っているはず ∴ ★★★まず それを 引く（★私は 中身を 読んでいない）。
```

## 5. ★★受入（★Taka の 完了条件を そのまま 使う・★足さない）

```
★★①General Manager の 職責が 確定（★★Taka §2 の 5段が そのまま 使えるか を 判定）
★★②Domain Manager の 母集団が ★★実態から 列挙（★★候補4つを 確定一覧に しない＝★Taka 明示）
★★③各 Domain と Worker の 境界が 確定（★★入力/出力/権限/状態/停止条件/上申条件 の 6欄）
★★④`manager_v0` が 吸収している ★★越境職責が ★★★全件（★★『主な物』では なく 全件）
★★⑤既存で 流用できる 部分と 新規が 要る 部分が 分離
★★⑥次に 実装する ★★最小の1件 が 特定

★★★出す物 = ★1枚の 表（★Taka §7 の 9欄を そのまま）
★★★この段階で 作らない = ★新しい Manager ／ ★新台帳 ／ ★新しい口
```

## 6. ★★注意（★★今回 特に 効く物）

```
★★[[absence-reads-as-compliance]]: ★★『service が 分かれている＝Domain Manager』と ★読まない
   ―― ★Taka §4 が ★名指しで 禁じている。
★★[[in-the-machine-or-delete-it]]: ★★『職責越境を 検出できるようにする』(★Taka §2)
   = ★★人の注意では なく ★機械で 出す形に する（★★でなければ また 太る）。
★★[[taka-skeleton-first-not-flesh]]: ★★実装より 先に 構造（★Taka §7）。
★★[[recycle-the-method-not-the-feature]]: ★DW の 役割分離（PLAN/GENERATE/AUDIT/UPPER_REVIEW/DISPOSE）は
   ★★既に 在る ∴ ★★★壊して 上から 被せない（★Taka §5・★明示）。
★★★本線（EVO-0058 経路表）との 関係 = ★★MGR が 決める
   ―― ★★但し ★経路表 Domain は ★Taka §4 で ★★先行実例に 指定されている
      ∴ ★★本線と 別物に しない 方が 筋（★★これは 私の 見立て・★数では ない）。
```
