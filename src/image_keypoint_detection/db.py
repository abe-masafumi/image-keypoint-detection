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
