# 確認シート M10（1回目）　確認日：2026-10-07（本人実行・合格の報告）

VS Code のターミナル（PowerShell）で、上から順にコマンドを貼り付けて実行してください。
文字化けするときは、先に `$env:PYTHONIOENCODING="utf-8"` と `[Console]::OutputEncoding=[Text.Encoding]::UTF8` を実行してください。

## 確認項目
| No | 確認項目 | やること | 期待する結果 | 結果（○／×） | 何をしたら、どうなったか（×のとき） |
|---|---|---|---|---|---|
| 1 | 自動テスト全件合格 | `.\.venv\Scripts\python.exe -m pytest` | 最後の行が「160 passed」（failed・error がない） | ○ | |
| 2 | 島しょ部などで座標系が正しく選ばれる（計画①） | `.\.venv\Scripts\python.exe -m pytest tests\test_prefectures.py -v` | `test_select_zone_locations PASSED`（東京の島・沖縄・鹿児島の島・北海道の25か所）と `test_real_data PASSED`（全国2,481基の内訳。SKIPPED ではない） | ○ | |
| 3 | 隣接県のデータを1つ外すと一覧が出て止まる（計画②） | 下の「No.3 のコマンド」を順に実行 | 「次のデータが足りません。…」の下に `海岸線 愛媛県（38）: data/raw/coastline/C23-*_38_GML/*_Coastline.shp` の1行だけが出て止まる。最後のコマンドでフォルダ名が `C23-06_38_GML` に戻っている | ○ | |
| 4 | 海のない県（長野）は海岸線を探さない（計画③） | 下の「No.4 のコマンド」を順に実行 | 1つ目：長野111基の標高を取得してエラーなく終わる（ネットへの問い合わせあり。数分の見込み・推測）。2つ目：「次のデータが足りません。…」の下に **河川** の9行（長野県（20）、群馬県（10）、埼玉県（11）、新潟県（15）、富山県（16）、山梨県（19）、岐阜県（21）、静岡県（22）、愛知県（23）の順）だけが出て、**海岸線の行が1行もない** | ○ | |

### No.3 のコマンド（愛媛の海岸線を一時的に外す → 実行 → 必ず戻す）
```
Rename-Item data\raw\coastline\C23-06_38_GML _C23-06_38_GML
.\.venv\Scripts\python.exe src\add_river_coast.py --pref 36
Rename-Item data\raw\coastline\_C23-06_38_GML C23-06_38_GML
Get-ChildItem data\raw\coastline -Name
```

### No.4 のコマンド
```
.\.venv\Scripts\python.exe src\add_elevation.py --pref 20
.\.venv\Scripts\python.exe src\add_river_coast.py --pref 20
```
- 補足：長野の隣接8県の河川データはまだ置いていないため、M10 では「海岸線を探さない」ことまでを確かめます。実データで海岸が「対象外（海のない県）」と表示されることは、自動テスト（test_no_sea_flag、No.1 に含む）で確認済みとし、長野の河川データを揃える M11 の通し実行でもう一度確かめます。

- 問題タブの件数：エラー0件（本人の「合格」の報告による。2026-10-07）
- Claude の追加確認：elevation_20.csv は111基すべて「取得済」（1m 109・5m 1・10m 1）。data/raw/coastline のフォルダ名は元どおり（C23-06_36〜39_GML）
- 気づいたこと・新しい要望（要望は「変更要求」として別扱いにします）：なし。計画③の実データでの「対象外」確認を M11 へ回すことを本人が了承（2026-10-07）
