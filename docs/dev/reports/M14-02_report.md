# 完了報告 M14-02

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| tests/test_make_map.py | 21873 | test_real_hazard_popup のハザード取得日期待値を hazard_36.csv から動的に取得して比較するように修正（YYYY-MM-DD 形式のアサーション含む） |
| tests/test_build_site.py | 24057 | test_real_hazard_table のハザード取得日期待値を hazard_36.csv から動的に取得して比較するように修正（YYYY-MM-DD 形式のアサーション含む） |
| docs/dev/reports/M14-02_report.md | 3430 | 本完了報告 |

## 指示された実行結果

### 1. `python -m pytest -q`（最後の行）
```
196 passed in 404.32s (0:06:44)
```

### 2. `python -m pytest -q tests/test_make_map.py::test_real_hazard_popup tests/test_build_site.py::test_real_hazard_table`（最後の行）
```
2 passed in 1.19s
```

### 3. `git diff -w tests/`
```
diff --git a/tests/test_build_site.py b/tests/test_build_site.py
index 9671ab2..0142146 100644
--- a/tests/test_build_site.py
+++ b/tests/test_build_site.py
@@ -332,7 +332,11 @@ def test_real_hazard_table(tmp_path):
         ['土砂災害', '31%（22／71基）', '9%（30／349点）', '—', '—'],
     ]
     assert rows == expected_rows
-    assert "ハザード情報取得日：2026-10-14" in idx_text
+    hazard_file = proj_root / "data" / "processed" / "hazard_36.csv"
+    df_haz = pd.read_csv(hazard_file, dtype=str, encoding='utf-8-sig')
+    exp_date = df_haz['取得日'].dropna().max()
+    assert re.match(r'^\d{4}-\d{2}-\d{2}$', exp_date)
+    assert f"ハザード情報取得日：{exp_date}" in idx_text
 
 def test_back_to_index_link(tmp_path):
     out_dir = create_fake_output(tmp_path, "36")
diff --git a/tests/test_make_map.py b/tests/test_make_map.py
index 6c387d9..eb3f7e9 100644
--- a/tests/test_make_map.py
+++ b/tests/test_make_map.py
@@ -406,7 +406,11 @@ def test_real_hazard_popup():
         row = mon_df[mon_df['ID'] == mon_id].iloc[0]
         assert make_map.make_hazard_lines(row) == exp_lines
         
-    assert mon_df['ハザード取得日'].dropna().max() == '2026-10-04'
+    import re
+    df_haz = pd.read_csv(hazard_file, dtype=str, encoding='utf-8-sig')
+    exp_date = df_haz['取得日'].dropna().max()
+    assert re.match(r'^\d{4}-\d{2}-\d{2}$', exp_date)
+    assert mon_df['ハザード取得日'].dropna().max() == exp_date
 
 def test_legend_details_position(tmp_path, monkeypatch):
     monkeypatch.setitem(make_map.PREFECTURES, '99', 'テスト県')
```

### 4. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['tests/test_make_map.py','tests/test_build_site.py']]"`
```
tests/test_make_map.py False
tests/test_build_site.py False
```

### 5. 変更した2ファイルのバイト数
```
tests/test_make_map.py: 21873 bytes
tests/test_build_site.py: 24057 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. `python -m pytest -q` が全件合格（196 passed）：確認済み
  2. `python -m pyflakes tests/test_make_map.py tests/test_build_site.py` 0件、LF：確認済み
  3. `git diff -w tests/` が上の2か所（＋日付を求める数行）だけ：確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
