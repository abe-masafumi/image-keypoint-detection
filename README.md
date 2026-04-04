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
   `.env.example` を参考に `.env` を作成し、`LOG_PATH`、`IMAGE_PATH`、`S3_BUCKET`、DB 接続情報を設定する

## Run
`PYTHONPATH=src python main.py`

この段階ではプロジェクト土台のみで、`.env` を含む設定値の読込確認までを行う。
