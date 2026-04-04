from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    log_path: str
    image_path: str
    s3_bucket: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_instance_connection_name: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv(dotenv_path=Path(".env"), override=False)
        return cls(
            log_path=os.getenv("LOG_PATH", "logs/app.log"),
            image_path=os.getenv("IMAGE_PATH", ""),
            s3_bucket=os.getenv("S3_BUCKET", "noseid-prod"),
            db_host=os.getenv("DB_HOST", ""),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", ""),
            db_user=os.getenv("DB_USER", ""),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_instance_connection_name=os.getenv(
                "DB_INSTANCE_CONNECTION_NAME",
                "",
            ),
        )
