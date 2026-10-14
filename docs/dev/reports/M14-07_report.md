# 完了報告 M14-07

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/check_public.py | 10370 | collect_targets に data/raw 直下の .csv および .agents を追加。find_private_info に PDF（stream〜endstream 除去、/Author 検出）および PNG（tEXt/zTXt/iTXt チャンク解析）の検査を追加 |
| src/build_national.py | 41636 | quiet=True の場合でも公開前チェックを実施し、問題があれば RuntimeError("公開前チェック：問題あり（<件数>件）") を発生させるように変更 |
| tests/test_check_public.py | 12543 | test_check_real_project に denshouhi_20260924.csv と national_report.pdf の確認を追加。テストケース (a)〜(e) および .agents フォルダのテストを追加 |
| tests/test_build_national.py | 16525 | quiet=True で公開前チェックに問題がある場合に RuntimeError が発生することを確認するテスト test_build_national_quiet_private_info_error を追加 |
| docs/dev/reports/M14-07_report.md | 14891 | 本報告書 |

## 指示された実行結果

### 1. `git diff src/check_public.py src/build_national.py`
```diff
diff --git a/src/build_national.py b/src/build_national.py
index 853aed0..c8b108b 100644
--- a/src/build_national.py
+++ b/src/build_national.py
@@ -889,21 +889,21 @@ def build_national(output_dir=None, site_dir=None, data_dir=None, quiet=False):
     # 公開前チェック
     issues = find_private_info(created_files)
 
-    size_kb = index_html_path.stat().st_size / 1024
-
-    try:
-        rel_index_path = index_html_path.relative_to(PROJECT_ROOT).as_posix()
-    except ValueError:
-        rel_index_path = str(index_html_path)
-
-    if not quiet:
-        print(f"全国ページ：{rel_index_path}")
-        print(f"碑：{total_monuments:,}基（{len(PREFECTURES)}都道府県）\u3000伝承碑データ取得日：{latest_date}")
-        print(f"色分け地図（碑の数）：0：{c_dist['0']}／1〜9：{c_dist['1〜9']}／10〜19：{c_dist['10〜19']}／20〜49：{c_dist['20〜49']}／50〜99：{c_dist['50〜99']}／100以上：{c_dist['100以上']}")
-        print(f"一覧の地形分類：{len(lf_options) - 1}区分＋データなし（データなし {mon_no_data:,}基）")
-        print(f"作成したファイル：{len(created_files)}")
-        print(f"docs/index.html のサイズ：{size_kb:.1f} KB")
-        if issues:
+    if issues:
+        if quiet:
+            raise RuntimeError(f"公開前チェック：問題あり（{len(issues)}件）")
+        else:
+            size_kb = index_html_path.stat().st_size / 1024
+            try:
+                rel_index_path = index_html_path.relative_to(PROJECT_ROOT).as_posix()
+            except ValueError:
+                rel_index_path = str(index_html_path)
+            print(f"全国ページ：{rel_index_path}")
+            print(f"碑：{total_monuments:,}基（{len(PREFECTURES)}都道府県）\u3000伝承碑データ取得日：{latest_date}")
+            print(f"色分け地図（碑の数）：0：{c_dist['0']}／1〜9：{c_dist['1〜9']}／10〜19：{c_dist['10〜19']}／20〜49：{c_dist['20〜49']}／50〜99：{c_dist['50〜99']}／100以上：{c_dist['100以上']}")
+            print(f"一覧の地形分類：{len(lf_options) - 1}区分＋データなし（データなし {mon_no_data:,}基）")
+            print(f"作成したファイル：{len(created_files)}")
+            print(f"docs/index.html のサイズ：{size_kb:.1f} KB")
             print("公開前チェック：問題あり")
             for p, l, msg in issues:
                 try:
@@ -912,8 +912,20 @@ def build_national(output_dir=None, site_dir=None, data_dir=None, quiet=False):
                     rel_p = p
                 print(f"{rel_p} ({l}行目): {msg}")
             sys.exit(1)
-        else:
-            print("公開前チェック：問題なし")
+
+    if not quiet:
+        size_kb = index_html_path.stat().st_size / 1024
+        try:
+            rel_index_path = index_html_path.relative_to(PROJECT_ROOT).as_posix()
+        except ValueError:
+            rel_index_path = str(index_html_path)
+        print(f"全国ページ：{rel_index_path}")
+        print(f"碑：{total_monuments:,}基（{len(PREFECTURES)}都道府県）\u3000伝承碑データ取得日：{latest_date}")
+        print(f"色分け地図（碑の数）：0：{c_dist['0']}／1〜9：{c_dist['1〜9']}／10〜19：{c_dist['10〜19']}／20〜49：{c_dist['20〜49']}／50〜99：{c_dist['50〜99']}／100以上：{c_dist['100以上']}")
+        print(f"一覧の地形分類：{len(lf_options) - 1}区分＋データなし（データなし {mon_no_data:,}基）")
+        print(f"作成したファイル：{len(created_files)}")
+        print(f"docs/index.html のサイズ：{size_kb:.1f} KB")
+        print("公開前チェック：問題なし")
 
     return created_files
 
diff --git a/src/check_public.py b/src/check_public.py
index 66ac645..7870a28 100644
--- a/src/check_public.py
+++ b/src/check_public.py
@@ -1,6 +1,8 @@
 import argparse
 import sys
 import re
+import struct
+import zlib
 from pathlib import Path
 
 PROJECT_ROOT = Path(__file__).resolve().parent.parent
@@ -29,6 +31,117 @@ def find_private_info(paths):
         except ValueError:
             rel_path = path_obj
 
+        suffix = path_obj.suffix.lower()
+
+        # PDF ファイルの検査
+        if suffix == '.pdf':
+            try:
+                data = path_obj.read_bytes()
+            except Exception:
+                continue
+
+            # stream〜endstream の間（圧縮された中身）を取り除く
+            cleaned = re.sub(rb'stream.*?endstream', b'', data, flags=re.DOTALL)
+            text = cleaned.decode('latin-1')
+
+            # /Author があれば種類「PDFの作成者情報」として1件にする（行番号は 1）
+            if '/Author' in text:
+                found_issues.append((str(rel_path), 1, "PDFの作成者情報"))
+
+            for i, line in enumerate(text.splitlines(), 1):
+                for m in win_pattern.finditer(line):
+                    user_name = m.group(1)
+                    if user_name.startswith('<') or '%USERPROFILE%' in line:
+                        continue
+                    found_issues.append((str(rel_path), i, "Windowsパス（ユーザー名: <ユーザー名>）"))
+
+                for m in unix_pattern.finditer(line):
+                    user_name = m.group(1)
+                    if user_name.startswith('<') or '%USERPROFILE%' in line:
+                        continue
+                    found_issues.append((str(rel_path), i, "ホームディレクトリ（ユーザー名: <ユーザー名>）"))
+
+                for m in email_pattern.finditer(line):
+                    email = m.group(0)
+                    if email.endswith('@users.noreply.github.com'):
+                        continue
+                    found_issues.append((str(rel_path), i, "メールアドレス"))
+            continue
+
         # PNG ファイルの検査
+        if suffix == '.png':
+            try:
+                data = path_obj.read_bytes()
+            except Exception:
+                continue
+
+            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
+                continue
+
+            pos = 8
+            data_len = len(data)
+            text_chunks = []
+
+            while pos + 8 <= data_len:
+                length, chunk_type = struct.unpack('>I4s', data[pos:pos+8])
+                pos += 8
+                if pos + length + 4 > data_len:
+                    break
+                chunk_data = data[pos:pos+length]
+                pos += length + 4
+
+                if chunk_type == b'tEXt':
+                    text_chunks.append(chunk_data.decode('utf-8', errors='replace'))
+                elif chunk_type == b'zTXt':
+                    null_idx = chunk_data.find(b'\x00')
+                    if null_idx != -1 and null_idx + 2 <= len(chunk_data):
+                        kw = chunk_data[:null_idx].decode('utf-8', errors='replace')
+                        comp_data = chunk_data[null_idx+2:]
+                        try:
+                            decompressed = zlib.decompress(comp_data)
+                            txt = decompressed.decode('utf-8', errors='replace')
+                            text_chunks.append(f"{kw}\n{txt}")
+                        except Exception:
+                            pass
+                elif chunk_type == b'iTXt':
+                    parts = chunk_data.split(b'\x00', 3)
+                    if len(parts) >= 4:
+                        kw = parts[0].decode('utf-8', errors='replace')
+                        flag = parts[1][0] if len(parts[1]) > 0 else 0
+                        raw_text = parts[3]
+                        if flag == 1:
+                            try:
+                                raw_text = zlib.decompress(raw_text)
+                            except Exception:
+                                pass
+                        txt = raw_text.decode('utf-8', errors='replace')
+                        text_chunks.append(f"{kw}\n{txt}")
+                    else:
+                        text_chunks.append(chunk_data.decode('utf-8', errors='replace'))
+                elif chunk_type == b'IEND':
+                    break
+
+            for chunk_text in text_chunks:
+                for line in chunk_text.splitlines():
+                    for m in win_pattern.finditer(line):
+                        user_name = m.group(1)
+                        if user_name.startswith('<') or '%USERPROFILE%' in line:
+                            continue
+                        found_issues.append((str(rel_path), 1, "Windowsパス（ユーザー名: <ユーザー名>）"))
+
+                    for m in unix_pattern.finditer(line):
+                        user_name = m.group(1)
+                        if user_name.startswith('<') or '%USERPROFILE%' in line:
+                            continue
+                        found_issues.append((str(rel_path), 1, "ホームディレクトリ（ユーザー名: <ユーザー名>）"))
+
+                    for m in email_pattern.finditer(line):
+                        email = m.group(0)
+                        if email.endswith('@users.noreply.github.com'):
+                            continue
+                        found_issues.append((str(rel_path), 1, "メールアドレス"))
+            continue
+
         # テキストとして読めないファイル（画像など）やバイナリは飛ばす
         try:
             with open(path_obj, 'rb') as f:
@@ -71,7 +184,7 @@ def find_private_info(paths):
 
 def collect_targets(root):
     root_path = Path(root).resolve()
-    target_dirs = ['src', 'tests', 'docs', 'output']
+    target_dirs = ['src', 'tests', 'docs', 'output', '.agents']
     
     paths_to_check = []
     
@@ -79,6 +192,15 @@ def collect_targets(root):
         dir_path = root_path / d
         if dir_path.exists():
             paths_to_check.extend(list(dir_path.rglob('*')))
+
+    # data/raw/<フォルダ>/ の直下にある .csv だけ対象に加える
+    raw_dir = root_path / 'data' / 'raw'
+    if raw_dir.exists():
+        for folder in raw_dir.iterdir():
+            if folder.is_dir() and folder.name not in ['rivers', 'coastline']:
+                for p in folder.iterdir():
+                    if p.is_file() and p.suffix.lower() == '.csv':
+                        paths_to_check.append(p)
             
     for p in root_path.iterdir():
         if p.is_file():
@@ -95,8 +217,16 @@ def collect_targets(root):
             continue
             
         top_folder = rel_path.parts[0]
-        if top_folder in ['.venv', '.git', 'data', '_to_delete']:
+        if top_folder in ['.venv', '.git', '_to_delete']:
             continue
+
+        if top_folder == 'data':
+            # data/raw/<フォルダ>/<ファイル名.csv> だけ許可
+            if not (len(rel_path.parts) == 4 and
+                    rel_path.parts[1] == 'raw' and
+                    rel_path.parts[2] not in ['rivers', 'coastline'] and
+                    rel_path.suffix.lower() == '.csv'):
+                continue
             
         if '__pycache__' in rel_path.parts:
             continue
```

