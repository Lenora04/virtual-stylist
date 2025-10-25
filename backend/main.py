import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv

# Firebase
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Import agents
from agents.OutfitGenerator import generate_outfit_recommendation
from agents.trendanalyzer import get_trend_agent, parse_trend_response
from agents.product_search_agent import get_product_search_agent, parser as product_parser
from agents.user_preference_agent import adjust_outfit_with_preferences

# Load environment variables
load_dotenv()

# ----------------- Configuration and Initialization -----------------
# Define valid categories and their emojis
CLOSET_CATEGORIES = {
    'tops': '👚',
    'bottoms': '👖',
    'dresses': '👗',
    'outerwear': '🧥',
    'shoes': '👟',
    'accessories': '💎'
}
DEFAULT_EMOJI = '✨'


# ----------------- Firebase Initialization -----------------
cred_path = os.environ.get("FIREBASE_SERVICE_KEY_PATH")
if not cred_path or not os.path.exists(cred_path):
    raise FileNotFoundError(f"Firebase JSON not found. Set FIREBASE_SERVICE_KEY_PATH in .env (tried {cred_path})")

cred = credentials.Certificate(cred_path)

try:
    app_firebase = firebase_admin.initialize_app(cred)
except ValueError:
    app_firebase = firebase_admin.get_app()

db = firestore.client(app=app_firebase)

# ----------------- Flask Setup -----------------
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")

# ----------------- Utility Functions -----------------
def get_user_closet_data(uid):
    """Retrieves all categorized items from the user's closet document."""
    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    # Returns the full dict, where keys are categories and values are lists of items
    return doc.to_dict() if doc.exists else {}

def get_all_closet_items_flat(uid):
    """Retrieves all items from all categories as a single, flat list for the Outfit Generator."""
    closet_data = get_user_closet_data(uid)
    all_items = []
    for items_list in closet_data.values():
        if isinstance(items_list, list):
            all_items.extend(items_list)
    return all_items

# ----------------- ROUTES -----------------

@app.route("/")
def home():
    if "uid" in session:
        # No longer needs to fetch the full closet for index.html
        return render_template("index.html")
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
            # Initialize with empty categories if it doesn't exist
            if not user_ref.get().exists:
                initial_closet = {cat: [] for cat in CLOSET_CATEGORIES}
                user_ref.set(initial_closet)
            return jsonify({"message": "Authentication successful!"}), 200
        except Exception as e:
            print("Login error:", e)
            return jsonify({"message": "Login failed"}), 500
    return render_template("login.html")

@app.route("/closet/<category>")
def closet_category_page(category):
    if "uid" not in session:
        return redirect(url_for("login_page"))

    if category not in CLOSET_CATEGORIES:
        return redirect(url_for("home")) # Redirect to home if category is invalid

    uid = session["uid"]
    closet_data = get_user_closet_data(uid)
    
    # Get the list of items for the specific category
    category_items = closet_data.get(category, [])
    
    return render_template(
        "closet_category.html", 
        category=category, 
        emoji=CLOSET_CATEGORIES.get(category, DEFAULT_EMOJI),
        items=category_items
    )

@app.route("/add-item", methods=["POST"])
def add_item():
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    uid = session["uid"]
    item = request.form.get("itemInput", "").strip()
    category = request.form.get("category")
    
    if not item or not category or category not in CLOSET_CATEGORIES:
        return jsonify({"message": "Invalid item or category."}), 400
    
    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    closet_data = doc.to_dict() if doc.exists else {}

    # Get the list for the specific category or initialize it
    items = closet_data.get(category, [])
    if item not in items:
        items.append(item)
        user_ref.update({category: items})
        return jsonify({"message": "Item added", "item": item}), 200
    else:
        return jsonify({"message": "Item already in closet."}), 409


@app.route("/delete-item", methods=["POST"])
def delete_item():
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    uid = session["uid"]
    item = request.form.get("item")
    category = request.form.get("category")

    if not item or not category or category not in CLOSET_CATEGORIES:
        return jsonify({"message": "Invalid item or category"}), 400

    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    if not doc.exists:
        return jsonify({"message": "Closet not found"}), 404
        
    closet_data = doc.to_dict()
    items = closet_data.get(category, [])
    
    try:
        items.remove(item)
        user_ref.update({category: items})
        return jsonify({"message": "Item deleted", "item": item}), 200
    except ValueError:
        return jsonify({"message": "Item not found in this category"}), 404

