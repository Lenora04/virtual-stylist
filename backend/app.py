# app.py
# Backend for Virtual Stylist using Flask, Firebase, and outfit generation agents

import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials, auth

# Import the outfit generator functions
from agents.OutfitGenerator import generate_outfit_recommendation
from agents.trendanalyzer import get_trend_agent, parse_trend_response

# Load environment variables from the .env file
load_dotenv()

# Path to your service account key file
cred_path = os.environ.get(
    'FIREBASE_SERVICE_KEY_PATH',
    'C:/Users/USER/Desktop/stuff/IRWA/virtual-stylist/virtual-stylist-52782-firebase-adminsdk-fbsvc-6881e2d02f.json'
)
cred = credentials.Certificate(cred_path)

# Initialize Firebase Admin SDK
try:
    app_firebase = firebase_admin.initialize_app(cred)
except ValueError as e:
    print(f"Firebase app already initialized. Skipping... Error: {e}")
    app_firebase = firebase_admin.get_app()

db = firestore.client(app=app_firebase)

# --- Flask App Configuration ---
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')


# --- Routes ---

@app.route('/')
def home():
    """Main page if user is logged in, else redirect to login"""
    if 'uid' in session:
        uid = session['uid']
        user_ref = db.collection("closets").document(uid)
        doc = user_ref.get()

        user_closet = []
        if doc.exists:
            user_closet = doc.to_dict().get("items", [])

        return render_template('index.html', closet=user_closet)
    return redirect(url_for('login_page'))


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        id_token = request.form.get('id_token')

        if not id_token:
            return jsonify({'message': 'No ID token provided.'}), 400

        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get('uid')
            if not uid:
                return jsonify({'message': 'Invalid ID token: UID missing.'}), 401

            session['uid'] = uid

            user_ref = db.collection("closets").document(uid)
            if not user_ref.get().exists:
                user_ref.set({"items": []})

            return jsonify({'message': 'Authentication successful!'}), 200

        except firebase_admin.auth.InvalidIdTokenError:
            return jsonify({'message': 'Invalid ID token.'}), 401
        except firebase_admin.auth.ExpiredIdTokenError:
            return jsonify({'message': 'ID token has expired.'}), 401
        except firebase_admin.auth.RevokedIdTokenError:
            return jsonify({'message': 'ID token has been revoked.'}), 401
        except Exception as e:
            print("Login error:", e)
            return jsonify({'message': 'An unexpected server error occurred.'}), 500

    return render_template('login.html')


@app.route('/add-item', methods=['POST'])
def add_item():
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    uid = session['uid']
    item = request.form.get('itemInput')

    if item and item.strip():
        user_ref = db.collection("closets").document(uid)
        doc = user_ref.get()

        items = doc.to_dict().get("items", []) if doc.exists else []
        items.append(item.strip())
        user_ref.set({"items": items})

        return jsonify({'message': 'Item added successfully', 'item': item.strip()}), 200

    return jsonify({'message': 'Failed to add item. The item field cannot be empty.'}), 400


@app.route('/delete-item', methods=['POST'])
def delete_item():
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    uid = session['uid']
    item_to_delete = request.form.get('item')

    if not item_to_delete:
        return jsonify({'message': 'Item to delete not specified.'}), 400

    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()

    if doc.exists:
        items = doc.to_dict().get("items", [])
        try:
            items.remove(item_to_delete)
            user_ref.set({"items": items})
            return jsonify({'message': 'Item deleted successfully', 'item': item_to_delete}), 200
        except ValueError:
            return jsonify({'message': 'Item not found in closet.'}), 404
    else:
        return jsonify({'message': 'User closet not found.'}), 404


@app.route('/generate-outfit', methods=['POST'])
def generate_outfit():
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    uid = session['uid']
    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()
    user_closet = doc.to_dict().get("items", []) if doc.exists else []

    occasion = request.form.get('occasion', '')
    style = request.form.get('style_preference', '')
    gender = request.form.get('gender', 'person')
    disliked_outfit = request.form.get('disliked_outfit', None)
    recommendation_type = request.form.get('recommendation_type', 'closet')

    try:
        trend_response = analyze_trends_internal(f"{occasion} {style} fashion trends")
        trends = trend_response.get('current_trends', [])[:3]
    except:
        trends = []

    recommendation_text = generate_outfit_recommendation(
        user_closet, occasion, style, gender, disliked_outfit,
        recommendation_type, trends
    )

    if "Your closet is empty" in recommendation_text and recommendation_type == 'closet':
        return jsonify({'message': recommendation_text}), 400

    return jsonify({
        'recommendation': recommendation_text,
        'trends_considered': trends
    }), 200


@app.route('/analyze_trends', methods=['POST'])
def analyze_trends():
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        query = data.get("query", "current fashion trends")
        agent_executor = get_trend_agent()
        raw_response = agent_executor.invoke({"query": query})
        structured_response = parse_trend_response(raw_response)
        return jsonify(structured_response.dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def analyze_trends_internal(query):
    agent_executor = get_trend_agent()
    raw_response = agent_executor.invoke({"query": query})
    return parse_trend_response(raw_response).dict()


@app.route('/logout')
def logout():
    session.pop('uid', None)
    return redirect(url_for('login_page'))


@app.route('/firebase-config')
def firebase_config():
    firebase_config = {
        "apiKey": os.environ.get("FIREBASE_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.environ.get("FIREBASE_APP_ID")
    }
    return jsonify(firebase_config)


# --- New Subscriptions Page Route ---
@app.route('/subscription')
def subscriptions_page():
    """Renders the subscription plans page."""
    if 'uid' not in session:
        return redirect(url_for('login_page'))
    return render_template('subscription.html')


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=True)
