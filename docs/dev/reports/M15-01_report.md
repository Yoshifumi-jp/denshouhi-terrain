# 完了報告 M15-01

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| `src/add_landform_region.py` | 新規作成：地形分類の地域版（z=13、中分類）・広域版（z=8、大分類）を碑・比較地点に付与するプログラム（LF） | 11,522 |
| `tests/test_add_landform_region.py` | 新規作成：`src/add_landform_region.py` の単体テストおよび実データ照合テスト（計14件、LF） | 17,082 |
| `data/processed/landform_region_36.csv` | 実行により生成：徳島県（36）の碑の地域版・広域版地形分類データ（LF） | 7,759 |
| `data/processed/landform_region_points_36.csv` | 実行により生成：徳島県（36）の比較地点の地域版・広域版地形分類データ（LF） | 33,225 |
| `data/processed/landform_region_03.csv` | 実行により生成：岩手県（03）の碑の地域版・広域版地形分類データ（LF） | 18,283 |
| `data/processed/landform_region_points_03.csv` | 実行により生成：岩手県（03）の比較地点の地域版・広域版地形分類データ（LF） | 81,445 |
| `data/processed/landform_region_35.csv` | 実行により生成：山口県（35）の碑の地域版・広域版地形分類データ（LF） | 3,440 |
| `data/processed/landform_region_points_35.csv` | 実行により生成：山口県（35）の比較地点の地域版・広域版地形分類データ（LF） | 15,087 |
| `docs/dev/reports/M15-01_report.md` | 新規作成：本完了報告書（LF） | - |

## 自己チェック結果
- 問題タブのエラー件数：0件（`pyflakes src/add_landform_region.py tests/test_add_landform_region.py` 指摘0件）
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - 6 の6回の実行結果・7 の再実行結果が指示書の既知の答えと全件一致することを確認
  - 実データでの照合テスト（8件）を含む `pytest` 全238件合格を確認
  - 既存ファイルに変更がないこと、新規作成・出力ファイルの改行コードがすべて LF（`\r` が 0）であることを確認

### 6. 3県（碑・比較地点）の実行結果（まとめ表示）

#### (1) `python src/add_landform_region.py --pref 36`
```text
対象件数: 71
  取得済（地域版）: 69件
  取得済（広域版）: 0件
  データなし: 2件
  取得不可: 0件
問い合わせ回数: 33
キャッシュから読んだ回数: 0
表にないcodeの件数: 0
地形分類名ごとの件数:
  低地: 44件
  山地: 24件
  台地・段丘: 1件
```

#### (2) `python src/add_landform_region.py --pref 36 --target points`
```text
対象件数: 349
  取得済（地域版）: 343件
  取得済（広域版）: 0件
  データなし: 6件
  取得不可: 0件
問い合わせ回数: 33
キャッシュから読んだ回数: 33
表にないcodeの件数: 0
地形分類名ごとの件数:
  山地: 221件
  低地: 112件
  丘陵・小起伏地: 8件
  台地・段丘: 2件
```

#### (3) `python src/add_landform_region.py --pref 03`
```text
対象件数: 163
  取得済（地域版）: 163件
  取得済（広域版）: 0件
  データなし: 0件
  取得不可: 0件
問い合わせ回数: 64
キャッシュから読んだ回数: 0
表にないcodeの件数: 0
地形分類名ごとの件数:
  低地: 62件
  山地: 46件
  丘陵・小起伏地: 42件
  台地・段丘: 13件
```

#### (4) `python src/add_landform_region.py --pref 03 --target points`
```text
対象件数: 815
  取得済（地域版）: 798件
  取得済（広域版）: 0件
  データなし: 17件
  取得不可: 0件
問い合わせ回数: 53
キャッシュから読んだ回数: 64
表にないcodeの件数: 0
地形分類名ごとの件数:
  山地: 360件
  丘陵・小起伏地: 243件
  低地: 115件
  台地・段丘: 80件
```

#### (5) `python src/add_landform_region.py --pref 35`
```text
対象件数: 31
  取得済（地域版）: 31件
  取得済（広域版）: 0件
  データなし: 0件
  取得不可: 0件
問い合わせ回数: 22
キャッシュから読んだ回数: 0
表にないcodeの件数: 0
地形分類名ごとの件数:
  低地: 16件
  山地: 9件
  丘陵・小起伏地: 3件
  台地・段丘: 2件
  火山地形（やや不明瞭）: 1件
```

#### (6) `python src/add_landform_region.py --pref 35 --target points`
```text
対象件数: 155
  取得済（地域版）: 151件
  取得済（広域版）: 0件
  データなし: 4件
  取得不可: 0件
問い合わせ回数: 25
キャッシュから読んだ回数: 20
表にないcodeの件数: 0
地形分類名ごとの件数:
  山地: 91件
  低地: 35件
  丘陵・小起伏地: 16件
  残丘状地形: 5件
  台地・段丘: 3件
  火山地形（やや不明瞭）: 1件
```

### 7. 再実行（`python src/add_landform_region.py --pref 36`）のまとめ表示
```text
対象件数: 71
  取得済（地域版）: 69件
  取得済（広域版）: 0件
  データなし: 2件
  取得不可: 0件
問い合わせ回数: 0
キャッシュから読んだ回数: 33
表にないcodeの件数: 0
地形分類名ごとの件数:
  低地: 44件
  山地: 24件
  台地・段丘: 1件
```

### 8. `python -m pytest -q` の結果
```text
........................................................................ [ 30%]
........................................................................ [ 60%]
........................................................................ [ 90%]
......................                                                   [100%]
238 passed in 396.33s (0:06:36)
```

### 9. 改行コードの確認と `git status --short` の出力
```text
src/add_landform_region.py 0
tests/test_add_landform_region.py 0
data/processed\landform_region_03.csv 0
data/processed\landform_region_35.csv 0
data/processed\landform_region_36.csv 0
data/processed\landform_region_points_03.csv 0
data/processed\landform_region_points_35.csv 0
data/processed\landform_region_points_36.csv 0
?? src/add_landform_region.py
?? tests/test_add_landform_region.py
```

## 残った課題・気になる点
- なし

## 確認したいこと（あれば）
- なし

