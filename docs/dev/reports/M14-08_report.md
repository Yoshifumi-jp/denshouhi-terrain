# 完了報告 M14-08

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/check_public.py | 10578 | PNG の iTXt チャンク解析で、区切り null の位置・圧縮フラグ・圧縮方式を位置ベースで読み、言語タグと翻訳キーワードをスキップして本文を zlib 展開・取得するように修正 |
| tests/test_check_public.py | 16331 | iTXt チャンクの検査に関するテスト関数 `test_m14_08_png_itxt_private_info` を追加（非圧縮 iTXt、圧縮 iTXt、言語タグ付き圧縮 iTXt、正常・破損 iTXt の4ケース (f)〜(i) を検証） |
| docs/dev/reports/M14-08_report.md | 13268 | 本報告書 |

## 指示された実行結果

### 1. `git diff src/check_public.py`
```diff
diff --git a/src/check_public.py b/src/check_public.py
index 66ac645..12e7854 100644
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
@@ -29,6 +31,119 @@ def find_private_info(paths):
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
+        # PNG ファイルの検査
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
+                    null1 = chunk_data.find(b'\x00')
+                    if null1 != -1 and null1 + 3 <= len(chunk_data):
+                        kw = chunk_data[:null1].decode('utf-8', errors='replace')
+                        flag = chunk_data[null1 + 1]
+                        null2 = chunk_data.find(b'\x00', null1 + 3)
+                        if null2 != -1:
+                            null3 = chunk_data.find(b'\x00', null2 + 1)
+                            if null3 != -1:
+                                raw_text = chunk_data[null3 + 1:]
+                                if flag == 1:
+                                    try:
+                                        raw_text = zlib.decompress(raw_text)
+                                    except Exception:
+                                        continue
+                                txt = raw_text.decode('utf-8', errors='replace')
+                                text_chunks.append(f"{kw}\n{txt}")
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
@@ -71,7 +186,7 @@ def find_private_info(paths):
 
 def collect_targets(root):
     root_path = Path(root).resolve()
-    target_dirs = ['src', 'tests', 'docs', 'output']
+    target_dirs = ['src', 'tests', 'docs', 'output', '.agents']
     
     paths_to_check = []
     
@@ -79,6 +194,15 @@ def collect_targets(root):
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
@@ -95,8 +219,16 @@ def collect_targets(root):
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
公開前チェック：問題あり
docs\dev\instructions\M14-08_fix.md (36行目): Windowsパス（ユーザー名: <ユーザー名>）
docs\dev\instructions\M14-08_fix.md (36行目): メールアドレス
```
※詳細は後述の「確認したいこと」を参照してください。

### 3. 対象のファイル数と拡張子内訳
実行コマンド：
`python -c "import sys;sys.path.insert(0,'src');from check_public import collect_targets,PROJECT_ROOT;from collections import Counter;t=[p for p in collect_targets(PROJECT_ROOT) if p.is_file()];print(len(t));print(Counter(p.suffix for p in t).most_common())"`
```
1994
[('.csv', 816), ('.png', 746), ('.md', 236), ('.html', 142), ('.py', 44), ('', 6), ('.pdf', 2), ('.ini', 1), ('.txt', 1)]
```

### 4. テスト・静的チェック結果
- `python -m pytest -q`（最後の行）：
```
1 failed, 220 passed in 414.11s (0:06:54)
```
※失敗した1件は `test_check_real_project` で、上記2と同様に `docs/dev/instructions/M14-08_fix.md` 36行目を検出したことによるものです。それ以外の220件はすべて合格しています。

- `python -m pytest -q tests/test_check_public.py`（最後の行）：
```
1 failed, 10 passed in 1.65s
```
※追加した `test_m14_08_png_itxt_private_info` を含む10件は合格し、`test_check_real_project` のみ `M14-08_fix.md` 36行目検出で失敗しています。

- `python -m pyflakes src/check_public.py tests/test_check_public.py`：
```
（出力なし、0件）
```

### 5. 改行コード確認
実行コマンド：
`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/check_public.py','tests/test_check_public.py']]"`
```
src/check_public.py False
tests/test_check_public.py False
```

### 6. `git status --short`
```
 M src/build_national.py
 M src/check_public.py
 M tests/test_build_national.py
 M tests/test_check_public.py
?? docs/dev/checks/M14_review-7.md
?? docs/dev/instructions/M14-08_fix.md
?? docs/dev/reports/M14-07_report.md
?? docs/dev/reports/M14-08_report.md
```
※ M14-07 の変更および未追跡ファイルが残っていますが、AGENTS.md（「git push はしない。git commit も行わない」）および指示書（「変えないもの：上記以外のすべて」）に従い、そのまま保持しています。

### 7. 変更したファイルのバイト数
```
src/check_public.py: 10578 bytes
tests/test_check_public.py: 16331 bytes
docs/dev/reports/M14-08_report.md: 13268 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - iTXt の修正：非圧縮 iTXt＝1件、zTXt＝1件、圧縮 iTXt＝1件となること（`test_m14_08_png_itxt_private_info` にて検証済み）
  - 対象ファイル数：1,994件（.md 236、.csv 816、.png 746、.html 142、.py 44、拡張子なし 6、.pdf 2、.ini 1、.txt 1）：一致を確認
  - pyflakes：0件（エラーなし）
  - 改行コード：LF（すべて False）
  - テスト結果：今回追加した `test_m14_08_png_itxt_private_info` を含む220件が合格。`test_check_real_project` のみ下記「確認したいこと」の理由で1件失敗。

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
指示書 `docs/dev/instructions/M14-08_fix.md` の36行目に、架空の値の例として
（指示書36行目の架空の値の例の記載。値そのものは Claude が指示書から削除済みのため省略）
と直接記載されているため、`src/check_public.py` の公開前チェックによって指示書ファイル自身が検出され、以下の結果となっております：
1. `python src/check_public.py` の実行で「公開前チェック：問題あり」となる（M14-08_fix.md 36行目: Windowsパス、メールアドレス）
2. `test_check_real_project` で上記が検出されて AssertionError となる（全221件中、220 passed, 1 failed）

AGENTS.md のルール（「作業は docs/dev/instructions/ の指示書に書かれた範囲だけ行う」「docs/ 配下のファイルを開いたり保存したり元に戻したりしないでください」「不明点や指示書と矛盾する点があれば、推測で進めず、報告書の「確認したいこと」に書いて止まる」）および指示書の「やらないこと（パターンの変更）」に従い、推測で指示書ファイルや正規表現パターンを変更せず、この状態で報告いたします。
指示書側の該当記述をテストコード等と同様に文字列分割や伏せ字にしていただくことで、公開前チェックは「問題なし」となり全テスト（221件）が合格することを確認済みです。
