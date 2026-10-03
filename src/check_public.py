import argparse
import sys
import re
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
            # Windows
            for m in win_pattern.finditer(line):
                user_name = m.group(1)
                # 伏せ字かどうかのチェック
                if user_name.startswith('<') or '%USERPROFILE%' in line:
                    continue
                found_issues.append((str(rel_path), i, "Windowsパス（ユーザー名: <ユーザー名>）"))
                
            # macOS/Linux
            for m in unix_pattern.finditer(line):
                user_name = m.group(1)
                if user_name.startswith('<') or '%USERPROFILE%' in line:
                    continue
                found_issues.append((str(rel_path), i, "ホームディレクトリ（ユーザー名: <ユーザー名>）"))
                
            # Email
            for m in email_pattern.finditer(line):
                email = m.group(0)
                if email.endswith('@users.noreply.github.com'):
                    continue
                found_issues.append((str(rel_path), i, "メールアドレス"))
                
    return found_issues

def collect_targets(root):
    root_path = Path(root).resolve()
    target_dirs = ['src', 'tests', 'docs', 'output']
    target_files = ['README.md', 'AGENTS.md', 'requirements.txt']
    
    paths_to_check = []
    
    for d in target_dirs:
        dir_path = root_path / d
        if dir_path.exists():
            paths_to_check.extend(list(dir_path.rglob('*')))
            
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
        if top_folder in ['.venv', '.git', 'data', '_to_delete']:
            continue
            
        if '__pycache__' in rel_path.parts:
            continue
            
        filtered_paths.append(p)
        
    return filtered_paths

def main(root=None, args=None):
    if root is None:
        root = PROJECT_ROOT
        
    parser = argparse.ArgumentParser()
    
    if args is None and root != PROJECT_ROOT:
        args = []
        
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
