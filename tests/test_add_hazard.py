import pytest
import os
import csv
import sys
import subprocess
import codecs
from io import BytesIO
from PIL import Image
from pathlib import Path
from unittest.mock import patch

from src.hazard_layers import SHINSUI_LEGEND, DOSHA_LEGENDS, DOSHA_NAMES
from src.add_hazard import (
    lonlat_to_pixel,
    classify_pixel,
    summarize_dosha,
    process_monuments,
    main as hazard_main,
    PROJECT_ROOT
)

def test_lonlat_to_pixel():
    x, y, i, j = lonlat_to_pixel(134.584699, 34.066366, 17)
    assert (x, y, i, j) == (114536, 52329, 203, 249)
    x, y, i, j = lonlat_to_pixel(134.361023, 33.626738, 17)
    assert (x, y, i, j) == (114455, 52522, 91, 179)
    x, y, i, j = lonlat_to_pixel(133.829332, 33.876322, 17)
    assert (x, y, i, j) == (114261, 52413, 197, 104)

def test_classify_pixel_shinsui():
    for color, label in SHINSUI_LEGEND:
        assert classify_pixel((*color, 255), SHINSUI_LEGEND) == ('区域内', label, '完全一致')
    assert classify_pixel((255, 215, 190, 255), SHINSUI_LEGEND) == ('区域内', '0.5m〜3m', '近い色')
    assert classify_pixel((255, 255, 179, 0), SHINSUI_LEGEND) == ('区域外', '', '')
    assert classify_pixel((255, 255, 179, 127), SHINSUI_LEGEND) == ('区域外', '', '')
    assert classify_pixel((255, 255, 179, 128), SHINSUI_LEGEND) == ('区域内', '0.3m未満', '完全一致')
    assert classify_pixel(None, SHINSUI_LEGEND) == ('区域外', '', '')

def test_classify_pixel_dosha():
    for key, palette in DOSHA_LEGENDS.items():
        for color, label in palette:
            assert classify_pixel((*color, 255), palette) == ('区域内', label, '完全一致')
    assert classify_pixel((250, 70, 0, 255), DOSHA_LEGENDS['kyukei']) == ('区域内', '特別警戒区域（指定済）', '近い色')

def test_summarize_dosha():
    # ①土石流が警戒・急傾斜が特別 → 特別警戒区域・「土石流・急傾斜地の崩壊」
    res = {
        'doseki': ('区域内', '警戒区域（指定済）', '完全一致'),
        'kyukei': ('区域内', '特別警戒区域（指定済）', '完全一致'),
        'jisuberi': ('区域外', '', '')
    }
    assert summarize_dosha(res) == ('区域内', '特別警戒区域', '土石流・急傾斜地の崩壊', '', '完全一致')
    
    # ②急傾斜が警戒（指定予定）だけ → 警戒区域・指定予定「あり」
    res = {
        'doseki': ('区域外', '', ''),
        'kyukei': ('区域内', '警戒区域（指定予定）', '完全一致'),
        'jisuberi': ('区域外', '', '')
    }
    assert summarize_dosha(res) == ('区域内', '警戒区域', '急傾斜地の崩壊', 'あり', '完全一致')
    
    # ③3つとも区域外 → 区域外・各列空欄
    res = {k: ('区域外', '', '') for k in ['doseki', 'kyukei', 'jisuberi']}
    assert summarize_dosha(res) == ('区域外', '', '', '', '')
    
    # ④地すべりが取得不可 → 取得不可
    res = {
        'doseki': ('区域外', '', ''),
        'kyukei': ('区域外', '', ''),
        'jisuberi': ('取得不可', '', '')
    }
    assert summarize_dosha(res) == ('取得不可', '', '', '', '')
    
    # ⑤近い色を1つ含む → 色の一致「近い色」
    res = {
        'doseki': ('区域内', '警戒区域（指定済）', '近い色'),
        'kyukei': ('区域外', '', ''),
        'jisuberi': ('区域内', '特別警戒区域（指定済）', '完全一致')
    }
    assert summarize_dosha(res) == ('区域内', '特別警戒区域', '土石流・地すべり', '', '近い色')

def make_fake_png(color=(0,0,0,0)):
    img = Image.new("RGBA", (256, 256), color)
    b = BytesIO()
    img.save(b, format="PNG")
    return b.getvalue()

