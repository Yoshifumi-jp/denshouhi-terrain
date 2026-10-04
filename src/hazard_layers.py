# ハザードマップのレイヤー情報と凡例

# URLのパス
LAYERS = {
    'flood': '01_flood_l2_shinsuishin_data',
    'tsunami': '04_tsunami_newlegend_data',
    'hightide': '03_hightide_l2_shinsuishin_data',
    'doseki': '05_dosekiryukeikaikuiki',
    'kyukei': '05_kyukeishakeikaikuiki',
    'jisuberi': '05_jisuberikeikaikuiki'
}

# 浸水深の凡例（flood・tsunami・hightide共通）
# RGBのタプルから浸水深の区分へのマッピング
SHINSUI_LEGEND = [
    ((255, 255, 179), '0.3m未満'),
    ((247, 245, 169), '0.5m未満'),
    ((248, 225, 166), '0.5m〜1m'),
    ((255, 216, 192), '0.5m〜3m'),
    ((255, 183, 183), '3m〜5m'),
    ((255, 145, 145), '5m〜10m'),
    ((242, 133, 201), '10m〜20m'),
    ((220, 122, 220), '20m以上')
]

# 土砂災害警戒区域の現象名
DOSHA_NAMES = {
    'doseki': '土石流',
    'kyukei': '急傾斜地の崩壊',
    'jisuberi': '地すべり'
}

# 土砂災害警戒区域の凡例（レイヤーごと）
# RGBのタプルから区域・区分へのマッピング
DOSHA_LEGENDS = {
    'doseki': [
        ((165, 0, 33), '特別警戒区域（指定済）'),
        ((183, 51, 77), '特別警戒区域（指定予定）'),
        ((230, 200, 50), '警戒区域（指定済）'),
        ((235, 211, 91), '警戒区域（指定予定）')
    ],
    'kyukei': [
        ((250, 40, 0), '特別警戒区域（指定済）'),
        ((251, 83, 51), '特別警戒区域（指定予定）'),
        ((250, 230, 0), '警戒区域（指定済）'),
        ((251, 235, 51), '警戒区域（指定予定）')
    ],
    'jisuberi': [
        ((180, 0, 40), '特別警戒区域（指定済）'),
        ((195, 51, 83), '特別警戒区域（指定予定）'),
        ((255, 153, 0), '警戒区域（指定済）'),
        ((255, 173, 51), '警戒区域（指定予定）')
    ]
}


# 浸水深のレイヤーの現象名
SHINSUI_NAMES = {
    'flood': '洪水',
    'tsunami': '津波',
    'hightide': '高潮'
}

# 配信タイルのURL（add_hazard.py の default_fetch_func と同じ）
TILE_URL = "https://disaportaldata.gsi.go.jp/raster/{path}/{z}/{x}/{y}.png"

# 出典（ハザードマップポータルサイトのオープンデータの利用条件による）
HAZARD_SOURCE_NAME = "ハザードマップポータルサイト"
HAZARD_SOURCE_URL = "https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html"

# 浸水深3m以上とみなす区分（SHINSUI_LEGEND の「3m〜5m」から後ろ）
SHINSUI_3M_IJOU = [label for _, label in SHINSUI_LEGEND][[label for _, label in SHINSUI_LEGEND].index('3m〜5m'):]

# 県ごとのデータの年次に関する注意（全国展開時に県を追加する）
HAZARD_DATA_NOTES = {
    '36': [
        "津波：徳島県は2025年9月に新しい津波浸水想定を公表しましたが、ハザードマップポータルサイトの配信データは更新日が2023年で、それ以前の想定（平成24年公表）のままとみられます。最新の想定は徳島県のホームページでご確認ください。",
    ],
}
