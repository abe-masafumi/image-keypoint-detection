from __future__ import annotations

from dataclasses import dataclass

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PgConnection

from image_keypoint_detection.config import AppConfig


@dataclass(frozen=True)
class NoseImageRecord:
    id: int
    object_key: str


@dataclass(frozen=True)
class BatchTargetRecord:
    nose_image_id: int | None
    noseprint_id: int
    object_key: str | None
    latest_image_count: int


def connect_postgres(config: AppConfig) -> PgConnection:
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_latest_nose_images(
    config: AppConfig,
    *,
    limit: int | None,
) -> list[NoseImageRecord]:
    if limit is None:
        query = sql.SQL(
            """
            SELECT id, object_key
            FROM {}.{}
            ORDER BY id DESC
            """
        ).format(
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
        )
    else:
        query = sql.SQL(
            """
            SELECT id, object_key
            FROM {}.{}
            ORDER BY id DESC
            LIMIT %s
            """
        ).format(
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
        )

    with connect_postgres(config) as connection:
        with connection.cursor() as cursor:
            if limit is None:
                cursor.execute(query)
            else:
                cursor.execute(query, (limit,))
            rows = cursor.fetchall()

    return [
        NoseImageRecord(id=row[0], object_key=row[1])
        for row in rows
    ]


def fetch_nose_images_for_batch(
    config: AppConfig,
    *,
    limit: int | None,
) -> list[BatchTargetRecord]:
    if limit is None:
        query = sql.SQL(
            """
            WITH latest_image_stats AS (
                SELECT
                    noseprint_id,
                    COUNT(*) FILTER (WHERE is_latest = TRUE) AS latest_image_count,
                    MIN(id) FILTER (WHERE is_latest = TRUE) AS latest_image_id
                FROM {}.{}
                GROUP BY noseprint_id
            )
            SELECT
                lis.latest_image_id AS nose_image_id,
                nr.noseprint_id,
                ni.object_key,
                COALESCE(lis.latest_image_count, 0) AS latest_image_count
            FROM {}.{} nr
            LEFT JOIN latest_image_stats lis
              ON nr.noseprint_id = lis.noseprint_id
            LEFT JOIN {}.{} ni
              ON ni.id = lis.latest_image_id
            LEFT JOIN {}.{} niq
              ON nr.noseprint_id = niq.noseprint_id
            WHERE niq.noseprint_id IS NULL
            ORDER BY
              COALESCE(lis.latest_image_id, 2147483647) ASC,
              nr.noseprint_id ASC
            """
        ).format(
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_registration_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_update_table),
        )
    else:
        query = sql.SQL(
            """
            WITH latest_image_stats AS (
                SELECT
                    noseprint_id,
                    COUNT(*) FILTER (WHERE is_latest = TRUE) AS latest_image_count,
                    MIN(id) FILTER (WHERE is_latest = TRUE) AS latest_image_id
                FROM {}.{}
                GROUP BY noseprint_id
            )
            SELECT
                lis.latest_image_id AS nose_image_id,
                nr.noseprint_id,
                ni.object_key,
                COALESCE(lis.latest_image_count, 0) AS latest_image_count
            FROM {}.{} nr
            LEFT JOIN latest_image_stats lis
              ON nr.noseprint_id = lis.noseprint_id
            LEFT JOIN {}.{} ni
              ON ni.id = lis.latest_image_id
            LEFT JOIN {}.{} niq
              ON nr.noseprint_id = niq.noseprint_id
            WHERE niq.noseprint_id IS NULL
            ORDER BY
              COALESCE(lis.latest_image_id, 2147483647) ASC,
              nr.noseprint_id ASC
            LIMIT %s
            """
        ).format(
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_registration_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_update_table),
        )

    with connect_postgres(config) as connection:
        with connection.cursor() as cursor:
            if limit is None:
                cursor.execute(query)
            else:
                cursor.execute(query, (limit,))
            rows = cursor.fetchall()

    return [
        BatchTargetRecord(
            nose_image_id=row[0],
            noseprint_id=row[1],
            object_key=row[2],
            latest_image_count=row[3],
        )
        for row in rows
    ]


def insert_nose_image_quality(
    connection: PgConnection,
    config: AppConfig,
    *,
    noseprint_id: int,
    keypoints_orb: int,
    app_version: str | None,
) -> bool:
    query = sql.SQL(
        """
        INSERT INTO {}.{} (noseprint_id, keypoints_orb, app_version)
        VALUES (%s, %s, %s)
        ON CONFLICT (noseprint_id) DO NOTHING
        """
    ).format(
        sql.Identifier(config.db_schema),
        sql.Identifier(config.db_update_table),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                noseprint_id,
                keypoints_orb,
                app_version,
            ),
        )
        return cursor.rowcount == 1
