# ORB Keypoint Count 実装タスク

## 目的
- `nose_images` テーブルの `object_key` を起点に `noseid-prod` バケット上の画像を取得する
- OpenCV ORB で keypoint を計算し、検出件数 `len(keypoints)` を `keypoints_orb` カラムへ保存する
- 実行結果とエラー内容をプロジェクトのログファイルへ記録する

## 前提確認
- DB 接続情報の取得方法を決める
  - Cloud SQL の接続方式を決める
    - Public IP 接続
    - Private IP 接続
    - Cloud SQL Auth Proxy 利用
  - 接続先ホスト、ポート、DB 名、ユーザー、パスワード
  - インスタンス接続名が必要か確認する
    - 例: `project-id:region:instance-name`
  - 接続元から Cloud SQL へ疎通できるか確認する
  - SSL 接続が必要か確認する
  - 実行環境では環境変数で注入するか、設定ファイルで管理するかを決める
- AWS 認証情報の取得方法を決める
  - `noseid-prod` バケットへ `GetObject` できる IAM 権限が必要
- `nose_images` テーブル定義を確認する
  - `id`
  - `object_key`
  - `keypoints_orb`
  - 対象データの抽出条件が必要かどうか
- 一括実行の対象範囲を確認する
  - 全件更新
  - `keypoints_orb IS NULL` のみ更新
  - 特定期間や件数指定での実行が必要か

## 実装タスク

### 1. プロジェクト土台の作成
ブランチ名：`feature/01-project-setup`
- Python 実行エントリポイントを作成する
- 依存ライブラリ管理ファイルを追加する
  - `boto3`
  - `psycopg2-binary`
  - `opencv-python`
  - `numpy`
- 設定値を環境変数から読む仕組みを作る
  - ログファイルパス
  - 単画像検証用のローカル画像パス
  - 将来拡張用の S3 バケット名
  - 将来拡張用の DB 接続情報

### 2. 単画像の ORB keypoint 計算処理
ブランチ名：`feature/02-single-image-orb`
- OpenCV ORB で keypoint を検出する処理を実装する
- 基本フローを実装する
  - ローカル画像ファイルを読み込む
  - 必要に応じてグレースケール変換
  - ORB で `detect` または `detectAndCompute` を実行
  - `len(keypoints)` を算出
- ORB パラメータを設定可能にするか検討する
  - `nfeatures`
  - `scaleFactor`
  - `nlevels`
- 単画像に対して keypoint 数を標準出力またはログに出せるようにする

### 3. 単画像向けログ出力
ブランチ名：`feature/03-single-image-logging`
- 単画像実行時の成功時・失敗時のログ形式を定義する
- 最低限以下を出力する
  - 実行日時
  - 入力画像パス
  - エラー内容
  - スタックトレース
  - 成功 / 失敗
- 後続の S3 / DB / バッチ処理でも流用できるログ実装にする

### 4. 単画像 CLI / 実行方法の整備 (スキップ)
ブランチ名：`feature/04-single-image-cli`
- ローカル画像 1 枚を指定して実行するコマンドを決める
- 必要なら引数を追加する
  - `--image-path`
  - `--log-path`
  - `--nfeatures`
- `README.md` に単画像検証の実行手順を追記する

### 5. 単画像のテストと検証 (スキップ)
ブランチ名：`feature/05-single-image-test`
- 単体確認項目を整理する
  - ローカル画像を読み込める
  - ORB keypoint 数を取得できる
  - 画像が読めない場合に失敗ログが残る
- サンプル画像 1 枚で試験実行する
- 破損画像や非画像ファイルの異常系を確認する

### 6. S3 画像取得処理
ブランチ名：`feature/06-s3-image-fetch`
- `object_key` を使って `noseid-prod` バケットから画像を取得する処理を実装する
- S3 から取得したバイト列を OpenCV で扱える形式へ変換する
- 単画像 ORB 処理へ S3 取得結果を渡せるようにする
- 存在しないキー、権限不足、破損データに対する例外処理を実装する

### 7. DB アクセス処理
ブランチ名：`feature/07-db-access`
- DB 読み取りのみ実施する
- `nose_images` テーブルから対象レコードを取得するクエリを実装する
- 取得項目を定義する
  - `id`
  - `object_key`
- 更新処理は保留とする
  - `keypoints_orb` カラム作成待ちのため、このブランチでは実装しない
- 更新系のトランザクション方針は保留とする
  - 1件ごとに更新・コミットする
  - 一定件数ごとにまとめてコミットする

### 8. 更新バッチ処理
ブランチ名：`feature/08-keypoint-update-batch`
- まずは更新前バッチとして実装する
- DB 取得 -> S3 取得 -> ORB 計算 -> 更新対象データ作成の一連の処理をつなぐ
- DB 更新処理は `keypoints_orb` カラム作成後に追加する
- 1回の実行件数を制御できるようにする
  - `DB_FETCH_LIMIT`