### 2. `python src/check_public.py`
```
公開前チェック：問題なし
```

### 3. 対象の数：`python -c "import sys;sys.path.insert(0,'src');from check_public import collect_targets,PROJECT_ROOT;from collections import Counter;t=[p for p in collect_targets(PROJECT_ROOT) if p.is_file()];print(len(t));print(Counter(p.suffix for p in t).most_common())"`
```
1991
[('.csv', 816), ('.png', 746), ('.md', 233), ('.html', 142), ('.py', 44), ('', 6), ('.pdf', 2), ('.ini', 1), ('.txt', 1)]
```

### 4. テスト・静的チェック結果
- `python -m pytest -q`（最後の行）：
```
220 passed in 980.25s (0:16:20)
```

- `python -m pytest -q tests/test_check_public.py tests/test_build_national.py`（最後の行）：
```
18 passed in 3.16s
```

- `python -m pyflakes src/check_public.py src/build_national.py tests/test_check_public.py tests/test_build_national.py`：
```
（出力なし、0件）
```

### 5. 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/check_public.py','src/build_national.py','tests/test_check_public.py','tests/test_build_national.py']]"`
```
src/check_public.py False
src/build_national.py False
tests/test_check_public.py False
tests/test_build_national.py False
```

### 6. `git status --short`
```
 M src/build_national.py
 M src/check_public.py
 M tests/test_build_national.py
 M tests/test_check_public.py
?? docs/dev/reports/M14-07_report.md
```

### 7. 変更したファイルのバイト数
```
src/check_public.py: 10370 bytes
src/build_national.py: 41636 bytes
tests/test_check_public.py: 12543 bytes
tests/test_build_national.py: 16525 bytes
docs/dev/reports/M14-07_report.md: 14891 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python src/check_public.py` が「公開前チェック：問題なし」：確認済み
  - 対象のファイル数（ディレクトリを除く）：1,991（.csv 816, .png 746, .md 233, .html 142, .py 44, 拡張子なし 6, .pdf 2, .ini 1, .txt 1）：確認済み
  - 実データ検証：data/raw の CSV 0件、PDF 2件とも0件、PNG 746件すべて0件：確認済み
  - pytest 全件合格（220件）、pyflakes 0件、LF：確認済み
  - git diff は対象ファイルの4つだけ：確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
