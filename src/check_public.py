import argparse
import sys
import re
import struct
import zlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def find_private_info(paths):
    found_issues = []
    
    # 正規表現
    # Windows のユーザーフォルダ: [A-Za-z]:\Users\<何か>  (区切りは \ または /、または重ね)
    # 伏せ字 <...> や %USERPROFILE% を除外
    win_pattern = re.compile(r'[A-Za-z]:[\\/]+Users[\\/]+([^\\/<>…\s\`\'"()\[\]{}（）「」『』【】〔〕〈〉《》、。]+)')
    
    # macOS/Linux のホーム: /Users/<何か>/, /home/<何か>/
    unix_pattern = re.compile(r'(?<![A-Za-z]:)(?<![A-Za-z]:[\\/])[\\/](?:Users|home)[\\/]([^\\/<>…\s\`\'"()\[\]{}（）「」『』【】〔〕〈〉《》、。]+)[\\/]')
    
    # メールアドレス (xxx@users.noreply.github.com 以外)
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    for p in paths:
        path_obj = Path(p)
        if not path_obj.exists() or not path_obj.is_file():
            continue
            
        try:
            rel_path = path_obj.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = path_obj

        suffix = path_obj.suffix.lower()

        # PDF ファイルの検査
        if suffix == '.pdf':
            try:
                data = path_obj.read_bytes()
            except Exception:
                continue

            # stream〜endstream の間（圧縮された中身）を取り除く
            cleaned = re.sub(rb'stream.*?endstream', b'', data, flags=re.DOTALL)
            text = cleaned.decode('latin-1')

            # /Author があれば種類「PDFの作成者情報」として1件にする（行番号は 1）
            if '/Author' in text:
                found_issues.append((str(rel_path), 1, "PDFの作成者情報"))

            for i, line in enumerate(text.splitlines(), 1):
                for m in win_pattern.finditer(line):
                    user_name = m.group(1)
                    if user_name.startswith('<') or '%USERPROFILE%' in line:
                        continue
                    found_issues.append((str(rel_path), i, "Windowsパス（ユーザー名: <ユーザー名>）"))

                for m in unix_pattern.finditer(line):
                    user_name = m.group(1)
                    if user_name.startswith('<') or '%USERPROFILE%' in line:
                        continue
                    found_issues.append((str(rel_path), i, "ホームディレクトリ（ユーザー名: <ユーザー名>）"))

                for m in email_pattern.finditer(line):
                    email = m.group(0)
                    if email.endswith('@users.noreply.github.com'):
                        continue
                    found_issues.append((str(rel_path), i, "メールアドレス"))
            continue

        # PNG ファイルの検査
        if suffix == '.png':
            try:
                data = path_obj.read_bytes()
            except Exception:
                continue

            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                continue

            pos = 8
            data_len = len(data)
            text_chunks = []

            while pos + 8 <= data_len:
                length, chunk_type = struct.unpack('>I4s', data[pos:pos+8])
                pos += 8
                if pos + length + 4 > data_len:
                    break
                chunk_data = data[pos:pos+length]
                pos += length + 4

                if chunk_type == b'tEXt':
                    text_chunks.append(chunk_data.decode('utf-8', errors='replace'))
                elif chunk_type == b'zTXt':
                    null_idx = chunk_data.find(b'\x00')
                    if null_idx != -1 and null_idx + 2 <= len(chunk_data):
                        kw = chunk_data[:null_idx].decode('utf-8', errors='replace')
                        comp_data = chunk_data[null_idx+2:]
                        try:
                            decompressed = zlib.decompress(comp_data)
                            txt = decompressed.decode('utf-8', errors='replace')
                            text_chunks.append(f"{kw}\n{txt}")
                        except Exception:
                            pass
                elif chunk_type == b'iTXt':
                    null1 = chunk_data.find(b'\x00')
                    if null1 != -1 and null1 + 3 <= len(chunk_data):
                        kw = chunk_data[:null1].decode('utf-8', errors='replace')
                        flag = chunk_data[null1 + 1]
                        null2 = chunk_data.find(b'\x00', null1 + 3)
                        if null2 != -1:
                            null3 = chunk_data.find(b'\x00', null2 + 1)
                            if null3 != -1:
                                raw_text = chunk_data[null3 + 1:]
                                if flag == 1:
                                    try:
                                        raw_text = zlib.decompress(raw_text)
                                    except Exception:
                                        continue
                                txt = raw_text.decode('utf-8', errors='replace')
                                text_chunks.append(f"{kw}\n{txt}")
                elif chunk_type == b'IEND':
                    break

            for chunk_text in text_chunks:
                for line in chunk_text.splitlines():
                    for m in win_pattern.finditer(line):
                        user_name = m.group(1)
                        if user_name.startswith('<') or '%USERPROFILE%' in line:
                            continue
                        found_issues.append((str(rel_path), 1, "Windowsパス（ユーザー名: <ユーザー名>）"))

                    for m in unix_pattern.finditer(line):
                        user_name = m.group(1)
                        if user_name.startswith('<') or '%USERPROFILE%' in line:
                            continue
                        found_issues.append((str(rel_path), 1, "ホームディレクトリ（ユーザー名: <ユーザー名>）"))

                    for m in email_pattern.finditer(line):
                        email = m.group(0)
                        if email.endswith('@users.noreply.github.com'):
                            continue
                        found_issues.append((str(rel_path), 1, "メールアドレス"))
            continue

        # テキストとして読めないファイル（画像など）やバイナリは飛ばす
        try:
            with open(path_obj, 'rb') as f:
                head = f.read(1024)
                if head.startswith(b'\xff\xfe') or head.startswith(b'\xfe\xff'):
                    encoding = 'utf-16'
                elif b'\x00' in head:
                    continue
                else:
                    encoding = 'utf-8'
            with open(path_obj, 'r', encoding=encoding) as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            continue
            
        for i, line in enumerate(lines, 1):
            # Windowsパス
            for m in win_pattern.finditer(line):
                user_name = m.group(1)
                # 伏せ字かどうかのチェック
                if user_name.startswith('<') or '%USERPROFILE%' in line:
                    continue
                found_issues.append((str(rel_path), i, "Windowsパス（ユーザー名: <ユーザー名>）"))
                
            # macOS/Linuxパス
            for m in unix_pattern.finditer(line):
                user_name = m.group(1)
                if user_name.startswith('<') or '%USERPROFILE%' in line:
                    continue
                found_issues.append((str(rel_path), i, "ホームディレクトリ（ユーザー名: <ユーザー名>）"))
                
            # メールアドレス
            for m in email_pattern.finditer(line):
                email = m.group(0)
                if email.endswith('@users.noreply.github.com'):
                    continue
                found_issues.append((str(rel_path), i, "メールアドレス"))
                
    return found_issues

