import os
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import tools  

# ----------------------------------------------------
# Load API Key
# ----------------------------------------------------
load_dotenv()

# ----------------------------------------------------
# Define Trend Analysis Response Schema
# ----------------------------------------------------
class TrendAnalysisResponse(BaseModel):
    trend_topic: str
    current_trends: list[str]
    insights: str
    sources: list[str]
    tools_used: list[str]

# ----------------------------------------------------
# Initialize Gemini LLM
# ----------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# ----------------------------------------------------
# Pydantic Parser
# ----------------------------------------------------
parser = PydanticOutputParser(pydantic_object=TrendAnalysisResponse)

# ----------------------------------------------------
# Prompt for Trend Analysis
# ----------------------------------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a **Trend Analyzer Agent** specializing in fashion.
            Use the tools to gather data from Instagram, TikTok, Facebook, and fashion blogs.

            - Only include results directly related to fashion, style, outfits, OOTD, or clothing trends.
            - Discard unrelated results (celebrity gossip, tech, news not about clothing).
            - Extract hashtags, rising fashion topics, articles, challenges.
            - Always summarize and give insights.
            - Output must follow this JSON schema:
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
def get_trend_agent():
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# ----------------------------------------------------
# Helper Function to Parse Response
# ----------------------------------------------------
def parse_trend_response(raw_response):
    output = raw_response.get("output", "")
    clean_output = re.sub(r"```(?:json)?\n?|\n?```", "", output).strip()
    structured_response = parser.parse(clean_output)

    # Filter only fashion-related trends & sources
    FASHION_KEYWORDS = ["fashion", "style", "outfit", "ootd", "wear", "clothing", "look"]
    structured_response.current_trends = [
        t for t in structured_response.current_trends
        if any(word in t.lower() for word in FASHION_KEYWORDS)
    ]
    structured_response.sources = [
        s for s in structured_response.sources
        if any(word in s.lower() for word in FASHION_KEYWORDS)
    ]

    return structured_response

# ----------------------------------------------------
# Flask App
# ----------------------------------------------------
app = Flask(__name__)

@app.route("/analyze_trends", methods=["POST"])
def analyze_trends():
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"error": "Missing 'query' in request"}), 400

        agent_executor = get_trend_agent()
        raw_response = agent_executor.invoke({"query": query})
        structured_response = parse_trend_response(raw_response)

        return jsonify(structured_response.dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# Run Flask
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
