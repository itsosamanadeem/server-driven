from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_USER : str = os.getenv("POSTGRES_USER")  # type: ignore[assignment]
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")  # type: ignore[assignment]
POSTGRES_SERVER : str = os.getenv("POSTGRES_SERVER","localhost")  # type: ignore[assignment]
POSTGRES_PORT : str = os.getenv("POSTGRES_PORT",5433)  # type: ignore[assignment]
POSTGRES_DB : str = os.getenv("POSTGRES_DB","tdd")  # type: ignore[assignment]
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
