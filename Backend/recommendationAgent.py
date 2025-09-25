# recommendation_agent.py
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body

# Load API keys
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# FastAPI app
app = FastAPI(title="Recommendation Agent")

# --- Helper: Call Gemini API ---
def call_gemini_api(prompt, model_name="gemini-1.5-flash"):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, params={"key": GOOGLE_API_KEY}, json=payload)
        response.raise_for_status()
        data = response.json()
        if data and "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini API error:", e)
    return None

# --- Main Recommendation Endpoint ---
@app.post("/recommend-outfits")
def recommend_outfits(
    user_prefs: dict = Body(...),           # {"occasion": "party", "style": "streetwear", "closet": [...]}
    trend_info: dict = Body(...),           # {"current_trends": [...], "insights": "..."}
    base_outfit: dict = Body(...),          # {"recommendation": "...", "image_url": "..."}
):
    """
    Generate 3 more outfit recommendations by combining:
    - User preferences
    - Trend Analyzer insights
    - Outfit Generator base outfit
    """

    occasion = user_prefs.get("occasion", "")
    style = user_prefs.get("style", "")
    closet = ", ".join(user_prefs.get("closet", []))
    trends = ", ".join(trend_info.get("current_trends", []))
    insights = trend_info.get("insights", "")

    # Prompt for Gemini
    prompt = f"""
    You are a fashion recommendation agent.
    The user closet: {closet}
    Occasion: {occasion}
    Style preference: {style}
    Trends to consider: {trends}
    Trend insights: {insights}
    Already suggested outfit: {base_outfit.get('recommendation')}

    Task:
    Suggest 3 *different* alternative outfits (use closet items where possible).
    Each outfit should be short, clear, and stylish. 
    Format:
    - Outfit 1: ...
    - Outfit 2: ...
    - Outfit 3: ...
    """

    rec_text = call_gemini_api(prompt)

    if not rec_text:
        raise HTTPException(status_code=500, detail="Could not generate recommendations")

    return {
        "base_outfit": base_outfit,
        "extra_recommendations": rec_text,
        "trends_used": trend_info.get("current_trends", [])
    }
