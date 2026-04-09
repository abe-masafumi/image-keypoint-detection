from __future__ import annotations

from pathlib import Path

import cv2

from image_keypoint_detection.common import (
    FeatureDetectionResult,
    build_mask,
    draw_keypoint_count_label,
    draw_mask_outline,
)


def detect_sift_keypoints(
    image_path: str,
    *,
    output_image_path: str,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    nfeatures: int,
    contrast_threshold: float,
    edge_threshold: float,
    sigma: float,
) -> FeatureDetectionResult:
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
    sift = cv2.SIFT_create(
        nfeatures=nfeatures,
        contrastThreshold=contrast_threshold,
        edgeThreshold=edge_threshold,
        sigma=sigma,
    )
    keypoints, _ = sift.detectAndCompute(gray_image, mask)
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

    return FeatureDetectionResult(
        image_path=str(path),
        output_image_path=str(output_path),
        keypoint_count=len(keypoints),
        width=width,
        height=height,
        mask_mode=mask_mode,
        detector_type="sift",
    )