- 実行対象を再開しやすい形で取得できるようにする
  - 取得順を固定する
  - 既存条件で対象を絞れるようにする
- 更新前の dry-run 相当として結果を標準出力またはログへ出せるようにする
  - `id`
  - `object_key`
  - `keypoint_count`
  - `status`
- 1件ごとの成功 / 失敗を判定する
- 失敗しても全体処理を継続できるようにする
- 実行件数、成功件数、失敗件数、スキップ件数を集計する
- 本番更新対応時の実装方針を以下とする
  - `APP_MODE` はバッチ用で統一し、dry-run の有無は `BATCH_DRY_RUN=true/false` で切り替える
  - `BATCH_DRY_RUN=true`
    - DB 更新は行わない
    - `id`, `object_key`, `keypoint_count`, `status` を標準出力とログへ出力する
  - `BATCH_DRY_RUN=false`
    - `keypoints_orb` へ実際に更新する
  - 取得対象は `keypoints_orb IS NULL` のみとする
  - 取得順は `ORDER BY id ASC` で固定する
  - 実行件数は `DB_FETCH_LIMIT` で制御する
  - 更新 SQL は `WHERE id = %s AND keypoints_orb IS NULL` を含める
    - 途中停止後の再実行時に更新済みデータを自然にスキップできるようにする
  - 更新は 1件ごとに実施し、成功したものから順にコミットする
  - 1件失敗しても全体は継続し、失敗内容はログへ残す
  - `keypoints_orb` カラムを持つ更新先テーブルは、読み取り元テーブルとは別に指定できるようにする
    - 更新先テーブル名は環境変数で指定する
    - 例: `DB_UPDATE_TABLE`
  - `keypoints_orb` カラムを持つ更新先テーブルが未作成の場合は、本番更新処理を有効化しない

### 9. バッチ向けログ出力
ブランチ名：`feature/09-batch-logging`
- プロジェクト内のログファイル出力先を決める
- 成功時・失敗時のログ形式を定義する
- 最低限以下を出力する
  - 実行日時
  - `nose_images.id`
  - `object_key`
  - エラー内容
  - スタックトレース
  - 成功 / 失敗
- バッチ開始 / 終了ログとサマリーログも出力する

### 10. バッチ CLI / 実行方法の整備
ブランチ名：`feature/10-batch-cli`
- バッチ実行コマンドを決める
- 必要なら引数を追加する
  - `--limit`
  - `--dry-run`
  - `--only-null`
- `README.md` にバッチ実行手順と必要な環境変数を追記する

### 11. バッチのテストと検証
ブランチ名：`feature/11-batch-test`
- 確認項目を整理する
  - DB から対象データを取得できる
  - S3 から画像取得できる
  - 画像から ORB keypoint 数を取得できる
  - `keypoints_orb` が更新される
  - エラー時にログが残る
- 少件数で試験実行できるようにする
- 画像が読めないケース、S3 に存在しないケースの異常系を確認する

## 実装時の注意点
- `object_key` は S3 のフルパスではなくキー文字列として扱う
- OpenCV の画像デコード失敗時は DB 更新せず、失敗ログのみ残す
- 途中失敗時も他レコードの処理は継続する
- 全件処理時の負荷を考慮し、必要なら件数制限や再開しやすい仕組みを入れる
- 同じレコードを再実行したときの上書き方針を決める

## 未決事項
- `keypoints_orb` を更新対象にする条件
- 並列処理を行うかどうか
- ログファイル名と配置場所
- 実行スケジュールの有無
- 本番 DB / 本番 S3 に対する実行手順と権限管理

## Cloud SQL 接続確認で必要な情報
- DB エンジン種別
  - PostgreSQL か MySQL か
- Cloud SQL インスタンス情報
  - GCP Project ID
  - Region
  - Instance 名
  - Instance Connection Name
- 接続方式
  - Public IP / Private IP / Cloud SQL Auth Proxy のどれを使うか
- 接続先情報
  - Host
  - Port
  - Database 名
  - User 名
  - Password
- ネットワーク要件
  - 実行環境の送信元 IP を許可する必要があるか
  - VPC 接続が必要か
  - Proxy を経由するか
- 認証・権限
  - DB ユーザーに `nose_images` の `SELECT` / `UPDATE` 権限があるか
  - Cloud SQL Auth Proxy を使う場合は GCP サービスアカウント権限があるか
- SSL / 証明書要件
  - SSL 必須か
  - クライアント証明書の利用有無
- 対象スキーマ情報
  - `nose_images` テーブルのスキーマ名
  - `id`, `object_key`, `keypoints_orb` の型
  - 更新条件に使うカラムの有無
