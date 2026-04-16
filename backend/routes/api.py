from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from schemas.recipe_schema import ExtractRequest
from services.scraper import scrape_recipe_page
from services.llm import extract_recipe_with_llm
from services.cache import check_cache
from utils.validator import is_valid_url
from utils.logger import logger
from db.database import get_db
from db import crud

router = APIRouter()

@router.post("/extract")
def extract_recipe(request: ExtractRequest, db: Session = Depends(get_db)):
    url = request.url
    if not is_valid_url(url):
        logger.error(f"Invalid URL provided: {url}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL format")
        
    # Check cache
    try:
        cached = check_cache(db, url)
    except SQLAlchemyError as e:
        logger.error(f"Database unavailable during cache lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Check your Postgres credentials and container state.",
        )

    if cached:
        logger.info(f"Returning cached result for {url}")
        return {"source": "cache", "data": cached.extracted_data}
        
    # Scrape
    try:
        scrape_result = scrape_recipe_page(url)
    except ValueError as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to scrape URL: {e}")
        
    # LLM extraction
    try:
        extracted = extract_recipe_with_llm(scrape_result)
        # Convert pydantic to dict
        extracted_dict = extracted.model_dump()
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"LLM extraction failed: {e}")
        
    # Save to db
    try:
        crud.create_recipe(db, url=url, data=extracted_dict, raw_html=scrape_result["html"])
    except Exception as e:
        logger.error(f"Database save failed: {e}")
        
    return {"source": "live", "data": extracted_dict}

@router.get("/recipes")
def get_saved_recipes(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    try:
        recipes = crud.get_recipes(db, skip=skip, limit=limit)
    except SQLAlchemyError as e:
        logger.error(f"Failed to fetch recipes from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Check your Postgres credentials and container state.",
        )

    return [
        {
            "id": r.id, 
            "url": r.url, 
            "title": r.title, 
            "cuisine": r.cuisine, 
            "difficulty": r.difficulty, 
            "created_at": r.created_at
        } 
        for r in recipes
    ]

@router.get("/recipes/{recipe_id}")
def get_recipe_by_id(recipe_id: int, db: Session = Depends(get_db)):
    try:
        recipe = crud.get_recipe_by_id(db, recipe_id)
    except SQLAlchemyError as e:
        logger.error(f"Failed to fetch recipe {recipe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Check your Postgres credentials and container state.",
        )

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {
        "id": recipe.id,
        "url": recipe.url,
        "title": recipe.title,
        "data": recipe.extracted_data,
        "created_at": recipe.created_at
    }
