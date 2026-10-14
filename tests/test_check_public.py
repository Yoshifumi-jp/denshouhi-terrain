import pytest
import struct
import zlib
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

    raw_csv = PROJECT_ROOT / "data" / "raw" / "2026-09-24" / "denshouhi_20260924.csv"
    if raw_csv.exists():
        assert raw_csv in filtered_paths

    pdf_report = PROJECT_ROOT / "docs" / "national_report.pdf"
    if pdf_report.exists():
        assert pdf_report in filtered_paths
        
    issues = find_private_info(filtered_paths)
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
        check_main(root=tmp_path, args=[])
        
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
            check_main(root=tmp_path, args=[])
        assert exc.value.code == 0

def test_m14_07_collect_targets_data_raw(tmp_path):
    # (a) data/raw/2026-01-01/x.csv は対象、data/cache・data/processed・data/raw/rivers の下は対象外
    target_csv = tmp_path / "data" / "raw" / "2026-01-01" / "x.csv"
    target_csv.parent.mkdir(parents=True)
    target_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    cache_csv = tmp_path / "data" / "cache" / "c.csv"
    cache_csv.parent.mkdir(parents=True)
    cache_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    proc_csv = tmp_path / "data" / "processed" / "p.csv"
    proc_csv.parent.mkdir(parents=True)
    proc_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    rivers_csv = tmp_path / "data" / "raw" / "rivers" / "r.csv"
    rivers_csv.parent.mkdir(parents=True)
    rivers_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    coastline_csv = tmp_path / "data" / "raw" / "coastline" / "c.csv"
    coastline_csv.parent.mkdir(parents=True)
    coastline_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    targets = collect_targets(tmp_path)
    assert target_csv in targets
    assert cache_csv not in targets
    assert proc_csv not in targets
    assert rivers_csv not in targets
    assert coastline_csv not in targets

def test_m14_07_pdf_private_info(tmp_path):
    # (b) ユーザー名入りの Windows パスを /Author に入れた小さな PDF（文字列で組んでよい）→ 問題あり
    pdf_bad = tmp_path / "bad.pdf"
    bad_path = "C:" + "\\" + "Users" + "\\" + "taro"
    bad_content = (
        "%PDF-1.4\n"
        "1 0 obj\n"
        f"<< /Title (Test) /Author ({bad_path}) >>\n"
        "endobj\n"
        "%%EOF\n"
    )
    pdf_bad.write_text(bad_content, encoding="latin-1")
    issues_bad = find_private_info([pdf_bad])
    assert len(issues_bad) >= 1
    types_bad = [issue[2] for issue in issues_bad]
    assert "PDFの作成者情報" in types_bad

    # (c) 同じパスが stream〜endstream の中だけにある PDF → 問題なし
    pdf_good = tmp_path / "good.pdf"
    good_content = (
        "%PDF-1.4\n"
        "1 0 obj\n"
        "<< /Length 30 >>\n"
        "stream\n" +
        bad_path + "\\secret\n" +
        "endstream\n"
        "endobj\n"
        "%%EOF\n"
    )
    pdf_good.write_text(good_content, encoding="latin-1")
    issues_good = find_private_info([pdf_good])
    assert len(issues_good) == 0

def test_m14_07_png_private_info(tmp_path):
    def make_png(text_bytes):
        png_sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
        ihdr = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data))
        
        chunks = [png_sig, ihdr]
        if text_bytes:
            text_chunk_data = b'tEXt' + text_bytes
            text_chunk = struct.pack('>I', len(text_bytes)) + text_chunk_data + struct.pack('>I', zlib.crc32(text_chunk_data))
            chunks.append(text_chunk)
        iend_data = b'IEND'
        iend = struct.pack('>I', 0) + iend_data + struct.pack('>I', zlib.crc32(iend_data))
        chunks.append(iend)
        return b''.join(chunks)

    # (d) tEXt チャンクにメールアドレスを入れた PNG（struct と zlib.crc32 で組む）→ 問題あり
    png_bad = tmp_path / "bad.png"
    email_bytes = b"contact: test" + b"@" + b"example.com"
    png_bad.write_bytes(make_png(b'Comment\x00' + email_bytes))
    issues_bad = find_private_info([png_bad])
    assert len(issues_bad) == 1
    assert issues_bad[0][2] == "メールアドレス"
    assert issues_bad[0][1] == 1

    # (e) tEXt が「Software=Matplotlib…」だけの PNG → 問題なし
    png_good = tmp_path / "good.png"
    png_good.write_bytes(make_png(b'Software\x00Matplotlib version3.11.2, https://matplotlib.org/'))
    issues_good = find_private_info([png_good])
    assert len(issues_good) == 0

