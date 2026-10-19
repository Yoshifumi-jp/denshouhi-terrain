# 完了報告 M20-02

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| `src/build_national.py` | 全国ページ（`docs/index.html`）への地形分類（人工地形）の反映（一覧の列・絞り込み・人工地形集計表2つ・CSVダウンロード・出典・ご利用上の注意・まとめ表示の追加） | 63,799 bytes |
| `tests/test_build_national.py` | 人工地形の列・絞り込み、集計表2つ、ファイル欠損時の動作を検証するテスト関数3件を追加（既存テスト `test_national_region_column_and_filter` の見出し確認1行のみ、地域版列の後ろに人工地形列が入ったことに合わせて調整） | 61,935 bytes |
| `docs/index.html` | `.\.venv\Scripts\python.exe src\build_national.py` の実行により更新（人工地形の列・絞り込み・集計表2つ・ダウンロード・出典・注意書きを反映、LF） | 690,153 bytes |
| `docs/data/landform_artificial_all.csv` | `.\.venv\Scripts\python.exe src\build_national.py` の実行により `output/landform_artificial_all.csv` からコピー作成（LF） | 5,954 bytes |
| `docs/data/landform_artificial_cross_all.csv` | `.\.venv\Scripts\python.exe src\build_national.py` の実行により `output/landform_artificial_cross_all.csv` からコピー作成（LF） | 13,130 bytes |
| `docs/dev/reports/M20-02_report.md` | 本完了報告書の作成 | 13,205 bytes |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `.\.venv\Scripts\python.exe -m pytest -q` で 321 passed であることを確認。
  - `.\.venv\Scripts\python.exe src\build_national.py` の出力および生成された `docs/index.html`・`docs/data/landform_artificial_all.csv`・`docs/data/landform_artificial_cross_all.csv` が既知の答えと一致し、改行コードがすべて LF（CSV 2つは `output/` とバイト単位で同一）であることを確認。

### pytest 実行結果
`.\.venv\Scripts\python.exe -m pytest -q`
```text
........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 67%]
........................................................................ [ 89%]
.................................                                        [100%]
321 passed in 448.46s (0:07:28)
```

### `src\build_national.py` 実行結果（まとめ表示）
`.\.venv\Scripts\python.exe src\build_national.py`
```text
全国ページ：docs/index.html
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
色分け地図（碑の数）：0：0／1〜9：1／10〜19：6／20〜49：18／50〜99：15／100以上：7
一覧の地形分類：17区分＋データなし（データなし 929基）
一覧の地形分類（地域版）：12区分＋データなし（データなし 5基）
地域版の集計表：12行
一覧の人工地形：5区分（人工地形あり 288基／人工地形なし 1,264基／範囲外 929基）
人工地形の集計表：6行／自然地形×人工地形の表：24行
作成したファイル：13
docs/index.html のサイズ：674.0 KB
公開前チェック：問題なし
```

### 既知の答えとの照合（`docs/index.html` からの抜粋）

1. **碑の一覧の人工地形絞り込み（選択肢の順）**
```html
        <div class="filter-item">
            <label for="f-landform-artificial">人工地形：</label>
            <select id="f-landform-artificial">
                <option value="">すべて</option>
<option value="盛土地・埋立地">盛土地・埋立地</option>
<option value="干拓地">干拓地</option>
<option value="切土地">切土地</option>
<option value="改変工事中">改変工事中</option>
<option value="農耕平坦化地">農耕平坦化地</option>
<option value="人工地形なし">人工地形なし</option>
<option value="範囲外">範囲外</option>
            </select>
        </div>
```
- `MONUMENTS` の添字11の件数：盛土地・埋立地 199／干拓地 47／切土地 39／改変工事中 2／農耕平坦化地 1／人工地形なし 1,264／範囲外 929（取得不可・データなしは0基のため選択肢に出ない）
- 絞り込み件数の確認（`MONUMENTS` から集計）：
  - 人工地形＝干拓地 → 47基（うち 愛知23 が20、熊本43 が9、三重24 が7、佐賀41 が6、宮城04・大阪27・岡山33・山口35・愛媛38 が各1）
  - 都道府県＝東京（13）・人工地形＝盛土地・埋立地 → 33基
  - 都道府県＝兵庫（28）・人工地形＝切土地 → 8基
  - 人工地形＝改変工事中 → 2基（どちらも兵庫28）
  - 地形分類＝旧水部・人工地形＝干拓地 → 47基

