# 設計プラン: RTHREAD stage 2b 作り直し — 凍結軸(Frozenset)+ 多重所属 + 濃淡観測 + その他

- 起草: 設計/監査(CC-α)/ 2026-07-25 / 正本: `RRI_SPEC_MACHINE_v1_1.json` + Taka 方針(2026-07-24/25)
- 前提: 決定論素性マイニングは NO_STABLE(DE-0521)。前回の「場(field)化+mass保存」案は Taka 否定(筋が悪い)。

## §0. 合意した形(Taka 訂正の反映)
- **勘定科目 = ベクトルから自然抽出され Frozenset として凍結される離散な軸。** ベクトルの利得は fuzzy 化でなく**「科目を定義する作業から抜ける」**(軸がデータから落ちる→凍結→いじらない)。
- **要素は A and B(多重所属)可**。A or B の強制をしない。
- **濃淡(density)はそれ自体を観測量として表示**(橋渡し項の信号)。曖昧を解消するために凍結軸を再定義しない。
- **その他/未定(UNCLASSIFIED)**=どっちにもつかないものの受け皿(会計の「その他」)。
- **hard 不変量は問い台帳(stage1 I1=ゼロ落ち禁止・一度だけ処分)のみ。account 次元は soft。** 前回私が account に mass 保存を課したのは誤り→取り下げ済み。
- **密度は最後まで advisory・何も gate しない(T26)。**

## §1. 埋め込み源の決定 → 案C(CPU 埋め込み)採用(Taka 方針「CPU で代替できるなら」実現可能を確認)
**実測(2026-07-25):** GPU0 31.8/32.6GB・GPU1 31.2/32.6GB(空き 0.8〜1.4GB)、:8005 は chat 専用(`/v1/embeddings` 無し)、ローカル embedding 重み無し。**`torch 2.9`(CPU 可)+ `transformers 4.53` 実在**。スリープは DE-0086/0168/0170 に hang/VRAM 履歴=筋が悪い。
- **案C(採用): CPU で小型多言語 embedding モデル。** GPU 競合ゼロ・スリープ不要・:8005 不要(USE_VLLM_INFERENCE gate にも触れない)・**案A のタグ・ベクトル化より密な意味ベクトル**。corpus ~1215 件・短文 → CPU で数分。決定論(モデル pin + eval)。モデル=`intfloat/multilingual-e5-small`(384d・多言語=日本語含む・~470MB)を pin、初回 DL のみ(GPU/serve 不要の acquisition)。
- 案A(:8005 タグ・ベクトル化)/ 案B(GPU embedding serve)は案C が回らない時の fallback。スリープは最後。
- → **案C で進める**(GPU に触れず本物の意味ベクトルで「軸が出るか」を測れる)。

## §2. スライス構造(measure-first。前回同様、出なければ「出ない」を正当な結果に)
- **2b-r1(経験的テスト=最初のスライス):** :8005 分類→タグ・ベクトル化→**安定な密方向(軸候補)が在るか**を決定論抽出で測る。**負の制御(タグ shuffle→崩壊)/ cross-seed 安定 / byte一致抽出**、構造素性 NO_STABLE をベースラインに比較。
  - 出口: (i) K 個の安定軸が出る→**Frozenset 候補として凍結**へ / (ii) 拡散・軸ほぼ無し→**その他優勢=正当な初期状態**(実運用で話題が積もると結晶、を後で)。
- **2b-r2(軸が出た時のみ): 凍結 + 多重所属 + 濃淡。** 抽出軸を versioned Frozenset `ACCOUNT_AXES` に凍結。各問いに**軸ごとの密度**(多重所属可)+ 全軸で閾値未満なら**その他**。密度を観測量として projection に出す(gate しない)。
- **2b-r3: 再凍結規律。** その他が育って濃い方向を持ったら**稀に・意図的に・versioned で新軸を追加凍結**(早すぎ凍結=ノイズ / 凍結せず=churn を両避)。初版 promotion(T22)の軸版。

## §3. 規律
- **軸は抽出後に凍結・drift させない**(定義労働から抜ける)。多重所属可。濃淡=観測量。曖昧→その他。
- **hard は問い台帳 I1 のみ**。account 密度に保存則を課さない。
- **密度・embedding/タグは advisory・gate/branch/transition に入れない(T26)。**
- **measure-first**: 軸が在ると仮定しない。無ければ「その他優勢」を DE 化(前回 NO_STABLE と同じ retention)。
- :8005 実行は USE_VLLM_INFERENCE=Taka gate(energize 時)。

## §4. 要 Taka 判断
埋め込み源 = **案A(:8005 分類のベクトル化・新 infra 無し)で良いか**。良ければ 2b-r1 の spec を起こして実装へ。案B(embedding モデル serve)を望むなら GPU 検証から。
