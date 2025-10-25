import os
import time
import requests
from dotenv import load_dotenv
from agents.user_preference_agent import adjust_outfit_with_preferences  # integrate user preferences

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
TREND_ANALYZER_URL = os.environ.get("TREND_ANALYZER_URL", "http://localhost:5000/analyze_trends")


def analyze_fashion_trends(query="current fashion trends"):
    """Calls the trend analyzer API to get current fashion trends"""
    try:
        response = requests.post(TREND_ANALYZER_URL, json={"query": query}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Trend analyzer API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling trend analyzer: {e}")
        return None


def call_gemini_api(prompt, model_name="gemini-2.0-flash"):
    """Calls the Gemini API with exponential backoff for error handling."""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    retries = 0
    max_retries = 5
    base_delay = 1.0

    while retries < max_retries:
        try:
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(api_url, headers=headers, params={"key": GOOGLE_API_KEY}, json=payload)
            response.raise_for_status()
            data = response.json()
            if data and "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            return "No recommendation found."
        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            retries += 1
            delay = base_delay * (2 ** retries)
            print(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    return "Failed to get a recommendation after several retries."


def generate_outfit_recommendation(
    user_closet,
    occasion,
    style,
    gender,
    disliked_outfit=None,
    recommendation_type="closet",
    trends=None,
    preferences=None
):
    """Generates an outfit recommendation based on the provided parameters."""

    # --- Gender handling ---
    if gender == 'man':
        gender_term = "male"
        gender_constraint = "Do not recommend clothing typically worn by a woman."
    elif gender == 'woman':
        gender_term = "female"
        gender_constraint = "Do not recommend clothing typically worn by a man."
    else:
        gender_term = "person's"
        gender_constraint = "Recommend a gender-neutral or appropriate outfit for a general person."
    
    # Flag to track if we fell back to a general recommendation
    is_fallback = False

    # --- Build Gemini prompt (Initial Attempt: Closet) ---
    if recommendation_type == 'closet':
        if not user_closet:
            # Case 1: Closet is completely empty.
            return "Your closet is empty. Please add some items first or switch to 'General outfit idea'!"

        # Initial attempt to generate an outfit strictly from the closet
        gemini_prompt_closet = (
            f"You are a professional stylist. Recommend a stylish {gender_term} outfit strictly from this closet: "
            f"{', '.join(user_closet)}. "
            f"Occasion: '{occasion}', Style: '{style}'. {gender_constraint} "
            "Only use items explicitly listed in the closet. If no combination fits the occasion, clearly state 'No suitable combination found in the closet.' as the ONLY response text."
        )
        if trends:
            gemini_prompt_closet += f" Consider these current fashion trends: {', '.join(trends)}."
        
        # Add the common parts
        common_prompt_suffix = " Recommend a single complete outfit."
        if disliked_outfit:
            common_prompt_suffix += (
                f" The previous recommendation, '{disliked_outfit}', was not liked. "
                f"Provide a new recommendation that does not include items from the disliked outfit."
            )
        common_prompt_suffix += " Explain why this outfit is recommended concisely."
        
        gemini_prompt_closet += common_prompt_suffix

        # Get initial outfit from Gemini
        recommendation_text = call_gemini_api(gemini_prompt_closet)

        # Check if the closet items were insufficient (based on the instruction to the LLM)
        if "No suitable combination found in the closet" in recommendation_text or "No recommendation found" in recommendation_text:
            # Case 2: Closet is not empty, but items are insufficient. Fallback to general.
            is_fallback = True
            recommendation_type = 'general' # Change type for the next prompt
            
            # If we fall back, the general prompt is built and called below.
        else:
            # Successful closet recommendation, skip to preference adjustment.
            pass


    # --- Build Gemini prompt (General Outfit Idea / Fallback) ---
    if recommendation_type == 'general' or is_fallback:
        gemini_prompt = (
            f"You are a professional stylist. Recommend a stylish {gender_term} outfit. "
            f"For a '{occasion}' occasion and a '{style}' style. {gender_constraint}"
        )
        if trends:
            gemini_prompt += f" Consider these current fashion trends: {', '.join(trends)}."
        
        # Add the common parts
        gemini_prompt += " Please recommend a single, complete, and stylish outfit including one top and one bottom."
        
        if disliked_outfit:
            gemini_prompt += (
                f" The previous recommendation, '{disliked_outfit}', was not liked. "
                f"Provide a new recommendation that does not include items from the disliked outfit."
            )

        gemini_prompt += " Explain why this outfit is recommended concisely."
        
        recommendation_text = call_gemini_api(gemini_prompt)
        
        # Prepend the message about the fallback
        if is_fallback:
            recommendation_text = (
                "I couldn't find a complete outfit for this occasion and style from your current closet items. "
                "Here is a general outfit idea based on your preferences:\n\n" + recommendation_text
            )

    # --- Adjust with preferences ---
    if preferences:
        context = {"type": recommendation_type, "closet": user_closet if recommendation_type == 'closet' else []}
        # Adjust the outfit based on the current recommendation (whether closet-based or general)
        adjusted = adjust_outfit_with_preferences(recommendation_text, preferences, context)
        final_outfit = adjusted["outfit"]
        reasons = adjusted["reasons"]

        final_output = f"{final_outfit}\n\n(This recommendation considers your saved preferences.)"
        if reasons:
            final_output += "\n\nPreference-based reasoning:\n" + "\n".join(reasons)
        return final_output
    
    
    return recommendation_text or "Could not generate a text recommendation. Please try again."