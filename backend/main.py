
import os
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# Firebase Initialization
cred_path = os.environ.get(
    "FIREBASE_SERVICE_KEY_PATH",
    "C:/Users/HP/Desktop/IRWA Project/virtual-stylist/virtual-stylist-52782-firebase-adminsdk-fbsvc-6881e2d02f.json"
)
cred = credentials.Certificate(cred_path)
try:
    app_firebase = firebase_admin.initialize_app(cred)
except ValueError:
    app_firebase = firebase_admin.get_app()

db = firestore.client(app=app_firebase)

# Flask config
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")



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


@app.route("/get_preferences", methods=["GET"])
def get_preferences():
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    uid = session["uid"]
    user_doc = db.collection("users").document(uid).get()
    preferences = user_doc.to_dict().get("preferences", {}) if user_doc.exists else {}
    return jsonify(preferences), 200


@app.route("/save_preferences", methods=["POST"])
def save_preferences():
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    uid = session["uid"]
    data = request.get_json()
    prefs = data.get("preferences", {})
    
    try:
        db.collection("users").document(uid).set({"preferences": prefs}, merge=True)
        return jsonify({"message": "Preferences saved successfully"}), 200
    except Exception as e:
        print("Error saving preferences:", e)
        return jsonify({"error": "Failed to save preferences"}), 500


if __name__ == "_main_":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=True)