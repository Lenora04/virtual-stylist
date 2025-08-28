# app.py
# This is the backend for the Virtual Stylist application.
# It uses Flask to handle routes for user authentication, closet management,
# and outfit generation via the Gemini API.

import os
import time
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from firebase_admin import firestore

# --- Firebase Imports and Configuration ---
import firebase_admin
from firebase_admin import credentials, auth

# Load environment variables from the .env file
load_dotenv()

# Path to your service account key file
# IMPORTANT: Use an environment variable in production!
cred_path = os.environ.get('FIREBASE_SERVICE_KEY_PATH', 'C:/Users/USER/Desktop/stuff/IRWA/virtual-stylist/virtual-stylist-52782-firebase-adminsdk-fbsvc-6881e2d02f.json')
cred = credentials.Certificate(cred_path)

# Initialize Firebase Admin SDK
try:
    app_firebase = firebase_admin.initialize_app(cred)
except ValueError as e:
    print(f"Firebase app already initialized. Skipping... Error: {e}")
    app_firebase = firebase_admin.get_app()

db = firestore.client(app=app_firebase)

# --- Configuration ---
# You need to set your API keys as environment variables.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Set the template folder relative to the backend directory.
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'))
app = Flask(__name__, template_folder=template_dir)
# Set a secret key for session management.
app.secret_key = os.environ.get('FLASK_SECRET_KEY')


# --- Helper Functions ---
def call_gemini_api(prompt, model_name="gemini-1.5-flash-latest"):
    """
    Calls the Gemini API with exponential backoff for error handling.
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    # Simple exponential backoff retry logic
    retries = 0
    max_retries = 5
    base_delay = 1.0  # seconds

    while retries < max_retries:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
            }
            
            response = requests.post(
                api_url, 
                headers=headers, 
                params={"key": GOOGLE_API_KEY},
                json=payload
            )
            response.raise_for_status() # Raise an error for bad status codes

            data = response.json()
            if data and "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "No recommendation found."

        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            retries += 1
            delay = base_delay * (2 ** retries)
            print(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
        
    return "Failed to get a recommendation after several retries."


# --- Routes ---

@app.route('/')
def home():
    """Renders the main page if the user is logged in, otherwise redirects to login."""
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
    """Renders the register.html page."""
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        id_token = request.form.get('id_token')
        
        if not id_token:
            return jsonify({'message': 'No ID token provided.'}), 400

        try:
            # Verify Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get('uid')
            if not uid:
                return jsonify({'message': 'Invalid ID token: UID missing.'}), 401

            # Store UID in session
            session['uid'] = uid

            # Ensure user document exists in Firestore
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
            print("Login error:", e)  # Logs full error to server console
            return jsonify({'message': 'An unexpected server error occurred.'}), 500

    # For GET requests, render the login page
    return render_template('login.html')

@app.route('/add-item', methods=['POST'])
def add_item():
    """Adds a new item to the logged-in user's closet."""
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    uid = session['uid']
    item = request.form.get('itemInput')
    
    # Check if the item is not empty or just whitespace
    if item and item.strip():
        user_ref = db.collection("closets").document(uid)
        doc = user_ref.get()

        if doc.exists:
            items = doc.to_dict().get("items", [])
        else:
            items = []

        items.append(item.strip())
        user_ref.set({"items": items})  # overwrite with updated list

        return jsonify({'message': 'Item added successfully', 'item': item.strip()}), 200
    
    # Return a specific error message for an empty item
    return jsonify({'message': 'Failed to add item. The item field cannot be empty.'}), 400

@app.route('/delete-item', methods=['POST'])
def delete_item():
    """Deletes an item from the logged-in user's closet."""
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    uid = session['uid']
    item_to_delete = request.form.get('item')
    
    # Check if the item is not empty
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
            # Item not found in the list
            return jsonify({'message': 'Item not found in closet.'}), 404
    else:
        return jsonify({'message': 'User closet not found.'}), 404


@app.route('/generate-outfit', methods=['POST'])
def generate_outfit():
    """
    Generates an outfit recommendation using the Gemini API.
    """
    if 'uid' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    uid = session['uid']
    user_ref = db.collection("closets").document(uid)
    doc = user_ref.get()

    user_closet = []
    if doc.exists:
        user_closet = doc.to_dict().get("items", [])

    occasion = request.form.get('occasion', '')
    style = request.form.get('style_preference', '')
    gender = request.form.get('gender', 'person')
    disliked_outfit = request.form.get('disliked_outfit', None)
    recommendation_type = request.form.get('recommendation_type', 'closet')

    if recommendation_type == 'closet':
        if not user_closet:
            return jsonify({'message': 'Your closet is empty. Please add some items first or switch to "General outfit idea"!'}), 400
        
        # Craft the prompt for a closet-based recommendation
        gemini_prompt = (
            f"You are a professional stylist. Recommend a stylish {gender} outfit. "
            f"Based on a closet containing the following items: {', '.join(user_closet)}. "
            f"For the occasion: '{occasion}', "
            f"in the style of: '{style}', "
            f"please recommend a single, complete, and stylish outfit. "
            f"The outfit must be a logical combination of clothing items, for example do not pair a skirt/shirt with a dress "
            f"Do not recommend clothing worn by a woman if the gender is male. "
            f"Do not include items that are not in the closet. "
            f"if an outfit isnt possible with the available items, say so. "
        )

    else: 
        # Craft the prompt for a general recommendation
        gemini_prompt = (
            f"You are a professional fashion stylist. Recommend a stylish {gender} outfit. "
            f"For a '{occasion}' occasion and a '{style}' style, "
            f"please recommend a single, complete, and stylish outfit. "
            f"The outfit must include exactly one top and one bottom. "
            f"The recommendation should be practical and fashionable. "
            f"The outfit must be a logical combination of clothing items, for example do not pair a skirt/shirt with a dress "
            f"Do not recommend clothing  worn by a woman if the gender is male. "
        )

    # Add the disliked outfit as a negative constraint if it exists
    if disliked_outfit:
        gemini_prompt += f" The previous recommendation, '{disliked_outfit}', was not liked. Please provide a new recommendation that is significantly different and does not include any of the items mentioned in the disliked outfit. "

    gemini_prompt += f"Explain why this outfit is recommended, but keep the output text concise. If a complete and logical outfit is not possible from the provided items, say so."

    # 2. Get the outfit recommendation from the Gemini API
    recommendation_text = call_gemini_api(gemini_prompt)
    if not recommendation_text:
        return jsonify({'message': 'Could not generate a text recommendation. Please try again.'}), 500

    # 3. Return only the text recommendation to the frontend
    return jsonify({
        'recommendation': recommendation_text,
    }), 200

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.pop('uid', None)
    return redirect(url_for('login_page'))

# Route to provide Firebase configuration to the frontend
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

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=True)