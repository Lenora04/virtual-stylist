from langchain.tools import Tool
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# ---------------------------
# Trend Search Tools
# ---------------------------
FASHION_KEYWORDS = ["fashion", "style", "outfit", "ootd", "clothing", "look"]

def filter_results(results):
    return [
        r["body"] + " -> " + r["href"]
        for r in results
        if any(word in r["body"].lower() for word in FASHION_KEYWORDS)
    ]

def instagram_fashion_hashtags(query: str):
    with DDGS() as ddgs:
        results = list(ddgs.text(f"Instagram #{query} fashion", max_results=10))
    return filter_results(results)

instagram_tool = Tool(
    name="instagram_fashion_search",
    func=instagram_fashion_hashtags,
    description="Search Instagram fashion hashtags."
)

def tiktok_fashion_hashtags(query: str):
    with DDGS() as ddgs:
        results = list(ddgs.text(f"TikTok #{query} fashion trend", max_results=10))
    return filter_results(results)

tiktok_tool = Tool(
    name="tiktok_fashion_search",
    func=tiktok_fashion_hashtags,
    description="Search TikTok fashion hashtags."
)

def fashion_blogs_search(query: str):
    urls = [
        "https://www.vogue.com/fashion",
        "https://www.elle.com/fashion/",
        "https://www.harpersbazaar.com/fashion/",
        "https://www.un-fancy.com/",
        "https://fashionjackson.com/"
    ]
    articles = []
    for url in urls:
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")
            for link in soup.find_all("a", href=True)[:10]:
                text = link.get_text(strip=True)
                href = link["href"]
                if text and any(word in text.lower() for word in FASHION_KEYWORDS):
                    if href.startswith("/"):
                        href = url.rstrip("/") + href
                    articles.append(f"{text} -> {href}")
        except Exception as e:
            articles.append(f"Error fetching {url}: {str(e)}")
    return articles

blogs_tool = Tool(
    name="fashion_blogs_search",
    func=fashion_blogs_search,
    description="Search fashion blogs for latest articles."
)

# ---------------------------
# Shopping Site Search Tools
# ---------------------------
SHOPPING_SITES = ["https://www.temu.com/", "https://www.nolimit.lk/","https://mimosaforever.com/?srsltid=AfmBOop751_lo0po6pcgC0HFTbYfoCGixhzLfnh_WP7-eFE7ey1tGeVl","amazon.com"]
PRODUCT_KEYWORDS = ["shirt", "top", "dress", "jeans", "trousers", "jacket", "coat", "skirt", "sweater"]

def shopping_site_search(query: str):
    results_all = []
    with DDGS() as ddgs:
        for site in SHOPPING_SITES:
            search_query = f"site:{site} {query}"
            results = list(ddgs.text(search_query, max_results=5))
            # filter for fashion keywords
            for r in results:
                text = r.get("body", "")
                href = r.get("href", "")
                if any(word in text.lower() for word in PRODUCT_KEYWORDS):
                    results_all.append(f"{text} -> {href}")
    return results_all

shopping_tool = Tool(
    name="shopping_site_search",
    func=shopping_site_search,
    description="Search multiple shopping websites for clothing products."
)

# ---------------------------
# Export all tools
# ---------------------------
tools = [
    instagram_tool,
    tiktok_tool,
    blogs_tool,
    shopping_tool
]
