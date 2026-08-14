宛: DESIGN ／ 写: MGR ／ 発: Taka ／ 2026-08-14 19:1x ／ 台帳: `ITEM-2DER-EVO-0058`

**★これは Taka 正本。★本文を書き換えない。**（MGR は受領・登記・点検のみ）

★一文定義（§13）
  Route Worker = 2DERで実際に何がどこからどこへ通ったかを、証拠付きで観測・更新する機構。
  Manager      = 2DERが実際に行ったことと、本来行うべきことを比較し、次に何をすべきかを決める機構。
  境界         = 経路表は事実を言う。Manager はその事実の意味を判断する。

★最重要原則（§0）
  経路表は「実際にどう通ったか」を扱う。Manager は「それで正しいか」を扱う。
  Route Worker にシステム全体の正しさを判断させない。

★Route Worker が確認するもの（§2.1）= A 経路の存在 ／ B 両側証拠（handed_to・received_from）／
  C 実通過 ／ D 観測可能性 ／ E 再確認可能性
★Route Worker が判断してはいけないもの（§3）= 期待された機能か ／ 結果が正しいか ／
  この機能は必要か ／ 他機能との連動が正しいか ／ 全体目的との整合性
★出力は事実状態に限定（§4）= OBSERVED_BOTH_SIDES / OBSERVED_SENDER_ONLY / OBSERVED_RECEIVER_ONLY /
  PASSABLE / NOT_PASSABLE / NO_RECORD / UNKNOWN ／ ★PASSABLE ≠ CORRECT
★Expected と Observed を混ぜない（§6）
★Push と Pull の両方を使う（§7）―― どちらも責務境界を越えない
★完成条件（§11）= ①実行から経路証拠が自動で残る ②両側証拠から区間を自動生成 ③未登録区間を自動検出
  ④既存権限規則で許された区間を自動登録 ⑤人間が登録操作をしなくてよい
  ⑥Pull で経路表と実記録の差分を自動検出 ⑦Worker は「正しい機能か」まで判断しない
  ⑧Manager が後から Expected / Observed を比較できる
★実装上の制約（§12）= Route Worker に Manager の責務を追加しない ／
  迷ったら「実際に何が起きたか？」→ Route Worker ／「それで正しいのか？」→ Manager ／
  新機能の前に既存を確認する ／「見つからなかった」と「存在しない」を同一視しない ／
  ★経路表を作った後に人間が更新を忘れる構造は完成とみなさない

（★全文は Taka の投稿を逐語で台帳 `ITEM-2DER-EVO-0058` に登記した）
