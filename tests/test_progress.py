from src.progress import format_elapsed, should_print, progress_line

def test_format_elapsed():
    assert format_elapsed(0) == "0分00秒"
    assert format_elapsed(52) == "0分52秒"
    assert format_elapsed(59.9) == "0分59秒"
    assert format_elapsed(3599) == "59分59秒"
    assert format_elapsed(3600) == "1時間00分"
    assert format_elapsed(7265) == "2時間01分"

def test_should_print():
    assert should_print(10, 815) == True
    assert should_print(11, 815) == False
    assert should_print(815, 815) == True
    assert should_print(0, 0) == False
    assert should_print(5, 5) == True

def test_progress_line():
    expected = "  進捗 ハザード（比較地点） 10/815（1%）経過 0分52秒　問い合わせ 48枚・キャッシュ 12枚"
    actual = progress_line("ハザード（比較地点）", 10, 815, 52, 48, 12)
    assert actual == expected

