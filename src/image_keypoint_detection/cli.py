from __future__ import annotations

from image_keypoint_detection.config import AppConfig
from image_keypoint_detection.common import (
    build_output_image_path,
    collect_image_paths,
)
from image_keypoint_detection.orb import detect_orb_keypoints
from image_keypoint_detection.sift import detect_sift_keypoints


def main() -> int:
    config = AppConfig.from_env()
    if not config.image_path:
        print("IMAGE_PATH is not set")
        return 1

    try:
        image_paths = collect_image_paths(config.image_path)
    except Exception as exc:
        print(f"Failed to prepare input images: {exc}")
        return 1

    print("keypoint detection")
    print(f"INPUT_PATH={config.image_path}")
    print(f"IMAGE_COUNT={len(image_paths)}")
    print(f"DETECTOR_TYPE={config.detector_type}")
    print(f"MASK_MODE={config.mask_mode}")
    print(f"MASK_CENTER_X_RATIO={config.mask_center_x_ratio}")
    print(f"MASK_CENTER_Y_RATIO={config.mask_center_y_ratio}")
    print(f"MASK_RADIUS_RATIO={config.mask_radius_ratio}")
    print(f"MASK_RADIUS_X_RATIO={config.mask_radius_x_ratio}")
    print(f"MASK_RADIUS_Y_RATIO={config.mask_radius_y_ratio}")

    normalized_detector = config.detector_type.lower()
    if normalized_detector == "orb":
        print(f"ORB_NFEATURES={config.orb_nfeatures}")
        print(f"ORB_SCALE_FACTOR={config.orb_scale_factor}")
        print(f"ORB_NLEVELS={config.orb_nlevels}")
        print(f"ORB_FAST_THRESHOLD={config.orb_fast_threshold}")
        print(f"ORB_EDGE_THRESHOLD={config.orb_edge_threshold}")
    elif normalized_detector == "sift":
        print(f"SIFT_NFEATURES={config.sift_nfeatures}")
        print(f"SIFT_CONTRAST_THRESHOLD={config.sift_contrast_threshold}")
        print(f"SIFT_EDGE_THRESHOLD={config.sift_edge_threshold}")
        print(f"SIFT_SIGMA={config.sift_sigma}")
    else:
        print(f"Unsupported DETECTOR_TYPE: {config.detector_type}")
        return 1

    total_keypoints = 0
    for image_path in image_paths:
        output_image_path = build_output_image_path(
            image_path,
            input_path=config.image_path,
            output_image_path=config.output_image_path,
        )
        try:
            if normalized_detector == "orb":
                result = detect_orb_keypoints(
                    str(image_path),
                    output_image_path=str(output_image_path),
                    mask_mode=config.mask_mode,
                    mask_center_x_ratio=config.mask_center_x_ratio,
                    mask_center_y_ratio=config.mask_center_y_ratio,
                    mask_radius_ratio=config.mask_radius_ratio,
                    mask_radius_x_ratio=config.mask_radius_x_ratio,
                    mask_radius_y_ratio=config.mask_radius_y_ratio,
                    nfeatures=config.orb_nfeatures,
                    scale_factor=config.orb_scale_factor,
                    nlevels=config.orb_nlevels,
                    fast_threshold=config.orb_fast_threshold,
                    edge_threshold=config.orb_edge_threshold,
                )
            else:
                result = detect_sift_keypoints(
                    str(image_path),
                    output_image_path=str(output_image_path),
                    mask_mode=config.mask_mode,
                    mask_center_x_ratio=config.mask_center_x_ratio,
                    mask_center_y_ratio=config.mask_center_y_ratio,
                    mask_radius_ratio=config.mask_radius_ratio,
                    mask_radius_x_ratio=config.mask_radius_x_ratio,
                    mask_radius_y_ratio=config.mask_radius_y_ratio,
                    nfeatures=config.sift_nfeatures,
                    contrast_threshold=config.sift_contrast_threshold,
                    edge_threshold=config.sift_edge_threshold,
                    sigma=config.sift_sigma,
                )
        except Exception as exc:
            print(f"FAILED IMAGE_PATH={image_path} ERROR={exc}")
            continue

        total_keypoints += result.keypoint_count
        print(f"IMAGE_PATH={result.image_path}")
        print(f"OUTPUT_IMAGE_PATH={result.output_image_path}")
        print(f"IMAGE_SIZE={result.width}x{result.height}")
        print(f"DETECTOR_TYPE={result.detector_type}")
        print(f"MASK_MODE={result.mask_mode}")
        print(f"KEYPOINT_COUNT={result.keypoint_count}")

    print(f"TOTAL_KEYPOINT_COUNT={total_keypoints}")
    return 0
