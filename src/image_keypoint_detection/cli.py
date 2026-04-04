from __future__ import annotations

from image_keypoint_detection.config import AppConfig


def main() -> int:
    config = AppConfig.from_env()
    print("image-keypoint-detection project scaffold")
    print(f"LOG_PATH={config.log_path}")
    print(f"IMAGE_PATH={config.image_path or '<not set>'}")
    print(f"S3_BUCKET={config.s3_bucket}")
    print(f"DB_HOST={'<set>' if config.db_host else '<not set>'}")
    print(f"DB_PORT={config.db_port}")
    print(f"DB_NAME={'<set>' if config.db_name else '<not set>'}")
    print(f"DB_USER={'<set>' if config.db_user else '<not set>'}")
    print(
        "DB_INSTANCE_CONNECTION_NAME="
        f"{config.db_instance_connection_name or '<not set>'}"
    )
    return 0
