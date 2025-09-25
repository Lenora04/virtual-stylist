from flask import Blueprint, request, jsonify, session
from extensions import db
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY)

user_pref_bp = Blueprint("user_pref_bp", __name__)

def adjust_outfit_with_preferences(outfit, preferences):
    reasons = []
    if preferences.get("favorite_colors"):
        for color in preferences["favorite_colors"]:
            if color.lower() in outfit.lower():
                reasons.append(f"Matched your favorite color: {color}")

    skin_color = preferences.get("skin_color", "").lower()
    if skin_color and "black" in skin_color and "white" in outfit.lower():
        reasons.append("White looks great with your skin tone")

    height = preferences.get("height", 0)
    if height and int(height) < 160 and "long dress" in outfit.lower():
        reasons.append("Long dresses may overwhelm petite height")

    return {"outfit": outfit, "reasons": reasons}

@user_pref_bp.route("/get_preferences", methods=["GET"])
def get_preferences():
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    uid = session["uid"]
    doc = db.collection("users").document(uid).get()
    return jsonify(doc.to_dict().get("preferences", {}) if doc.exists else {}), 200

@user_pref_bp.route("/save_preferences", methods=["POST"])
def save_preferences():
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    preferences = data.get("preferences", {})
    uid = session["uid"]
    try:
        db.collection("users").document(uid).set({"preferences": preferences}, merge=True)
        return jsonify({"message": "Preferences saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
