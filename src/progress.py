# 進捗表示の共通処理

PROGRESS_EVERY = 10

def format_elapsed(seconds):
    """経過時間をフォーマットする"""
    sec = int(seconds)
    hours = sec // 3600
    minutes = (sec % 3600) // 60
    secs = sec % 60
    if hours > 0:
        return f"{hours}時間{minutes:02d}分"
    else:
        return f"{minutes}分{secs:02d}秒"

def should_print(done, total, every=PROGRESS_EVERY):
    """進捗を表示すべきかどうかを判定する"""
    if total <= 0:
        return False
    return done % every == 0 or done == total

def progress_line(label, done, total, elapsed_sec, fetch_count, cache_count):
    """進捗行の文字列を生成する"""
    percent = done * 100 // total
    elapsed = format_elapsed(elapsed_sec)
    return f"  進捗 {label} {done}/{total}（{percent}%）経過 {elapsed}　問い合わせ {fetch_count}枚・キャッシュ {cache_count}枚"
