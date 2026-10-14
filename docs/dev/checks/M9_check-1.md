# 確認シート M9（1回目）　確認日：2026-10-05

VS Code のターミナル（PowerShell）で、上から順にコマンドを貼り付けて実行してください。
`py` は `.\.venv\Scripts\python.exe` の略として書いています（そのまま `.\.venv\Scripts\python.exe` と打ってください）。

## 準備（念のための控え。1回だけ）
```
Copy-Item data\processed _to_delete\M9_before_processed -Recurse
Copy-Item output _to_delete\M9_before_output -Recurse
```

## 確認項目
| No | 確認項目 | やること | 期待する結果 | 結果（○／×） | 何をしたら、どうなったか（×のとき） |
|---|---|---|---|---|---|
| 1 | 全国の件数が元のCSVと一致 | `(Import-Csv data\raw\2026-09-24\denshouhi_20260924.csv -Encoding UTF8).Count` と `.\.venv\Scripts\python.exe src\load_monuments.py --pref all` | 1つ目が 2481。2つ目の最後に「県別のファイル: 47件」「全国の基数と県別ファイルの合計: 一致（2481基）」 | ○ | |
| 2 | 複数県を指定して取込できる | `.\.venv\Scripts\python.exe src\load_monuments.py --pref "03,20,28"` | 岩手 163基・長野 111基・兵庫 103基が出て、最後が「対象の県数: 3県　合計: 377基」 | ○ | |
| 3 | 誤った指定で止まる | `.\.venv\Scripts\python.exe src\load_monuments.py --pref 99` | 「エラー: --pref に使えない県コードがあります: 99（…）」と出て止まる | ○ | |
| 4 | 徳島の作り直し（第1版と同じ結果か） | 下の「No.4 のコマンド」を順に実行 | 5つともエラーなく終わる。ネットへの問い合わせは「0」の見込み。終わったら「実行した」と Claude に伝える（ハッシュ3件は Claude が確かめる） | ○ | |

### No.4 のコマンド（徳島：取込 → 比較地点 → ハザード判定（碑・比較地点）→ ハザードの集計）
```
.\.venv\Scripts\python.exe src\load_monuments.py --pref 36
.\.venv\Scripts\python.exe src\make_comparison_points.py --pref 36
.\.venv\Scripts\python.exe src\add_hazard.py --pref 36
.\.venv\Scripts\python.exe src\add_hazard.py --pref 36 --target points
.\.venv\Scripts\python.exe src\summarize_hazard.py --pref 36
```

- 問題タブの件数：エラー0件／警告0件（本人 2026-10-05）
- 気づいたこと・新しい要望（要望は「変更要求」として別扱いにします）：なし
- No.4 のハッシュ照合は Claude が実施（M9_review-1.md）
