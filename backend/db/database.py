import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(ENV_PATH)

DEFAULT_LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5433/recipes_db"
DEFAULT_DOCKER_DB_URL = "postgresql://postgres:postgres@db:5432/recipes_db"


def get_database_url() -> str:
    """Return a SQLAlchemy database URL for local or Docker execution."""
    run_env = os.getenv("RUN_ENV", "local").lower()

    if run_env == "docker":
        return os.getenv("DOCKER_DATABASE_URL", DEFAULT_DOCKER_DB_URL)

    return os.getenv("DATABASE_URL", DEFAULT_LOCAL_DB_URL)


DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
