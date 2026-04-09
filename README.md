# image-keypoint-detection
画像からkeypointを取得する

## Setup
1. Python 3.10 以降を用意する
2. 依存ライブラリをインストールする

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. 環境変数を設定する
   `.env.example` を参考に `.env` を作成し、`APP_MODE`、`LOG_PATH`、`IMAGE_PATH`、`OUTPUT_IMAGE_PATH`、`DETECTOR_TYPE`、`MASK_MODE`、`MASK_CENTER_X_RATIO`、`MASK_CENTER_Y_RATIO`、`MASK_RADIUS_RATIO`、`MASK_RADIUS_X_RATIO`、`MASK_RADIUS_Y_RATIO`、ORB / SIFT の各パラメータ、`S3_BUCKET`、DB 接続情報を設定する

## Run
`PYTHONPATH=src python main.py`

`IMAGE_PATH` には画像ファイルかディレクトリを指定できる。`sample_images` のようなディレクトリを指定すると、その配下の画像をすべて処理し、`OUTPUT_IMAGE_PATH` に指定したディレクトリへ `{元ファイル名}_keypoints.jpg` の形式で出力する。

`APP_MODE=db_fetch_latest` にすると、PostgreSQL に接続して `DB_SOURCE_TABLE` から最新データを取得する。`DB_FETCH_LIMIT` を指定した場合はその件数だけ取得し、未指定の場合は全件取得する。この仮実装は読み取り専用で、更新処理と削除処理は含まない。

`APP_MODE=image_keypoint` で画像から keypoint を取得する。`APP_MODE=db_fetch_latest` で DB から最新データを取得する。実行コマンドは同じで、`.env` の `APP_MODE` だけを切り替える。

## Cloud SQL Auth Proxy
Cloud SQL へ `APP_MODE=db_fetch_latest` で接続する場合は、先に `cloud-sql-proxy` を起動する必要がある。

```bash
cloud-sql-proxy --debug-logs --address 127.0.0.1 --port 15432 noseid-d8f00:asia-northeast1:paws-api
```

この場合の `.env` 例:

```env
APP_MODE=db_fetch_latest
DB_CONNECTION_TYPE=cloud_sql_auth_proxy
DB_HOST=127.0.0.1
DB_PORT=15432
DB_NAME=paws-api
DB_USER=postgres
DB_PASSWORD=...
DB_SCHEMA=public
DB_SOURCE_TABLE=nose_images
DB_UPDATE_TABLE=nose_images
DB_FETCH_LIMIT=
DB_INSTANCE_CONNECTION_NAME=noseid-d8f00:asia-northeast1:paws-api
```

`cloud-sql-proxy` を起動したまま、別ターミナルで以下を実行する。

```bash
PYTHONPATH=src python main.py
```

`DETECTOR_TYPE=orb` または `DETECTOR_TYPE=sift` を指定すると、同じ画像処理フローのまま検出器を切り替えられる。

`MASK_MODE=circle` にすると円形マスク、`MASK_MODE=ellipse` にすると横長や縦長を指定できる楕円マスクで keypoint を検出する。楕円では `MASK_RADIUS_X_RATIO` と `MASK_RADIUS_Y_RATIO` を使う。出力画像には検出対象の輪郭を黄色で描画し、その内部の keypoint を赤いドットで重ねる。マスクを使わない場合は `MASK_MODE=none` を指定する。

`LOG_PATH` に指定したディレクトリ配下へ、`YYYY-MM-DD.log` 形式の日付別ログファイルを作成する。ログ内容は JSON Lines 形式で、先頭に 1 回だけ実行共通情報を `run_start` として出し、その後に画像ごとの `image_result`、最後に `run_summary` を出力する。

ORB の主な設定:
- `ORB_NFEATURES`
- `ORB_SCALE_FACTOR`
- `ORB_NLEVELS`
- `ORB_FAST_THRESHOLD`
- `ORB_EDGE_THRESHOLD`

SIFT の主な設定:
- `SIFT_NFEATURES`
- `SIFT_CONTRAST_THRESHOLD`
- `SIFT_EDGE_THRESHOLD`
- `SIFT_SIGMA`
