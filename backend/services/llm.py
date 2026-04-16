import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from schemas.recipe_schema import RecipeExtract
from utils.logger import logger

load_dotenv()


def _get_candidate_models() -> list[str]:
    primary_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    fallback_models = os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-lite")

    models = [primary_model]
    models.extend(model.strip() for model in fallback_models.split(",") if model.strip())
    return models

def extract_recipe_with_llm(scrape_result: dict, prompt_path: str = "../prompts/recipe_extraction_prompt.txt") -> RecipeExtract:
    logger.info("Initializing LLM extraction")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("Valid GEMINI_API_KEY not found in environment.")
    
    # Load prompt
    try:
        # Resolve to absolute path or just assume it's run from backend/
        path_to_use = prompt_path if os.path.exists(prompt_path) else os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "recipe_extraction_prompt.txt")
        with open(path_to_use, "r", encoding="utf-8") as f:
            prompt_template_str = f.read()
    except FileNotFoundError:
        logger.warning(f"Prompt file not found, using default inline prompt.")
        prompt_template_str = """
        You are a strict, expert culinary data extractor.
        Extract the recipe details from the following web page content.
        DO NOT invent data. Use only the provided content.
        Return strictly in the requested JSON scheme.
        If ingredients are missing quantities, infer appropriately or leave empty.
        
        Content:
        {content}
        """
        
    prompt = PromptTemplate.from_template(prompt_template_str)
    
    # Prioritize schema.org JSON-LD if available, else raw text
    content_to_process = json.dumps(scrape_result["json_ld"]) if scrape_result.get("json_ld") else scrape_result["text"]
    
    last_error = None

    for model_name in _get_candidate_models():
        try:
            logger.info(f"Invoking LangChain Structured Output with model {model_name}")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.1,
                max_retries=2,
            )
            structured_llm = llm.with_structured_output(RecipeExtract)
            chain = prompt | structured_llm
            return chain.invoke({"content": content_to_process})
        except ChatGoogleGenerativeAIError as e:
            last_error = e
            logger.warning(f"Gemini model {model_name} failed: {e}")
        except Exception as e:
            last_error = e
            logger.warning(f"Unexpected LLM failure with model {model_name}: {e}")

    raise last_error if last_error else RuntimeError("LLM extraction failed without a specific error.")
