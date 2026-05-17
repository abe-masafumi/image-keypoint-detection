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
            SELECT
                ni.id AS nose_image_id,
                ni.noseprint_id,
                ni.object_key,
                1 AS latest_image_count
            FROM {}.{} ni
            LEFT JOIN {}.{} niq
                ON ni.id = niq.nose_image_id
            WHERE niq.nose_image_id IS NULL
            ORDER BY ni.id ASC
            """
        ).format(
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_source_table),
            sql.Identifier(config.db_schema),
            sql.Identifier(config.db_update_table),
        )
    else:
        query = sql.SQL(
            """
            SELECT
                ni.id AS nose_image_id,
                ni.noseprint_id,
                ni.object_key,
                1 AS latest_image_count
            FROM {}.{} ni
            LEFT JOIN {}.{} niq
                ON ni.id = niq.nose_image_id
            WHERE niq.nose_image_id IS NULL
            ORDER BY ni.id ASC
            LIMIT %s
            """
        ).format(
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
    nose_image_id: int,
    keypoints_orb: int,
    app_version: str | None,
) -> bool:
    query = sql.SQL(
        """
        INSERT INTO {}.{} (nose_image_id, keypoints_orb, app_version)
        VALUES (%s, %s, %s)
        ON CONFLICT (nose_image_id) DO NOTHING
        """
    ).format(
        sql.Identifier(config.db_schema),
        sql.Identifier(config.db_update_table),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                nose_image_id,
                keypoints_orb,
                app_version,
            ),
        )
        return cursor.rowcount == 1
