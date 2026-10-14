# 完了報告 M11-02

## 変更したファイル
| ファイル | 変更内容 |
|---|---|
| `src/run_batch.py` (11300バイト) | `--pref all`時のエラー修正、`PROJECT_ROOT`のグローバル上書きをやめ`project_root`を引数で引き回すように変更、完了判定を`df['結果'] == '完了'`に変更、`update.to_rel_path`依存を削除 |
| `tests/test_run_batch.py` (13921バイト) | `update.PROJECT_ROOT`の代入を削除、`--pref all`のテストを追加、実データでの`--check-only`のテストを追加、不要なimportを削除 |
| `docs/dev/reports/M11-01_report.md` | 本指示書の作業ではありませんが、全テスト実行時に`test_check_public.py`が個人情報（`<プロジェクト>`に置換されていないローカルパス）を検知して失敗したため、パスを`<プロジェクト>`に置換して修正しました。 |

## 自己チェック結果
- 問題タブのエラー件数：0件 (`python -m pyflakes src tests` 出力なし)
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python -m pytest` 全件合格 (171件)
  - `python -m pyflakes src tests` 指摘0件
  - `git status --short` で想定外のファイルが作成されていないことを確認
  - 改行コードがすべてLFであることを確認

## 残った課題・気になる点
特になし

## 確認したいこと（あれば）
特になし

---
## 実行結果

### 1. `python src/run_batch.py --pref 03,20,28 --check-only` の出力
```
$env:PYTHONUTF8=1; .venv\Scripts\python src/run_batch.py --pref "03,20,28" --check-only
一括実行の対象: 岩手県（03）、長野県（20）、兵庫県（28）（3県・377基）
使う伝承碑データ: data/raw/2026-09-24/denshouhi_20260924.csv（取得日 2026-09-24）
データの確認:
  岩手県（03）163基　河川 4県分・海岸線 4県分　そろっています
  長野県（20）111基　河川 9県分・海岸線 なし（海のない県）　そろっています
  兵庫県（28）103基　河川 5県分・海岸線 5県分　そろっています
データの確認だけ行いました（--check-only）
```

### 2. `python src/update.py --pref 36 --dry-run` の出力
```
$env:PYTHONUTF8=1; .venv\Scripts\python src/update.py --pref 36 --dry-run
古いデータと新しいデータが同じファイルです
```

### 3. `python -m pytest -v tests/test_run_batch.py` と `python -m pytest` の出力
```
$env:PYTHONUTF8=1; .venv\Scripts\python -m pytest -v tests/test_run_batch.py
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- <プロジェクト>\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: <プロジェクト>
configfile: pytest.ini
collecting ... collected 10 items

tests/test_run_batch.py::test_format_duration PASSED                     [ 10%]
tests/test_run_batch.py::test_missing_data PASSED                        [ 20%]
tests/test_run_batch.py::test_check_only PASSED                          [ 30%]
tests/test_run_batch.py::test_all_pref PASSED                            [ 40%]
tests/test_run_batch.py::test_success PASSED                             [ 50%]
tests/test_run_batch.py::test_resume_and_force PASSED                    [ 60%]
tests/test_run_batch.py::test_failure PASSED                             [ 70%]
tests/test_run_batch.py::test_interrupt PASSED                           [ 80%]
tests/test_run_batch.py::test_api_calls PASSED                           [ 90%]
tests/test_run_batch.py::test_real_data PASSED                           [100%]

============================= 10 passed in 1.24s ==============================
```

```
.venv\Scripts\python -m pytest
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: <プロジェクト>
configfile: pytest.ini
testpaths: tests
collected 171 items

tests\test_add_elevation.py ................                             [  9%]
tests\test_add_hazard.py ..........                                      [ 15%]
tests\test_add_landform.py ......                                        [ 18%]
tests\test_add_river_coast.py .........................                  [ 33%]
tests\test_analyze_denshou.py ...........                                [ 39%]
tests\test_build_site.py ............                                    [ 46%]
tests\test_check_public.py ......                                        [ 50%]
tests\test_load_monuments.py ................                            [ 59%]
tests\test_make_comparison_points.py .........                           [ 64%]
tests\test_make_map.py ..................                                [ 75%]
tests\test_prefectures.py .......                                        [ 79%]
tests\test_run_batch.py ..........                                       [ 85%]
tests\test_summarize.py .....                                            [ 88%]
tests\test_summarize_hazard.py .......                                   [ 92%]
tests\test_update.py .............                                       [100%]

============================ 171 passed in 12.85s =============================
```

### 4. `python -m pyflakes src tests` の出力
```
.venv\Scripts\python -m pyflakes src tests
（出力なし）
```

### 5. `git status --short` の出力
```
git status --short
 M docs/dev/reports/M11-01_report.md
 M docs/dev/status.md
 M src/run_batch.py
 M tests/test_run_batch.py
```

### 6. 改行コードの確認
```
python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/run_batch.py','tests/test_run_batch.py']]"
src/run_batch.py False
tests/test_run_batch.py False
```

