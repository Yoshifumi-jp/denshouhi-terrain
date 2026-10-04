# 完了報告 F-01

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/add_hazard.py | 13466 | print文の県名から「県」1文字を削除 |
| tests/test_add_hazard.py | 17207 | test_real_cacheに「徳島県」の出力を確認するassertを1行追加 |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：すべて満たしている

### 3. 改行コードの確認
```
src\add_hazard.py False
tests\test_add_hazard.py False
```

### 4. pytest の最後の行
```
============================ 134 passed in 11.98s =============================
```

### 5. ハッシュ値の確認
```
9a96085d74dcb2a6 hazard_summary_36.csv
b191e3742645ec6c hazard_36.csv
99c87b0ba59527e8 hazard_points_36.csv
```

### 6. git status の確認
```
 M docs/dev/status.md
 M src/add_hazard.py
 M tests/test_add_hazard.py
?? docs/dev/instructions/F-01_fix.md
```

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
