from __future__ import annotations

from pathlib import Path

import cv2
from image_keypoint_detection.common import (
    FeatureDetectionResult,
    build_mask,
    decode_image_bytes,
    draw_keypoint_count_label,
    draw_mask_outline,
)


def detect_orb_keypoints(
    image_path: str,
    *,
    output_image_path: str,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    mask_radius_x_ratio: float,
    mask_radius_y_ratio: float,
    nfeatures: int,
    scale_factor: float,
    nlevels: int,
    edge_threshold: int,
    first_level: int,
    wta_k: int,
    score_type: str,
    patch_size: int,
    fast_threshold: int,
) -> FeatureDetectionResult:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    source_image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if source_image is None:
        raise ValueError(f"Failed to decode image: {image_path}")

    gray_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
    return _detect_orb_keypoints(
        image_name=str(path),
        source_image=source_image,
        gray_image=gray_image,
        output_image_path=output_image_path,
        mask_mode=mask_mode,
        mask_center_x_ratio=mask_center_x_ratio,
        mask_center_y_ratio=mask_center_y_ratio,
        mask_radius_ratio=mask_radius_ratio,
        mask_radius_x_ratio=mask_radius_x_ratio,
        mask_radius_y_ratio=mask_radius_y_ratio,
        nfeatures=nfeatures,
        scale_factor=scale_factor,
        nlevels=nlevels,
        edge_threshold=edge_threshold,
        first_level=first_level,
        wta_k=wta_k,
        score_type=score_type,
        patch_size=patch_size,
        fast_threshold=fast_threshold,
    )


def detect_orb_keypoints_from_bytes(
    image_bytes: bytes,
    *,
    image_name: str,
    output_image_path: str,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    mask_radius_x_ratio: float,
    mask_radius_y_ratio: float,
    nfeatures: int,
    scale_factor: float,
    nlevels: int,
    edge_threshold: int,
    first_level: int,
    wta_k: int,
    score_type: str,
    patch_size: int,
    fast_threshold: int,
) -> FeatureDetectionResult:
    source_image, gray_image = decode_image_bytes(image_bytes)
    return _detect_orb_keypoints(
        image_name=image_name,
        source_image=source_image,
        gray_image=gray_image,
        output_image_path=output_image_path,
        mask_mode=mask_mode,
        mask_center_x_ratio=mask_center_x_ratio,
        mask_center_y_ratio=mask_center_y_ratio,
        mask_radius_ratio=mask_radius_ratio,
        mask_radius_x_ratio=mask_radius_x_ratio,
        mask_radius_y_ratio=mask_radius_y_ratio,
        nfeatures=nfeatures,
        scale_factor=scale_factor,
        nlevels=nlevels,
        edge_threshold=edge_threshold,
        first_level=first_level,
        wta_k=wta_k,
        score_type=score_type,
        patch_size=patch_size,
        fast_threshold=fast_threshold,
    )


def _detect_orb_keypoints(
    *,
    image_name: str,
    source_image,
    gray_image,
    output_image_path: str,
    mask_mode: str,
    mask_center_x_ratio: float,
    mask_center_y_ratio: float,
    mask_radius_ratio: float,
    mask_radius_x_ratio: float,
    mask_radius_y_ratio: float,
    nfeatures: int,
    scale_factor: float,
    nlevels: int,
    edge_threshold: int,
    first_level: int,
    wta_k: int,
    score_type: str,
    patch_size: int,
    fast_threshold: int,
) -> FeatureDetectionResult:
    mask = build_mask(
        gray_image,
        mask_mode=mask_mode,
        mask_center_x_ratio=mask_center_x_ratio,
        mask_center_y_ratio=mask_center_y_ratio,
        mask_radius_ratio=mask_radius_ratio,
        mask_radius_x_ratio=mask_radius_x_ratio,
        mask_radius_y_ratio=mask_radius_y_ratio,
    )
    orb = cv2.ORB_create(
        nfeatures=nfeatures,
        scaleFactor=scale_factor,
        nlevels=nlevels,
        edgeThreshold=edge_threshold,
        firstLevel=first_level,
        WTA_K=wta_k,
        scoreType=_resolve_orb_score_type(score_type),
        patchSize=patch_size,
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
        mask_radius_x_ratio=mask_radius_x_ratio,
        mask_radius_y_ratio=mask_radius_y_ratio,
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
        image_path=image_name,
        output_image_path=str(output_path),
        keypoint_count=len(keypoints),
        width=width,
        height=height,
        mask_mode=mask_mode,
        detector_type="orb",
    )


def _resolve_orb_score_type(score_type: str) -> int:
    normalized = score_type.strip().upper()
    if normalized == "HARRIS_SCORE":
        return cv2.ORB_HARRIS_SCORE
    if normalized == "FAST_SCORE":
        return cv2.ORB_FAST_SCORE
    raise ValueError(
        "Unsupported ORB_SCORE_TYPE. Use HARRIS_SCORE or FAST_SCORE."
    )
