# -*- coding: utf-8 -*-
"""src/summarize_region.py の単体テストおよび実データ照合テスト。"""

import csv
import pandas as pd
import pytest

from src.prefectures import PREFECTURES
from src.summarize import extract_relocated
from src.summarize_region import (
    get_project_root,
    check_region_files,
    load_region_pref,
    build_region_table,
    build_region_notes,
    count_uncounted,
    main,
)


def _make_mon_df(rows):
    """テスト用の monuments DataFrame を作成する"""
    cols = [
        "ID",
        "碑名",
        "所在地",
        "伝承内容",
        "種別_洪水",
        "種別_地震",
        "種別_津波",
        "種別_土砂災害",
        "種別_高潮",
        "種別_火山災害",
        "種別_その他",
    ]
    return pd.DataFrame(rows, columns=cols)


def _make_pt_df(rows):
    """テスト用の points DataFrame を作成する"""
    cols = [
        "ID",
        "元の碑ID",
        "碑名",
        "所在地",
        "種別_洪水",
        "種別_地震",
        "種別_津波",
        "種別_土砂災害",
        "種別_高潮",
        "種別_火山災害",
        "種別_その他",
    ]
    return pd.DataFrame(rows, columns=cols)


def _make_reg_df(rows):
    """テスト用の landform_region DataFrame を作成する"""
    cols = [
        "ID",
        "碑名",
        "緯度",
        "経度",
        "地域版_地形分類名",
        "地域版_コード",
        "地域版_重なり数",
        "地域版_状態",
        "取得日",
    ]
    return pd.DataFrame(rows, columns=cols)


