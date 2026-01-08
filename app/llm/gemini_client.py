"""
Gemini Client - Google Gemini Integration for Question Refinement
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Manages Gemini client instances for question refinement"""
    
    def __init__(self):
        self._client: Optional[BaseChatModel] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Gemini client"""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Question refinement will not work.")
            return
        
        try:
            self._client = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                google_api_key=settings.GEMINI_API_KEY,
                # langchain-google-genai currently does not support SystemMessage in some versions.
                # This converts the leading SystemMessage to HumanMessage automatically.
                convert_system_message_to_human=True,
            )
            
            logger.info(f"Gemini client initialized with model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self._client = None
    
    @property
    def client(self) -> Optional[BaseChatModel]:
        """Get Gemini client instance"""
        return self._client
    
    def is_available(self) -> bool:
        """Check if Gemini is available"""
        return self._client is not None


# Global Gemini client instance
gemini_client = GeminiClient()
