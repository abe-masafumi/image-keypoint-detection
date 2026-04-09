from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class FeatureDetectionResult:
    image_path: str
    output_image_path: str
    keypoint_count: int
    width: int
    height: int
    mask_mode: str
    detector_type: str


def collect_image_paths(input_path: str) -> list[Path]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    if path.is_file():
        return [path]

    image_paths = sorted(
        file_path
        for file_path in path.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        raise ValueError(f"No image files found in directory: {input_path}")

    return image_paths


def build_output_image_path(
    source_image_path: Path,
    *,
    input_path: str,
    output_image_path: str,
) -> Path:
    input_root = Path(input_path)
    output_path = Path(output_image_path)

    if input_root.is_dir() or not output_path.suffix:
        if output_path.suffix:
            output_dir = output_path.parent
        else:
            output_dir = output_path
        return output_dir / (
            f"{source_image_path.stem}_keypoints{source_image_path.suffix}"
        )

    return output_path


def build_mask(
    gray_image: np.ndarray,
    *,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    mask_radius_x_ratio: float,
    mask_radius_y_ratio: float,
) -> np.ndarray | None:
    normalized_mode = mask_mode.lower()
    if normalized_mode == "none":
        return None
    if normalized_mode not in {"circle", "ellipse"}:
        raise ValueError(f"Unsupported MASK_MODE: {mask_mode}")

    height, width = gray_image.shape[:2]
    center = (
        int(round(width * mask_center_x_ratio)),
        int(round(height * mask_center_y_ratio)),
    )
    mask = np.zeros((height, width), dtype=np.uint8)
    if normalized_mode == "circle":
        radius = max(1, int(round(min(width, height) * mask_radius_ratio)))
        cv2.circle(mask, center, radius, 255, -1)
    else:
        axes = (
            max(1, int(round(width * mask_radius_x_ratio))),
            max(1, int(round(height * mask_radius_y_ratio))),
        )
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask


def draw_mask_outline(
    image: np.ndarray,
    *,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    mask_radius_x_ratio: float,
    mask_radius_y_ratio: float,
) -> None:
    normalized_mode = mask_mode.lower()
    if normalized_mode not in {"circle", "ellipse"}:
        return

    height, width = image.shape[:2]
    center = (
        int(round(width * mask_center_x_ratio)),
        int(round(height * mask_center_y_ratio)),
    )
    if normalized_mode == "circle":
        radius = max(1, int(round(min(width, height) * mask_radius_ratio)))
        cv2.circle(image, center, radius, (0, 255, 255), 2)
    else:
        axes = (
            max(1, int(round(width * mask_radius_x_ratio))),
            max(1, int(round(height * mask_radius_y_ratio))),
        )
        cv2.ellipse(image, center, axes, 0, 0, 360, (0, 255, 255), 2)


def draw_keypoint_count_label(image: np.ndarray, keypoint_count: int) -> None:
    label = str(keypoint_count)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    margin = 16

    (text_width, text_height), baseline = cv2.getTextSize(
        label,
        font,
        font_scale,
        thickness,
    )

    x = max(margin, image.shape[1] - text_width - margin)
    y = max(text_height + margin, image.shape[0] - baseline - margin)

    top_left = (x - 10, y - text_height - 10)
    bottom_right = (x + text_width + 10, y + baseline + 10)
    cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), -1)
    cv2.putText(
        image,
        label,
        (x, y),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
