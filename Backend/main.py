# app.py
# Backend for the Virtual Stylist application
# Handles authentication, closet management, trend analysis, preferences, outfit generation, and product search.

import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Import agents
from agents.OutfitGenerator import generate_outfit_recommendation
from agents.trendanalyzer import get_trend_agent, parse_trend_response
from agents.product_search_agent import get_product_search_agent, parser as product_parser
from agents.user_preference_agent import adjust_outfit_with_preferences  # <-- your user_pref blueprint logic extracted

# Load environment variables
load_dotenv()

# Firebase Initialization
cred_path = os.environ.get(
    "FIREBASE_SERVICE_KEY_PATH",
    "C:/Users/USER/Desktop/stuff/IRWA/virtual-stylist/virtual-stylist-52782-firebase-adminsdk.json"
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


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    """Home page with closet items."""
    if "uid" in session:
        uid = session["uid"]
        user_ref = db.collection("closets").document(uid)
        doc = user_ref.get()
        user_closet = doc.to_dict().get("items", []) if doc.exists else []
        return render_template("index.html", closet=user_closet)
    return redirect(url_for("login_page"))


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        id_token = request.form.get("id_token")
        if not id_token:
            return jsonify({"message": "No ID token provided."}), 400
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            if not uid:
                return jsonify({"message": "Invalid ID token"}), 401

            session["uid"] = uid
            user_ref = db.collection("closets").document(uid)
            if not user_ref.get().exists:
                user_ref.set({"items": []})

            return jsonify({"message": "Authentication successful!"}), 200
        except Exception as e:
            print("Login error:", e)
            return jsonify({"message": "Login failed"}), 500
    return render_template("login.html")


@app.route("/add-item", methods=["POST"])
def add_item():
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    uid = session["uid"]
    item = request.form.get("itemInput", "").strip()
    if not item:
        return jsonify({"message": "Item cannot be empty."}), 400

    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    items = doc.to_dict().get("items", []) if doc.exists else []
    items.append(item)
    user_ref.set({"items": items})
    return jsonify({"message": "Item added", "item": item}), 200


@app.route("/delete-item", methods=["POST"])
def delete_item():
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    uid = session["uid"]
    item = request.form.get("item")
    if not item:
        return jsonify({"message": "Item not specified"}), 400

    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    if not doc.exists:
        return jsonify({"message": "Closet not found"}), 404

    items = doc.to_dict().get("items", [])
    try:
        items.remove(item)
        user_ref.set({"items": items})
        return jsonify({"message": "Item deleted", "item": item}), 200
    except ValueError:
        return jsonify({"message": "Item not found"}), 404


@app.route("/generate-outfit", methods=["POST"])
def generate_outfit():
    """Full pipeline: trends → preferences → outfit → product search."""
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    uid = session["uid"]
    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    user_closet = doc.to_dict().get("items", []) if doc.exists else []

    # Get form inputs
    occasion = request.form.get("occasion", "")
    style = request.form.get("style_preference", "")
    gender = request.form.get("gender", "person")
    disliked_outfit = request.form.get("disliked_outfit", None)
    recommendation_type = request.form.get("recommendation_type", "closet")

    # Step 1: Analyze trends
    try:
        trend_response = analyze_trends_internal(f"{occasion} {style} fashion trends")
        trends = trend_response.get("current_trends", [])[:3]
    except Exception:
        trends = []

    # Step 2: Outfit recommendation
    recommendation_text = generate_outfit_recommendation(
        user_closet, occasion, style, gender,
        disliked_outfit, recommendation_type, trends
    )
    if "Your closet is empty" in recommendation_text and recommendation_type == "closet":
        return jsonify({"message": recommendation_text}), 400

    # Step 3: Apply user preferences
    user_doc = db.collection("users").document(uid).get()
    preferences = user_doc.to_dict().get("preferences", {}) if user_doc.exists else {}
    adjusted = adjust_outfit_with_preferences(recommendation_text, preferences)

    # Step 4: Product search with tools
    agent_executor = get_product_search_agent()
    raw_response = agent_executor.invoke({"outfit_description": adjusted["outfit"]})
    output = raw_response.get("output", "")
    structured_response = {}
    try:
        structured_response = product_parser.parse(output)
        structured_response = structured_response.dict()
    except Exception:
        structured_response = {"outfit": adjusted["outfit"], "shopping_links": [], "sources": []}

    # Final return
    return jsonify({
        "recommendation": adjusted["outfit"],
        "reasons": adjusted["reasons"],
        "trends_considered": trends,
        "products": structured_response
    }), 200


@app.route("/analyze_trends", methods=["POST"])
def analyze_trends():
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        data = request.get_json()
        query = data.get("query", "current fashion trends")
        return jsonify(analyze_trends_internal(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def analyze_trends_internal(query):
    agent_executor = get_trend_agent()
    raw_response = agent_executor.invoke({"query": query})
    return parse_trend_response(raw_response).dict()


@app.route("/logout")
def logout():
    session.pop("uid", None)
    return redirect(url_for("login_page"))


@app.route("/firebase-config")
def firebase_config():
    return jsonify({
        "apiKey": os.environ.get("FIREBASE_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.environ.get("FIREBASE_APP_ID")
    })
@app.route("/user-profile", methods=["GET"])
def user_profile():
    """Return user profile and preferences."""
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    uid = session["uid"]
    user_doc = db.collection("users").document(uid).get()
    preferences = user_doc.to_dict().get("preferences", {}) if user_doc.exists else {}
    return jsonify({
        "uid": uid,
        "preferences": preferences
    })

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
    
    # Save to Firestore
    try:
        db.collection("users").document(uid).set({"preferences": prefs}, merge=True)
        return jsonify({"message": "Preferences saved successfully"}), 200
    except Exception as e:
        print("Error saving preferences:", e)
        return jsonify({"error": "Failed to save preferences"}), 500
    
@app.route("/userprofile")
def userprofile_page():
    """Render the user profile form (HTML)."""
    if "uid" not in session:
        return redirect(url_for("login_page"))
    return render_template("userprofile.html")


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=True)
