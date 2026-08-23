候補1 参照抽出の欠陥修正 before/after (6指標)

母集団: 構造化行(最新ts版) 1,169行 / 132 thread

■ occurrence 単位 (既知値 file偽陽性23/34・symbolマーカー由来727/735 と同じ鍵)
  kind      before  after  実在率(前→後)   マーカー由来率(前→後)
  file          97     66  0.619 → 0.879   0.330 → 0.000
  symbol       736     11  0.071 → 0.818   0.986 → 0.000
  2der_id      125    125  0.984 → 0.984   除去0 (SUPERSEDES の正当refを保った)
  api            3      3  1.000 → 1.000   除去0

■ 既知の偽陽性の除去率
  file 非実在 37 → 8   除去 29/37 = 0.784
  symbol マーカー由来 725/727 = 0.997 を除去
    (残る2件は PROGRESS マーカー内 = 人が書いた文 → 意図して残した)

■ 既知の正当refの recall
  出所を鍵にした場合: 205/205 = 1.000
  実在を鍵にした場合: 44/45 = 0.978 (1件 rri/intent_record.py が落ちた)
  ★原因分離: その1件は IMMUTABLE_TESTS 内の生成試験コードのリテラル2箇所のみ。
    依頼文には1件も現れない。∴ 実在するが依頼由来ではない = 落として正しい。
    ★除外規則は広げていない(SKELETON / IMMUTABLE_TESTS の2種のまま)。
    ★recall の鍵として「実在」を使ったのが誤り。正しい鍵は「出所」。

■ 残った非実在(候補1の対象外・別原因)
  file 8件: これから作る予定(twoder/turn_overtaken.py) / 置換子(twoder/X.py) /
            repo境界(workcell.py) / 抽出器の切り出しずれ(s_*.py 4件)
  symbol 2件: classify_account(未実装の予定) / test_(★接頭辞だけの抽出器バグ)

■ symbol を A4 入力へ戻すか → 戻さない(推奨)
  精度は 0.071 → 0.818 に回復した。しかし A4 は「TASK 間で共有される鍵」で似ているかを見る。
  ★2 thread 以上で共有される symbol = 0件。
   (対照: file は 9件・37 thread=28.0% を覆う / symbol は 7 thread=5.3%)
  ∴ 戻しても類似度への寄与は数学的に 0。精度不足ではなく厚み不足が理由。
  ★自動復帰させていない。REF_KINDS_EXCLUDED は ("symbol",) のまま。

■ 触っていないもの
  台帳の refs 履歴 / 既定 skip_generated=False (従来と完全に同じ返り)
