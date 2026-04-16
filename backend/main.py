from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import models  # noqa: F401 - ensure SQLAlchemy models are registered
from db.database import Base, engine
from routes import api
from utils.logger import logger

try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
except Exception as e:
    logger.error(f"Database initialization failed. Are you sure Postgres is running? {e}")

app = FastAPI(title="Recipe Extractor & Meal Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Recipe Extractor API running"}
