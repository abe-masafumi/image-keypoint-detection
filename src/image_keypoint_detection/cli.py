from __future__ import annotations

from image_keypoint_detection.config import AppConfig
from image_keypoint_detection.orb import (
    build_output_image_path,
    collect_image_paths,
    detect_orb_keypoints,
)


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

    print("ORB keypoint detection")
    print(f"INPUT_PATH={config.image_path}")
    print(f"IMAGE_COUNT={len(image_paths)}")
    print(f"ORB_MASK_MODE={config.orb_mask_mode}")
    print(f"ORB_MASK_CENTER_X_RATIO={config.orb_mask_center_x_ratio}")
    print(f"ORB_MASK_CENTER_Y_RATIO={config.orb_mask_center_y_ratio}")
    print(f"ORB_MASK_RADIUS_RATIO={config.orb_mask_radius_ratio}")
    print(f"ORB_NFEATURES={config.orb_nfeatures}")
    print(f"ORB_SCALE_FACTOR={config.orb_scale_factor}")
    print(f"ORB_NLEVELS={config.orb_nlevels}")
    print(f"ORB_FAST_THRESHOLD={config.orb_fast_threshold}")
    print(f"ORB_EDGE_THRESHOLD={config.orb_edge_threshold}")

    total_keypoints = 0
    for image_path in image_paths:
        output_image_path = build_output_image_path(
            image_path,
            input_path=config.image_path,
            output_image_path=config.output_image_path,
        )
        try:
            result = detect_orb_keypoints(
                str(image_path),
                output_image_path=str(output_image_path),
                mask_mode=config.orb_mask_mode,
                mask_center_x_ratio=config.orb_mask_center_x_ratio,
                mask_center_y_ratio=config.orb_mask_center_y_ratio,
                mask_radius_ratio=config.orb_mask_radius_ratio,
                nfeatures=config.orb_nfeatures,
                scale_factor=config.orb_scale_factor,
                nlevels=config.orb_nlevels,
                fast_threshold=config.orb_fast_threshold,
                edge_threshold=config.orb_edge_threshold,
            )
        except Exception as exc:
            print(f"FAILED IMAGE_PATH={image_path} ERROR={exc}")
            continue

        total_keypoints += result.keypoint_count
        print(f"IMAGE_PATH={result.image_path}")
        print(f"OUTPUT_IMAGE_PATH={result.output_image_path}")
        print(f"IMAGE_SIZE={result.width}x{result.height}")
        print(f"MASK_MODE={result.mask_mode}")
        print(f"KEYPOINT_COUNT={result.keypoint_count}")

    print(f"TOTAL_KEYPOINT_COUNT={total_keypoints}")
    return 0