def test_cache_and_fetch(tmp_path):
    input_csv = tmp_path / "in.csv"
    input_csv.write_text("ID,碑名,緯度,経度\n1,A,34.0,134.0\n2,B,34.0,134.0\n3,C,35.0,135.0", encoding="utf-8-sig")
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    
    fetch_calls = []
    sleep_calls = []
    
    def fake_fetch(path, z, x, y):
        fetch_calls.append((path, z, x, y))
        if path == "04_tsunami_newlegend_data" and x == 114688:
            return None # 404
        if path == "05_dosekiryukeikaikuiki" and x == 114688:
            raise Exception("error")
        return make_fake_png((255, 255, 179, 255))
        
    def fake_sleep():
        sleep_calls.append(1)
        
    process_monuments('99', 'monuments', str(input_csv), str(output_csv), str(cache_dir), fake_fetch, fake_sleep)
    
    assert len(fetch_calls) == 6 * 2
    assert len(sleep_calls) == len(fetch_calls)
    
    # e. 404 のとき <y>.none ができる／例外のとき <y>.png も <y>.none もできない
    tsunami_dir = cache_dir / "tsunami" / "17" / "114688"
    assert (tsunami_dir / "51917.none").exists()
    assert not (tsunami_dir / "51917.png").exists()
    
    doseki_dir = cache_dir / "doseki" / "17" / "114688"
    assert not (doseki_dir / "51917.none").exists()
    assert not (doseki_dir / "51917.png").exists()
    
    fetch_calls.clear()
    sleep_calls.clear()
    process_monuments('99', 'monuments', str(input_csv), str(output_csv), str(cache_dir), fake_fetch, fake_sleep)
    
    assert len(fetch_calls) == 1
    assert len(sleep_calls) == 1

