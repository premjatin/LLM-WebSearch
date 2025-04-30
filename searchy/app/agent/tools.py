from langchain.tools import Tool
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from app.rag.retriever import retrieve_context # Import the RAG retriever

# === Web Search Tool (Keep as is or refine error handling) ===
def duckduckgo_search(query: str) -> list[str]:
    """Runs DuckDuckGo search and returns the top 3 links."""
    print(f"--- Running DuckDuckGo Search for: {query} ---")
    links = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5)
            links = [r['href'] for r in results if r.get('href')][:3]
    except Exception as e: print(f"DuckDuckGo search failed: {e}")
    print(f"--- Found Links: {links} ---"); return links

def fetch_web_content_from_links(links: list[str]) -> str:
    """Fetches and scrapes content from a list of URLs."""
    print(f"--- Fetching content for links: {links} ---"); texts = []
    for url in links:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}; r = requests.get(url, timeout=10, headers=headers); r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for script_or_style in soup(["script", "style"]): script_or_style.decompose()
            text = soup.get_text(separator=" ", strip=True); texts.append(text[:2500])
            print(f"--- Successfully scraped: {url} ---")
        except Exception as e: print(f"--- Failed to fetch/scrape {url}: {e} ---")
    if not texts: return "No readable content found from web links."; content = "\n\n---\n\n".join(texts)
    print(f"--- Web Search Combined Content Length: {len(content)} ---"); return content

def search_and_scrape(query: str) -> str:
    """
    Performs a DuckDuckGo search for the query, retrieves the top 3 links,
    and scrapes the content from those links. Returns the combined scraped text.
    Use this for current events or information not found in the internal knowledge base.
    """
    print("--- Executing Web Search Tool ---")
    links = duckduckgo_search(query)
    if not links: return "Web search did not return any usable links."
    return fetch_web_content_from_links(links)

web_search_tool = Tool(
    name="WebSearch", # Shorter name can be helpful
    func=search_and_scrape,
    description="Searches the web (DuckDuckGo) for a query, fetches content from top results. Use this for recent events, real-time information, or topics likely not covered in the internal knowledge base."
)

# === RAG Tool ===
def rag_search(query: str) -> str:
    """
    Searches the internal knowledge base (RAG) for information related to the query.
    Returns relevant text chunks found.
    """
    print(f"--- Executing RAG Tool with query: {query} ---")
    return retrieve_context(query, k=3) # Retrieve top 3 chunks

rag_tool = Tool(
    name="InternalKnowledgeSearch",
    func=rag_search,
    description="Searches the internal knowledge base for specific information, documents, or context provided to the system. Use this FIRST for queries about internal procedures, specific datasets, or documented knowledge before trying a general web search."
)


# List of tools available to the agent
agent_tools = [rag_tool, web_search_tool]