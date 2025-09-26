import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

# Read the path from environment variable
cred_path = os.environ.get("FIREBASE_SERVICE_KEY_PATH")

if not cred_path or not os.path.exists(cred_path):
    raise FileNotFoundError(
        f"Firebase JSON not found. Set FIREBASE_SERVICE_KEY_PATH in .env (tried {cred_path})"
    )

# Initialize Firebase
cred = credentials.Certificate(cred_path)
try:
    app_firebase = firebase_admin.initialize_app(cred)
except ValueError:
    app_firebase = firebase_admin.get_app()

db = firestore.client(app=app_firebase)
