# 完了報告 M14-06

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/update_all.py | 17669 | 「県の作り直し」コマンドへの --force 追加、get_prefs_for_site_build での reset_index(drop=True) 追加 |
| tests/test_update_all.py | 23317 | test_2・test_6 の期待値更新（--force 対応）、test_8（前回失敗時の --force 再構築検証）・test_9（空行混在時の site_build 対象判定検証）の追加 |
| docs/dev/reports/M14-06_report.md | 4052 | 本報告書 |

## 指示された実行結果

### 1. `git diff src/update_all.py`
```diff
diff --git a/src/update_all.py b/src/update_all.py
index a724940..06e7e2b 100644
--- a/src/update_all.py
+++ b/src/update_all.py
@@ -182,7 +182,7 @@ def get_prefs_for_site_build(rebuild_pref_codes, update_history_all_path):
     if update_history_all_path.exists():
         try:
             df_hist = pd.read_csv(update_history_all_path, encoding="utf-8-sig", dtype=str)
-            df_hist = df_hist.dropna(how="all")
+            df_hist = df_hist.dropna(how="all").reset_index(drop=True)
             if not df_hist.empty:
                 completed_indices = df_hist.index[df_hist["結果"] == "完了"].tolist()
                 if completed_indices:
@@ -386,7 +386,7 @@ def main(args=None, runner=None, root=None, now=None):
     if rebuild_codes:
         steps.append((
             f"県の作り直し（{len(rebuild_codes)}県）",
-            [sys.executable, str(root / "src" / "run_batch.py"), "--pref", ",".join(rebuild_codes)]
+            [sys.executable, str(root / "src" / "run_batch.py"), "--pref", ",".join(rebuild_codes), "--force"]
         ))
 
     steps.append((
```

### 2. `python src/update_all.py --dry-run` と、その前後の `git status --short`

- `--dry-run` の直前の `git status --short`:
```
 M src/update_all.py
 M tests/test_update_all.py
```

- `python src/update_all.py --dry-run`:
```
全国の更新：使う伝承碑データ data/raw/2026-09-24/denshouhi_20260924.csv（取得日 2026-09-24、2,481基・47都道府県）
県ごとの判定：
  最新で作成済み：47県
  変更なし（作り直しません）：0県
  作り直す：0県
全国のページ：作り直します（全国の作り直しの記録がないため）
確認だけ行いました（--dry-run）。何も書き込んでいません
```

- `--dry-run` の直後の `git status --short`:
```
 M src/update_all.py
 M tests/test_update_all.py
```

### 3. `python -m pytest -q`（最後の行）、`python -m pytest -q tests/test_update_all.py`（最後の行）、`python -m pyflakes src/update_all.py tests/test_update_all.py`

- `python -m pytest -q`（最後の行）：
```
215 passed in 866.29s (0:14:26)
```

- `python -m pytest -q tests/test_update_all.py`（最後の行）：
```
9 passed in 2.83s
```

- `python -m pyflakes src/update_all.py tests/test_update_all.py`：
```
（出力なし、0件）
```

### 4. 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/update_all.py','tests/test_update_all.py']]"`
```
src/update_all.py False
tests/test_update_all.py False
```

### 5. 変更したファイルのバイト数
```
src/update_all.py: 17669 bytes
tests/test_update_all.py: 23317 bytes
docs/dev/reports/M14-06_report.md: 4052 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. `python src/update_all.py --dry-run` の表示が M14-05 の報告と同じ7行で、実行前後で git status が変わらないこと：確認済み
  2. pytest 全件合格（215件）、pyflakes 0件、LF であること：確認済み
  3. git diff は src/update_all.py と tests/test_update_all.py だけであること：確認済み
  4. 作成・変更した各ファイルが空（0バイト）でないこと：確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
