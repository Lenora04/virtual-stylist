from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS   

# ----------------------------------------------------
# Helper function to format results
# ----------------------------------------------------
def format_results(results):
    """Return all results as 'text -> url' without filtering"""
    return [r["body"] + " -> " + r["href"] for r in results]

# ----------------------------------------------------
# Input Schema for Tools
# ----------------------------------------------------
class SearchInput(BaseModel):
    query: str = Field(..., description="Search query for outfits or clothing.")

# ----------------------------------------------------
# Amazon Search
# ----------------------------------------------------
def amazon_search(query: str):
    with DDGS() as ddgs:
        results = list(ddgs.text(f"site:amazon.com {query}", max_results=10))
    return format_results(results)

amazon_tool = StructuredTool.from_function(
    func=amazon_search,
    name="amazon_outfit_search",
    description="Search Amazon for outfits and clothing products to buy.",
    args_schema=SearchInput,
)

# ----------------------------------------------------
# Zara Search
# ----------------------------------------------------
def zara_search(query: str):
    url = f"https://www.zara.com/ww/en/search?searchTerm={query}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        products = []
        for item in soup.find_all("a", href=True)[:10]:
            text = item.get_text(strip=True)
            href = item["href"]
            if text:
                if href.startswith("/"):
                    href = "https://www.zara.com" + href
                products.append(f"{text} -> {href}")
        return products
    except Exception as e:
        return [f"Error fetching Zara: {str(e)}"]

zara_tool = StructuredTool.from_function(
    func=zara_search,
    name="zara_outfit_search",
    description="Search Zara for outfits, dresses, and trending clothing.",
    args_schema=SearchInput,
)

# ----------------------------------------------------
# H&M Search
# ----------------------------------------------------
def hm_search(query: str):
    url = f"https://www2.hm.com/en_us/search-results.html?q={query}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        products = []
        for item in soup.find_all("a", href=True)[:10]:
            text = item.get_text(strip=True)
            href = item["href"]
            if text:
                if href.startswith("/"):
                    href = "https://www2.hm.com" + href
                products.append(f"{text} -> {href}")
        return products
    except Exception as e:
        return [f"Error fetching H&M: {str(e)}"]

hm_tool = StructuredTool.from_function(
    func=hm_search,
    name="hm_outfit_search",
    description="Search H&M for clothing and outfits to purchase.",
    args_schema=SearchInput,
)

# ----------------------------------------------------
# Export Tools
# ----------------------------------------------------
tools = [amazon_tool, zara_tool, hm_tool]
