# extensions.py
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

cred_path = os.environ.get(
    "FIREBASE_SERVICE_KEY_PATH",
    "C:/Users/ASUS/Desktop/Virtual Stylist/virtual-stylist/virtual-stylist-52782-firebase-adminsdk-fbsvc-6881e2d02f.json"
)
cred = credentials.Certificate(cred_path)

try:
    app_firebase = firebase_admin.initialize_app(cred)
except ValueError:
    app_firebase = firebase_admin.get_app()

db = firestore.client(app=app_firebase)
