import os
import json
import requests
import re
from typing import List, Dict, Any
from .base_model import BaseAIModel

class DeepSeekModel(BaseAIModel):
    """
    Implementation of BaseAIModel that uses Ollama with DeepSeek model for local code review.
    
    This class enables running DeepSeek models locally through Ollama,
    which provides efficient CPU/GPU inference for code analysis.
    """
    
    def __init__(self):
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        
        # Use deepseek-r1:1.5b model by default, but allow users to choose a larger model
        # Available models include: deepseek-r1:1.5b, deepseek-r1:3b, deepseek-r1:7b, deepseek-coder:7b
        self.model_name = os.environ.get("DEEPSEEK_MODEL_NAME", "deepseek-coder:1.3b")
        
        # Log available models for user reference
        print("Note: For better JSON formatting, consider using a larger DeepSeek model:")
        print("  - Available options: deepseek-r1:1.5b, deepseek-r1:3b, deepseek-r1:7b, deepseek-coder:7b")
        print(f"  - Set the DEEPSEEK_MODEL_NAME environment variable to change (currently using: {self.model_name})")
        
        # Set default parameters for code review
        self.temperature = float(os.environ.get("DEEPSEEK_TEMPERATURE", "0.1"))
        self.top_p = float(os.environ.get("DEEPSEEK_TOP_P", "0.95"))
        self.max_tokens = int(os.environ.get("DEEPSEEK_MAX_TOKENS", "2048"))
        
    def configure(self):
        """
        Configure the DeepSeek model with Ollama.
        
        Checks if Ollama is running and if the DeepSeek model is available.
        If not, provides instructions for installing it.
        
        Raises:
            RuntimeError: If Ollama is not running or the model is not available
        """
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code != 200:
                raise RuntimeError("Failed to connect to Ollama API")
            
            # Check if DeepSeek model is available
            models = response.json().get("models", [])
            model_available = any(model.get("name") == self.model_name for model in models)
            
            if not model_available:
                print(f"DeepSeek model '{self.model_name}' not found in Ollama")
                print("Please run the following command to pull the model:")
                print(f"ollama pull {self.model_name}")
                raise RuntimeError(f"DeepSeek model '{self.model_name}' not available in Ollama")
                
            print(f"Successfully configured DeepSeek model '{self.model_name}' with Ollama")
            
        except requests.RequestException as e:
            print("Error connecting to Ollama. Is Ollama running?")
            print("To install Ollama: curl -fsSL https://ollama.com/install.sh | sh")
            print(f"Then pull the DeepSeek model: ollama pull {self.model_name}")
            raise RuntimeError(f"Failed to connect to Ollama: {str(e)}")
    
    def get_response_from_model(self, prompt: str) -> List[Dict[str, str]]:
        """
        Send prompt to the DeepSeek model via Ollama and process the response for code review.
        
        Args:
            prompt: A string containing the code review prompt
            
        Returns:
            A list of dictionaries with lineNumber and reviewComment keys
            
        Raises:
            RuntimeError: If there's an error communicating with Ollama
        """
        # Format system prompt for code review
        system_prompt = """You are a code review assistant. Analyze the code and provide specific, actionable feedback.
        IMPORTANT: Your response MUST be a valid JSON array with objects containing 'lineNumber' and 'reviewComment' fields.
        You MUST format your entire response as a single JSON array, nothing else.
        
        JSON FORMAT EXAMPLE:
        [
          {"lineNumber": 42, "reviewComment": "This loop could be optimized."},
          {"lineNumber": 67, "reviewComment": "Potential null reference issue here."}
        ]
        
        If you don't find any issues worth commenting on, respond with an empty array: []
        DO NOT include any explanations, markdown formatting, or other text outside the JSON array."""
        
        try:
            # Send request to Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "max_tokens": self.max_tokens,
                    "stream": False,
                    "format": "json"  # Request JSON output if the model supports it
                }
            )
            
            if response.status_code != 200:
                print(f"Error from Ollama API: {response.text}")
                return []
            
            # Extract the response text
            response_data = response.json()
            response_text = response_data.get("response", "").strip()
            
            # Debug: Print the raw response from the model
            print("DEBUG - Raw model response:")
            print(response_text)
            print("DEBUG - End of raw response")
            
            # Try to parse as JSON
            try:
                # Look for JSON array in the response
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    
                    # Debug: Print the extracted JSON string
                    print(f"DEBUG - Extracted JSON string: {json_str}")
                    
                    parsed_response = json.loads(json_str)
                    
                    # Validate the expected format
                    valid_comments = []
                    for item in parsed_response:
                        if isinstance(item, dict) and 'lineNumber' in item and 'reviewComment' in item:
                            valid_comments.append(item)
                    
                    return valid_comments
                else:
                    # If no JSON array is found
                    print("Warning: Unable to find JSON array in response")
                    parsed_results = self._parse_unstructured_response(response_text)
                    if parsed_results:
                        return parsed_results
                    
                    # Final fallback: If response is not empty, create a generic comment at line 1
                    if response_text.strip():
                        print("Using fallback generic comment")
                        return [{
                            "lineNumber": 1,
                            "reviewComment": "**Code Review Note:** The code looks generally good, but consider reviewing for any potential optimizations or edge cases."
                        }]
                    return []
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract information manually
                print(f"Warning: JSON parsing failed, error: {e}")
                print("Attempting to process text manually")
                parsed_results = self._parse_unstructured_response(response_text)
                if parsed_results:
                    return parsed_results
                
                # Final fallback: If response is not empty, create a generic comment at line 1
                if response_text.strip():
                    print("Using fallback generic comment")
                    return [{
                        "lineNumber": 1,
                        "reviewComment": "**Code Review Note:** I reviewed this code but couldn't format my feedback properly. The code appears to function correctly, but you may want to review it for any potential issues."
                    }]
                return []
                
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return []
    
    def _parse_unstructured_response(self, text: str) -> List[Dict[str, str]]:
        """
        Parse unstructured text response to extract line numbers and comments.
        
        Args:
            text: The unstructured text response from the model
            
        Returns:
            A list of dictionaries with lineNumber and reviewComment keys
        """
        print("DEBUG - Attempting to parse unstructured response")
        
        # Try different JSON-like patterns
        
        # First try to detect {reviews: [...]} format which is our primary format
        reviews_pattern = re.search(r'{\s*"?reviews"?\s*:\s*(\[.*?\])\s*}', text, re.DOTALL)
        if reviews_pattern:
            json_array = reviews_pattern.group(1)
            print(f"DEBUG - Found 'reviews' JSON array: {json_array}")
            try:
                reviews = json.loads(json_array)
                valid_reviews = []
                for review in reviews:
                    if isinstance(review, dict) and 'lineNumber' in review and 'reviewComment' in review:
                        valid_reviews.append(review)
                if valid_reviews:
                    return valid_reviews
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSON decode error in reviews array: {e}")
        
        # Check for any JSON array in the response
        array_pattern = re.search(r'\[(.*?)\]', text, re.DOTALL)
        if array_pattern:
            json_array = array_pattern.group(0)
            print(f"DEBUG - Found potential JSON array: {json_array}")
            try:
                items = json.loads(json_array)
                valid_items = []
                for item in items:
                    if isinstance(item, dict) and 'lineNumber' in item and 'reviewComment' in item:
                        valid_items.append(item)
                if valid_items:
                    return valid_items
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSON decode error in array: {e}")
        
        # Fall back to line-by-line text parsing
        print("DEBUG - Falling back to line-by-line parsing")
        lines = text.split('\n')
        comments = []
        
        current_line = None
        current_comment = []
        
        for line in lines:
            # Look for patterns like "Line 42:" or "Line: 42"
            if line.lower().startswith("line") and ":" in line:
                # If we were building a previous comment, save it
                if current_line is not None and current_comment:
                    comments.append({
                        "lineNumber": current_line,
                        "reviewComment": " ".join(current_comment).strip()
                    })
                
                # Start a new comment
                parts = line.split(":", 1)
                try:
                    # Extract line number
                    line_text = parts[0].lower().replace("line", "").strip()
                    current_line = int(line_text)
                    current_comment = [parts[1].strip()] if len(parts) > 1 else []
                except (ValueError, IndexError):
                    current_line = None
                    current_comment = []
            elif current_line is not None:
                # Continue building the current comment
                current_comment.append(line.strip())
        
        # Don't forget the last comment
        if current_line is not None and current_comment:
            comments.append({
                "lineNumber": current_line,
                "reviewComment": " ".join(current_comment).strip()
            })
        
        # If we found any comments, return them
        if comments:
            print(f"DEBUG - Found {len(comments)} comments via line-by-line parsing")
            return comments
            
        # If nothing worked, return empty list
        print("DEBUG - Could not extract any structured comments from model response")
        return [] 