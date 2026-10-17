# 完了報告 M17-02

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| src/build_national.py | 全国ページ（docs/index.html）への地形分類（地域版）の反映（一覧の列・絞り込み・地域版集計表・CSVダウンロード・ご利用上の注意・まとめ表示の追加） | 50,102 bytes |
| tests/test_build_national.py | 地域版の列・絞り込み、集計表、ファイル欠損時の動作を検証するテスト関数3件を追加 | 40,214 bytes |
| docs/index.html | `python src/build_national.py` の実行により更新（地域版の列・絞り込み・集計表・ダウンロード・注意書きを反映、LF） | 633,861 bytes |
| docs/data/landform_region_all.csv | `python src/build_national.py` の実行により `output/landform_region_all.csv` からコピー作成（LF） | 11,860 bytes |
| docs/dev/reports/M17-02_report.md | 本完了報告書の作成 | 7,051 bytes |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python -m pytest -q` で 271 passed であることを確認。
  - `python src/build_national.py` の出力および生成された `docs/index.html`・`docs/data/landform_region_all.csv` が既知の答えと一致し、改行コードが LF であることを確認。

### pytest 実行結果
```text
........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 79%]
.......................................................                  [100%]
271 passed in 468.84s (0:07:48)
```

### `python src/build_national.py` 実行結果（まとめ表示）
```text
全国ページ：docs/index.html
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
色分け地図（碑の数）：0：0／1〜9：1／10〜19：6／20〜49：18／50〜99：15／100以上：7
一覧の地形分類：17区分＋データなし（データなし 929基）
一覧の地形分類（地域版）：12区分＋データなし（データなし 5基）
地域版の集計表：12行
作成したファイル：11
docs/index.html のサイズ：619.0 KB
公開前チェック：問題なし
```

### 既知の答えとの照合（`docs/index.html` からの抜粋）

1. **碑の一覧の地域版絞り込み（選択肢の順：12区分＋データなし）**
```html
        <div class="filter-item">
            <label for="f-landform-region">地形分類（地域版）：</label>
            <select id="f-landform-region">
                <option value="">すべて</option>
<option value="低地">低地</option>
<option value="山地">山地</option>
<option value="台地・段丘">台地・段丘</option>
<option value="丘陵・小起伏地">丘陵・小起伏地</option>
<option value="火山麓地形">火山麓地形</option>
<option value="火山地形（やや不明瞭）">火山地形（やや不明瞭）</option>
<option value="火山地形（明瞭）">火山地形（明瞭）</option>
<option value="砂丘">砂丘</option>
<option value="火山性丘陵">火山性丘陵</option>
<option value="残丘状地形">残丘状地形</option>
<option value="カルスト地形">カルスト地形</option>
<option value="湖">湖</option>
<option value="データなし">データなし</option>
            </select>
        </div>
```
- `MONUMENTS` の添字10の件数：低地 1,325／山地 472／台地・段丘 264／丘陵・小起伏地 199／火山麓地形 92／火山地形（やや不明瞭） 53／火山地形（明瞭） 29／砂丘 22／火山性丘陵 12／残丘状地形 5／カルスト地形 2／湖 1／データなし 5
- 絞り込み件数の確認：
  - 地域版＝火山麓地形 → 92基（うち 県コード42（長崎県）が25基、県コード10（群馬県）が20基）
  - 都道府県＝徳島県（36）・地域版＝低地 → 44基
  - 都道府県＝岩手県（03）・地域版＝山地 → 46基

2. **一覧の表見出し**
```html
                <tr><th>ID</th><th>碑名</th><th>都道府県</th><th>所在地</th><th>災害種別</th><th>地形分類</th><th>地形分類（地域版）</th><th>建立年</th><th>地図</th></tr>
```

3. **地域版の集計表と注（A＝5、B＝118）**
```html
    <h2>地形分類（地域版・全碑・全種別）</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>地形分類</th><th>碑の数</th><th>碑の割合</th><th>まわりの数</th><th>まわりの割合</th></tr>
            </thead>
            <tbody>
<tr><td>低地</td><td>1325</td><td>53.5%</td><td>4331</td><td>35.3%</td></tr>
<tr><td>山地</td><td>472</td><td>19.1%</td><td>4078</td><td>33.2%</td></tr>
<tr><td>台地・段丘</td><td>264</td><td>10.7%</td><td>1160</td><td>9.4%</td></tr>
<tr><td>丘陵・小起伏地</td><td>199</td><td>8.0%</td><td>1323</td><td>10.8%</td></tr>
<tr><td>火山麓地形</td><td>92</td><td>3.7%</td><td>534</td><td>4.3%</td></tr>
<tr><td>火山地形（やや不明瞭）</td><td>53</td><td>2.1%</td><td>388</td><td>3.2%</td></tr>
<tr><td>火山地形（明瞭）</td><td>29</td><td>1.2%</td><td>139</td><td>1.1%</td></tr>
<tr><td>砂丘</td><td>22</td><td>0.9%</td><td>93</td><td>0.8%</td></tr>
<tr><td>火山性丘陵</td><td>12</td><td>0.5%</td><td>112</td><td>0.9%</td></tr>
<tr><td>残丘状地形</td><td>5</td><td>0.2%</td><td>64</td><td>0.5%</td></tr>
<tr><td>カルスト地形</td><td>2</td><td>0.1%</td><td>5</td><td>0.0%</td></tr>
<tr><td>湖</td><td>1</td><td>0.0%</td><td>50</td><td>0.4%</td></tr>
            </tbody>
        </table>
    </div>
    <p>地域版で値が取れなかった碑 5基・まわりの地点 118点は、割合の計算から除いています。</p>
    <p>地域版は詳細版より分類が粗い（中分類12種）ため、碑とまわりの地点（100m〜2,000m）が同じ分類になりやすく、差が出にくくなります。</p>
```

4. **データのダウンロードとご利用上の注意（詳細版の注も変わらないことを確認）**
```html
        <li><a href="data/landform_all.csv">地形分類</a></li>
        <li><a href="data/landform_region_all.csv">地形分類（地域版）</a></li>
        <li><a href="data/relocated_all.csv">移転碑の一覧</a></li>
```
```html
        <li>地形分類（自然地形）のデータは整備された地域が限られ、全国の碑の 37.4%（929基）はデータがありません。</li>
        <li>地形分類（地域版）は、詳細版のない地域も含めて全国の碑に付けたものです（値が取れなかった碑 5基）。詳細版とは分類の細かさが違うため、別の列・別の表にしています。</li>
```

## 残った課題・気になる点
- なし

## 確認したいこと（あれば）
- なし