def test_m14_07_agents_dir(tmp_path):
    agents_dir = tmp_path / ".agents"
    agents_dir.mkdir()
    rule_file = agents_dir / "rule.md"
    rule_file.write_text("agent rule", encoding="utf-8")
    targets = collect_targets(tmp_path)
    assert rule_file in targets

def test_m14_08_png_itxt_private_info(tmp_path):
    def make_png(chunk_type, chunk_payload):
        png_sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
        ihdr = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data))

        chunks = [png_sig, ihdr]
        if chunk_type and chunk_payload is not None:
            c_data = chunk_type + chunk_payload
            chunk = struct.pack('>I', len(chunk_payload)) + c_data + struct.pack('>I', zlib.crc32(c_data))
            chunks.append(chunk)
        iend_data = b'IEND'
        iend = struct.pack('>I', 0) + iend_data + struct.pack('>I', zlib.crc32(iend_data))
        chunks.append(iend)
        return b''.join(chunks)

    # (f) 非圧縮の iTXt（キーワード Comment、圧縮フラグ 0、方式 0、言語タグ・翻訳キーワードは空、本文にメールアドレス）→ 1件・種類「メールアドレス」・行番号 1
    email_bytes = b"contact: test" + b"@" + b"example.com"
    f_payload = b'Comment\x00\x00\x00\x00\x00' + email_bytes
    png_f = tmp_path / "f_uncompressed.png"
    png_f.write_bytes(make_png(b'iTXt', f_payload))
    issues_f = find_private_info([png_f])
    assert len(issues_f) == 1
    assert issues_f[0][1] == 1
    assert issues_f[0][2] == "メールアドレス"

    # (g) 圧縮した iTXt（圧縮フラグ 1、方式 0、本文を zlib.compress したもの、中にメールアドレス）→ 1件・種類「メールアドレス」・行番号 1
    g_payload = b'Comment\x00\x01\x00\x00\x00' + zlib.compress(email_bytes)
    png_g = tmp_path / "g_compressed.png"
    png_g.write_bytes(make_png(b'iTXt', g_payload))
    issues_g = find_private_info([png_g])
    assert len(issues_g) == 1
    assert issues_g[0][1] == 1
    assert issues_g[0][2] == "メールアドレス"

    # (h) 言語タグ ja・翻訳キーワードがある圧縮 iTXt（中にユーザー名入りの Windows パス）→ 1件以上・種類に「Windowsパス（ユーザー名: <ユーザー名>）」を含む
    bad_path = b"C:" + b"\\" + b"Users" + b"\\" + b"taro" + b"\\documents"
    h_payload = b'Comment\x00\x01\x00' + b'ja\x00' + "コメント".encode('utf-8') + b'\x00' + zlib.compress(bad_path)
    png_h = tmp_path / "h_lang_compressed.png"
    png_h.write_bytes(make_png(b'iTXt', h_payload))
    issues_h = find_private_info([png_h])
    assert len(issues_h) >= 1
    types_h = [issue[2] for issue in issues_h]
    assert "Windowsパス（ユーザー名: <ユーザー名>）" in types_h

    # (i) 本文に問題のない圧縮 iTXt、および途中で切れた壊れた iTXt（IndexError などで落ちないこと）→ 0件
    safe_payload = b'Comment\x00\x01\x00\x00\x00' + zlib.compress(b"safe text content")
    png_safe = tmp_path / "i_safe.png"
    png_safe.write_bytes(make_png(b'iTXt', safe_payload))

    # 壊れた iTXt
    png_corrupt1 = tmp_path / "i_corrupt1.png"
    png_corrupt1.write_bytes(make_png(b'iTXt', b"NoNullByteAtAll"))

    png_corrupt2 = tmp_path / "i_corrupt2.png"
    png_corrupt2.write_bytes(make_png(b'iTXt', b"Comment\x00\x01"))

    png_corrupt3 = tmp_path / "i_corrupt3.png"
    png_corrupt3.write_bytes(make_png(b'iTXt', b"Comment\x00\x01\x00NoSecondNull"))

    png_corrupt4 = tmp_path / "i_corrupt4.png"
    png_corrupt4.write_bytes(make_png(b'iTXt', b"Comment\x00\x01\x00ja\x00NoThirdNull"))

    png_corrupt5 = tmp_path / "i_corrupt5.png"
    png_corrupt5.write_bytes(make_png(b'iTXt', b"Comment\x00\x01\x00\x00\x00NotZlibData"))

    issues_i = find_private_info([
        png_safe,
        png_corrupt1,
        png_corrupt2,
        png_corrupt3,
        png_corrupt4,
        png_corrupt5,
    ])
    assert len(issues_i) == 0


