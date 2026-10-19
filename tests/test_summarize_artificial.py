# -*- coding: utf-8 -*-
"""src/summarize_artificial.py の単体テストおよび実データ照合テスト。"""

import pandas as pd
import pytest

from src.prefectures import PREFECTURES
from src.summarize import extract_relocated
from src.summarize_artificial import (
    FIXED_ARTIFICIAL_NAMES,
    get_project_root,
    check_artificial_files,
    load_artificial_pref,
    build_artificial_table,
    build_artificial_cross_table,
    build_artificial_notes,
    build_artificial_cross_notes,
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


def _make_art_df(rows):
    """テスト用の landform_artificial DataFrame を作成する"""
    cols = [
        "ID",
        "碑名",
        "緯度",
        "経度",
        "人工地形名",
        "人工地形コード",
        "人工地形_重なり数",
        "人工地形_状態",
        "取得日",
    ]
    return pd.DataFrame(rows, columns=cols)


def _make_lf_df(rows):
    """テスト用の landform（詳細版）DataFrame を作成する"""
    cols = [
        "ID",
        "碑名",
        "緯度",
        "経度",
        "地形分類名",
        "地形分類コード",
        "地形分類_状態",
        "取得日",
    ]
    return pd.DataFrame(rows, columns=cols)


def _write_csv(df, path):
    """テスト用CSVを UTF-8 BOM・LF で書き出す"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        df.to_csv(f, index=False, lineterminator="\n")


def test_a_count_only_valid_status_and_notes(tmp_path, capsys):
    """(a) 「取得済」「人工地形なし」だけを数え、範囲外・取得不可を数えない（注の行の a〜d の件数も確かめる）"""
    proc_dir = tmp_path / "data" / "processed"

    # 碑7基：取得済1、人工地形なし1（数える＝2）、範囲外2(a=2)、取得不可3(c=3)
    mon_rows = [
        [f"36001-{i:03d}", f"碑{i}", "徳島県", "伝承", 1, 0, 0, 0, 0, 0, 0]
        for i in range(1, 8)
    ]
    art_mon_rows = [
        ["36001-001", "碑1", "34.0", "134.0", "盛土地・埋立地", "301011", 1, "取得済", "2026-10-18"],
        ["36001-002", "碑2", "34.0", "134.0", "", "", 0, "人工地形なし", "2026-10-18"],
        ["36001-003", "碑3", "34.0", "134.0", "", "", 0, "範囲外", "2026-10-18"],
        ["36001-004", "碑4", "34.0", "134.0", "", "", 0, "範囲外", "2026-10-18"],
        ["36001-005", "碑5", "34.0", "134.0", "", "", 0, "取得不可", ""],
        ["36001-006", "碑6", "34.0", "134.0", "", "", 0, "取得不可", ""],
        ["36001-007", "碑7", "34.0", "134.0", "", "", 0, "取得不可", ""],
    ]
    lf_mon_rows = [
        ["36001-001", "碑1", "34.0", "134.0", "氾濫平野・海岸平野", "10501", "取得済", "2026-10-10"],
        ["36001-002", "碑2", "34.0", "134.0", "山地斜面等", "10101", "取得済", "2026-10-10"],
        ["36001-003", "碑3", "34.0", "134.0", "", "", "データなし", "2026-10-10"],
        ["36001-004", "碑4", "34.0", "134.0", "", "", "データなし", "2026-10-10"],
        ["36001-005", "碑5", "34.0", "134.0", "", "", "取得不可", ""],
        ["36001-006", "碑6", "34.0", "134.0", "", "", "取得不可", ""],
        ["36001-007", "碑7", "34.0", "134.0", "", "", "取得不可", ""],
    ]

    # 比較地点13点：取得済1、人工地形なし3（数える＝4）、範囲外4(b=4)、取得不可5(d=5)
    pt_rows = [
        [f"36001-001-P{i:02d}", "36001-001", f"P{i}", "徳島県", 1, 0, 0, 0, 0, 0, 0]
        for i in range(1, 14)
    ]
    art_pt_rows = [
        ["36001-001-P01", "P1", "34.0", "134.0", "切土地", "301012", 1, "取得済", "2026-10-18"],
        ["36001-001-P02", "P2", "34.0", "134.0", "", "", 0, "人工地形なし", "2026-10-18"],
        ["36001-001-P03", "P3", "34.0", "134.0", "", "", 0, "人工地形なし", "2026-10-18"],
        ["36001-001-P04", "P4", "34.0", "134.0", "", "", 0, "人工地形なし", "2026-10-18"],
    ]
    lf_pt_rows = [
        ["36001-001-P01", "P1", "34.0", "134.0", "山地斜面等", "10101", "取得済", "2026-10-10"],
        ["36001-001-P02", "P2", "34.0", "134.0", "山地斜面等", "10101", "取得済", "2026-10-10"],
        ["36001-001-P03", "P3", "34.0", "134.0", "氾濫平野・海岸平野", "10501", "取得済", "2026-10-10"],
        ["36001-001-P04", "P4", "34.0", "134.0", "氾濫平野・海岸平野", "10501", "取得済", "2026-10-10"],
    ]
    for i in range(5, 9):
        art_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "", "", 0, "範囲外", "2026-10-18"])
        lf_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "", "", "データなし", "2026-10-10"])
    for i in range(9, 14):
        art_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "", "", 0, "取得不可", ""])
        lf_pt_rows.append([f"36001-001-P{i:02d}", f"P{i}", "34.0", "134.0", "", "", "取得不可", ""])

    _write_csv(_make_mon_df(mon_rows), proc_dir / "monuments_36.csv")
    _write_csv(_make_pt_df(pt_rows), proc_dir / "points_36.csv")
    _write_csv(_make_art_df(art_mon_rows), proc_dir / "landform_artificial_36.csv")
    _write_csv(_make_art_df(art_pt_rows), proc_dir / "landform_artificial_points_36.csv")
    _write_csv(_make_lf_df(lf_mon_rows), proc_dir / "landform_36.csv")
    _write_csv(_make_lf_df(lf_pt_rows), proc_dir / "landform_points_36.csv")

    main(["--pref", "36"], base_dir=tmp_path)
    out = capsys.readouterr().out
    assert "人工地形を調べた地点（全碑）：碑 2基／比較地点 4点" in out
    assert "数えていない地点（全碑）：範囲外 碑 2・比較地点 4、取得不可 碑 3・比較地点 5" in out
    assert "人工地形ありの割合（全碑・全種別）：碑 0.500／比較地点 0.250" in out

    csv_text = (tmp_path / "output" / "landform_artificial_36.csv").read_text(encoding="utf-8-sig")
    assert "注：数えていない地点：範囲外（詳細版のデータなし）碑 2・比較地点 4、取得不可 碑 3・比較地点 5" in csv_text

    mon, pt = load_artificial_pref("36", tmp_path)
    assert count_uncounted(mon, pt) == (2, 4, 3, 5)
    df = build_artificial_table(mon, pt, [])
    sub = df[(df["範囲"] == "全碑") & (df["災害種別"] == "全種別")].set_index("人工地形名")
    assert sub.loc["盛土地・埋立地", "碑_件数"] == 1
    assert sub.loc["盛土地・埋立地", "碑_割合"] == 0.5
    assert sub.loc["人工地形なし", "碑_件数"] == 1
    assert sub.loc["人工地形なし", "碑_割合"] == 0.5
    assert sub.loc["切土地", "比較地点_件数"] == 1
    assert sub.loc["切土地", "比較地点_割合"] == 0.25
    assert sub.loc["人工地形なし", "比較地点_件数"] == 3
    assert sub.loc["人工地形なし", "比較地点_割合"] == 0.75


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
        "人工地形名": ["盛土地・埋立地", ""],
        "人工地形_状態": ["取得済", "人工地形なし"],
        "地形分類名": ["氾濫平野・海岸平野", "山地斜面等"],
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
        "人工地形名": ["盛土地・埋立地", "盛土地・埋立地", ""],
        "人工地形_状態": ["取得済", "取得済", "人工地形なし"],
        "地形分類名": ["氾濫平野・海岸平野", "氾濫平野・海岸平野", "山地斜面等"],
    })

    rel_ids = extract_relocated(mon)["ID"].tolist()
    assert rel_ids == ["36001-001"]

    df = build_artificial_table(mon, pt, rel_ids)

    all_sub = df[(df["範囲"] == "全碑") & (df["災害種別"] == "全種別")].set_index("人工地形名")
    assert all_sub.loc["盛土地・埋立地", "碑_件数"] == 1
    assert all_sub.loc["人工地形なし", "碑_件数"] == 1
    assert all_sub.loc["盛土地・埋立地", "比較地点_件数"] == 2
    assert all_sub.loc["人工地形なし", "比較地点_件数"] == 1

    ex_sub = df[(df["範囲"] == "移転碑を除く") & (df["災害種別"] == "全種別")].set_index("人工地形名")
    assert ex_sub.loc["盛土地・埋立地", "碑_件数"] == 0
    assert ex_sub.loc["盛土地・埋立地", "碑_割合"] == 0.0
    assert ex_sub.loc["人工地形なし", "碑_件数"] == 1
    assert ex_sub.loc["人工地形なし", "碑_割合"] == 1.0
    assert ex_sub.loc["盛土地・埋立地", "比較地点_件数"] == 0
    assert ex_sub.loc["盛土地・埋立地", "比較地点_割合"] == 0.0
    assert ex_sub.loc["人工地形なし", "比較地点_件数"] == 1
    assert ex_sub.loc["人工地形なし", "比較地点_割合"] == 1.0


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
        "人工地形名": ["切土地", "盛土地・埋立地"],
        "人工地形_状態": ["取得済", "取得済"],
        "地形分類名": ["山地斜面等", "氾濫平野・海岸平野"],
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
        "人工地形名": ["切土地", ""],
        "人工地形_状態": ["取得済", "人工地形なし"],
        "地形分類名": ["山地斜面等", "氾濫平野・海岸平野"],
    })

    df = build_artificial_table(mon, pt, [])

    flood = df[(df["範囲"] == "全碑") & (df["災害種別"] == "洪水")].set_index("人工地形名")
    assert flood.loc["切土地", "碑_件数"] == 1
    assert flood.loc["盛土地・埋立地", "碑_件数"] == 1
    assert flood.loc["切土地", "比較地点_件数"] == 1
    assert flood.loc["人工地形なし", "比較地点_件数"] == 1

    landslide = df[(df["範囲"] == "全碑") & (df["災害種別"] == "土砂災害")].set_index("人工地形名")
    assert landslide.loc["切土地", "碑_件数"] == 1
    assert landslide.loc["盛土地・埋立地", "碑_件数"] == 0
    assert landslide.loc["切土地", "比較地点_件数"] == 1
    assert landslide.loc["人工地形なし", "比較地点_件数"] == 0


def test_d_fixed_category_order_and_extra_category():
    """(d) 区分の6行が固定順で、0件の行も出る。5つ以外の人工地形名（例「不明（code=99999）」）は改変工事中と人工地形なしの間に入る"""
    mon = pd.DataFrame({
        "ID": ["M1"],
        "碑名": ["碑1"],
        "所在地": ["所"],
        "伝承内容": [""],
        "種別_洪水": [1],
        "種別_地震": [0],
        "種別_津波": [0],
        "種別_土砂災害": [0],
        "種別_高潮": [0],
        "種別_火山災害": [0],
        "種別_その他": [0],
        "人工地形名": ["干拓地"],
        "人工地形_状態": ["取得済"],
        "地形分類名": ["旧水部"],
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
        "人工地形名": [""],
        "人工地形_状態": ["人工地形なし"],
        "地形分類名": ["旧水部"],
    })

    df = build_artificial_table(mon, pt, [])
    expected_6 = FIXED_ARTIFICIAL_NAMES + ["人工地形なし"]
    assert len(df) == 2 * 8 * 6  # 96行
    for r in ["全碑", "移転碑を除く"]:
        for dt in ["全種別", "洪水", "地震", "津波", "土砂災害", "高潮", "火山災害", "その他"]:
            sub = df[(df["範囲"] == r) & (df["災害種別"] == dt)]
            assert list(sub["人工地形名"]) == expected_6

    # 5つ以外の人工地形名が混ざったケース
    pt_extra = pd.DataFrame({
        "ID": ["P1", "P2"],
        "元の碑ID": ["M1", "M1"],
        "種別_洪水": [1, 1],
        "種別_地震": [0, 0],
        "種別_津波": [0, 0],
        "種別_土砂災害": [0, 0],
        "種別_高潮": [0, 0],
        "種別_火山災害": [0, 0],
        "種別_その他": [0, 0],
        "人工地形名": ["不明（code=99999）", "不明（code=88888）"],
        "人工地形_状態": ["取得済", "取得済"],
        "地形分類名": ["旧水部", "旧水部"],
    })
    df_extra = build_artificial_table(mon, pt_extra, [])
    expected_extra = FIXED_ARTIFICIAL_NAMES + ["不明（code=88888）", "不明（code=99999）", "人工地形なし"]
    sub_extra = df_extra[(df_extra["範囲"] == "全碑") & (df_extra["災害種別"] == "全種別")]
    assert list(sub_extra["人工地形名"]) == expected_extra


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
        "人工地形名": ["盛土地・埋立地"],
        "人工地形_状態": ["取得済"],
        "地形分類名": ["氾濫平野・海岸平野"],
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
        "人工地形名": [""],
        "人工地形_状態": ["人工地形なし"],
        "地形分類名": ["氾濫平野・海岸平野"],
    })

    df = build_artificial_table(mon, pt, [])
    volc = df[(df["範囲"] == "全碑") & (df["災害種別"] == "火山災害")]
    assert (volc["碑_件数"] == 0).all()
    assert (volc["碑_割合"] == 0).all()
    assert (volc["比較地点_件数"] == 0).all()
    assert (volc["比較地点_割合"] == 0).all()


def test_f_cross_table_natural_ordering_and_ratios():
    """(f) 表2：自然地形の並び順（比較地点 → 碑 → 名前）と、割合が同じ自然地形の中の割合になっている"""
    # 自然地形4つ：
    # 「扇状地」: 比較地点 3, 碑 0 -> 1位
    # 「台地・段丘」: 比較地点 1, 碑 2 -> 2位
    # 「旧水部」: 比較地点 1, 碑 1 -> 名前順で「旧水部」 < 「自然堤防」 -> 3位
    # 「自然堤防」: 比較地点 1, 碑 1 -> 4位
    mon = pd.DataFrame({
        "ID": ["M1", "M2", "M3", "M4"],
        "碑名": ["1", "2", "3", "4"],
        "所在地": ["所"] * 4,
        "伝承内容": ["移設された", "", "", ""],  # M1 は移転碑
        "種別_洪水": [1, 1, 1, 1],
        "種別_地震": [0] * 4,
        "種別_津波": [0] * 4,
        "種別_土砂災害": [0] * 4,
        "種別_高潮": [0] * 4,
        "種別_火山災害": [0] * 4,
        "種別_その他": [0] * 4,
        "人工地形名": ["盛土地・埋立地", "", "干拓地", ""],
        "人工地形_状態": ["取得済", "人工地形なし", "取得済", "人工地形なし"],
        "地形分類名": ["台地・段丘", "台地・段丘", "旧水部", "自然堤防"],
    })
    pt = pd.DataFrame({
        "ID": ["P1", "P2", "P3", "P4", "P5", "P6"],
        "元の碑ID": ["M2", "M2", "M2", "M1", "M3", "M4"],
        "種別_洪水": [1] * 6,
        "種別_地震": [0] * 6,
        "種別_津波": [0] * 6,
        "種別_土砂災害": [0] * 6,
        "種別_高潮": [0] * 6,
        "種別_火山災害": [0] * 6,
        "種別_その他": [0] * 6,
        "人工地形名": ["切土地", "", "", "盛土地・埋立地", "干拓地", ""],
        "人工地形_状態": ["取得済", "人工地形なし", "人工地形なし", "取得済", "取得済", "人工地形なし"],
        "地形分類名": ["扇状地", "扇状地", "扇状地", "台地・段丘", "旧水部", "自然堤防"],
    })

    rel_ids = extract_relocated(mon)["ID"].tolist()
    df_cross = build_artificial_cross_table(mon, pt, rel_ids)

    expected_nat_order = ["扇状地", "台地・段丘", "旧水部", "自然堤防"]
    assert len(df_cross) == 2 * 4 * 6

    for r in ["全碑", "移転碑を除く"]:
        sub_r = df_cross[df_cross["範囲"] == r]
        nat_in_r = list(dict.fromkeys(sub_r["自然地形名"]))
        assert nat_in_r == expected_nat_order

    # 全碑・扇状地：碑0、比較地点3（切土地1、人工地形なし2）
    fan_all = df_cross[(df_cross["範囲"] == "全碑") & (df_cross["自然地形名"] == "扇状地")].set_index("人工地形名")
    assert fan_all.loc["切土地", "碑_件数"] == 0
    assert fan_all.loc["切土地", "碑_割合"] == 0.0
    assert fan_all.loc["切土地", "比較地点_件数"] == 1
    assert fan_all.loc["切土地", "比較地点_割合"] == 0.333
    assert fan_all.loc["人工地形なし", "比較地点_件数"] == 2
    assert fan_all.loc["人工地形なし", "比較地点_割合"] == 0.667

    # 全碑・台地・段丘：碑2（盛土地・埋立地1、人工地形なし1）、比較地点1（盛土地・埋立地1）
    ter_all = df_cross[(df_cross["範囲"] == "全碑") & (df_cross["自然地形名"] == "台地・段丘")].set_index("人工地形名")
    assert ter_all.loc["盛土地・埋立地", "碑_件数"] == 1
    assert ter_all.loc["盛土地・埋立地", "碑_割合"] == 0.5
    assert ter_all.loc["人工地形なし", "碑_件数"] == 1
    assert ter_all.loc["人工地形なし", "碑_割合"] == 0.5
    assert ter_all.loc["盛土地・埋立地", "比較地点_件数"] == 1
    assert ter_all.loc["盛土地・埋立地", "比較地点_割合"] == 1.0

    # 移転碑を除く・台地・段丘：M1とP4が除かれるため碑1（人工地形なし1）、比較地点0
    ter_ex = df_cross[(df_cross["範囲"] == "移転碑を除く") & (df_cross["自然地形名"] == "台地・段丘")].set_index("人工地形名")
    assert ter_ex.loc["人工地形なし", "碑_件数"] == 1
    assert ter_ex.loc["人工地形なし", "碑_割合"] == 1.0
    assert ter_ex.loc["盛土地・埋立地", "比較地点_件数"] == 0
    assert ter_ex.loc["盛土地・埋立地", "比較地点_割合"] == 0.0


def test_g_missing_files_error_and_no_output(tmp_path, capsys):
    """(g) 入力ファイルが足りない県があると、エラー文2行・終了コード 1・何も書き出さない"""
    proc_dir = tmp_path / "data" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 35 は5ファイルだけ（landform_points_35.csv が不足）、36 は全ファイルなし
    _write_csv(
        _make_mon_df([["35001-001", "碑", "山口県", "", 1, 0, 0, 0, 0, 0, 0]]),
        proc_dir / "monuments_35.csv",
    )
    _write_csv(
        _make_pt_df([["35001-001-P1", "35001-001", "P1", "山口県", 1, 0, 0, 0, 0, 0, 0]]),
        proc_dir / "points_35.csv",
    )
    _write_csv(
        _make_art_df([["35001-001", "碑", "34.0", "131.0", "", "", 0, "人工地形なし", "2026-10-18"]]),
        proc_dir / "landform_artificial_35.csv",
    )
    _write_csv(
        _make_art_df([["35001-001-P1", "P1", "34.0", "131.0", "", "", 0, "人工地形なし", "2026-10-18"]]),
        proc_dir / "landform_artificial_points_35.csv",
    )
    _write_csv(
        _make_lf_df([["35001-001", "碑", "34.0", "131.0", "山地斜面等", "10101", "取得済", "2026-10-10"]]),
        proc_dir / "landform_35.csv",
    )

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35,36"], base_dir=tmp_path)

    assert e.value.code == 1
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert len(out_lines) == 2
    assert out_lines[0] == "エラー：ファイルが足りない県があります：山口県（35）、徳島県（36）"
    assert out_lines[1] == '先に実行してください：python src/run_artificial_batch.py --pref "35,36"'

    out_dir = tmp_path / "output"
    assert not out_dir.exists() or list(out_dir.iterdir()) == []


def test_h_output_format_bom_lf_columns_and_pref_mode(tmp_path, monkeypatch):
    """(h) 出力が BOM 付き・LF・列名と順番が指示どおり。県指定のときは all・cross を書かない"""
    monkeypatch.setattr("src.summarize_artificial.PREFECTURES", {"35": "山口県", "36": "徳島県"})
    monkeypatch.setattr("src.load_monuments.PREFECTURES", {"35": "山口県", "36": "徳島県"})

    proc_dir = tmp_path / "data" / "processed"
    for pref, art_name, art_st, lf_name in [
        ("35", "切土地", "取得済", "山地斜面等"),
        ("36", "盛土地・埋立地", "取得済", "氾濫平野・海岸平野"),
    ]:
        _write_csv(
            _make_mon_df([[f"{pref}001-001", "碑1", "県", "伝承", 1, 0, 0, 0, 0, 0, 0]]),
            proc_dir / f"monuments_{pref}.csv",
        )
        _write_csv(
            _make_pt_df([[f"{pref}001-001-P1", f"{pref}001-001", "P1", "県", 1, 0, 0, 0, 0, 0, 0]]),
            proc_dir / f"points_{pref}.csv",
        )
        _write_csv(
            _make_art_df([[f"{pref}001-001", "碑1", "34.0", "134.0", art_name, "301011", 1, art_st, "2026-10-18"]]),
            proc_dir / f"landform_artificial_{pref}.csv",
        )
        _write_csv(
            _make_art_df([[f"{pref}001-001-P1", "P1", "34.0", "134.0", "", "", 0, "人工地形なし", "2026-10-18"]]),
            proc_dir / f"landform_artificial_points_{pref}.csv",
        )
        _write_csv(
            _make_lf_df([[f"{pref}001-001", "碑1", "34.0", "134.0", lf_name, "10101", "取得済", "2026-10-10"]]),
            proc_dir / f"landform_{pref}.csv",
        )
        _write_csv(
            _make_lf_df([[f"{pref}001-001-P1", "P1", "34.0", "134.0", lf_name, "10101", "取得済", "2026-10-10"]]),
            proc_dir / f"landform_points_{pref}.csv",
        )

    out_dir = tmp_path / "output"

    # 県指定（36のみ）のときは all・cross を書かない
    main(["--pref", "36"], base_dir=tmp_path)
    assert (out_dir / "landform_artificial_36.csv").exists()
    assert not (out_dir / "landform_artificial_35.csv").exists()
    assert not (out_dir / "landform_artificial_all.csv").exists()
    assert not (out_dir / "landform_artificial_cross_all.csv").exists()

    # all のときは県別＋all＋cross を書く
    main(["--pref", "all"], base_dir=tmp_path)
    for fname in [
        "landform_artificial_35.csv",
        "landform_artificial_36.csv",
        "landform_artificial_all.csv",
    ]:
        fpath = out_dir / fname
        assert fpath.exists()
        raw = fpath.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), f"{fname} に UTF-8 BOM がありません"
        assert b"\r" not in raw, f"{fname} に CR (\\r) が含まれています"

        lines = fpath.read_text(encoding="utf-8-sig").splitlines()
        assert lines[0].split(",") == [
            "範囲",
            "災害種別",
            "人工地形名",
            "碑_件数",
            "碑_割合",
            "比較地点_件数",
            "比較地点_割合",
        ]
        assert lines[-4] == "注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。"
        assert lines[-3] == "注：人工地形は、地形分類（自然地形）の詳細版で値が取れた地点だけで調べています。割合は「人工地形あり」と「人工地形なし」を合わせた数に対する割合です。"
        assert lines[-2] == "注：数えていない地点：範囲外（詳細版のデータなし）碑 0・比較地点 0、取得不可 碑 0・比較地点 0"
        assert lines[-1] == "出典：国土地理院 地形分類（人工地形）を加工して作成"

    cross_path = out_dir / "landform_artificial_cross_all.csv"
    assert cross_path.exists()
    raw_cross = cross_path.read_bytes()
    assert raw_cross.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw_cross
    cross_lines = cross_path.read_text(encoding="utf-8-sig").splitlines()
    assert cross_lines[0].split(",") == [
        "範囲",
        "自然地形名",
        "人工地形名",
        "碑_件数",
        "碑_割合",
        "比較地点_件数",
        "比較地点_割合",
    ]
    assert cross_lines[-3] == "注：自然地形は地形分類（自然地形）の詳細版の分類名です。割合は、同じ自然地形の中で数えた地点に対する割合です。"
    assert cross_lines[-2] == "注：数えていない地点：範囲外（詳細版のデータなし）碑 0・比較地点 0、取得不可 碑 0・比較地点 0"
    assert cross_lines[-1] == "出典：国土地理院 地形分類（自然地形）・地形分類（人工地形）を加工して作成"


def test_i_real_data_verification():
    """(i) 実データでの照合（data/processed に47県の6ファイルがそろっているときだけ動かし、なければ pytest.skip。output/ には書かない）"""
    root_dir = get_project_root()
    missing = check_artificial_files(sorted(PREFECTURES.keys()), root_dir)
    if missing:
        pytest.skip("実データが47県そろっていないためスキップします")

    # 徳島（36）の照合
    mon_36, pt_36 = load_artificial_pref("36", root_dir)
    rel_36 = extract_relocated(mon_36)["ID"].tolist()
    assert len(mon_36) == 71
    assert len(mon_36) - len(rel_36) == 69
    assert len(pt_36) == 349
    assert len(pt_36[~pt_36["元の碑ID"].isin(rel_36)]) == 339
    assert count_uncounted(mon_36, pt_36) == (11, 62, 0, 0)
    df_36 = build_artificial_table(mon_36, pt_36, rel_36)
    assert len(df_36) == 96
    sub_36 = df_36[(df_36["範囲"] == "全碑") & (df_36["災害種別"] == "全種別")].set_index("人工地形名")
    assert (sub_36.loc["盛土地・埋立地", "碑_件数"], sub_36.loc["盛土地・埋立地", "比較地点_件数"]) == (12, 29)
    assert (sub_36.loc["盛土地・埋立地", "碑_割合"], sub_36.loc["盛土地・埋立地", "比較地点_割合"]) == (0.200, 0.101)
    assert (sub_36.loc["切土地", "碑_件数"], sub_36.loc["切土地", "比較地点_件数"]) == (0, 2)
    assert (sub_36.loc["切土地", "碑_割合"], sub_36.loc["切土地", "比較地点_割合"]) == (0.000, 0.007)
    for z_name in ["干拓地", "農耕平坦化地", "改変工事中"]:
        assert (sub_36.loc[z_name, "碑_件数"], sub_36.loc[z_name, "比較地点_件数"]) == (0, 0)
    assert (sub_36.loc["人工地形なし", "碑_件数"], sub_36.loc["人工地形なし", "比較地点_件数"]) == (48, 256)

    # 佐賀（41）の照合
    mon_41, pt_41 = load_artificial_pref("41", root_dir)
    rel_41 = extract_relocated(mon_41)["ID"].tolist()
    df_41 = build_artificial_table(mon_41, pt_41, rel_41)
    sub_41 = df_41[(df_41["範囲"] == "全碑") & (df_41["災害種別"] == "全種別")].set_index("人工地形名")
    assert sub_41["碑_件数"].sum() == 35
    assert sub_41["比較地点_件数"].sum() == 173
    assert (sub_41.loc["盛土地・埋立地", "碑_件数"], sub_41.loc["盛土地・埋立地", "比較地点_件数"]) == (1, 4)
    assert (sub_41.loc["切土地", "碑_件数"], sub_41.loc["切土地", "比較地点_件数"]) == (0, 4)
    assert (sub_41.loc["干拓地", "碑_件数"], sub_41.loc["干拓地", "比較地点_件数"]) == (6, 34)
    assert (sub_41.loc["農耕平坦化地", "碑_件数"], sub_41.loc["農耕平坦化地", "比較地点_件数"]) == (0, 0)
    assert (sub_41.loc["改変工事中", "碑_件数"], sub_41.loc["改変工事中", "比較地点_件数"]) == (0, 1)
    assert (sub_41.loc["人工地形なし", "碑_件数"], sub_41.loc["人工地形なし", "比較地点_件数"]) == (28, 130)

    # 全国（47都道府県）の照合
    mon_list = []
    pt_list = []
    for pref in sorted(PREFECTURES.keys()):
        m, p = load_artificial_pref(pref, root_dir)
        mon_list.append(m)
        pt_list.append(p)
    all_mon = pd.concat(mon_list, ignore_index=True)
    all_pt = pd.concat(pt_list, ignore_index=True)
    all_rel = extract_relocated(all_mon)["ID"].tolist()

    assert count_uncounted(all_mon, all_pt) == (929, 4890, 0, 0)

    # 表1の照合
    df_all = build_artificial_table(all_mon, all_pt, all_rel)
    assert len(df_all) == 96

    def _check_table1_group(r_name, dt_name, expected_m_total, expected_p_total, expected_pairs):
        sub = df_all[(df_all["範囲"] == r_name) & (df_all["災害種別"] == dt_name)].set_index("人工地形名")
        assert int(sub["碑_件数"].sum()) == expected_m_total
        assert int(sub["比較地点_件数"].sum()) == expected_p_total
        for cat, (mc, pc) in zip(FIXED_ARTIFICIAL_NAMES + ["人工地形なし"], expected_pairs):
            assert (int(sub.loc[cat, "碑_件数"]), int(sub.loc[cat, "比較地点_件数"])) == (mc, pc)
        return sub

    _check_table1_group(
        "全碑",
        "全種別",
        1552,
        7505,
        [(199, 732), (39, 214), (47, 222), (1, 9), (2, 16), (1264, 6312)],
    )
    storm_sub = _check_table1_group(
        "全碑",
        "高潮",
        123,
        603,
        [(22, 87), (1, 11), (43, 163), (0, 2), (0, 2), (57, 338)],
    )
    assert storm_sub.loc["盛土地・埋立地", "碑_割合"] == 0.179
    assert storm_sub.loc["干拓地", "碑_割合"] == 0.350
    assert storm_sub.loc["人工地形なし", "碑_割合"] == 0.463

    _check_table1_group(
        "全碑",
        "洪水",
        729,
        3522,
        [(66, 190), (15, 85), (1, 27), (1, 6), (0, 6), (646, 3208)],
    )
    _check_table1_group(
        "移転碑を除く",
        "全種別",
        1488,
        7209,
        [(194, 695), (38, 209), (45, 210), (1, 9), (1, 15), (1209, 6071)],
    )

    # 表2の照合
    df_cross = build_artificial_cross_table(all_mon, all_pt, all_rel)
    assert len(df_cross) == 216  # 2 * 18 * 6
    expected_nat_18 = [
        "山地斜面等",
        "氾濫平野・海岸平野",
        "台地・段丘",
        "旧水部",
        "扇状地",
        "水部",
        "自然堤防",
        "砂州・砂丘",
        "旧河道",
        "山麓堆積地形",
        "後背低地・湿地",
        "河川敷・浜",
        "凹地・浅い谷",
        "崖・段丘崖",
        "地すべり地形",
        "天井川等",
        "不明（code=）",
        "落堀",
    ]
    nat_all_order = list(dict.fromkeys(df_cross[df_cross["範囲"] == "全碑"]["自然地形名"]))
    assert nat_all_order == expected_nat_18

    # 旧水部（碑114／比較地点464）
    kyu = df_cross[(df_cross["範囲"] == "全碑") & (df_cross["自然地形名"] == "旧水部")].set_index("人工地形名")
    assert (int(kyu["碑_件数"].sum()), int(kyu["比較地点_件数"].sum())) == (114, 464)
    assert (int(kyu.loc["盛土地・埋立地", "碑_件数"]), int(kyu.loc["盛土地・埋立地", "比較地点_件数"])) == (66, 242)
    assert (int(kyu.loc["干拓地", "碑_件数"]), int(kyu.loc["干拓地", "比較地点_件数"])) == (47, 219)
    assert (int(kyu.loc["改変工事中", "碑_件数"]), int(kyu.loc["改変工事中", "比較地点_件数"])) == (0, 1)
    assert (int(kyu.loc["人工地形なし", "碑_件数"]), int(kyu.loc["人工地形なし", "比較地点_件数"])) == (1, 2)
    assert kyu.loc["盛土地・埋立地", "碑_割合"] == 0.579
    assert kyu.loc["干拓地", "碑_割合"] == 0.412

    # 氾濫平野・海岸平野（451／1,882）
    plain = df_cross[(df_cross["範囲"] == "全碑") & (df_cross["自然地形名"] == "氾濫平野・海岸平野")].set_index("人工地形名")
    assert (int(plain["碑_件数"].sum()), int(plain["比較地点_件数"].sum())) == (451, 1882)
    assert (int(plain.loc["盛土地・埋立地", "碑_件数"]), int(plain.loc["盛土地・埋立地", "比較地点_件数"])) == (97, 317)
    assert (int(plain.loc["切土地", "碑_件数"]), int(plain.loc["切土地", "比較地点_件数"])) == (3, 13)
    assert (int(plain.loc["干拓地", "碑_件数"]), int(plain.loc["干拓地", "比較地点_件数"])) == (0, 1)
    assert (int(plain.loc["改変工事中", "碑_件数"]), int(plain.loc["改変工事中", "比較地点_件数"])) == (0, 2)
    assert (int(plain.loc["人工地形なし", "碑_件数"]), int(plain.loc["人工地形なし", "比較地点_件数"])) == (351, 1549)

    # 山地斜面等（205／2,460）
    slope = df_cross[(df_cross["範囲"] == "全碑") & (df_cross["自然地形名"] == "山地斜面等")].set_index("人工地形名")
    assert (int(slope["碑_件数"].sum()), int(slope["比較地点_件数"].sum())) == (205, 2460)
    assert (int(slope.loc["盛土地・埋立地", "碑_件数"]), int(slope.loc["盛土地・埋立地", "比較地点_件数"])) == (3, 40)
    assert (int(slope.loc["切土地", "碑_件数"]), int(slope.loc["切土地", "比較地点_件数"])) == (21, 143)
    assert (int(slope.loc["農耕平坦化地", "碑_件数"]), int(slope.loc["農耕平坦化地", "比較地点_件数"])) == (1, 9)
    assert (int(slope.loc["改変工事中", "碑_件数"]), int(slope.loc["改変工事中", "比較地点_件数"])) == (2, 13)
    assert (int(slope.loc["人工地形なし", "碑_件数"]), int(slope.loc["人工地形なし", "比較地点_件数"])) == (178, 2255)

