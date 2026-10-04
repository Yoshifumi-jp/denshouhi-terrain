# 指示書 M8-05（修正・集計表のテストの行の順と移転碑の確認）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください。

## 目的（このテーマ1つ）
tests/test_summarize_hazard.py の test_d_e_f_g_main に、行の順と移転碑そのものの除外の確認を入れる。**本体（src/）・出力（output/）・tests/test_add_hazard.py は変えない。**

## 対象ファイル
- tests/test_summarize_hazard.py（test_d_e_f_g_main だけ）

## 不具合の内容（M8_review-4）
- 起きていること：Claude が本体をわざと壊して試すと、「ハザードの並び順を逆にする」「範囲（全碑／移転碑を除く）の順を逆にする」をテストが見逃した。実データのテストを外すと「移転碑そのものを除かない」も見逃した
- 原因の見立て：「# g」の確認が列名（df.columns[:3]）だけになっている。M8-04 で row_t_ex の 碑_数 の確認を消した

## やること
1. 「# g」の `assert list(df.columns[:3]) == [...]` を次に置き換える。偽データ（make_fake_data）で出る全行の 範囲・災害種別・ハザード の3列を、期待する並びのリストと **そのまま** 比べる
   ```python
   # g 行の順：範囲 → 災害種別 → ハザード
   hazards = ['洪水（想定最大規模）', '津波', '高潮', '土砂災害']
   expected = []
   for r, types in [('全碑', ['全種別', '洪水', '地震', '津波']), ('移転碑を除く', ['全種別', '地震', '津波'])]:
       for t in types:
           for h in hazards:
               expected.append([r, t, h])
   assert df[['範囲', '災害種別', 'ハザード']].values.tolist() == expected
   ```
   （移転碑を除くと碑1が除かれ、洪水の碑が0基になるため「移転碑を除く・洪水」の行は出ない。もし実際の出力がこのリストと違ったら、テストを合わせず、報告書の「確認したいこと」に書いて止まる）
2. 移転碑を除く の確認に、次の2行を加える（M8-04 で消した確認を戻す）
   ```python
   row_t_ex2 = df[(df['範囲'] == '移転碑を除く') & (df['災害種別'] == '津波') & (df['ハザード'] == '津波')].iloc[0]
   assert row_t_ex2['碑_数'] == 1
   ```

## やらないこと
- 上の2つ以外の変更。作業用スクリプトの作成

## 完成の条件
- `python -m pytest -q` 全件合格（120件）、問題タブ エラー0件
- src/・output/・tests/test_add_hazard.py に変更なし（git status で確認）

## 完了後
- docs/dev/reports/M8-05_report.md に報告を書く（_template.md の書式）。全体の `python -m pytest -q` の最後の行を画面に出たとおりそのまま貼る。変更したファイルをバイト数つきで書く
