from urllib.parse import quote_plus

from decouple import config as decouple_config
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool


class DBConnection:
    def __init__(self, pool_size=5, max_overflow=10):
        db_host = decouple_config("DB_HOST")
        db_user = decouple_config("DB_USER")
        db_pass = quote_plus(decouple_config("DB_PASS"))
        db_name = decouple_config("DB_NAME")
        db_port = decouple_config("DB_PORT")
        self.db_engine = create_engine(
            f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}',
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )

    def execute(self, query, params=None):
        with Session(self.db_engine) as session:
            result = session.execute(text(query), params)
            session.commit()
            return result

    def fetch_all_data(self, query, params=None):
        result = self.execute(query, params)
        return result.fetchall()
