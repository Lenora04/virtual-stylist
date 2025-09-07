import os
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import tools  # clothing store search tools

# ----------------------------------------------------
# Load API Key
# ----------------------------------------------------
load_dotenv()

# ----------------------------------------------------
# Define Outfit Search Response Schema
# ----------------------------------------------------
class OutfitSearchResponse(BaseModel):
    outfit_query: str
    normalized_description: str
    store_links: dict[str, str]
    recommended_items: list[str]
    tools_used: list[str]

# ----------------------------------------------------
# Initialize Gemini LLM
# ----------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# ----------------------------------------------------
# Pydantic Parser
# ----------------------------------------------------
parser = PydanticOutputParser(pydantic_object=OutfitSearchResponse)

# ----------------------------------------------------
# Prompt for Outfit Search
# ----------------------------------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an **Outfit Search Agent**.

            - Take a raw outfit description (e.g., "trendy black leather jacket with slim jeans").
            - Normalize it into a clear shopping query.
            - Use the tools to generate store-specific search links.
            - Recommend a few related fashion items (synonyms, variations).
            - Always output following the JSON schema:
            {format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# ----------------------------------------------------
# Create Agent Executor
# ----------------------------------------------------
def get_outfit_agent():
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# ----------------------------------------------------
# Helper Function to Parse Response
# ----------------------------------------------------
def parse_outfit_response(raw_response):
    output = raw_response.get("output", "")
    clean_output = re.sub(r"```(?:json)?\n?|\n?```", "", output).strip()
    return parser.parse(clean_output)

# ----------------------------------------------------
# Flask App
# ----------------------------------------------------
app = Flask(__name__)

@app.route("/search_outfit", methods=["POST"])
def search_outfit():
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"error": "Missing 'query' in request"}), 400

        agent_executor = get_outfit_agent()
        raw_response = agent_executor.invoke({"query": query})
        structured_response = parse_outfit_response(raw_response)

        return jsonify(structured_response.dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# Run Flask
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)  # runs on 5001 to avoid clash

