from sqlalchemy.orm import Session
from db.models import RecipeModel

def get_recipe_by_url(db: Session, url: str):
    return db.query(RecipeModel).filter(RecipeModel.url == url).first()

def get_recipes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RecipeModel).order_by(RecipeModel.created_at.desc()).offset(skip).limit(limit).all()

def get_recipe_by_id(db: Session, recipe_id: int):
    return db.query(RecipeModel).filter(RecipeModel.id == recipe_id).first()

def create_recipe(db: Session, url: str, data: dict, raw_html: str = None):
    db_recipe = RecipeModel(
        url=url,
        title=data.get("title", "Unknown"),
        cuisine=data.get("cuisine", "Unknown"),
        difficulty=data.get("difficulty", "medium"),
        extracted_data=data,
        raw_html=raw_html
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe
