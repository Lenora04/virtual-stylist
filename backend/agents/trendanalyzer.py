# agents/trendanalyzer.py
import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import tools 

load_dotenv()

class TrendAnalysisResponse(BaseModel):
    trend_topic: str
    current_trends: list[str]
    insights: str
    sources: list[str]
    tools_used: list[str]

llm = ChatGoogleGenerativeAI(
    model="gemma-3-4b-it",
    temperature=0.2,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

parser = PydanticOutputParser(pydantic_object=TrendAnalysisResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a Trend Analyzer Agent...{format_instructions}"""),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

def get_trend_agent():
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def parse_trend_response(raw_response):
    output = raw_response.get("output", "")
    clean_output = re.sub(r"```(?:json)?\n?|\n?```", "", output).strip()
    structured_response = parser.parse(clean_output)

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
