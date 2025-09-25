# agents/product_search_agent.py
import os
import re
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel
from tools import tools  # <-- Import your scraping tools

load_dotenv()

# ----------------------------------------------
# Define Product Search Response Schema
# ----------------------------------------------
class ProductSearchResponse(BaseModel):
    outfit: str
    shopping_links: list[str]
    sources: list[str]

# ----------------------------------------------
# Initialize Gemini
# ----------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.4,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# ----------------------------------------------
# Parser
# ----------------------------------------------
parser = PydanticOutputParser(pydantic_object=ProductSearchResponse)

# ----------------------------------------------
# Prompt (FIXED: Added {agent_scratchpad})
# ----------------------------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a **Product Search Agent**.
            Given an outfit description, break it into individual clothing items
            and use the available tools (Temu, Amazon, eBay, Zara, H&M) to
            fetch real shopping links.

            - Ensure links are relevant and working product pages.
            - At least one link per clothing item.
            - Avoid irrelevant results (toys, electronics, non-fashion).
            - Output MUST follow this JSON schema:
            {format_instructions}

            Remember to include the agent scratchpad for reasoning:
            {agent_scratchpad}
            """,
        ),
        ("human", "{outfit_description}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# ----------------------------------------------
# Create Agent Executor with Tools
# ----------------------------------------------
def get_product_search_agent():
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# ----------------------------------------------
# Blueprint
# ----------------------------------------------
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

        # Parse clean JSON
        output = raw_response.get("output", "")
        clean_output = re.sub(r"```(?:json)?\n?|\n?```", "", output).strip()
        structured_response = parser.parse(clean_output)

        return jsonify(structured_response.model_dump()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500