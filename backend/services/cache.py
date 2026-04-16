import hashlib
from sqlalchemy.orm import Session
from db.crud import get_recipe_by_url
from utils.logger import logger

def check_cache(db: Session, url: str):
    logger.info(f"Checking cache for {url}")
    return get_recipe_by_url(db, url)

def compute_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()
