from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from image_keypoint_detection.config import AppConfig
from image_keypoint_detection.common import (
    build_output_image_path,
    collect_image_paths,
)
from image_keypoint_detection.db import (
    fetch_latest_nose_images,
    fetch_nose_images_for_batch,
    insert_nose_image_quality,
    connect_postgres,
)
from image_keypoint_detection.logger import (
    build_error_fields,
    log_event,
    setup_logger,
)
from image_keypoint_detection.orb import (
    detect_orb_keypoints,
    detect_orb_keypoints_from_bytes,
)
from image_keypoint_detection.s3 import fetch_s3_object_bytes
from image_keypoint_detection.sift import (
    detect_sift_keypoints,
    detect_sift_keypoints_from_bytes,
)


def main() -> int:
    config = AppConfig.from_env()
    logger = setup_logger(config.log_path)
    batch_error_logger = setup_logger(
        config.batch_error_log_path,
        logger_name="image_keypoint_detection_batch_errors",
        daily_rotate=False,
    )
    run_at = datetime.now(timezone.utc).isoformat()

    if config.app_mode == "db_fetch_latest":
        return run_db_fetch_latest(config, logger, run_at)
    if config.app_mode == "batch_prepare_keypoints":
        return run_batch_prepare_keypoints(
            config,
            logger,
            batch_error_logger,
            run_at,
        )

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
        print(f"ORB_EDGE_THRESHOLD={config.orb_edge_threshold}")
        print(f"ORB_FIRST_LEVEL={config.orb_first_level}")
        print(f"ORB_WTA_K={config.orb_wta_k}")
        print(f"ORB_SCORE_TYPE={config.orb_score_type}")
        print(f"ORB_PATCH_SIZE={config.orb_patch_size}")
        print(f"ORB_FAST_THRESHOLD={config.orb_fast_threshold}")
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
                    edge_threshold=config.orb_edge_threshold,
                    first_level=config.orb_first_level,
                    wta_k=config.orb_wta_k,
                    score_type=config.orb_score_type,
                    patch_size=config.orb_patch_size,
                    fast_threshold=config.orb_fast_threshold,
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


def run_db_fetch_latest(config: AppConfig, logger, run_at: str) -> int:
    print("db latest records fetch")
    print(f"DB_CONNECTION_TYPE={config.db_connection_type}")
    print(f"DB_HOST={config.db_host}")
    print(f"DB_PORT={config.db_port}")
    print(f"DB_NAME={config.db_name}")
    print(f"DB_SCHEMA={config.db_schema}")
    print(f"DB_SOURCE_TABLE={config.db_source_table}")
    print(f"DB_FETCH_LIMIT={config.db_fetch_limit}")

    log_event(
        logger,
        event="db_fetch_start",
        executed_at=run_at,
        db_connection_type=config.db_connection_type,
        db_host=config.db_host,
        db_port=config.db_port,
        db_name=config.db_name,
        db_schema=config.db_schema,
        db_source_table=config.db_source_table,
        db_fetch_limit=config.db_fetch_limit,
        status="started",
    )

    try:
        records = fetch_latest_nose_images(config, limit=config.db_fetch_limit)
    except Exception as exc:
        print(f"DB fetch failed: {exc}")
        log_event(
            logger,
            event="db_fetch_failure",
            executed_at=run_at,
            db_schema=config.db_schema,
            db_source_table=config.db_source_table,
            db_fetch_limit=config.db_fetch_limit,
            status="failure",
            **build_error_fields(exc),
        )
        return 1

    for record in records:
        print(f"nose_image_id={record.id} object_key={record.object_key}")
        log_event(
            logger,
            event="db_fetch_record",
            executed_at=run_at,
            id=record.id,
            object_key=record.object_key,
            status="success",
            error_message="",
            stack_trace="",
        )

    log_event(
        logger,
        event="db_fetch_summary",
        executed_at=run_at,
        db_schema=config.db_schema,
        db_source_table=config.db_source_table,
        fetched_count=len(records),
        status="completed",
        error_message="",
        stack_trace="",
    )
    return 0


