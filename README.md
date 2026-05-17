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
   `.env.example` を参考に `.env` を作成し、`APP_MODE`、`LOG_PATH`、`BATCH_ERROR_LOG_PATH`、`IMAGE_PATH`、`OUTPUT_IMAGE_PATH`、`DETECTOR_TYPE`、`MASK_MODE`、`MASK_CENTER_X_RATIO`、`MASK_CENTER_Y_RATIO`、`MASK_RADIUS_RATIO`、`MASK_RADIUS_X_RATIO`、`MASK_RADIUS_Y_RATIO`、ORB / SIFT の各パラメータ、`AWS_PROFILE`、`S3_BUCKET`、DB 接続情報を設定する

## Run
`PYTHONPATH=src python main.py`

`IMAGE_PATH` には画像ファイルかディレクトリを指定できる。`sample_images` のようなディレクトリを指定すると、その配下の画像をすべて処理し、`OUTPUT_IMAGE_PATH` に指定したディレクトリへ `{元ファイル名}_keypoints.jpg` の形式で出力する。

S3 接続で named profile を使う場合は `AWS_PROFILE` を設定する。例: `AWS_PROFILE=nose-id-prod`

実行コマンドは同じで、`.env` の `APP_MODE` だけを切り替える。

### APP_MODE=image_keypoint
ローカル画像を対象に keypoint を取得する。

実行内容:
- `IMAGE_PATH` から画像ファイルまたはディレクトリを読む
- `DETECTOR_TYPE` に応じて ORB / SIFT で `keypoint_count` を算出する
- 出力画像を `OUTPUT_IMAGE_PATH` 配下に保存する
- 標準出力とログへ結果を出力する

主な入力:
- `IMAGE_PATH`
- `OUTPUT_IMAGE_PATH`
- `DETECTOR_TYPE`
- `MASK_MODE`
- ORB / SIFT の各パラメータ

### APP_MODE=db_fetch_latest
DB からレコード取得だけを行う読み取り専用モード。

実行内容:
- PostgreSQL に接続する
- `DB_SOURCE_TABLE` から `id`, `object_key` を取得する
- `DB_FETCH_LIMIT` を指定した場合はその件数だけ取得する
- `DB_FETCH_LIMIT` 未指定の場合は全件取得する
- 標準出力とログへ結果を出力する

補足:
- このモードは読み取り専用
- 更新処理と削除処理は含まない

主な入力:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_SCHEMA`
- `DB_SOURCE_TABLE`
- `DB_FETCH_LIMIT`

### APP_MODE=batch_prepare_keypoints
dry-run と本番更新の両方に対応するバッチモード。

実行内容:
- `nose_registrations.noseprint_id` を基点に対象を取得する
- `nose_images` のうち `is_latest = TRUE` の画像を使う
- `object_key` を使って `S3_BUCKET` から画像を取得する
- `DETECTOR_TYPE` に応じて ORB / SIFT で `keypoint_count` を算出する
- 出力画像を `OUTPUT_IMAGE_PATH` 配下に保存する
- 標準出力とログへ `id`, `noseprint_id`, `object_key`, `keypoint_count`, `status` を出力する
- 最後に成功件数、失敗件数、スキップ件数、登録件数、合計 keypoint 数を出力する

補足:
- `BATCH_DRY_RUN=true` の場合は dry-run として動作し、DB 更新は行わない
- `BATCH_DRY_RUN=false` の場合は `nose_image_quality` へ登録する
- `nose_image_quality` には `noseprint_id`, `keypoints_orb`, `app_version` を登録し、`created_at` は default を使う
- `app_version` は `DB_UPDATE_APP_VERSION` を設定しない場合 `NULL` で登録する
- 実行件数は `DB_FETCH_LIMIT` で制御する
- `DB_FETCH_LIMIT` 未指定の場合は全件取得する
- `nose_image_quality` に既存レコードがある `noseprint_id` は自動的に対象外になる
- `is_latest = TRUE` が 1件でない `noseprint_id` はスキップしてログへ残す

主な入力:
- `BATCH_DRY_RUN`
- `DB_REGISTRATION_TABLE`
- `DB_SOURCE_TABLE`
- `DB_UPDATE_TABLE`
- `DB_FETCH_LIMIT`
- `DB_UPDATE_APP_VERSION`
- `S3_BUCKET`
- `AWS_PROFILE`
- `DETECTOR_TYPE`
- `OUTPUT_IMAGE_PATH`
- ORB / SIFT の各パラメータ

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

`BATCH_ERROR_LOG_PATH` には、バッチ更新中に更新できなかったデータや異常が発生したデータだけを追記する。`status=failure` と `status=skipped` のレコードが JSON Lines 形式で保存される。

ORB の主な設定:
- `ORB_NFEATURES`
- `ORB_SCALE_FACTOR`
- `ORB_NLEVELS`
- `ORB_EDGE_THRESHOLD`
- `ORB_FIRST_LEVEL`
- `ORB_WTA_K`
- `ORB_SCORE_TYPE`
- `ORB_PATCH_SIZE`
- `ORB_FAST_THRESHOLD`

SIFT の主な設定:
- `SIFT_NFEATURES`
- `SIFT_CONTRAST_THRESHOLD`
- `SIFT_EDGE_THRESHOLD`
- `SIFT_SIGMA`


## SQL

- nose_image_quality.idを指定して画像を特定する

```
\prompt 'nose_image_quality.idを入力してください: ' quality_id

SELECT
  niq.id AS nose_image_quality_id,
  niq.noseprint_id,
  niq.keypoints_orb,
  niq.app_version,
  niq.created_at,
  ni.id AS nose_image_id,
  ni.object_key,
  ni.is_latest
FROM public.nose_image_quality niq
JOIN public.nose_images ni
  ON niq.noseprint_id = ni.noseprint_id
WHERE niq.id = :quality_id
  AND ni.is_latest = TRUE;
```
