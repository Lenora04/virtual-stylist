# agents/product_search_agent.py
import os
import re
import requests  # Added to validate URLs
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel
from tools import tools, SHOPPING_SITES 

load_dotenv()

# ------------------------------------------------
# Helper to validate real, reachable product links 
# ------------------------------------------------
def validate_links(links):
    valid_links = []
    for url in links:
        try:
            if not any(site in url for site in SHOPPING_SITES):
                continue  # Skip unknown sites
            res = requests.head(url, allow_redirects=True, timeout=5)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                valid_links.append(url)
        except Exception:
            continue
    return valid_links


# Define Product Search Response Schema
# --- CHANGE START ---
class ProductSearchResponse(BaseModel):
    # This field will now hold the complete, descriptive text of the recommended outfit
    full_outfit_description: str
    shopping_links: list[str]
# --- CHANGE END ---


# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.4,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Parser
parser = PydanticOutputParser(pydantic_object=ProductSearchResponse)

# Dynamic site list for prompt
site_list = "\n".join([f"- {site}" for site in SHOPPING_SITES])

# ----------------------------------------------
# Prompt (UPDATED: explicitly force tool use)
# ----------------------------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
            You are a Product Search Agent.

            Given an outfit description, first, re-state the full, complete outfit recommendation text exactly as provided.
            Second, use ONLY the provided shopping tool to find real, valid product links from these supported shopping sites:

            {site_list}

            - Do NOT invent or guess product URLs.
            - If exact product links are not available, return a working search link such as https://www.amazon.com/s?k=<item+name>.
            - If no matching products are found, omit the link entirely.
            - At least one link per clothing item if available.
            - Links must be full product pages, not category or ad links.
            - Output MUST follow this JSON schema, ensuring the '{ProductSearchResponse.model_fields['full_outfit_description'].alias or 'full_outfit_description'}' field contains the complete descriptive outfit text:
            
            {{format_instructions}}

            {{agent_scratchpad}}
            """,
        ),
        ("human", "{outfit_description}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# Create Agent Executor with Tools
def get_product_search_agent():
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


# Blueprint
product_search_bp = Blueprint("product_search_bp", __name__)

@product_search_bp.route("/search_products", methods=["POST"])
def search_products():
    try:
        data = request.get_json()
        outfit_description = data.get("outfit", "")

        if not outfit_description:
            return jsonify({"error": "Missing 'outfit' in request"}), 400

        # Run agent with tools
        agent_executor = get_product_search_agent()
        raw_response = agent_executor.invoke({"outfit_description": outfit_description})

        # Parse and clean
        output = raw_response.get("output", "")
        clean_output = re.sub(r"```(?:json)?\n?|\n?```", "", output).strip()
        structured_response = parser.parse(clean_output)

        #Validate and filter links
        structured_response.shopping_links = validate_links(structured_response.shopping_links)
        # Note: structured_response.sources is not in the Pydantic model, removed unnecessary line.

        # --- CHANGE START ---
        # Using model_dump() which is the correct Pydantic V2 method
        # The frontend will now receive a JSON with a field named 'full_outfit_description'
        return jsonify(structured_response.model_dump()), 200
        # --- CHANGE END ---

    except Exception as e:
        return jsonify({"error": str(e)}), 500