def run_batch_prepare_keypoints(
    config: AppConfig,
    logger,
    batch_error_logger,
    run_at: str,
) -> int:
    print("batch prepare keypoints")
    print(f"BATCH_DRY_RUN={config.batch_dry_run}")
    print(f"DB_REGISTRATION_TABLE={config.db_schema}.{config.db_registration_table}")
    print(f"DB_SOURCE_TABLE={config.db_schema}.{config.db_source_table}")
    print(f"DB_UPDATE_TABLE={config.db_schema}.{config.db_update_table}")
    print(f"S3_BUCKET={config.s3_bucket}")
    print(f"DB_FETCH_LIMIT={config.db_fetch_limit}")
    print(f"DETECTOR_TYPE={config.detector_type}")

    normalized_detector = config.detector_type.lower()
    if normalized_detector not in {"orb", "sift"}:
        print(f"Unsupported DETECTOR_TYPE: {config.detector_type}")
        return 1

    log_event(
        logger,
        event="batch_prepare_start",
        executed_at=run_at,
        batch_dry_run=config.batch_dry_run,
        db_registration_table=config.db_registration_table,
        db_schema=config.db_schema,
        db_source_table=config.db_source_table,
        db_update_table=config.db_update_table,
        s3_bucket=config.s3_bucket,
        db_fetch_limit=config.db_fetch_limit,
        detector_type=config.detector_type,
        status="started",
    )

    try:
        records = fetch_nose_images_for_batch(config, limit=config.db_fetch_limit)
    except Exception as exc:
        print(f"Batch source fetch failed: {exc}")
        log_event(
            logger,
            event="batch_prepare_failure",
            executed_at=run_at,
            batch_dry_run=config.batch_dry_run,
            db_registration_table=config.db_registration_table,
            db_schema=config.db_schema,
            db_source_table=config.db_source_table,
            db_update_table=config.db_update_table,
            status="failure",
            **build_error_fields(exc),
        )
        _log_batch_issue(
            batch_error_logger,
            event="batch_prepare_failure",
            executed_at=run_at,
            batch_dry_run=config.batch_dry_run,
            db_registration_table=config.db_registration_table,
            db_schema=config.db_schema,
            db_source_table=config.db_source_table,
            db_update_table=config.db_update_table,
            status="failure",
            **build_error_fields(exc),
        )
        return 1

    success_count = 0
    failure_count = 0
    skip_count = 0
    total_keypoint_count = 0
    inserted_count = 0

    connection = None
    if not config.batch_dry_run:
        try:
            connection = connect_postgres(config)
        except Exception as exc:
            print(f"Batch update connection failed: {exc}")
            log_event(
                logger,
                event="batch_prepare_failure",
                executed_at=run_at,
                batch_dry_run=config.batch_dry_run,
                db_registration_table=config.db_registration_table,
                db_schema=config.db_schema,
                db_source_table=config.db_source_table,
                db_update_table=config.db_update_table,
                status="failure",
                **build_error_fields(exc),
            )
            _log_batch_issue(
                batch_error_logger,
                event="batch_prepare_failure",
                executed_at=run_at,
                batch_dry_run=config.batch_dry_run,
                db_registration_table=config.db_registration_table,
                db_schema=config.db_schema,
                db_source_table=config.db_source_table,
                db_update_table=config.db_update_table,
                status="failure",
                **build_error_fields(exc),
            )
            return 1

    try:
        for record in records:
            if (
                record.latest_image_count != 1
                or record.nose_image_id is None
                or not record.object_key
            ):
                skip_count += 1
                error_message = (
                    "Skipped because latest image count is not exactly 1"
                )
                print(
                    f"noseprint_id={record.noseprint_id} "
                    f"latest_image_count={record.latest_image_count} "
                    f"status=skipped reason=\"{error_message}\""
                )
                log_event(
                    logger,
                    event="batch_prepare_result",
                    executed_at=run_at,
                    nose_image_id=record.nose_image_id,
                    noseprint_id=record.noseprint_id,
                    object_key=record.object_key or "",
                    latest_image_count=record.latest_image_count,
                    status="skipped",
                    error_message=error_message,
                    stack_trace="",
                )
                _log_batch_issue(
                    batch_error_logger,
                    event="batch_prepare_result",
                    executed_at=run_at,
                    nose_image_id=record.nose_image_id,
                    noseprint_id=record.noseprint_id,
                    object_key=record.object_key or "",
                    latest_image_count=record.latest_image_count,
                    status="skipped",
                    error_message=error_message,
                    stack_trace="",
                )
                continue

            output_image_path = build_output_image_path(
                Path(record.object_key.split("/")[-1]),
                input_path=config.db_source_table,
                output_image_path=config.output_image_path,
            )
            try:
                image_bytes = fetch_s3_object_bytes(
                    config.s3_bucket,
                    record.object_key,
                    aws_profile=config.aws_profile,
                )
                if normalized_detector == "orb":
                    result = detect_orb_keypoints_from_bytes(
                        image_bytes,
                        image_name=record.object_key,
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
                        edge_threshold=config.orb_edge_threshold,
                        first_level=config.orb_first_level,
                        wta_k=config.orb_wta_k,
                        score_type=config.orb_score_type,
                        patch_size=config.orb_patch_size,
                        fast_threshold=config.orb_fast_threshold,
                    )
                else:
                    result = detect_sift_keypoints_from_bytes(
                        image_bytes,
                        image_name=record.object_key,
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
                failure_count += 1
                print(
                    f"nose_image_id={record.nose_image_id} noseprint_id={record.noseprint_id} "
                    f"object_key={record.object_key} status=failure error={exc}"
                )
                log_event(
                    logger,
                    event="batch_prepare_result",
                    executed_at=run_at,
                    nose_image_id=record.nose_image_id,
                    noseprint_id=record.noseprint_id,
                    object_key=record.object_key,
                    status="failure",
                    **build_error_fields(exc),
                )
                _log_batch_issue(
                    batch_error_logger,
                    event="batch_prepare_result",
                    executed_at=run_at,
                    nose_image_id=record.nose_image_id,
                    noseprint_id=record.noseprint_id,
                    object_key=record.object_key,
                    status="failure",
                    **build_error_fields(exc),
                )
                continue

            if not config.batch_dry_run:
                try:
                    inserted = insert_nose_image_quality(
                        connection,
                        config,
                        noseprint_id=record.noseprint_id,
                        keypoints_orb=result.keypoint_count,
                        app_version=config.db_update_app_version,
                    )
                    connection.commit()
                except Exception as exc:
                    connection.rollback()
                    failure_count += 1
                    print(
                        f"id={record.nose_image_id} noseprint_id={record.noseprint_id} "
                        f"object_key={record.object_key} status=failure error={exc}"
                    )
                    log_event(
                        logger,
                        event="batch_prepare_result",
                        executed_at=run_at,
                        nose_image_id=record.nose_image_id,
                        noseprint_id=record.noseprint_id,
                        object_key=record.object_key,
                        keypoint_count=result.keypoint_count,
                        status="failure",
                        **build_error_fields(exc),
                    )
                    _log_batch_issue(
                        batch_error_logger,
                        event="batch_prepare_result",
                        executed_at=run_at,
                        nose_image_id=record.nose_image_id,
                        noseprint_id=record.noseprint_id,
                        object_key=record.object_key,
                        keypoint_count=result.keypoint_count,
                        status="failure",
                        **build_error_fields(exc),
                    )
                    continue

                if inserted:
                    inserted_count += 1
                else:
                    skip_count += 1
                    print(
                        f"nose_image_id={record.nose_image_id} noseprint_id={record.noseprint_id} "
                        f"object_key={record.object_key} keypoint_count={result.keypoint_count} "
                        "status=skipped reason=\"nose_image_quality already exists\""
                    )
                    log_event(
                        logger,
                        event="batch_prepare_result",
                        executed_at=run_at,
                        nose_image_id=record.nose_image_id,
                        noseprint_id=record.noseprint_id,
                        object_key=record.object_key,
                        output_image_path=result.output_image_path,
                        keypoint_count=result.keypoint_count,
                        status="skipped",
                        error_message="nose_image_quality already exists",
                        stack_trace="",
                    )
                    _log_batch_issue(
                        batch_error_logger,
                        event="batch_prepare_result",
                        executed_at=run_at,
                        nose_image_id=record.nose_image_id,
                        noseprint_id=record.noseprint_id,
                        object_key=record.object_key,
                        output_image_path=result.output_image_path,
                        keypoint_count=result.keypoint_count,
                        status="skipped",
                        error_message="nose_image_quality already exists",
                        stack_trace="",
                    )
                    continue

            success_count += 1
            total_keypoint_count += result.keypoint_count
            print(
                f"nose_image_id={record.nose_image_id} noseprint_id={record.noseprint_id} "
                f"object_key={record.object_key} keypoint_count={result.keypoint_count} "
                f"status=success"
            )
            log_event(
                logger,
                event="batch_prepare_result",
                executed_at=run_at,
                nose_image_id=record.nose_image_id,
                noseprint_id=record.noseprint_id,
                object_key=record.object_key,
                output_image_path=result.output_image_path,
                keypoint_count=result.keypoint_count,
                status="success",
                error_message="",
                stack_trace="",
            )
    finally:
        if connection is not None:
            connection.close()

    log_event(
        logger,
        event="batch_prepare_summary",
        executed_at=run_at,
        batch_dry_run=config.batch_dry_run,
        total_record_count=len(records),
        success_count=success_count,
        failure_count=failure_count,
        skip_count=skip_count,
        inserted_count=inserted_count,
        total_keypoint_count=total_keypoint_count,
        status="completed",
        error_message="",
        stack_trace="",
    )
    print(f"SUCCESS_COUNT={success_count}")
    print(f"FAILURE_COUNT={failure_count}")
    print(f"SKIP_COUNT={skip_count}")
    print(f"INSERTED_COUNT={inserted_count}")
    print(f"TOTAL_KEYPOINT_COUNT={total_keypoint_count}")
    return 0


def _log_batch_issue(logger, **fields) -> None:
    log_event(logger, **fields)
