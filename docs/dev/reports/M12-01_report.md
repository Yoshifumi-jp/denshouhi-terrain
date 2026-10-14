# 完了報告 M12-01

## 変更・作成したファイルとバイト数
- src/progress.py (新規, 903 bytes)
- src/add_hazard.py (変更, 13596 bytes)
- src/add_landform.py (変更, 9072 bytes)
- tests/test_progress.py (新規, 884 bytes)
- tests/test_add_hazard.py (変更, 18343 bytes)
- tests/test_add_landform.py (変更, 10357 bytes)

## 1. pytest の出力
```
> python -m pytest -v tests/test_progress.py tests/test_add_hazard.py tests/test_add_landform.py
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- <プロジェクト>\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: <プロジェクト>
configfile: pytest.ini
collecting ... collected 21 items

tests/test_progress.py::test_format_elapsed PASSED                       [  4%]
tests/test_progress.py::test_should_print PASSED                         [  9%]
tests/test_progress.py::test_progress_line PASSED                        [ 14%]
tests/test_add_hazard.py::test_lonlat_to_pixel PASSED                    [ 19%]
tests/test_add_hazard.py::test_classify_pixel_shinsui PASSED             [ 23%]
tests/test_add_hazard.py::test_classify_pixel_dosha PASSED               [ 28%]
tests/test_add_hazard.py::test_summarize_dosha PASSED                    [ 33%]
tests/test_add_hazard.py::test_cache_and_fetch PASSED                    [ 38%]
tests/test_add_hazard.py::test_main_execution PASSED                     [ 42%]
tests/test_add_hazard.py::test_main_errors PASSED                        [ 47%]
tests/test_add_hazard.py::test_main_sys_argv PASSED                      [ 52%]
tests/test_add_hazard.py::test_launch_method PASSED                      [ 57%]
tests/test_add_hazard.py::test_real_cache PASSED                         [ 61%]
tests/test_add_hazard.py::test_progress_output PASSED                    [ 66%]
tests/test_add_landform.py::test_lonlat_to_tile PASSED                   [ 71%]
tests/test_add_landform.py::test_no_duplicate_codes_in_mapping PASSED    [ 76%]
tests/test_add_landform.py::test_process_monuments PASSED                [ 80%]
tests/test_add_landform.py::test_gzip_response PASSED                    [ 85%]
tests/test_add_landform.py::test_pref_validation PASSED                  [ 90%]
tests/test_add_landform.py::test_cache_untouched PASSED                  [ 95%]
tests/test_add_landform.py::test_progress_output PASSED                  [100%]

============================= 21 passed in 2.70s ==============================

> python -m pytest
（省略）
============================ 176 passed in 34.08s =============================
```
※テスト関数の数は171件から176件に5件増加しました（test_progress.pyの3件 ＋ test_add_hazard.pyの1件 ＋ test_add_landform.pyの1件）。増えた件数と一致しています。

## 2. test_real_cache の「進捗」8行
```
> python -m pytest -s tests/test_add_hazard.py -k real_cache
  進捗 ハザード（碑） 10/71（14%）経過 0分00秒　問い合わせ 0枚・キャッシュ 60枚
  進捗 ハザード（碑） 20/71（28%）経過 0分00秒　問い合わせ 0枚・キャッシュ 114枚
  進捗 ハザード（碑） 30/71（42%）経過 0分00秒　問い合わせ 0枚・キャッシュ 150枚
  進捗 ハザード（碑） 40/71（56%）経過 0分00秒　問い合わせ 0枚・キャッシュ 192枚
  進捗 ハザード（碑） 50/71（70%）経過 0分00秒　問い合わせ 0枚・キャッシュ 234枚
  進捗 ハザード（碑） 60/71（84%）経過 0分00秒　問い合わせ 0枚・キャッシュ 252枚
  進捗 ハザード（碑） 70/71（98%）経過 0分00秒　問い合わせ 0枚・キャッシュ 294枚
  進捗 ハザード（碑） 71/71（100%）経過 0分00秒　問い合わせ 0枚・キャッシュ 300枚
```

## 3. pyflakes の出力
```
> python -m pyflakes src tests
```
(指摘0件)

## 4. git status --short の出力
```
> git status --short
 M docs/dev/01_plan.md
 M docs/dev/status.md
 M src/add_hazard.py
 M src/add_landform.py
 M tests/test_add_hazard.py
 M tests/test_add_landform.py
?? docs/dev/instructions/M12-01_impl.md
?? docs/dev/m12_downloads.md
?? src/progress.py
?? tests/test_progress.py
```

## 5. 改行コードの確認
```
> python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/progress.py','src/add_hazard.py','src/add_landform.py','tests/test_progress.py','tests/test_add_hazard.py','tests/test_add_landform.py']]"
src/progress.py False
src/add_hazard.py False
src/add_landform.py False
tests/test_progress.py False
tests/test_add_hazard.py False
tests/test_add_landform.py False
```

