## データのダウンロード

```
scrapy crawl shitsugi -o ./out/shitsugi.jl
scrapy crawl member -a diet=208 -o ./out/member.jl
scrapy crawl minutes -a first_date=2022-01-17 -a last_date=2022-06-15
scrapy crawl gclip
```

```
wget https://raw.githubusercontent.com/smartnews-smri/house-of-councillors/main/data/giin.csv -o ./data/giin.csv
```

## データの生成

### 基本データ

| 　スクリプト                     | 出力                  | 依存                        |
|----------------------------|---------------------|---------------------------|
| clip.py                    | clip.csv            |                           |
| minutes.py                 | minutes.csv         |                           |
| member.py                  | member.csv          |                           | 
| gclip.py                   | gclip.csv           |                           |
| topic.py                   | topic.csv           | clip_topic, clip_category |

### 中間データ

| 　スクリプト                     | 出力                  | 依存                        |
|----------------------------|---------------------|---------------------------|
| clip_topic_match.py        | clip_topic.csv      |                           |
| clip_category_match.py     | clip_category.csv   |                           |
| clip_minutes_match.py      | clip_minutes.csv    |                           |
| clip_member_match.py       | clip_member.csv     |                           |
| clip_gclip_match.py        | clip_gclip.csv      | clip_minutes              |
| clip_clip_match.py         | clip_clip.csv       | clip_minutes              |
| member_topic_match.py      | member_topic.csv    | clip_topic, clip_member   |
| topic_topic_match.py       | topic_topic.csv     | clip_topic                |

### 最終データ

| 　スクリプト                     | 出力                  | 依存                               |
|----------------------------|---------------------|----------------------------------|
| build_artifact_clip.py     | ${clip_id}.json     |                                  | 
| build_artifact_member.py   | ${member_id}.json   |                                  |
| build_artifact_topic.py    | ${topic_id}.json    |                                  |
| build_artifact_category.py | ${category_id}.json |                                  |
| build_artifact_home.py     | home.json           | artifact_clip, artifact_category |
| clip_image.py              | ${clip_id}.jpg      |                                  | 

## スキーマ

### clip.csv

| カラム     | 内容      | 例         |
|---------|---------|-----------|
| clip_id | ID      | 100       | 
| title   | タイトル    | 円安について    | 
| name    | 質問者名    | 田中太郎      |
| date    | 日付      | 2022-03-01 |
| session | 回次      | 208       | 
| house   | 議会      | 参議院       |
| meeting | 会議      | 予算委員会     |
| issue   | 会議番号    | 3         |
| url     | 質疑項目URL | 　         |

## minutes.csv

| カラム        | 内容   | 例 |
|------------|------|-----------|
| minutes_id | ID   | 120814024X01620220325 |
| session    | 回次   | 208 |
| house      | 議会   | 参議院 |
| meeting    | 会議   | 予算委員会 |
| issue      | 会議番号 | 3 |

### member.csv

| カラム       | 内容     | 例         | 
|-----------|--------|-----------|
| member_id | ID     | 100　      |
| name      | 名前     | 田中 太郎     | 
| yomi      | 読み     | たなか たろう   |
| group     | 会派     | 無所属       |
| block     | 選挙区    | 比例        |
| tenure    | 任期     | 令和4年7月25日 |

### gclip.csv

| カラム | 内容 | 例                     |
|-------------|-------|-----------------------|
| gclip_id | ID | 11464                 |
| video_id | 審議中継ID | 6952                  |
| minutes_id | 会議録ID | 120814370X01620220607 |

### clip_minutes.csv

| カラム        | 内容     | 例     |
|------------|--------|-------|
| clip_id    | クリップID | 100   |
| minutes_id | 会議録ID  | 田中 太郎 |
| speech_id  | 発言番号   | 5     |
| score      | 関連度    | 0.85  |

### clip_member.csv

| カラム       | 内容     | 例 |
|-----------|--------|-----------|
| clip_id   | クリップID | 100 |
| member_id | メンバーID | 200 |

### clip_gclip.csv

| カラム        | 内容      | 例 |
|------------|---------|-----------|
| clip_id    | クリップID  | 100 |
| gclip_id   | GclipID | 1000 |
| start_msec | 開始時間    | 4000000 |

### clip_clip.csv

| カラム          | 内容         | 例         |
|--------------|------------|-----------|
| clip_id      | クリップID     | 100       |
| clip_id_list | クリップIDのリスト | 200;300   |
| score_list   | 関連度のリスト    | 0.85;0.70 |

### clip_category.csv

| カラム         | 内容     | 例   |
|-------------|--------|-----|
| clip_id     | クリップID | 100 |
| category_id | カテゴリID | 3   |