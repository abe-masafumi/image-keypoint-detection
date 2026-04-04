from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class OrbResult:
    image_path: str
    output_image_path: str
    keypoint_count: int
    width: int
    height: int
    mask_mode: str


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


def detect_orb_keypoints(
    image_path: str,
    *,
    output_image_path: str,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    nfeatures: int,
    scale_factor: float,
    nlevels: int,
    fast_threshold: int,
    edge_threshold: int,
) -> OrbResult:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    source_image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if source_image is None:
        raise ValueError(f"Failed to decode image: {image_path}")

    gray_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
    mask = build_mask(
        gray_image,
        mask_mode=mask_mode,
        mask_center_x_ratio=mask_center_x_ratio,
        mask_center_y_ratio=mask_center_y_ratio,
        mask_radius_ratio=mask_radius_ratio,
    )
    orb = cv2.ORB_create(
        nfeatures=nfeatures,
        scaleFactor=scale_factor,
        nlevels=nlevels,
        edgeThreshold=edge_threshold,
        fastThreshold=fast_threshold,
    )
    keypoints, _ = orb.detectAndCompute(gray_image, mask)
    output_path = Path(output_image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    annotated_image = source_image.copy()
    draw_mask_outline(
        annotated_image,
        mask_mode=mask_mode,
        mask_center_x_ratio=mask_center_x_ratio,
        mask_center_y_ratio=mask_center_y_ratio,
        mask_radius_ratio=mask_radius_ratio,
    )
    for keypoint in keypoints:
        x, y = keypoint.pt
        cv2.circle(
            annotated_image,
            center=(int(round(x)), int(round(y))),
            radius=2,
            color=(0, 0, 255),
            thickness=-1,
        )
    draw_keypoint_count_label(annotated_image, len(keypoints))

    if not cv2.imwrite(str(output_path), annotated_image):
        raise ValueError(f"Failed to write output image: {output_image_path}")

    height, width = gray_image.shape[:2]

    return OrbResult(
        image_path=str(path),
        output_image_path=str(output_path),
        keypoint_count=len(keypoints),
        width=width,
        height=height,
        mask_mode=mask_mode,
    )


def build_mask(
    gray_image: np.ndarray,
    *,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
) -> np.ndarray | None:
    normalized_mode = mask_mode.lower()
    if normalized_mode == "none":
        return None
    if normalized_mode != "circle":
        raise ValueError(f"Unsupported ORB_MASK_MODE: {mask_mode}")

    height, width = gray_image.shape[:2]
    center = (
        int(round(width * mask_center_x_ratio)),
        int(round(height * mask_center_y_ratio)),
    )
    radius = max(1, int(round(min(width, height) * mask_radius_ratio)))

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)
    return mask


def draw_mask_outline(
    image: np.ndarray,
    *,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
) -> None:
    normalized_mode = mask_mode.lower()
    if normalized_mode != "circle":
        return

    height, width = image.shape[:2]
    center = (
        int(round(width * mask_center_x_ratio)),
        int(round(height * mask_center_y_ratio)),
    )
    radius = max(1, int(round(min(width, height) * mask_radius_ratio)))
    cv2.circle(image, center, radius, (0, 255, 255), 2)


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
