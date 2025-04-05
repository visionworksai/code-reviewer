import os
import json
from typing import List, Dict, Any
import google.generativeai as Client
from .base_model import BaseAIModel

class GeminiModel(BaseAIModel):
    """
    Implementation of BaseAIModel for Google's Gemini AI models.
    
    Handles configuration, API communication, and response parsing for 
    Google's Gemini models specifically.
    """
    
    def configure(self):
        """
        Configure the Gemini client with API key from environment variables.
        
        Raises:
            ValueError: If GEMINI_API_KEY environment variable is not set
        """
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        Client.configure(api_key=api_key)
        
    def get_response_from_model(self, prompt: str) -> List[Dict[str, str]]:
        """
        Send prompt to Gemini API and parse the structured response.
        
        Args:
            prompt: The code review prompt to send to Gemini
            
        Returns:
            List of dictionaries with lineNumber and reviewComment keys
        """
        # Get the model name from environment variables or use default
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-001')
        gemini_model = Client.GenerativeModel(model_name)

        # Configure generation parameters
        generation_config = {
            "max_output_tokens": 8192,
            "temperature": 0.8,
            "top_p": 0.95,
        }

        print(f"Sending prompt to Gemini model: {model_name}")
        
        try:
            # Call the Gemini API
            response = gemini_model.generate_content(prompt, generation_config=generation_config)
            
            # Process and clean the response text
            response_text = self._clean_response_text(response.text)
            
            # Parse the JSON response
            return self._parse_response_json(response_text)
            
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return []
    
    def _clean_response_text(self, text: str) -> str:
        """
        Clean the response text by removing markdown code blocks.
        
        Args:
            text: The raw response text from Gemini
            
        Returns:
            Cleaned response text ready for JSON parsing
        """
        text = text.strip()
        
        # Remove markdown code block markers if present
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        if text.endswith('```'):
            text = text[:-3]  # Remove ```
            
        return text.strip()
    
    def _parse_response_json(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from Gemini and extract review comments.
        
        Args:
            response_text: Cleaned response text from Gemini
            
        Returns:
            List of valid review comments
        """
        try:
            data = json.loads(response_text)
            
            # Verify response contains the expected structure
            if "reviews" in data and isinstance(data["reviews"], list):
                reviews = data["reviews"]
                
                # Filter to only include valid review objects
                valid_reviews = []
                for review in reviews:
                    if "lineNumber" in review and "reviewComment" in review:
                        valid_reviews.append(review)
                    else:
                        print(f"Skipping invalid review format: {review}")
                
                return valid_reviews
            else:
                print("Error: Response doesn't contain valid 'reviews' array")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response_text}")
            return [] 