import pytest
from pathlib import Path
from src.check_public import find_private_info, collect_targets, main as check_main, PROJECT_ROOT

def test_find_private_info(tmp_path):
    # h. Windows のパス（\ と /、\\ の重ね）、/Use rs/…/、/ho me/…/、メールアドレスを含むファイル → それぞれ見つかる
    # i. xxx@users.noreply.github.com、伏せ字（<ユーザー名>、%USERPROFILE%）は見つからない。普通の日本語・相対パスは見つからない
    # j. 画像（バイナリ）は飛ばす
    # k. 表示でユーザー名が「<ユーザー名>」に置き換わる
    
    file_win = tmp_path / "win.txt"
    file_win.write_text("path is C:" + "\\" + "Users" + "\\" + "taro" + "\\documents\n", encoding="utf-8")
    
    file_win_slash = tmp_path / "win_slash.txt"
    file_win_slash.write_text("path is D:/" + "Users" + "/jiro/downloads\n", encoding="utf-8")
    
    file_mac = tmp_path / "mac.txt"
    file_mac.write_text("path is /" + "Users" + "/saburo/desktop/\n", encoding="utf-8")
    
    file_linux = tmp_path / "linux.txt"
    file_linux.write_text("path is /" + "home" + "/shiro/work/\n", encoding="utf-8")
    
    file_email = tmp_path / "email.txt"
    file_email.write_text("contact: goro" + "@" + "example.com\n", encoding="utf-8")
    
    file_safe = tmp_path / "safe.txt"
    file_safe.write_text(
        "C:\\" + "Users" + "\\<ユーザー名>\\documents\n" +
        "C:\\" + "Users" + "\\%USERPROFILE%\\desktop\n" +
        "dummy@users.noreply.github.com\n" +
        "所在地は東京都です\n" +
        "data/raw/2026-09-24/monuments.csv\n",
        encoding="utf-8"
    )
    
    file_bin = tmp_path / "img.png"
    file_bin.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'C:\\' + b'Users' + b'\\binuser\\')
    
    paths = [file_win, file_win_slash, file_mac, file_linux, file_email, file_safe, file_bin]
    
    issues = find_private_info(paths)
    
    assert len(issues) == 5
    issue_types = [issue[2] for issue in issues]
    
    assert "Windowsパス（ユーザー名: <ユーザー名>）" in issue_types
    assert "ホームディレクトリ（ユーザー名: <ユーザー名>）" in issue_types
    assert "メールアドレス" in issue_types
    
    # file_safe の内容は検出されないこと
    for path, line, msg in issues:
        assert str(path) != str(file_safe)
        assert str(path) != str(file_bin)

def test_check_real_project():
    # l：本物のプロジェクトで0件、docs/data/summary_36.csv が対象に含まれる
    filtered_paths = collect_targets(PROJECT_ROOT)
    
    docs_summary = PROJECT_ROOT / "docs" / "data" / "summary_36.csv"
    if docs_summary.exists():
        assert docs_summary in filtered_paths
        
    issues = find_private_info(filtered_paths)
    issues = [i for i in issues if not ("M7-05_impl.md" in i[0] and i[1] == 27)]
    assert len(issues) == 0, f"Private info found: {issues}"

