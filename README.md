# Agentic AI Virtual Stylist System

## Project Overview
This project is an agentic AI-based virtual stylist system that provides personalized outfit recommendations. The system uses multiple AI agents working together to analyze fashion trends, generate outfit recommendations based on user preferences and closet items, and provide shopping links. It features user authentication, a categorized virtual closet, and a beautiful magical-themed user interface.

## Technology Stack

### Backend
- **Flask** - Web framework for RESTful API
- **Firebase Admin SDK** - Authentication and Firestore database
- **LangChain** - Agent framework for multi-agent orchestration
- **Google Gemini API** - LLM for outfit generation and analysis
- **Python 3.x** - Backend programming language

### Frontend
- **HTML5/CSS3** - Frontend structure and styling
- **JavaScript** - Client-side interactivity
- **Tailwind CSS** - Utility-first CSS framework
- **Font Awesome** - Icons
- **Firebase Client SDK** - Client-side authentication

### Key Libraries
- `langchain-google-genai` - LangChain integration with Google Gemini
- `duckduckgo-search` - Web search for trend analysis
- `beautifulsoup4` - Web scraping for fashion blogs
- `wikipedia` - Fashion trend research
- `firebase-admin` - Backend Firebase integration
- `python-dotenv` - Environment variable management

## System Architecture

### Multi-Agent System
The system consists of four specialized AI agents that work together:

1. **Trend Analyzer Agent** (`agents/trendanalyzer.py`)
   - Researches current fashion trends using web search tools
   - Analyzes Instagram, TikTok, and fashion blog content
   - Provides trend insights and sources

2. **Outfit Generator Agent** (`agents/OutfitGenerator.py`)
   - Generates outfit recommendations based on:
     - User's virtual closet items
     - Occasion and style preferences
     - Current fashion trends
     - Gender preferences
   - Uses Google Gemini API for intelligent outfit creation

3. **User Preference Agent** (`agents/user_preference_agent.py`)
   - Adjusts outfit recommendations based on saved user preferences
   - Considers factors like:
     - Skin tone
     - Height and body type
     - Style preferences
     - Additional notes

4. **Product Search Agent** (`agents/product_search_agent.py`)
   - Searches for shopping links based on outfit recommendations
   - Validates and filters product URLs
   - Provides curated shopping links from trusted fashion retailers

### Project Structure

```
virtual-stylist/
├── backend/
│   ├── agents/
│   │   ├── OutfitGenerator.py          # Main outfit generation agent
│   │   ├── trendanalyzer.py            # Trend analysis agent
│   │   ├── product_search_agent.py     # Shopping link search agent
│   │   └── user_preference_agent.py    # User preference adjustment agent
│   ├                          
│   ├── main.py                          # Main Flask application entry point
│   ├── extensions.py                    # Firebase initialization module
│   ├── tools.py                         # LangChain tools for web search and scraping
│   ├── recommendationAgent.py           # Legacy recommendation agent
│   └── requirements.txt                 # Python dependencies
├── frontend/
│   └── templates/
│       ├── index.html                   # Main dashboard with closet and outfit generation
│       ├── login.html                   # User login page
│       ├── register.html                # User registration page
│       ├── userprofile.html             # User profile and preferences page
│       ├── closet_category.html         # Category-specific closet view
│       ├── subscription.html            # Subscription plans page
│       ├── premium-monthly.html         # Monthly premium subscription
│       └── premium-yearly.html          # Yearly premium subscription
├── venv/                                # Python virtual environment
├── requirements.txt                     # Root-level dependencies
├── virtual-stylist-52782-firebase-adminsdk-*.json  # Firebase service account key
└── README.md                            # This file
```

## Features

### User Management
- **Firebase Authentication** - Secure user login and registration
- **Session Management** - Flask sessions for user state
- **User Profiles** - Save and manage style preferences

### Virtual Closet
- **Categorized Storage** - Organize items by category:
  - 👚 Tops
  - 👖 Bottoms
  - 👗 Dresses/Outfits
  - 🧥 Outerwear/Jackets
  - 👟 Footwear
  - 💎 Accessories
- **Add/Delete Items** - Manage your virtual wardrobe
- **Cloud Storage** - Firebase Firestore for persistent storage

### Outfit Generation
- **Closet-Based Recommendations** - Generate outfits from your existing items
- **General Outfit Ideas** - Get inspiration for new styles
- **Trend Integration** - Recommendations consider current fashion trends
- **Preference Alignment** - Personalized based on saved preferences
- **Shopping Links** - Find similar items online

