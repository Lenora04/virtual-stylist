import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from product_search import get_outfit_agent, parse_outfit_response
from tools import tools 

# Load environment variables
load_dotenv()
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Outfit Search Endpoint
@app.route("/search_outfit", methods=["POST"])
def search_outfit():
    try:
        data = request.get_json()
        outfit = data.get("outfit", "")
        api_key = data.get("api_key", "")

        # Authenticate agent
        if api_key != AGENT_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401

        if not outfit:
            return jsonify({"error": "Missing 'outfit' in request"}), 400

        # Initialize agent executor with StructuredTools
        agent_executor = get_outfit_agent()

        # LLM + StructuredTools handle query expansion and store search
        raw_response = agent_executor.invoke({"query": outfit})
        structured_response = parse_outfit_response(raw_response)

        return jsonify(structured_response.dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
