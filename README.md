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
   `.env.example` を参考に `.env` を作成し、`LOG_PATH`、`IMAGE_PATH`、`OUTPUT_IMAGE_PATH`、`ORB_NFEATURES`、`ORB_SCALE_FACTOR`、`ORB_NLEVELS`、`ORB_FAST_THRESHOLD`、`ORB_EDGE_THRESHOLD`、`S3_BUCKET`、DB 接続情報を設定する

## Run
`PYTHONPATH=src python main.py`

`IMAGE_PATH` には画像ファイルかディレクトリを指定できる。`sample_images` のようなディレクトリを指定すると、その配下の画像をすべて処理し、`OUTPUT_IMAGE_PATH` に指定したディレクトリへ `{元ファイル名}_keypoints.jpg` の形式で出力する。
