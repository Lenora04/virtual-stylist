from flask import Blueprint, request, jsonify, session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

user_pref_bp = Blueprint("user_pref_bp", __name__)


def adjust_outfit_with_preferences(outfit, preferences, context=None):
    print(" [DEBUG] User Preference Agent Invoked")
    print(" Preferences received:", preferences)
    print(" Initial outfit suggestion:", outfit)

    reasons = []
    context = context or {"type": "general", "closet": []}
    recommendation_type = context["type"]

    # --- Rule-based feedback ---
    skin_color = preferences.get("skin_color", "").lower()
    if skin_color and any(c in outfit.lower() for c in ["white", "bright", "coral"]) and ("tan" in skin_color or "dark" in skin_color or "olive" in skin_color):
        reasons.append("White or bright/vibrant colors complement your skin tone beautifully.")

    try:
        height = int(preferences.get("height", 0))
        if height and height < 160 and "long dress" in outfit.lower():
            reasons.append("Long dresses may be overwhelming for a petite height. Consider a slightly shorter hemline or tailoring.")
    except (ValueError, TypeError):
        pass

    try:
        weight = int(preferences.get("weight", 0))
        if weight and weight > 90 and "tight crop top" in outfit.lower():
            reasons.append("Suggesting a more flowy top for comfort and a flattering fit.")
    except (ValueError, TypeError):
        pass

    # --- CLOSET mode: strictly no adjustment ---
    if recommendation_type == 'closet':
        additional_notes = preferences.get("additional_notes", "")
        if additional_notes:
            reasons.append(f"Notes received but not used: '{additional_notes}'. Closet items are strictly enforced.")
        return {"outfit": outfit, "reasons": reasons}

    # --- LLM adjustment for general recommendations ---
    additional_notes = preferences.get("additional_notes", "")
    if additional_notes:
        closet_items = context.get("closet", [])
        adjustment_constraint = (
            "You can suggest different items, but the new outfit must be a complete combination (top+bottom or dress/jumpsuit)."
        )

        prompt = f"""
        You are a virtual stylist. I have an outfit suggestion and a user's free-text preferences.
        Analyze the Proposed Outfit against the User Notes.
        
        User Notes: "{additional_notes}"
        Proposed Outfit: "{outfit}"
        
        Respond ONLY with:
        1. MATCH|Reason if outfit is fine.
        2. ADJUST|New complete outfit. {adjustment_constraint}
        """
        try:
            response = llm.invoke([HumanMessage(content=prompt)]).content.strip()
            if response.startswith("MATCH|"):
                llm_reason = response.split("|", 1)[1].strip()
                reasons.append(f"Style Notes Check: {llm_reason}")
            elif response.startswith("ADJUST|"):
                new_outfit = response.split("|", 1)[1].strip()
                reasons.append("Style Notes Check: Adjusted the outfit to better fit your notes.")
                outfit = new_outfit
        except Exception:
            reasons.append("Error processing style notes with LLM.")

    return {"outfit": outfit, "reasons": reasons}


# --- Route Handlers ---
@user_pref_bp.route("/get_preferences", methods=["GET"])
def get_preferences():
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({}), 200


@user_pref_bp.route("/save_preferences", methods=["POST"])
def save_preferences():
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    preferences = data.get("preferences", {})
    uid = session["uid"]
    try:
        print(f"Saving preferences for user {uid}: {preferences}")
        return jsonify({"message": "Preferences saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500