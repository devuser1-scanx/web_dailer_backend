from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from config import (
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_HOST,
    DB_PORT,
    INSTANCE_CONNECTION_NAME,
)


def build_database_url():
    if INSTANCE_CONNECTION_NAME:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            query={
                "host": f"/cloudsql/{INSTANCE_CONNECTION_NAME}"
            },
        )

    return URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )


engine = create_engine(
    build_database_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def test_db_connection():
    with SessionLocal() as db:
        result = db.execute(text("SELECT 1")).scalar()
        return result == 1