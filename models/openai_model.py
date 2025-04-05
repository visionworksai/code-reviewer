import os
import json
import openai
from typing import List, Dict, Any
from .base_model import BaseAIModel

class OpenAIModel(BaseAIModel):
    """
    Implementation of BaseAIModel for OpenAI's models.
    
    This class handles configuration, API communication, and response parsing
    for OpenAI models like GPT-4.
    """
    
    def configure(self):
        """
        Configure the OpenAI client with API key from environment variables.
        
        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Configure the OpenAI client
        openai.api_key = api_key
        
        # Set organization ID if provided
        org_id = os.environ.get('OPENAI_ORGANIZATION')
        if org_id:
            openai.organization = org_id
    
    def get_response_from_model(self, prompt: str) -> List[Dict[str, str]]:
        """
        Send prompt to OpenAI API and parse the structured response.
        
        Args:
            prompt: The code review prompt to send to OpenAI
            
        Returns:
            List of dictionaries with lineNumber and reviewComment keys
        """
        # Get model name from environment or use default
        model_name = os.environ.get('OPENAI_MODEL', 'gpt-4')
        
        # Configure completion parameters
        completion_params = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a skilled code reviewer. Respond with JSON containing code review comments."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"}
        }
        
        print(f"Sending prompt to OpenAI model: {model_name}")
        # Log the completion parameters for debugging
        print(f"Completion parameters: {json.dumps(completion_params, indent=2)}")
        
        # Maximum number of retries for rate limit errors
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Call the OpenAI API
                response = openai.chat.completions.create(**completion_params)
                
                # Extract response content
                response_text = response.choices[0].message.content
                
                # Process the response
                return self._parse_response_json(response_text)
                
            except openai.RateLimitError as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    print(f"Rate limit exceeded. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"Rate limit exceeded and max retries reached: {e}")
                    return []
                    
            except openai.APIError as e:
                print(f"OpenAI API error: {e}")
                return []
                
            except openai.APIConnectionError as e:
                print(f"Network error connecting to OpenAI API: {e}")
                return []
                
            except openai.AuthenticationError as e:
                print(f"Authentication error with OpenAI API: {e}")
                return []
                
            except openai.InvalidRequestError as e:
                print(f"Invalid request to OpenAI API: {e}")
                return []
                
            except Exception as e:
                print(f"Unexpected error during OpenAI API call: {e}")
                return []
    
    def _parse_response_json(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from OpenAI and extract review comments.
        
        Args:
            response_text: Response text from OpenAI
            
        Returns:
            List of valid review comments
        """
        try:
            # Parse the JSON response
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
                print(f"Response content: {data}")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response_text}")
            return [] 