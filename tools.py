from langchain.tools import tool
import os
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
from dotenv import load_dotenv
from security import validate_public_http_url

load_dotenv()
REQUEST_TIMEOUT_SECONDS = 12
MAX_SCRAPED_CHARACTERS = 12000


def _get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured. Add it to .env.")
    return TavilyClient(api_key=api_key)


@tool
def web_search(query: str) -> str:
    """Search the web and return titles, URLs and source snippets."""
    query = query.strip() if isinstance(query, str) else ""
    if not query:
        raise ValueError("Search query must not be empty.")
    results = _get_tavily_client().search(query=query, max_results=5).get("results", [])
    if not results:
        return "No search results were found."
    return "\n----\n".join(
        f"Title: {item.get('title', 'Untitled')}\nURL: {item.get('url', '')}\n"
        f"Snippet: {str(item.get('content', ''))[:500]}"
        for item in results
    )


@tool
def scrape_url(url: str) -> str:
    """Fetch a public HTTP(S) HTML/text page and return bounded readable text."""
    safe_url = validate_public_http_url(url)
    response = requests.get(
        safe_url, timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "QuorumResearchBot/1.0"}, allow_redirects=False,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError("Only HTML and plain-text pages can be scraped.")
    if len(response.content) > 2_000_000:
        raise ValueError("Page exceeds the 2 MB scraping limit.")
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)[:MAX_SCRAPED_CHARACTERS]