2. **一覧の表見出し（10列）**
```html
                <tr><th>ID</th><th>碑名</th><th>都道府県</th><th>所在地</th><th>災害種別</th><th>地形分類</th><th>地形分類（地域版）</th><th>人工地形</th><th>建立年</th><th>地図</th></tr>
```

3. **表A（人工地形・全碑・全種別、6行）と注（C＝929、D＝4,890）、表B（自然地形×人工地形・全碑、24行）**
```html
    <h2>地形分類（人工地形・全碑・全種別）</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>人工地形</th><th>碑の数</th><th>碑の割合</th><th>まわりの数</th><th>まわりの割合</th></tr>
            </thead>
            <tbody>
<tr><td>盛土地・埋立地</td><td>199</td><td>12.8%</td><td>732</td><td>9.8%</td></tr>
<tr><td>干拓地</td><td>47</td><td>3.0%</td><td>222</td><td>3.0%</td></tr>
<tr><td>切土地</td><td>39</td><td>2.5%</td><td>214</td><td>2.9%</td></tr>
<tr><td>改変工事中</td><td>2</td><td>0.1%</td><td>16</td><td>0.2%</td></tr>
<tr><td>農耕平坦化地</td><td>1</td><td>0.1%</td><td>9</td><td>0.1%</td></tr>
<tr><td>人工地形なし</td><td>1264</td><td>81.4%</td><td>6312</td><td>84.1%</td></tr>
            </tbody>
        </table>
    </div>
    <p>人工地形を調べていない碑 929基・まわりの地点 4,890点（地形分類の詳細版のデータがない範囲外など）は、割合の計算から除いています。</p>
    <p>人工地形は自然地形の上に重なる情報です（例：もとは旧水部〔昔の海・湖・沼〕だった所を干拓・埋め立てた土地）。データを整備した時点の状態で、その後の造成・埋立は入っていません。</p>

    <h2>自然地形×人工地形（全碑）</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>自然地形</th><th>人工地形</th><th>碑の数</th><th>碑の割合</th><th>まわりの数</th><th>まわりの割合</th></tr>
            </thead>
            <tbody>
<tr><td>氾濫平野・海岸平野</td><td>盛土地・埋立地</td><td>97</td><td>21.5%</td><td>317</td><td>16.8%</td></tr>
<tr><td>旧水部</td><td>盛土地・埋立地</td><td>66</td><td>57.9%</td><td>242</td><td>52.2%</td></tr>
<tr><td>旧水部</td><td>干拓地</td><td>47</td><td>41.2%</td><td>219</td><td>47.2%</td></tr>
<tr><td>山地斜面等</td><td>切土地</td><td>21</td><td>10.2%</td><td>143</td><td>5.8%</td></tr>
<tr><td>旧河道</td><td>盛土地・埋立地</td><td>7</td><td>12.5%</td><td>19</td><td>11.4%</td></tr>
<tr><td>台地・段丘</td><td>切土地</td><td>6</td><td>3.6%</td><td>35</td><td>4.6%</td></tr>
<tr><td>自然堤防</td><td>盛土地・埋立地</td><td>6</td><td>3.5%</td><td>19</td><td>5.3%</td></tr>
<tr><td>山麓堆積地形</td><td>盛土地・埋立地</td><td>5</td><td>7.9%</td><td>5</td><td>3.5%</td></tr>
<tr><td>扇状地</td><td>切土地</td><td>5</td><td>4.1%</td><td>8</td><td>2.1%</td></tr>
<tr><td>山地斜面等</td><td>盛土地・埋立地</td><td>3</td><td>1.5%</td><td>40</td><td>1.6%</td></tr>
<tr><td>氾濫平野・海岸平野</td><td>切土地</td><td>3</td><td>0.7%</td><td>13</td><td>0.7%</td></tr>
<tr><td>河川敷・浜</td><td>盛土地・埋立地</td><td>3</td><td>37.5%</td><td>5</td><td>8.8%</td></tr>
<tr><td>砂州・砂丘</td><td>盛土地・埋立地</td><td>3</td><td>2.2%</td><td>26</td><td>10.0%</td></tr>
<tr><td>台地・段丘</td><td>盛土地・埋立地</td><td>2</td><td>1.2%</td><td>10</td><td>1.3%</td></tr>
<tr><td>天井川等</td><td>切土地</td><td>2</td><td>28.6%</td><td>0</td><td>0.0%</td></tr>
<tr><td>山地斜面等</td><td>改変工事中</td><td>2</td><td>1.0%</td><td>13</td><td>0.5%</td></tr>
<tr><td>後背低地・湿地</td><td>盛土地・埋立地</td><td>2</td><td>16.7%</td><td>15</td><td>14.4%</td></tr>
<tr><td>水部</td><td>盛土地・埋立地</td><td>2</td><td>11.8%</td><td>21</td><td>5.6%</td></tr>
<tr><td>地すべり地形</td><td>盛土地・埋立地</td><td>1</td><td>20.0%</td><td>1</td><td>4.3%</td></tr>
<tr><td>山地斜面等</td><td>農耕平坦化地</td><td>1</td><td>0.5%</td><td>9</td><td>0.4%</td></tr>
<tr><td>山麓堆積地形</td><td>切土地</td><td>1</td><td>1.6%</td><td>6</td><td>4.2%</td></tr>
<tr><td>崖・段丘崖</td><td>盛土地・埋立地</td><td>1</td><td>14.3%</td><td>0</td><td>0.0%</td></tr>
<tr><td>旧河道</td><td>切土地</td><td>1</td><td>1.8%</td><td>0</td><td>0.0%</td></tr>
<tr><td>落堀</td><td>盛土地・埋立地</td><td>1</td><td>100.0%</td><td>0</td><td>0.0%</td></tr>
            </tbody>
        </table>
    </div>
    <p>人工地形のある碑を、自然地形との組み合わせで数えたものです（碑が0基の組み合わせは省いています）。割合は、同じ自然地形の碑（まわりの地点）のうち人工地形を調べたものに対する割合です。</p>
```

