# run_backend.ps1
# This script automates the process of setting up and running your Flask backend.

# 1. Set the location to the backend folder
Set-Location "C:\Users\USER\Desktop\stuff\IRWA\virtual-stylist\backend"

# 2. Activate the Python virtual environment
& "C:\Users\USER\Desktop\stuff\IRWA\virtual-stylist\venv\Scripts\Activate.ps1"

# 3. Set the required environment variables
# You must replace these placeholder values with your actual keys from your .env file
# This is a secure way to pass them to your Python application.
$env:FLASK_SECRET_KEY = '\xa2\xb4)\xf3f\xbc\x97F\xc1\x04\xbb\xd7\xe2\xdf91\x9f\xe5\x8f6\xed\xa4\x14\xa0'
$env:GOOGLE_API_KEY = "AIzaSyBKOxUad5U56YPeG2vlPbtz5HjLYtcdCKI"
$env:FIREBASE_SERVICE_KEY_PATH = "C:/Users/USER/Desktop/stuff/IRWA/virtual-stylist/virtual-stylist-52782-firebase-adminsdk-fbsvc-6881e2d02f.json"

# 4. Run the Flask application
python app.py

