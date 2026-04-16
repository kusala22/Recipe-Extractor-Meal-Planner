import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base

class RecipeModel(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, index=True)
    cuisine = Column(String)
    difficulty = Column(String)
    extracted_data = Column(JSONB, nullable=False)
    raw_html = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
