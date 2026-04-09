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
   `.env.example` を参考に `.env` を作成し、`LOG_PATH`、`IMAGE_PATH`、`OUTPUT_IMAGE_PATH`、`DETECTOR_TYPE`、`MASK_MODE`、`MASK_CENTER_X_RATIO`、`MASK_CENTER_Y_RATIO`、`MASK_RADIUS_RATIO`、`MASK_RADIUS_X_RATIO`、`MASK_RADIUS_Y_RATIO`、ORB / SIFT の各パラメータ、`S3_BUCKET`、DB 接続情報を設定する

## Run
`PYTHONPATH=src python main.py`

`IMAGE_PATH` には画像ファイルかディレクトリを指定できる。`sample_images` のようなディレクトリを指定すると、その配下の画像をすべて処理し、`OUTPUT_IMAGE_PATH` に指定したディレクトリへ `{元ファイル名}_keypoints.jpg` の形式で出力する。

`DETECTOR_TYPE=orb` または `DETECTOR_TYPE=sift` を指定すると、同じ画像処理フローのまま検出器を切り替えられる。

`MASK_MODE=circle` にすると円形マスク、`MASK_MODE=ellipse` にすると横長や縦長を指定できる楕円マスクで keypoint を検出する。楕円では `MASK_RADIUS_X_RATIO` と `MASK_RADIUS_Y_RATIO` を使う。出力画像には検出対象の輪郭を黄色で描画し、その内部の keypoint を赤いドットで重ねる。マスクを使わない場合は `MASK_MODE=none` を指定する。

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
