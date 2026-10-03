# ソース確認 M3（1回目）　確認日：2026-09-30

- 確認範囲：15a8e43（M2 合格）からの差分＋影響範囲（src/add_river_coast.py、src/prefectures.py、src/add_elevation.py、tests/test_add_river_coast.py、tests/test_add_elevation.py、tests/test_load_monuments.py、requirements.txt）
- ファイルサイズ：報告・復元記録のとおり（0バイト・巻き戻りなし）
- 出力 river_coast_36.csv：71行、列は指示書どおり。河川コードは10桁の文字列、河川名の文字化けなし。「河川の標高なし」5基はいずれも河口付近で最近点が海・水面上（地理院の標高APIが「-----」を返す地点）であり、処理としては妥当

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | tests/test_add_river_coast.py 59–116行 | 指示書 11-e のテストが指示どおりでない。「碑 2.0m・河川 5.0m → −3.0m」を −1.5m に変えており、「河川の標高なし」「通信エラー」の場合が検査されていない | M3-02_fix |
| 2 | 中 | tests/test_add_river_coast.py 118–146行／src/add_river_coast.py 70–86行 | 指示書 11-f のテストが本体の読み込み処理を呼ばず、テスト内で同じ処理を書き直している（本体が壊れても合格してしまう）。読み込み処理が関数に分かれていない（指示書 手順10） | M3-02_fix |
| 3 | 軽微 | src/add_river_coast.py 3–4行・57行 | 使っていない import（datetime 以外の math・glob）と変数 p1 | M3-04 |
| 4 | 軽微 | src/add_river_coast.py 13–14行 | warnings.filterwarnings("ignore") で全ての警告を消している。座標系の不一致などの警告も見えなくなる | M3-04 |
| 5 | 軽微 | docs/dev/reports/M3-01_report.md | AGENTS.md の「ファイル名とバイト数」の一覧がない | M3-02_fix で記載させる |

## 判定：不合格（修正1回目）
- 本体の処理結果は実データで妥当。不足はテストの2点（No.1・2）で、1テーマ（テストを指示書どおりにする）として M3-02_fix にまとめる
- 地形分類は M3-04_impl に番号を繰り下げる（2026-09-30 CR-1 により M3-03 から変更）
