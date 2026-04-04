from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class OrbResult:
    image_path: str
    output_image_path: str
    keypoint_count: int
    width: int
    height: int


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
    orb = cv2.ORB_create(
        nfeatures=nfeatures,
        scaleFactor=scale_factor,
        nlevels=nlevels,
        edgeThreshold=edge_threshold,
        fastThreshold=fast_threshold,
    )
    keypoints, _ = orb.detectAndCompute(gray_image, None)
    output_path = Path(output_image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    annotated_image = source_image.copy()
    for keypoint in keypoints:
        x, y = keypoint.pt
        cv2.circle(
            annotated_image,
            center=(int(round(x)), int(round(y))),
            radius=2,
            color=(0, 0, 255),
            thickness=-1,
        )

    if not cv2.imwrite(str(output_path), annotated_image):
        raise ValueError(f"Failed to write output image: {output_image_path}")

    height, width = gray_image.shape[:2]

    return OrbResult(
        image_path=str(path),
        output_image_path=str(output_path),
        keypoint_count=len(keypoints),
        width=width,
        height=height,
    )
