from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    app_mode: str
    log_path: str
    image_path: str
    output_image_path: str
    detector_type: str
    mask_mode: str
    mask_center_x_ratio: float
    mask_center_y_ratio: float
    mask_radius_ratio: float
    mask_radius_x_ratio: float
    mask_radius_y_ratio: float
    orb_nfeatures: int
    orb_scale_factor: float
    orb_nlevels: int
    orb_fast_threshold: int
    orb_edge_threshold: int
    sift_nfeatures: int
    sift_contrast_threshold: float
    sift_edge_threshold: float
    sift_sigma: float
    s3_bucket: str
    db_connection_type: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_schema: str
    db_source_table: str
    db_update_table: str
    db_fetch_limit: int | None
    db_instance_connection_name: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv(dotenv_path=Path(".env"), override=False)
        return cls(
            app_mode=os.getenv("APP_MODE", "image_keypoint"),
            log_path=os.getenv("LOG_PATH", "logs/app.log"),
            image_path=os.getenv("IMAGE_PATH", ""),
            output_image_path=os.getenv(
                "OUTPUT_IMAGE_PATH",
                "output_images/sample_keypoints.jpg",
            ),
            detector_type=os.getenv("DETECTOR_TYPE", "orb"),
            mask_mode=os.getenv("MASK_MODE", "none"),
            mask_center_x_ratio=float(os.getenv("MASK_CENTER_X_RATIO", "0.5")),
            mask_center_y_ratio=float(os.getenv("MASK_CENTER_Y_RATIO", "0.5")),
            mask_radius_ratio=float(os.getenv("MASK_RADIUS_RATIO", "0.35")),
            mask_radius_x_ratio=float(os.getenv("MASK_RADIUS_X_RATIO", "0.45")),
            mask_radius_y_ratio=float(os.getenv("MASK_RADIUS_Y_RATIO", "0.35")),
            orb_nfeatures=int(os.getenv("ORB_NFEATURES", "500")),
            orb_scale_factor=float(os.getenv("ORB_SCALE_FACTOR", "1.2")),
            orb_nlevels=int(os.getenv("ORB_NLEVELS", "8")),
            orb_fast_threshold=int(os.getenv("ORB_FAST_THRESHOLD", "20")),
            orb_edge_threshold=int(os.getenv("ORB_EDGE_THRESHOLD", "31")),
            sift_nfeatures=int(os.getenv("SIFT_NFEATURES", "0")),
            sift_contrast_threshold=float(
                os.getenv("SIFT_CONTRAST_THRESHOLD", "0.04")
            ),
            sift_edge_threshold=float(os.getenv("SIFT_EDGE_THRESHOLD", "10")),
            sift_sigma=float(os.getenv("SIFT_SIGMA", "1.6")),
            s3_bucket=os.getenv("S3_BUCKET", "noseid-prod"),
            db_connection_type=os.getenv("DB_CONNECTION_TYPE", "public_ip"),
            db_host=os.getenv("DB_HOST", ""),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", ""),
            db_user=os.getenv("DB_USER", ""),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_schema=os.getenv("DB_SCHEMA", "public"),
            db_source_table=os.getenv("DB_SOURCE_TABLE", "nose_images"),
            db_update_table=os.getenv("DB_UPDATE_TABLE", "nose_images"),
            db_fetch_limit=_get_optional_int("DB_FETCH_LIMIT"),
            db_instance_connection_name=os.getenv(
                "DB_INSTANCE_CONNECTION_NAME",
                "",
            ),
        )


def _get_optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    return int(value)