4. **データのダウンロード・出典・ご利用上の注意（E＝929、既存の文は不変）**
```html
    <h2>データのダウンロード（CSV、Excel で開けます）</h2>
    <ul>
        <li><a href="national_report.pdf">印刷用PDF（A4・7ページ）</a></li>
        <li><a href="data/summary_all.csv">集計表</a></li>
        <li><a href="data/hazard_summary_all.csv">ハザードマップの想定区域との重なり</a></li>
        <li><a href="data/landform_all.csv">地形分類</a></li>
        <li><a href="data/landform_region_all.csv">地形分類（地域版）</a></li>
        <li><a href="data/landform_artificial_all.csv">地形分類（人工地形）</a></li>
        <li><a href="data/landform_artificial_cross_all.csv">自然地形×人工地形</a></li>
        <li><a href="data/relocated_all.csv">移転碑の一覧</a></li>
        <li><a href="data/pref_counts_all.csv">都道府県別の件数</a></li>
        <li><a href="data/years_all.csv">年代別の碑の数</a></li>
    </ul>
```
```html
    <h2>出典</h2>
    <ul>
        <li>自然災害伝承碑：国土地理院（<a href="https://www.gsi.go.jp/bousaichiri/denshouhi.html">https://www.gsi.go.jp/bousaichiri/denshouhi.html</a>）</li>
        <li>標高・傾斜：国土地理院 標高API（標高タイル）から算出</li>
        <li>地形分類：国土地理院 地形分類（自然地形）</li>
        <li>地形分類（人工地形）：国土地理院 地形分類（人工地形）</li>
        <li>河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）</li>
```
```html
        <li>地形分類（自然地形）のデータは整備された地域が限られ、全国の碑の 37.4%（929基）はデータがありません。</li>
        <li>地形分類（地域版）は、詳細版のない地域も含めて全国の碑に付けたものです（値が取れなかった碑 5基）。詳細版とは分類の細かさが違うため、別の列・別の表にしています。</li>
        <li>地形分類（人工地形）は、詳細版がある範囲（主な平野部）の碑だけに付けています（範囲外の碑 929基）。データを整備した時点の状態で、その後の造成・埋立は入っていません。人工地形は自然地形の上に重なる情報のため、別の列・別の表にしています。</li>
        <li>1基の碑が複数の災害種別を持つことがあります。</li>
```

## 残った課題・気になる点
- 指示書の絞り込み例に「長崎42 が7」と記載されていましたが、実データの干拓地7基は県コード24（三重県）でした（干拓地全体は47基で一致）。
- 既存テスト `test_national_region_column_and_filter` 内の表見出しアサーションが `"<th>地形分類</th><th>地形分類（地域版）</th><th>建立年</th>"` と隣接を前提にしていたため、本指示書で `<th>地形分類（地域版）</th>` の直後に `<th>人工地形</th>` を挿入したことに伴い、`"<th>地形分類</th><th>地形分類（地域版）</th>"` に1行のみ調整しました。

## 確認したいこと（あれば）
- なし
