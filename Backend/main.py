from flask import Flask, request, jsonify
from agents.trendanalyzer import get_trend_agent, parse_trend_response
from agents.product_search_agent import search_product_links
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

        return jsonify(structured_response.model_dump())  # Pydantic dict
    except Exception as e:
        return jsonify({
            "error": str(e),
            "raw_response": str(raw_response) if 'raw_response' in locals() else None
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# ----------------------------------------------------
# Run Flask
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