def collect_targets(root):
    root_path = Path(root).resolve()
    target_dirs = ['src', 'tests', 'docs', 'output', '.agents']
    
    paths_to_check = []
    
    for d in target_dirs:
        dir_path = root_path / d
        if dir_path.exists():
            paths_to_check.extend(list(dir_path.rglob('*')))

    # data/raw/<フォルダ>/ の直下にある .csv だけ対象に加える
    raw_dir = root_path / 'data' / 'raw'
    if raw_dir.exists():
        for folder in raw_dir.iterdir():
            if folder.is_dir() and folder.name not in ['rivers', 'coastline']:
                for p in folder.iterdir():
                    if p.is_file() and p.suffix.lower() == '.csv':
                        paths_to_check.append(p)
            
    for p in root_path.iterdir():
        if p.is_file():
            paths_to_check.append(p)
            
    filtered_paths = []
    for p in paths_to_check:
        try:
            rel_path = p.relative_to(root_path)
        except ValueError:
            continue
            
        if not rel_path.parts:
            continue
            
        top_folder = rel_path.parts[0]
        if top_folder in ['.venv', '.git', '_to_delete']:
            continue

        if top_folder == 'data':
            # data/raw/<フォルダ>/<ファイル名.csv> だけ許可
            if not (len(rel_path.parts) == 4 and
                    rel_path.parts[1] == 'raw' and
                    rel_path.parts[2] not in ['rivers', 'coastline'] and
                    rel_path.suffix.lower() == '.csv'):
                continue
            
        if '__pycache__' in rel_path.parts:
            continue
            
        filtered_paths.append(p)
        
    return filtered_paths

def main(root=None, args=None):
    if root is None:
        root = PROJECT_ROOT
        
    parser = argparse.ArgumentParser()
    parser.parse_args(args)
    
    filtered_paths = collect_targets(root)
    issues = find_private_info(filtered_paths)
    
    if issues:
        print("公開前チェック：問題あり")
        for path, line_num, issue_type in issues:
            print(f"{path} ({line_num}行目): {issue_type}")
        sys.exit(1)
    else:
        print("公開前チェック：問題なし")
        sys.exit(0)

if __name__ == '__main__':
    main()
