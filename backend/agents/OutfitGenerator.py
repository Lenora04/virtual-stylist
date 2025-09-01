# agents/OutfitGenerator.py
import os
import time
import requests
from flask import current_app

class OutfitGenerator:
    def __init__(self):
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")
    
    def call_gemini_api(self, prompt, model_name="gemini-1.5-flash-latest"):
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
                    params={"key": self.google_api_key},
                    json=payload
                )
                response.raise_for_status() # Raise an error for bad status codes

                data = response.json()
                if data and "candidates" in data and len(data["candidates"]) > 0:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "No recommendation found."

            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"API call failed: {e}")
                retries += 1
                delay = base_delay * (2 ** retries)
                current_app.logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            
        return "Failed to get a recommendation after several retries."
    
    def generate_outfit_prompt(self, user_closet, occasion, style, gender, disliked_outfit=None, recommendation_type="closet"):
        """
        Generates a prompt for the Gemini API based on the user's input.
        """
        if recommendation_type == 'closet':
            if not user_closet:
                return None
            
            # Craft the prompt for a closet-based recommendation
            prompt = (
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
            prompt = (
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
            prompt += f" The previous recommendation, '{disliked_outfit}', was not liked. Please provide a new recommendation that is significantly different and does not include any of the items mentioned in the disliked outfit. "

        prompt += f"Explain why this outfit is recommended, but keep the output text concise. If a complete and logical outfit is not possible from the provided items, say so."
        
        return prompt
    
    def generate_outfit(self, user_closet, occasion, style, gender, disliked_outfit=None, recommendation_type="closet"):
        """
        Generates an outfit recommendation using the Gemini API.
        """
        prompt = self.generate_outfit_prompt(
            user_closet, occasion, style, gender, 
            disliked_outfit, recommendation_type
        )
        
        if not prompt:
            return "Your closet is empty. Please add some items first or switch to 'General outfit idea'!"
        
        # Get the outfit recommendation from the Gemini API
        recommendation_text = self.call_gemini_api(prompt)
        
        if not recommendation_text:
            return "Could not generate a text recommendation. Please try again."
            
        return recommendation_text