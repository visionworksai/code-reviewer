import os
import json
import anthropic
from typing import List, Dict, Any
from .base_model import BaseAIModel

class ClaudeModel(BaseAIModel):
    """
    Implementation of BaseAIModel for Anthropic's Claude models.
    
    This class handles configuration, API communication, and response parsing
    for Claude models like Claude 3 Opus/Sonnet/Haiku.
    """
    
    def configure(self):
        """
        Configure the Anthropic client with API key from environment variables.
        
        Raises:
            ValueError: If CLAUDE_API_KEY environment variable is not set
        """
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
        
        # Configure the Anthropic client
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def get_response_from_model(self, prompt: str) -> List[Dict[str, str]]:
        """
        Send prompt to Claude API and parse the structured response.
        
        Args:
            prompt: The code review prompt to send to Claude
            
        Returns:
            List of dictionaries with lineNumber and reviewComment keys
        """
        # Get model name from environment or use default
        model_name = os.environ.get('CLAUDE_MODEL', 'claude-3-7-sonnet')
        
        # Configure completion parameters
        system_prompt = "You are a skilled code reviewer. Respond with JSON containing code review comments."
        
        print(f"Sending prompt to Claude model: {model_name}")
        # Log the request parameters for debugging
        request_params = {
            "model": model_name,
            "system": system_prompt,
            "max_tokens": 4000,
            "temperature": 0.7
        }
        print(f"Request parameters: {json.dumps(request_params, indent=2)}")
        
        # Maximum number of retries for rate limit errors
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Call the Claude API
                response = self.client.messages.create(
                    model=model_name,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                
                # Extract response content
                response_text = response.content[0].text
                
                # Process the response
                return self._parse_response_json(response_text)
                
            except anthropic.RateLimitError as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    print(f"Rate limit exceeded. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"Rate limit exceeded and max retries reached: {e}")
                    return []
                    
            except anthropic.APIError as e:
                print(f"Claude API error: {e}")
                return []
                
            except anthropic.APIConnectionError as e:
                print(f"Network error connecting to Claude API: {e}")
                return []
                
            except anthropic.AuthenticationError as e:
                print(f"Authentication error with Claude API: {e}")
                return []
                
            except anthropic.BadRequestError as e:
                print(f"Invalid request to Claude API: {e}")
                return []
                
            except Exception as e:
                print(f"Unexpected error during Claude API call: {e}")
                return []
    
    def _parse_response_json(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from Claude and extract review comments.
        
        Args:
            response_text: Response text from Claude
            
        Returns:
            List of valid review comments
        """
        # Clean up the response if it contains markdown code blocks
        response_text = self._clean_response_text(response_text)
        
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
    
    def _clean_response_text(self, text: str) -> str:
        """
        Clean the response text by removing markdown code blocks.
        
        Args:
            text: The raw response text from Claude
            
        Returns:
            Cleaned response text ready for JSON parsing
        """
        text = text.strip()
        
        # Remove markdown code block markers if present
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        elif text.startswith('```'):
            # Find the first newline to skip the language identifier line
            first_newline = text.find('\n')
            if first_newline != -1:
                text = text[first_newline + 1:]
            else:
                text = text[3:]  # Remove just the ``` if no newline found
                
        if text.endswith('```'):
            text = text[:-3]  # Remove ```
            
        return text.strip() 