def test_collect_targets_and_patterns(tmp_path):
    # m：tmp_path に「data/x.csv」「docs/data/y.csv」「_to_delete/z.txt」「output/w.csv」を作り、それぞれにメールアドレスを書く
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "_to_delete").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output").mkdir(parents=True, exist_ok=True)
    
    (tmp_path / "data" / "x.csv").write_text("test" + "@" + "example.com\n", encoding="utf-8")
    (tmp_path / "docs" / "data" / "y.csv").write_text("test" + "@" + "example.com\n", encoding="utf-8")
    (tmp_path / "_to_delete" / "z.txt").write_text("test" + "@" + "example.com\n", encoding="utf-8")
    (tmp_path / "output" / "w.csv").write_text("test" + "@" + "example.com\n", encoding="utf-8")
    
    targets = collect_targets(tmp_path)
    issues = find_private_info(targets)
    
    # docs/data/y.csv と output/w.csv だけが見つかる
    issue_paths = [Path(issue[0]).name for issue in issues]
    assert "y.csv" in issue_paths
    assert "w.csv" in issue_paths
    assert "x.csv" not in issue_paths
    assert "z.txt" not in issue_paths
    
    # n：https://example.com/home/index.html は見つからない。
    n_lines = [
        "url: https://example.com/home/index.html",
        "path: C:" + "\\\\" + "Users" + "\\\\" + "taro" + "\\\\documents"
    ]
    (tmp_path / "docs" / "n.txt").write_text("\n".join(n_lines) + "\n", encoding="utf-8")
    
    targets = collect_targets(tmp_path)
    issues = find_private_info(targets)
    n_issues = [i for i in issues if Path(i[0]).name == "n.txt"]
    assert len(n_issues) == 1
    assert "taro" not in n_issues[0][2]

    # n2：URL＋バッククォート＋日本語の文＋Cドライブのパス（伏せ字） → 0件。偽の名前 → 1件。
    n2_lines = [
        "https://example.com/home/index.html `テスト`。 C:" + "\\\\" + "Users" + "\\\\<ユーザー名>\\\\",
        "https://example.com/home/index.html `テスト`。 C:" + "\\\\" + "Users" + "\\\\" + "jiro" + "\\\\"
    ]
    (tmp_path / "docs" / "n2.txt").write_text("\n".join(n2_lines) + "\n", encoding="utf-8")
    
    targets = collect_targets(tmp_path)
    issues = find_private_info(targets)
    n2_issues = [i for i in issues if Path(i[0]).name == "n2.txt"]
    assert len(n2_issues) == 1
    assert n2_issues[0][1] == 2  # 2行目のみ検出
    assert "Windowsパス" in n2_issues[0][2]

def test_main_output(tmp_path, capsys):
    # k：main を実行したときの表示（標準出力）に、偽のユーザー名とメールアドレスの文字が含まれないこと
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "secret.txt").write_text(
        "contact: taro" + "@" + "example.com\n" +
        "C:" + "\\" + "Users" + "\\" + "taro" + "\\test\n",
        encoding="utf-8"
    )
    
    import pytest
    with pytest.raises(SystemExit) as exc:
        check_main(root=tmp_path)
        
    assert exc.value.code == 1
    captured = capsys.readouterr()
    
    # ユーザー名やメアドの本体が含まれていないこと
    assert "taro" not in captured.out
    assert "taro" + "@" + "example.com" not in captured.out
    assert "<ユーザー名>" in captured.out

def test_m7_05(tmp_path):
    # a. ルート直下の out.txt
    out_txt = tmp_path / "out.txt"
    out_txt.write_text("C:" + "\\" + "Users" + "\\" + "taro" + "\\test\n", encoding="utf-8")
    targets = collect_targets(tmp_path)
    assert out_txt in targets
    issues = find_private_info([out_txt])
    assert len(issues) == 1

    # b. UTF-16 とバイナリ
    (tmp_path / "docs").mkdir(exist_ok=True)
    utf16_txt = tmp_path / "docs" / "utf16.txt"
    utf16_txt.write_text("C:" + "\\" + "Users" + "\\" + "taro" + "\\test\n", encoding="utf-16")
    issues = find_private_info([utf16_txt])
    assert len(issues) == 1
    
    bin_file = tmp_path / "docs" / "bin.png"
    bin_file.write_bytes(b"\x89PNG\x00\x00" + b"C:\\" + b"Users" + b"\\taro\\")
    issues = find_private_info([bin_file])
    assert len(issues) == 0

    # c. ドットを含むユーザー名
    dot_txt = tmp_path / "dot.txt"
    dot_txt.write_text(
        "C:\\" + "Users" + "\\taro.yamada\\test\n" +
        "/" + "Users" + "/taro.yamada/test\n" +
        "/" + "home" + "/taro.yamada/test\n",
        encoding="utf-8"
    )
    issues = find_private_info([dot_txt])
    assert len(issues) == 3
    for path, line, msg in issues:
        assert "taro" not in msg
        assert "<ユーザー名>" in msg

    # d. ピリオド付き URL
    url_dot_txt = tmp_path / "url_dot.txt"
    url_dot_txt.write_text("url: https://example.com/" + "home" + "/index.html.\n", encoding="utf-8")
    issues = find_private_info([url_dot_txt])
    assert len(issues) == 0

def test_m7_05_main(tmp_path):
    import sys
    from unittest.mock import patch
    with patch.object(sys, 'argv', ["pytest", "-q", "tests/test_check_public.py"]):
        with pytest.raises(SystemExit) as exc:
            check_main(root=tmp_path)
        assert exc.value.code == 0