def _write_csv(df, path):
    """テスト用CSVを UTF-8 BOM・LF で書き出す"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        df.to_csv(f, index=False, lineterminator="\n")


def test_a_count_only_region_status_and_notes(tmp_path, capsys):
    """(a) 「取得済（地域版）」だけを数え、広域版・データなし・取得不可を数えない（注の行の a〜f の件数も確かめる）"""
    proc_dir = tmp_path / "data" / "processed"

    # 碑8基：地域版2、データなし1(a=1)、広域版2(c=2)、取得不可3(e=3)
    mon_rows = [
        [f"36001-{i:03d}", f"碑{i}", "徳島県", "伝承", 1, 0, 0, 0, 0, 0, 0]
        for i in range(1, 9)
    ]
    reg_mon_rows = [
        ["36001-001", "碑1", "34.0", "134.0", "低地", "51", 1, "取得済（地域版）", "2026-10-16"],
        ["36001-002", "碑2", "34.0", "134.0", "山地", "11", 1, "取得済（地域版）", "2026-10-16"],
        ["36001-003", "碑3", "34.0", "134.0", "", "", 0, "データなし", "2026-10-16"],
        ["36001-004", "碑4", "34.0", "134.0", "低地", "5", 1, "取得済（広域版）", "2026-10-16"],
        ["36001-005", "碑5", "34.0", "134.0", "山地・丘陵", "1", 1, "取得済（広域版）", "2026-10-16"],
        ["36001-006", "碑6", "34.0", "134.0", "", "", 0, "取得不可", ""],
        ["36001-007", "碑7", "34.0", "134.0", "", "", 0, "取得不可", ""],
        ["36001-008", "碑8", "34.0", "134.0", "", "", 0, "取得不可", ""],
    ]

    # 比較地点18点：地域版3、データなし4(b=4)、広域版5(d=5)、取得不可6(f=6)
    pt_rows = [
        [f"36001-001-P{i:02d}", "36001-001", f"P{i}", "徳島県", 1, 0, 0, 0, 0, 0, 0]
        for i in range(1, 19)
    ]
    reg_pt_rows = [
        ["36001-001-P01", "P1", "34.0", "134.0", "低地", "51", 1, "取得済（地域版）", "2026-10-16"],
        ["36001-001-P02", "P2", "34.0", "134.0", "低地", "51", 1, "取得済（地域版）", "2026-10-16"],
        ["36001-001-P03", "P3", "34.0", "134.0", "山地", "11", 1, "取得済（地域版）", "2026-10-16"],
    ]
    for i in range(4, 8):
        reg_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "", "", 0, "データなし", "2026-10-16"])
    for i in range(8, 13):
        reg_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "低地", "5", 1, "取得済（広域版）", "2026-10-16"])
    for i in range(13, 19):
        reg_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "", "", 0, "取得不可", ""])

    _write_csv(_make_mon_df(mon_rows), proc_dir / "monuments_36.csv")
    _write_csv(_make_pt_df(pt_rows), proc_dir / "points_36.csv")
    _write_csv(_make_reg_df(reg_mon_rows), proc_dir / "landform_region_36.csv")
    _write_csv(_make_reg_df(reg_pt_rows), proc_dir / "landform_region_points_36.csv")

    main(["--pref", "36"], base_dir=tmp_path)
    out = capsys.readouterr().out
    assert "地域版で数えた地点（全碑）：碑 2基／比較地点 3点" in out
    assert "数えていない地点（全碑）：データなし 碑 1・比較地点 4、広域版 碑 2・比較地点 5、取得不可 碑 3・比較地点 6" in out

    csv_text = (tmp_path / "output" / "landform_region_36.csv").read_text(encoding="utf-8-sig")
    assert "注：数えていない地点：データなし 碑 1・比較地点 4、広域版で補った地点 碑 2・比較地点 5、取得不可 碑 3・比較地点 6" in csv_text

    mon, pt = load_region_pref("36", tmp_path)
    df = build_region_table(mon, pt, [])
    sub = df[(df["範囲"] == "全碑") & (df["災害種別"] == "全種別")]
    # 広域版の「山地・丘陵」は含まれず、「低地」と「山地」の2行だけ
    assert list(sub["地形分類名"]) == ["低地", "山地"]
    assert list(sub["碑_件数"]) == [1, 1]
    assert list(sub["碑_割合"]) == [0.5, 0.5]
    assert list(sub["比較地点_件数"]) == [2, 1]
    assert list(sub["比較地点_割合"]) == [0.667, 0.333]


def test_b_relocated_excluded():
    """(b) 移転碑（伝承内容に「移設」）とその比較地点が「移転碑を除く」から除かれる"""
    mon = pd.DataFrame({
        "ID": ["36001-001", "36001-002"],
        "碑名": ["碑1", "碑2"],
        "所在地": ["徳島", "徳島"],
        "伝承内容": ["道路工事に伴い現在地へ移設された", "昔からこの場所にある"],
        "種別_洪水": [1, 1],
        "種別_地震": [0, 0],
        "種別_津波": [0, 0],
        "種別_土砂災害": [0, 0],
        "種別_高潮": [0, 0],
        "種別_火山災害": [0, 0],
        "種別_その他": [0, 0],
        "地域版_地形分類名": ["低地", "山地"],
        "地域版_コード": ["51", "11"],
        "地域版_状態": ["取得済（地域版）", "取得済（地域版）"],
    })
    pt = pd.DataFrame({
        "ID": ["P1", "P2", "P3"],
        "元の碑ID": ["36001-001", "36001-001", "36001-002"],
        "種別_洪水": [1, 1, 1],
        "種別_地震": [0, 0, 0],
        "種別_津波": [0, 0, 0],
        "種別_土砂災害": [0, 0, 0],
        "種別_高潮": [0, 0, 0],
        "種別_火山災害": [0, 0, 0],
        "種別_その他": [0, 0, 0],
        "地域版_地形分類名": ["低地", "低地", "山地"],
        "地域版_コード": ["51", "51", "11"],
        "地域版_状態": ["取得済（地域版）", "取得済（地域版）", "取得済（地域版）"],
    })

    rel_ids = extract_relocated(mon)["ID"].tolist()
    assert rel_ids == ["36001-001"]

    df = build_region_table(mon, pt, rel_ids)

    all_sub = df[(df["範囲"] == "全碑") & (df["災害種別"] == "全種別")]
    assert dict(zip(all_sub["地形分類名"], all_sub["碑_件数"])) == {"低地": 1, "山地": 1}
    assert dict(zip(all_sub["地形分類名"], all_sub["比較地点_件数"])) == {"低地": 2, "山地": 1}

    ex_sub = df[(df["範囲"] == "移転碑を除く") & (df["災害種別"] == "全種別")]
    assert dict(zip(ex_sub["地形分類名"], ex_sub["碑_件数"])) == {"低地": 0, "山地": 1}
    assert dict(zip(ex_sub["地形分類名"], ex_sub["碑_割合"])) == {"低地": 0.0, "山地": 1.0}
    assert dict(zip(ex_sub["地形分類名"], ex_sub["比較地点_件数"])) == {"低地": 0, "山地": 1}
    assert dict(zip(ex_sub["地形分類名"], ex_sub["比較地点_割合"])) == {"低地": 0.0, "山地": 1.0}


def test_c_disaster_type_filtering_multi_label():
    """(c) 災害種別の絞り込み（1基が2種別を持つ例）"""
    mon = pd.DataFrame({
        "ID": ["M1", "M2"],
        "碑名": ["碑1", "碑2"],
        "所在地": ["徳島", "徳島"],
        "伝承内容": ["伝承1", "伝承2"],
        "種別_洪水": [1, 1],
        "種別_地震": [0, 0],
        "種別_津波": [0, 0],
        "種別_土砂災害": [1, 0],  # M1 は洪水と土砂災害の2種別を持つ
        "種別_高潮": [0, 0],
        "種別_火山災害": [0, 0],
        "種別_その他": [0, 0],
        "地域版_地形分類名": ["山地", "低地"],
        "地域版_コード": ["11", "51"],
        "地域版_状態": ["取得済（地域版）", "取得済（地域版）"],
    })
    pt = pd.DataFrame({
        "ID": ["P1", "P2"],
        "元の碑ID": ["M1", "M2"],
        "種別_洪水": [1, 1],
        "種別_地震": [0, 0],
        "種別_津波": [0, 0],
        "種別_土砂災害": [1, 0],
        "種別_高潮": [0, 0],
        "種別_火山災害": [0, 0],
        "種別_その他": [0, 0],
        "地域版_地形分類名": ["山地", "低地"],
        "地域版_コード": ["11", "51"],
        "地域版_状態": ["取得済（地域版）", "取得済（地域版）"],
    })

    df = build_region_table(mon, pt, [])

    flood = df[(df["範囲"] == "全碑") & (df["災害種別"] == "洪水")]
    assert dict(zip(flood["地形分類名"], flood["碑_件数"])) == {"山地": 1, "低地": 1}

    landslide = df[(df["範囲"] == "全碑") & (df["災害種別"] == "土砂災害")]
    assert dict(zip(landslide["地形分類名"], landslide["碑_件数"])) == {"山地": 1, "低地": 0}
    assert dict(zip(landslide["地形分類名"], landslide["比較地点_件数"])) == {"山地": 1, "低地": 0}


def test_d_ordering_and_zero_rows_in_all_groups():
    """(d) どのグループにも同じ分類が同じ順で出る（0件の行も出る）。並び順の同数の決め方（比較地点 → 碑 → コード）"""
    # 分類4つ：
    # A(code="51"): 比較地点 3, 碑 0 -> 比較地点最多で1位
    # B(code="41"): 比較地点 1, 碑 2 -> 比較地点1で並み、碑2で2位
    # C(code="9"):  比較地点 1, 碑 1 -> 比較地点1・碑1で並み、コード数値 9 < 11 で3位（文字列比較なら "11" < "9" になるケース）
    # D(code="11"): 比較地点 1, 碑 1 -> コード数値 11 で4位
    mon = pd.DataFrame({
        "ID": ["M1", "M2", "M3", "M4"],
        "碑名": ["1", "2", "3", "4"],
        "所在地": ["所", "所", "所", "所"],
        "伝承内容": ["", "", "", ""],
        "種別_洪水": [1, 1, 0, 0],
        "種別_地震": [0, 0, 1, 1],
        "種別_津波": [0, 0, 0, 0],
        "種別_土砂災害": [0, 0, 0, 0],
        "種別_高潮": [0, 0, 0, 0],
        "種別_火山災害": [0, 0, 0, 0],
        "種別_その他": [0, 0, 0, 0],
        "地域版_地形分類名": ["台地・段丘", "台地・段丘", "テスト分類C", "山地"],
        "地域版_コード": ["41", "41", "9", "11"],
        "地域版_状態": ["取得済（地域版）"] * 4,
    })
    pt = pd.DataFrame({
        "ID": ["P1", "P2", "P3", "P4", "P5", "P6"],
        "元の碑ID": ["M1", "M1", "M1", "M2", "M3", "M4"],
        "種別_洪水": [1, 1, 1, 1, 0, 0],
        "種別_地震": [0, 0, 0, 0, 1, 1],
        "種別_津波": [0, 0, 0, 0, 0, 0],
        "種別_土砂災害": [0, 0, 0, 0, 0, 0],
        "種別_高潮": [0, 0, 0, 0, 0, 0],
        "種別_火山災害": [0, 0, 0, 0, 0, 0],
        "種別_その他": [0, 0, 0, 0, 0, 0],
        "地域版_地形分類名": ["低地", "低地", "低地", "台地・段丘", "テスト分類C", "山地"],
        "地域版_コード": ["51", "51", "51", "41", "9", "11"],
        "地域版_状態": ["取得済（地域版）"] * 6,
    })

    df = build_region_table(mon, pt, [])
    expected_order = ["低地", "台地・段丘", "テスト分類C", "山地"]
    expected_codes = ["51", "41", "9", "11"]

    # 2範囲 × 8種別 ＝ 16グループのすべてで同じ4分類が同じ順で出て、0件の行も出ること
    assert len(df) == 2 * 8 * 4
    for r in ["全碑", "移転碑を除く"]:
        for dt in ["全種別", "洪水", "地震", "津波", "土砂災害", "高潮", "火山災害", "その他"]:
            sub = df[(df["範囲"] == r) & (df["災害種別"] == dt)]
            assert list(sub["地形分類名"]) == expected_order
            assert list(sub["地形分類コード"]) == expected_codes


def test_e_zero_denominator_ratio_is_zero():
    """(e) 割合の分母が 0 のとき 0"""
    mon = pd.DataFrame({
        "ID": ["M1"],
        "碑名": ["碑1"],
        "所在地": ["徳島"],
        "伝承内容": ["伝承"],
        "種別_洪水": [1],
        "種別_地震": [0],
        "種別_津波": [0],
        "種別_土砂災害": [0],
        "種別_高潮": [0],
        "種別_火山災害": [0],
        "種別_その他": [0],
        "地域版_地形分類名": ["低地"],
        "地域版_コード": ["51"],
        "地域版_状態": ["取得済（地域版）"],
    })
    pt = pd.DataFrame({
        "ID": ["P1"],
        "元の碑ID": ["M1"],
        "種別_洪水": [1],
        "種別_地震": [0],
        "種別_津波": [0],
        "種別_土砂災害": [0],
        "種別_高潮": [0],
        "種別_火山災害": [0],
        "種別_その他": [0],
        "地域版_地形分類名": ["低地"],
        "地域版_コード": ["51"],
        "地域版_状態": ["取得済（地域版）"],
    })

    df = build_region_table(mon, pt, [])
    # 火山災害は碑0・比較地点0なので分母0
    volc = df[(df["範囲"] == "全碑") & (df["災害種別"] == "火山災害")].iloc[0]
    assert volc["碑_件数"] == 0
    assert volc["碑_割合"] == 0
    assert volc["比較地点_件数"] == 0
    assert volc["比較地点_割合"] == 0


def test_f_missing_files_error_and_no_output(tmp_path, capsys):
    """(f) 入力ファイルが足りない県があると、エラー文2行・終了コード 1・何も書き出さない"""
    proc_dir = tmp_path / "data" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 35 は monuments_35.csv のみ（残り3ファイル不足）、36 は全ファイルなし
    _write_csv(
        _make_mon_df([["35001-001", "碑", "山口県", "", 1, 0, 0, 0, 0, 0, 0]]),
        proc_dir / "monuments_35.csv",
    )

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35,36"], base_dir=tmp_path)

    assert e.value.code == 1
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert len(out_lines) == 2
    assert out_lines[0] == "エラー：ファイルが足りない県があります：山口県（35）、徳島県（36）"
    assert out_lines[1] == '先に実行してください：python src/run_region_batch.py --pref "35,36"'

    out_dir = tmp_path / "output"
    assert not out_dir.exists() or list(out_dir.iterdir()) == []


def test_g_output_format_bom_lf_columns_and_notes(tmp_path, monkeypatch):
    """(g) 出力が BOM 付き・LF・列名と順番が指示どおり"""
    monkeypatch.setattr("src.summarize_region.PREFECTURES", {"35": "山口県", "36": "徳島県"})
    monkeypatch.setattr("src.load_monuments.PREFECTURES", {"35": "山口県", "36": "徳島県"})

    proc_dir = tmp_path / "data" / "processed"
    for pref, lf_name, lf_code in [("35", "山地", "11"), ("36", "低地", "51")]:
        _write_csv(
            _make_mon_df([[f"{pref}001-001", "碑1", "県", "伝承", 1, 0, 0, 0, 0, 0, 0]]),
            proc_dir / f"monuments_{pref}.csv",
        )
        _write_csv(
            _make_pt_df([[f"{pref}001-001-P1", f"{pref}001-001", "P1", "県", 1, 0, 0, 0, 0, 0, 0]]),
            proc_dir / f"points_{pref}.csv",
        )
        _write_csv(
            _make_reg_df([[f"{pref}001-001", "碑1", "34.0", "134.0", lf_name, lf_code, 1, "取得済（地域版）", "2026-10-16"]]),
            proc_dir / f"landform_region_{pref}.csv",
        )
        _write_csv(
            _make_reg_df([[f"{pref}001-001-P1", "P1", "34.0", "134.0", lf_name, lf_code, 1, "取得済（地域版）", "2026-10-16"]]),
            proc_dir / f"landform_region_points_{pref}.csv",
        )

    main(["--pref", "all"], base_dir=tmp_path)

    out_dir = tmp_path / "output"
    for fname in ["landform_region_35.csv", "landform_region_36.csv", "landform_region_all.csv"]:
        fpath = out_dir / fname
        assert fpath.exists()
        raw = fpath.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), f"{fname} に UTF-8 BOM がありません"
        assert b"\r" not in raw, f"{fname} に CR (\\r) が含まれています"

        lines = fpath.read_text(encoding="utf-8-sig").splitlines()
        header = lines[0].split(",")
        assert header == [
            "範囲",
            "災害種別",
            "地形分類名",
            "地形分類コード",
            "碑_件数",
            "碑_割合",
            "比較地点_件数",
            "比較地点_割合",
        ]
        # 末尾4行の注・出典の確認
        assert lines[-4] == "注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。"
        assert lines[-3] == "注：地形分類（自然地形）の地域版（中分類）で値が取れた地点だけを数えています。詳細版の表（landform_XX.csv・landform_all.csv）とは分類の細かさが違うため、別の表にしています。"
        assert lines[-2] == "注：数えていない地点：データなし 碑 0・比較地点 0、広域版で補った地点 碑 0・比較地点 0、取得不可 碑 0・比較地点 0"
        assert lines[-1] == "出典：国土地理院 地形分類（自然地形）を加工して作成"


def test_h_real_data_verification():
    """(h) 実データでの照合（data/processed に47県の4ファイルがそろっているときだけ動かし、なければ pytest.skip）"""
    root_dir = get_project_root()
    missing = check_region_files(sorted(PREFECTURES.keys()), root_dir)
    if missing:
        pytest.skip("実データが47県そろっていないためスキップします")

    # 徳島（36）の照合
    mon_36, pt_36 = load_region_pref("36", root_dir)
    rel_36 = extract_relocated(mon_36)["ID"].tolist()
    df_36 = build_region_table(mon_36, pt_36, rel_36)
    assert len(df_36) == 2 * 8 * 4  # 64行
    sub_36 = df_36[(df_36["範囲"] == "全碑") & (df_36["災害種別"] == "全種別")]
    assert len(sub_36) == 4
    expected_36 = [
        ("山地", 24, 221),
        ("低地", 44, 112),
        ("丘陵・小起伏地", 0, 8),
        ("台地・段丘", 1, 2),
    ]
    for idx, (name, m_c, p_c) in enumerate(expected_36):
        row = sub_36.iloc[idx]
        assert row["地形分類名"] == name
        assert row["碑_件数"] == m_c
        assert row["比較地点_件数"] == p_c

    # 岩手（03）の照合
    mon_03, pt_03 = load_region_pref("03", root_dir)
    rel_03 = extract_relocated(mon_03)["ID"].tolist()
    df_03 = build_region_table(mon_03, pt_03, rel_03)
    sub_03 = df_03[(df_03["範囲"] == "全碑") & (df_03["災害種別"] == "全種別")]
    expected_03 = [
        ("山地", 46, 360),
        ("丘陵・小起伏地", 42, 243),
        ("低地", 62, 115),
        ("台地・段丘", 13, 80),
    ]
    for idx, (name, m_c, p_c) in enumerate(expected_03):
        row = sub_03.iloc[idx]
        assert row["地形分類名"] == name
        assert row["碑_件数"] == m_c
        assert row["比較地点_件数"] == p_c

    # 北海道（01）は8分類
    mon_01, pt_01 = load_region_pref("01", root_dir)
    rel_01 = extract_relocated(mon_01)["ID"].tolist()
    df_01 = build_region_table(mon_01, pt_01, rel_01)
    sub_01 = df_01[(df_01["範囲"] == "全碑") & (df_01["災害種別"] == "全種別")]
    assert len(sub_01) == 8

    # 全国（47都道府県）の照合
    mon_list = []
    pt_list = []
    for pref in sorted(PREFECTURES.keys()):
        m, p = load_region_pref(pref, root_dir)
        mon_list.append(m)
        pt_list.append(p)
    all_mon = pd.concat(mon_list, ignore_index=True)
    all_pt = pd.concat(pt_list, ignore_index=True)
    all_rel = extract_relocated(all_mon)["ID"].tolist()
    df_all = build_region_table(all_mon, all_pt, all_rel)

    assert len(df_all) == 192  # 2 * 8 * 12
    sub_all = df_all[(df_all["範囲"] == "全碑") & (df_all["災害種別"] == "全種別")]
    assert len(sub_all) == 12

    expected_order_all = [
        "低地",
        "山地",
        "丘陵・小起伏地",
        "台地・段丘",
        "火山麓地形",
        "火山地形（やや不明瞭）",
        "火山地形（明瞭）",
        "火山性丘陵",
        "砂丘",
        "残丘状地形",
        "湖",
        "カルスト地形",
    ]
    assert list(sub_all["地形分類名"]) == expected_order_all

    by_name = sub_all.set_index("地形分類名")
    assert (by_name.loc["低地", "碑_件数"], by_name.loc["低地", "比較地点_件数"]) == (1325, 4331)
    assert (by_name.loc["山地", "碑_件数"], by_name.loc["山地", "比較地点_件数"]) == (472, 4078)
    assert (by_name.loc["湖", "碑_件数"], by_name.loc["湖", "比較地点_件数"]) == (1, 50)
    assert (by_name.loc["カルスト地形", "碑_件数"], by_name.loc["カルスト地形", "比較地点_件数"]) == (2, 5)

    # 数えていない地点の照合
    assert count_uncounted(all_mon, all_pt) == (5, 118, 0, 0, 0, 0)

