from __future__ import annotations

from datetime import datetime, timezone

from image_keypoint_detection.config import AppConfig
from image_keypoint_detection.common import (
    build_output_image_path,
    collect_image_paths,
)
from image_keypoint_detection.logger import (
    build_error_fields,
    log_event,
    setup_logger,
)
from image_keypoint_detection.orb import detect_orb_keypoints
from image_keypoint_detection.sift import detect_sift_keypoints


def main() -> int:
    config = AppConfig.from_env()
    logger = setup_logger(config.log_path)
    run_at = datetime.now(timezone.utc).isoformat()

    if not config.image_path:
        print("IMAGE_PATH is not set")
        log_event(
            logger,
            executed_at=run_at,
            input_image_path=config.image_path,
            status="failure",
            **build_error_fields(ValueError("IMAGE_PATH is not set")),
        )
        return 1

    try:
        image_paths = collect_image_paths(config.image_path)
    except Exception as exc:
        print(f"Failed to prepare input images: {exc}")
        log_event(
            logger,
            event="run_failure",
            executed_at=run_at,
            input_image_path=config.image_path,
            status="failure",
            **build_error_fields(exc),
        )
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

    log_event(
        logger,
        event="run_start",
        executed_at=run_at,
        input_path=config.image_path,
        image_count=len(image_paths),
        detector_type=config.detector_type,
        mask_mode=config.mask_mode,
        mask_center_x_ratio=config.mask_center_x_ratio,
        mask_center_y_ratio=config.mask_center_y_ratio,
        mask_radius_ratio=config.mask_radius_ratio,
        mask_radius_x_ratio=config.mask_radius_x_ratio,
        mask_radius_y_ratio=config.mask_radius_y_ratio,
        status="started",
    )

    total_keypoints = 0
    success_count = 0
    failure_count = 0
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
            failure_count += 1
            log_event(
                logger,
                event="image_result",
                executed_at=run_at,
                input_image_path=str(image_path),
                status="failure",
                **build_error_fields(exc),
            )
            continue

        total_keypoints += result.keypoint_count
        success_count += 1
        print(f"IMAGE_PATH={result.image_path}")
        print(f"OUTPUT_IMAGE_PATH={result.output_image_path}")
        print(f"IMAGE_SIZE={result.width}x{result.height}")
        print(f"DETECTOR_TYPE={result.detector_type}")
        print(f"MASK_MODE={result.mask_mode}")
        print(f"KEYPOINT_COUNT={result.keypoint_count}")
        log_event(
            logger,
            event="image_result",
            executed_at=run_at,
            input_image_path=result.image_path,
            output_image_path=result.output_image_path,
            keypoint_count=result.keypoint_count,
            status="success",
            error_message="",
            stack_trace="",
        )

    print(f"TOTAL_KEYPOINT_COUNT={total_keypoints}")
    log_event(
        logger,
        event="run_summary",
        executed_at=run_at,
        total_image_count=len(image_paths),
        success_count=success_count,
        failure_count=failure_count,
        total_keypoint_count=total_keypoints,
        status="completed",
        error_message="",
        stack_trace="",
    )
    return 0
