import requests
from bs4 import BeautifulSoup
import json
from utils.logger import logger

FALLBACK_PROXY_PREFIX = "https://r.jina.ai/http://"


def _extract_recipe_payload_from_html(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    # Look for schema.org/Recipe JSON-LD
    json_ld_data = None
    structured_scripts = soup.find_all('script', type='application/ld+json')
    for script in structured_scripts:
        if script.string:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Recipe' or 'Recipe' in data.get('@type', []):
                        json_ld_data = data
                        break
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and (item.get('@type') == 'Recipe' or 'Recipe' in item.get('@type', [])):
                            json_ld_data = item
                            break
            except json.JSONDecodeError:
                continue

    # Remove noise
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'iframe']):
        element.decompose()

    # Prefer <main> or <article>, else fallback to body
    main_content = soup.find('article') or soup.find('main') or soup.body
    text_content = ""
    if main_content:
        text_content = main_content.get_text(separator='\n', strip=True)

    # Trim to avoid massive token overflow, but keep it large enough
    MAX_CHARS = 50000
    if len(text_content) > MAX_CHARS:
        text_content = text_content[:MAX_CHARS]
        logger.warning(f"Trimmed content for {source_url} to {MAX_CHARS} characters.")

    return {
        "text": text_content,
        "html": html,
        "json_ld": json_ld_data
    }


def _fetch_with_fallback_proxy(url: str, timeout: int = 20) -> dict:
    proxy_url = f"{FALLBACK_PROXY_PREFIX}{url}"
    logger.info(f"Trying fallback proxy fetch for {url}")
    response = requests.get(proxy_url, timeout=timeout)
    response.raise_for_status()

    markdown = response.text
    if "Title: Page Not Found" in markdown:
        raise ValueError("The recipe page could not be found. Double-check the URL and remove any extra path fragments.")

    return {
        "text": markdown[:50000],
        "html": markdown,
        "json_ld": None,
    }


def scrape_recipe_page(url: str) -> dict:
    logger.info(f"Scraping URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code in (401, 402, 403):
            logger.warning(f"Primary fetch blocked for {url} with status {response.status_code}")
            return _fetch_with_fallback_proxy(url)

        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Primary fetch failed for {url}: {e}")
        try:
            return _fetch_with_fallback_proxy(url)
        except requests.RequestException as proxy_error:
            logger.error(f"Fallback fetch failed for {url}: {proxy_error}")
            raise ValueError(f"Failed to fetch content from URL: {str(proxy_error)}")

    return _extract_recipe_payload_from_html(response.text, url)
