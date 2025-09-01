# outfit_generator.py
# This file contains the logic for generating outfit recommendations using the Gemini API.

import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TREND_ANALYZER_URL = os.environ.get("TREND_ANALYZER_URL", "http://localhost:5000/analyze_trends")

def analyze_fashion_trends(query="current fashion trends"):
    """
    Calls the trend analyzer API to get current fashion trends
    """
    try:
        response = requests.post(
            TREND_ANALYZER_URL,
            json={"query": query},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Trend analyzer API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling trend analyzer: {e}")
        return None

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


def generate_outfit_recommendation(user_closet, occasion, style, gender, disliked_outfit=None, recommendation_type="closet", trends=None):
    """
    Generates an outfit recommendation based on the provided parameters.
    
    Args:
        user_closet (list): List of items in the user's closet
        occasion (str): The occasion for the outfit
        style (str): Style preference
        gender (str): Gender for the outfit
        disliked_outfit (str, optional): Previous disliked outfit to avoid
        recommendation_type (str): Either 'closet' or 'general'
        trends (list, optional): Current fashion trends to consider
    
    Returns:
        str: The generated outfit recommendation
    """
    
    if recommendation_type == 'closet':
        if not user_closet:
            return "Your closet is empty. Please add some items first or switch to 'General outfit idea'!"
        
        # Craft the prompt for a closet-based recommendation
        gemini_prompt = (
            f"You are a professional stylist. Recommend a stylish {gender} outfit. "
            f"Based on a closet containing the following items: {', '.join(user_closet)}. "
            f"For the occasion: '{occasion}', "
            f"in the style of: '{style}', "
        )
        
        # Add trend information if available
        if trends:
            gemini_prompt += f"Consider these current fashion trends: {', '.join(trends)}. "
            
        gemini_prompt += (
            f"Please recommend a single, complete, and stylish outfit. "
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
        )
        
        # Add trend information if available
        if trends:
            gemini_prompt += f"Consider these current fashion trends: {', '.join(trends)}. "
            
        gemini_prompt += (
            f"Please recommend a single, complete, and stylish outfit. "
            f"The outfit must include exactly one top and one bottom. "
            f"The recommendation should be practical and fashionable. "
            f"The outfit must be a logical combination of clothing items, for example do not pair a skirt/shirt with a dress "
            f"Do not recommend clothing worn by a woman if the gender is male. "
        )

    # Add the disliked outfit as a negative constraint if it exists
    if disliked_outfit:
        gemini_prompt += f" The previous recommendation, '{disliked_outfit}', was not liked. Please provide a new recommendation that is significantly different and does not include any of the items mentioned in the disliked outfit. "

    gemini_prompt += f"Explain why this outfit is recommended, but keep the output text concise. If a complete and logical outfit is not possible from the provided items, say so."

    # Get the outfit recommendation from the Gemini API
    recommendation_text = call_gemini_api(gemini_prompt)
    
    return recommendation_text if recommendation_text else "Could not generate a text recommendation. Please try again."