def test_main_execution(tmp_path):
    input_csv = tmp_path / "monuments_99.csv"
    input_csv.write_text("ID,碑名,緯度,経度\n1,A,34.0,134.0\n2,B,34.5,134.5\n3,C,35.0,135.0\n4,D,35.5,135.5", encoding="utf-8-sig")
    
    points_csv = tmp_path / "points_99.csv"
    points_csv.write_text("ID,碑名,元の碑ID,緯度,経度\np1,PA,1,34.0,134.0\np2,PB,2,34.5,134.5\np3,PC,3,35.0,135.0\np4,PD,4,35.5,135.5", encoding="utf-8-sig")
    
    x1, y1, i1, j1 = lonlat_to_pixel(134.0, 34.0, 17)
    x2, y2, i2, j2 = lonlat_to_pixel(134.5, 34.5, 17)
    x3, y3, i3, j3 = lonlat_to_pixel(135.0, 35.0, 17)
    x4, y4, i4, j4 = lonlat_to_pixel(135.5, 35.5, 17)
    
    def fake_fetch(path, z, x, y):
        if path == "01_flood_l2_shinsuishin_data" and x == x1 and y == y1:
            img = Image.new("RGBA", (256, 256), (0,0,0,0))
            img.putpixel((i1, j1), (255, 216, 192, 255))
            b = BytesIO()
            img.save(b, format="PNG")
            return b.getvalue()
        if path == "05_kyukeishakeikaikuiki" and x == x1 and y == y1:
            img = Image.new("RGBA", (256, 256), (0,0,0,0))
            img.putpixel((i1, j1), (250, 70, 0, 255))
            b = BytesIO()
            img.save(b, format="PNG")
            return b.getvalue()
        if path == "04_tsunami_newlegend_data" and x == x2 and y == y2:
            img = Image.new("RGBA", (256, 256), (0,0,0,0))
            img.putpixel((i2, j2), (255, 215, 190, 255))
            b = BytesIO()
            img.save(b, format="PNG")
            return b.getvalue()
        if x == x3 and y == y3:
            raise Exception("fetch error")
        return make_fake_png((0,0,0,0))
        
    def fake_sleep(): pass
    
    with patch("src.add_hazard.PROJECT_ROOT", tmp_path), \
         patch("src.add_hazard.PREFECTURES", {"99": "テスト"}), \
         patch("src.add_hazard.default_fetch_func", fake_fetch), \
         patch("src.add_hazard.default_sleep_fn", fake_sleep):
         
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        input_csv.rename(tmp_path / "data" / "processed" / "monuments_99.csv")
        points_csv.rename(tmp_path / "data" / "processed" / "points_99.csv")
        
        hazard_main(["--pref", "99"])
        
        out_mon = tmp_path / "data" / "processed" / "hazard_99.csv"
        
        with open(out_mon, "rb") as f:
            head = f.read(3)
            assert head == codecs.BOM_UTF8
            
        with open(out_mon, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            expected_cols = ["ID", "碑名", "緯度", "経度", "洪水_状態", "洪水_浸水深", "洪水_色の一致", "津波_状態", "津波_浸水深", "津波_色の一致", "高潮_状態", "高潮_浸水深", "高潮_色の一致", "土砂_状態", "土砂_区分", "土砂_現象", "土砂_指定予定", "土砂_色の一致", "近い色の記録", "取得日"]
            assert header == expected_cols
            
            rows = list(reader)
            assert len(rows) == 4
            assert rows[0][0] == "1"
            assert rows[0][4] == "区域内"
            assert rows[0][5] == "0.5m〜3m"
            assert rows[0][6] == "完全一致"
            assert rows[0][13] == "区域内"
            assert rows[0][14] == "特別警戒区域"
            assert rows[0][15] == "急傾斜地の崩壊"
            assert rows[0][17] == "近い色"
            assert rows[0][18] == "急傾斜地の崩壊=250,70,0,255"
            
            assert rows[1][0] == "2"
            assert rows[1][7] == "区域内"
            assert rows[1][8] == "0.5m〜3m"
            assert rows[1][9] == "近い色"
            assert rows[1][18] == "津波=255,215,190,255"
            
            assert rows[2][0] == "3"
            assert rows[2][4] == "取得不可"
            assert rows[2][13] == "取得不可"
            assert rows[2][18] == ""
            assert rows[2][19] == ""  # 取得不可がある行は取得日が空欄
            
            assert rows[3][0] == "4"
            assert rows[3][4] == "区域外"
            assert rows[3][7] == "区域外"
            assert rows[3][10] == "区域外"
            assert rows[3][13] == "区域外"
            assert rows[3][5] == ""
            assert rows[3][14] == ""
            assert rows[3][6] == ""
            assert rows[3][17] == ""
            assert rows[3][19] != ""  # 取得日が空欄でない
            
        hazard_main(["--pref", "99", "--target", "points"])
        out_pts = tmp_path / "data" / "processed" / "hazard_points_99.csv"
        with open(out_pts, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            expected_pts_cols = ["ID", "碑名", "元の碑ID", "緯度", "経度", "洪水_状態", "洪水_浸水深", "洪水_色の一致", "津波_状態", "津波_浸水深", "津波_色の一致", "高潮_状態", "高潮_浸水深", "高潮_色の一致", "土砂_状態", "土砂_区分", "土砂_現象", "土砂_指定予定", "土砂_色の一致", "近い色の記録", "取得日"]
            assert header == expected_pts_cols
            rows = list(reader)
            assert len(rows) == 4
            assert rows[0][0] == "p1"
            assert rows[0][2] == "1"
            
        with open(out_mon, "rb") as f:
            content1 = f.read()
        
        hazard_main(["--pref", "99"])
        
        with open(out_mon, "rb") as f:
            content2 = f.read()
            
        def remove_date(b_str):
            lines = b_str.split(b"\n")
            out = []
            for line in lines:
                if not line.strip(): continue
                parts = line.split(b",")
                out.append(b",".join(parts[:-1]))
            return b"\n".join(out)
            
        assert remove_date(content1) == remove_date(content2)

def test_main_errors(capsys, tmp_path):
    with patch("src.add_hazard.PROJECT_ROOT", tmp_path), \
         patch("src.add_hazard.PREFECTURES", {"99": "テスト"}):
        
        with pytest.raises(SystemExit) as exc:
            hazard_main(["--pref", "all"])
        assert exc.value.code == 1
        
        with pytest.raises(SystemExit) as exc:
            hazard_main(["--pref", "00"])
        assert exc.value.code == 1
        
        with pytest.raises(SystemExit) as exc:
            hazard_main(["--pref", "48"])
        assert exc.value.code == 1
        
        with pytest.raises(SystemExit) as exc:
            hazard_main(["--pref", "99"])
        assert exc.value.code == 1
        assert "先に python src/load_monuments.py --pref 99 を実行してください" in capsys.readouterr().out
        
        # 比較地点の場合
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "processed" / "monuments_99.csv").touch()
        with pytest.raises(SystemExit) as exc:
            hazard_main(["--pref", "99", "--target", "points"])
        assert exc.value.code == 1
        assert "先に python src/make_comparison_points.py --pref 99 を実行してください" in capsys.readouterr().out

def test_main_sys_argv(tmp_path):
    with patch("src.add_hazard.PROJECT_ROOT", tmp_path), \
         patch("src.add_hazard.PREFECTURES", {"99": "テスト"}), \
         patch.object(sys, 'argv', ["pytest", "-q", "tests/test_add_hazard.py"]):
        with pytest.raises(SystemExit) as exc:
            hazard_main(["--pref", "all"])
        assert exc.value.code == 1

def test_launch_method():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    res = subprocess.run([sys.executable, "src/add_hazard.py", "--pref", "00"], cwd=str(PROJECT_ROOT), capture_output=True, env=env)
    assert res.returncode == 1
    stdout_str = res.stdout.decode('cp932', errors='replace')
    stderr_str = res.stderr.decode('cp932', errors='replace')
    assert "エラー: --pref には 01" in stdout_str and "47" in stdout_str

def test_real_cache(capsys):
    input_csv = PROJECT_ROOT / "data" / "processed" / "monuments_36.csv"
    cache_dir = PROJECT_ROOT / "data" / "cache" / "hazard"
    
    if not input_csv.exists() or not cache_dir.exists():
        pytest.skip("Real data not found")
        
    def fail_fetch(*args):
        pytest.skip("Cache missing")
        return None
        
    def no_sleep(): pass
    
    times = []
    out_mon = PROJECT_ROOT / "data" / "processed" / "hazard_36.csv"
    out_pts = PROJECT_ROOT / "data" / "processed" / "hazard_points_36.csv"
    
    if out_mon.exists():
        times.append((out_mon, out_mon.stat().st_mtime))
    if out_pts.exists():
        times.append((out_pts, out_pts.stat().st_mtime))
        
    cache_times = {}
    for p in cache_dir.rglob("*.*"):
        if p.suffix in (".png", ".none"):
            cache_times[str(p)] = p.stat().st_mtime
            
    results = process_monuments('36', 'monuments', str(input_csv), os.devnull, str(cache_dir), fail_fetch, no_sleep)
    
    out = capsys.readouterr().out
    assert "ハザード区域の判定：徳島県（36）・碑" in out
    assert "対象：71件" in out
    assert "洪水（想定最大規模）：区域内 16／区域外 55／取得不可 0" in out
    assert "0.5m未満 2／0.5m〜3m 10／3m〜5m 2／5m〜10m 2" in out
    assert "津波：区域内 50／区域外 21／取得不可 0" in out
    assert "0.3m未満 1／0.5m〜1m 1／0.5m〜3m 9／3m〜5m 4／5m〜10m 35" in out
    assert "高潮：区域内 24／区域外 47／取得不可 0" in out
    assert "0.3m未満 7／0.5m未満 3／0.5m〜1m 8／0.5m〜3m 6" in out
    assert "土砂災害：区域内 22（特別警戒区域 5・警戒区域 17、指定予定を含む 0）／区域外 49／取得不可 0" in out
    assert "近い色で判定：1件" in out
    
    if out_mon.exists():
        assert out_mon.stat().st_mtime == times[0][1]
    if out_pts.exists() and len(times) > 1:
        assert out_pts.stat().st_mtime == times[1][1]
        
    for p in cache_dir.rglob("*.*"):
        if p.suffix in (".png", ".none") and str(p) in cache_times:
            assert p.stat().st_mtime == cache_times[str(p)]
        
    res_dict = {r["ID"]: r for r in results}
    assert res_dict["36201-001"]["洪水_浸水深"] == "0.5m〜3m"
    assert res_dict["36201-001"]["津波_浸水深"] == "0.5m〜3m"
    assert res_dict["36201-001"]["高潮_浸水深"] == "0.5m〜3m"
    assert res_dict["36201-001"]["土砂_状態"] == "区域外"
    
    assert res_dict["36368-003"]["土砂_区分"] == "特別警戒区域"
    assert res_dict["36368-003"]["土砂_現象"] == "土石流・急傾斜地の崩壊"
    
    assert res_dict["36388-006"]["津波_浸水深"] == "5m〜10m"
    assert res_dict["36388-006"]["土砂_区分"] == "特別警戒区域"
    assert res_dict["36388-006"]["土砂_現象"] == "急傾斜地の崩壊"
    assert res_dict["36388-006"]["土砂_色の一致"] == "近い色"
    
    assert res_dict["36383-003"]["土砂_区分"] == "警戒区域"
    assert res_dict["36383-003"]["土砂_現象"] == "急傾斜地の崩壊・地すべり"
    
    assert res_dict["36208-001"]["土砂_区分"] == "警戒区域"
    assert res_dict["36208-001"]["土砂_現象"] == "地すべり"
    
    assert res_dict["36388-011"]["洪水_状態"] == "区域外"
    assert res_dict["36388-011"]["津波_状態"] == "区域外"
    assert res_dict["36388-011"]["高潮_状態"] == "区域外"
    assert res_dict["36388-011"]["土砂_状態"] == "区域外"
    
    assert res_dict["36204-005"]["津波_浸水深"] == "5m〜10m"
    assert res_dict["36204-005"]["高潮_浸水深"] == "0.5m〜1m"
    assert res_dict["36204-005"]["土砂_区分"] == "警戒区域"
    assert res_dict["36204-005"]["土砂_現象"] == "土石流"
