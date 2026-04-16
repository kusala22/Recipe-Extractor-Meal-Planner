from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Ingredient(BaseModel):
    quantity: str = Field(description="Quantity like '1', '1/2', '200'. If none, leave empty string.", default="")
    unit: str = Field(description="Unit like 'cup', 'tbsp', 'g', 'oz', or 'whole'", default="")
    item: str = Field(description="The ingredient name, e.g., 'diced tomatoes', 'chicken breast'")

class NutritionEstimate(BaseModel):
    calories: Optional[int] = Field(description="Estimated calories per serving", default=0)
    protein: Optional[str] = Field(description="Estimated protein in grams", default="0g")
    carbs: Optional[str] = Field(description="Estimated carbs in grams", default="0g")
    fat: Optional[str] = Field(description="Estimated fat in grams", default="0g")

class RecipeExtract(BaseModel):
    title: str = Field(description="The title of the recipe")
    cuisine: Optional[str] = Field(description="The cuisine type, e.g., Italian, Mexican", default="Unknown")
    prep_time: Optional[str] = Field(description="Preparation time", default="Unknown")
    cook_time: Optional[str] = Field(description="Cooking time", default="Unknown")
    total_time: Optional[str] = Field(description="Total time", default="Unknown")
    servings: Optional[str] = Field(description="Number of servings", default="Unknown")
    difficulty: str = Field(description="easy, medium, or hard", default="medium")
    ingredients: List[Ingredient] = Field(description="List of ingredients")
    instructions: List[str] = Field(description="List of instructions step by step")
    nutrition_estimate: NutritionEstimate = Field(description="Estimated nutrition per serving")
    substitutions: List[str] = Field(description="3 ingredient substitutions as string sentences", default_factory=list)
    shopping_list: Dict[str, List[str]] = Field(
        description="Shopping list grouped by keys like 'dairy', 'produce', 'pantry', etc.", default_factory=dict
    )
    related_recipes: List[str] = Field(description="3 titles of related recipes", default_factory=list)

class ExtractRequest(BaseModel):
    url: str
