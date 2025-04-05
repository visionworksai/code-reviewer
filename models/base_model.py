from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAIModel(ABC):
    """
    Abstract base class that defines the interface for all AI models.
    
    All AI model implementations (Gemini, OpenAI, etc.) should inherit from this
    class and implement the required methods.
    """
    
    @abstractmethod
    def configure(self):
        """
        Configure the AI model client with appropriate API keys and settings.
        
        Each specific model implementation will handle its own API configuration.
        """
        pass
    
    @abstractmethod
    def get_response_from_model(self, prompt: str) -> List[Dict[str, str]]:
        """
        Send prompt to AI model and get structured response for code review.
        
        Args:
            prompt: A string containing the code review prompt
            
        Returns:
            A list of dictionaries with lineNumber and reviewComment keys
        """
        pass 