@app.route("/generate-outfit", methods=["POST"])
def generate_outfit():
    if "uid" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    uid = session["uid"]
    # Now use the new function to get a flat list of all items
    user_closet = get_all_closet_items_flat(uid)

    # Get user preferences
    user_doc = db.collection("users").document(uid).get()
    preferences = user_doc.to_dict().get("preferences", {}) if user_doc.exists else {}

    # Read parameters from form
    occasion = request.form.get("occasion", "")
    style = request.form.get("style_preference", "")
    disliked_outfit = request.form.get("disliked_outfit", None)
    recommendation_type = request.form.get("recommendation_type", "closet")
    
    # Prioritize gender from saved preferences, then fallback to form, then default
    gender = preferences.get("gender", request.form.get("gender", "person"))

    # Step 1: Analyze trends
    try:
        trend_response = analyze_trends_internal(f"{occasion} {style} fashion trends")
        
        # --- NEW LOGIC: Check if the trend analyzer indicated a non-fashion query ---
        insights = trend_response.get("insights", "")
        if "not about fashion" in insights.lower() or "cannot fulfill this request" in insights.lower():
            # Return a clear message to the user and stop processing
            return jsonify({
                "recommendation_text": "I'm sorry, that query does not seem related to fashion or clothing. Please try searching for an occasion or a style!",
                "reasons": [],
                "trends_considered": [],
                "shopping_links": [],
                "sources": []
            }), 400
        # --- END NEW LOGIC ---

        trends = trend_response.get("current_trends", [])[:3]
    except Exception:
        trends = []

    # Step 2: Generate base outfit recommendation
    recommendation_text = generate_outfit_recommendation(
        user_closet, occasion, style, gender,
        disliked_outfit, recommendation_type, trends
    )
    
    # --- MODIFIED LOGIC: Check for specific error messages from the agent ---
    if "Your closet is empty" in recommendation_text and recommendation_type == "closet":
        return jsonify({"message": recommendation_text}), 400
    
    # If the recommendation starts with the fallback message, it's NOT an error, 
    # but a successful generation that needs a shopping link, so we continue.
    # The string "I couldn't find a complete outfit" means a general recommendation was provided.
    
    # Step 3: Adjust with user preferences
    # Preferences were already fetched
    # The 'recommendation_text' already contains the preference adjustment if 'preferences' was passed.
    
    # The structure of recommendation_text now needs to be parsed if preferences were included
    # to separate the outfit description from the preference reasoning.
    
    # For simplicity and to avoid overcomplicating parsing, we'll assume the final output 
    # from the agent is the full text, and we'll extract the core outfit description 
    # for the Product Search Agent.

    # Extract the core outfit text for the Product Search Agent
    # We look for the part before the preference-based reasoning, if it exists.
    core_outfit_description = recommendation_text.split("\n\n(This recommendation considers your saved preferences.)")[0].strip()

    # We need to manually construct the structure that the frontend expects from the final text
    # that already includes preference adjustments.
    
    # Simple split to extract reasons
    reasons = []
    if "Preference-based reasoning" in recommendation_text:
        reason_part = recommendation_text.split("Preference-based reasoning:\n")[-1]
        reasons = [line.strip() for line in reason_part.split('\n') if line.strip()]

    # Step 4: Product search agent
    agent_executor = get_product_search_agent()
    # Use the core outfit description for a better search result
    raw_response = agent_executor.invoke({"outfit_description": core_outfit_description}) 
    output = raw_response.get("output", "")

    structured_response = {}
    try:
        structured_response = product_parser.parse(output).dict()
    except Exception:
        structured_response = {"outfit": core_outfit_description, "shopping_links": [], "sources": []}

    # Return everything cleanly for frontend
    return jsonify({
        "recommendation_text": recommendation_text, # Full stylist text including warnings/preferences
        "reasons": reasons,
        "trends_considered": trends,
        "shopping_links": structured_response.get("shopping_links", []),
        "sources": structured_response.get("sources", [])
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
    if "uid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    uid = session["uid"]
    user_doc = db.collection("users").document(uid).get()
    preferences = user_doc.to_dict().get("preferences", {}) if user_doc.exists else {}
    return jsonify({"uid": uid, "preferences": preferences})

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

@app.route("/userprofile")
def userprofile_page():
    if "uid" not in session:
        return redirect(url_for("login_page"))
    return render_template("userprofile.html")
    
@app.route('/subscription')
def subscriptions_page():
    """Renders the subscription plans page."""
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    return render_template('subscription.html')

# ----------------- New Subscription Pages -----------------
@app.route('/premium-monthly')
def premium_monthly_page():
    """Renders the monthly premium subscription page."""
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    return render_template('premium-monthly.html')


@app.route('/premium-yearly')
def premium_yearly_page():
    """Renders the yearly premium subscription page."""
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    return render_template('premium-yearly.html')

# ----------------- Run App -----------------
if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=True)