### User Preferences
- **Style Preferences** - Save your preferred styles
- **Physical Attributes** - Height, weight, skin tone considerations
- **Gender Preferences** - Personalized recommendations
- **Additional Notes** - Custom styling notes

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Firebase project with Authentication and Firestore enabled
- Google Cloud API key with Gemini API access
- Git (optional)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd virtual-stylist
```

### Step 2: Set Up Virtual Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - **On Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **On macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

### Step 3: Install Dependencies

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

   Or install from the root directory:
   ```bash
   pip install -r requirements.txt
   ```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
# Firebase Configuration
FIREBASE_SERVICE_KEY_PATH=path/to/your/firebase-service-account-key.json
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
FIREBASE_APP_ID=your-app-id

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
HOST=127.0.0.1
PORT=5000
```

**Important Notes:**
- Place your Firebase service account JSON file in the project root
- Update `FIREBASE_SERVICE_KEY_PATH` to point to this file
- Get your Firebase config from Firebase Console → Project Settings → General
- Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Step 5: Initialize Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Enable **Authentication** → Sign-in method → Email/Password
4. Enable **Firestore Database** → Create database (start in test mode)
5. Download your service account key:
   - Project Settings → Service Accounts → Generate New Private Key
   - Save the JSON file in your project root

### Step 6: Run the Application

1. Make sure you're in the backend directory with the virtual environment activated:
   ```bash
   cd backend
   ```

2. Run the Flask application:
   ```bash
   python main.py
   ```
   
   Or:
   ```bash
   python app.py
   ```

3. You should see output indicating the Flask server is running:
   ```
   * Running on http://127.0.0.1:5000
   ```

### Step 7: Access the Application

1. Open your web browser
2. Navigate to: `http://127.0.0.1:5000`
3. You'll be redirected to the login page
4. Register a new account or log in with existing credentials

## Usage Guide

### Getting Started

1. **Register/Login**: Create an account or log in with existing credentials
2. **Build Your Closet**: Add items to your virtual closet by category
3. **Set Preferences**: Go to Profile to save your style preferences
4. **Generate Outfits**: Use the outfit generator with your occasion and style preferences

### Generating Outfits

1. Enter an **occasion** (e.g., "casual date", "job interview", "beach party")
2. Enter a **style preference** (e.g., "boho chic", "minimalist", "vintage")
3. Choose recommendation type:
   - **Based on my Closet**: Uses only items you've added
   - **A General Outfit Idea**: Provides inspiration with new suggestions
4. Click **Generate Outfit** and wait for the AI agents to work their magic!

### Managing Your Closet

1. Click on any category card from the main dashboard
2. Add items by typing and clicking "Add Item"
3. Delete items by clicking the delete button next to each item
4. Items are automatically saved to your Firebase account

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /register` - Registration page
- `GET /logout` - Logout user

### Closet Management
- `GET /closet/<category>` - View items in a specific category
- `POST /add-item` - Add item to closet
- `POST /delete-item` - Remove item from closet

### Outfit Generation
- `POST /generate-outfit` - Generate outfit recommendation
- `POST /analyze_trends` - Analyze fashion trends

### User Profile
- `GET /userprofile` - User profile page
- `GET /user-profile` - Get user profile data (JSON)
- `GET /get_preferences` - Get user preferences (JSON)
- `POST /save_preferences` - Save user preferences

### Configuration
- `GET /firebase-config` - Get Firebase client configuration (JSON)

### Subscriptions
- `GET /subscription` - Subscription plans page
- `GET /premium-monthly` - Monthly premium page
- `GET /premium-yearly` - Yearly premium page

## Troubleshooting

### Common Issues

1. **Firebase Authentication Errors**
   - Verify your Firebase service account key path is correct
   - Check that Authentication is enabled in Firebase Console
   - Ensure Firestore Database is initialized

2. **Gemini API Errors**
   - Verify your `GEMINI_API_KEY` is set correctly in `.env`
   - Check your API quota at Google AI Studio
   - Ensure the API key has access to Gemini models

3. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using the correct Python version (3.8+)
   - Check that your virtual environment is activated

4. **Port Already in Use**
   - Change the `PORT` in your `.env` file
   - Or stop any process using port 5000

5. **Template Not Found**
   - Ensure you're running the Flask app from the correct directory
   - Check that the `frontend/templates` directory exists

## Development Notes

### Agent Workflow
1. **Trend Analysis**: User query triggers trend analyzer to research current fashion
2. **Outfit Generation**: Outfit generator creates recommendation based on trends and user closet
3. **Preference Adjustment**: User preference agent fine-tunes the recommendation
4. **Product Search**: Product search agent finds shopping links for recommended items

### Database Structure

**Firestore Collections:**
- `closets/{uid}` - User closet items organized by category
- `users/{uid}` - User preferences and profile data

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license information here]

## Acknowledgments

- Built with Flask and LangChain
- Powered by Google Gemini AI
- Firebase for backend services
- Tailwind CSS for styling
