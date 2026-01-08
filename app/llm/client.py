"""
LLM Client - OpenAI Integration
"""
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Manages LLM client instances"""
    
    def __init__(self):
        self._client: Optional[BaseChatModel] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize LLM client"""
        # Support both OPENAI_API_KEY and API_KEY_OPENAI
        api_key = settings.OPENAI_API_KEY or settings.API_KEY_OPENAI
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. LLM features will not work.")
            return
        
        self._client = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=api_key,
        )
        
        logger.info(f"LLM client initialized with model: {settings.LLM_MODEL}")
    
    @property
    def client(self) -> Optional[BaseChatModel]:
        """Get LLM client instance"""
        return self._client
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        return self._client is not None


# Global LLM client instance
llm_client = LLMClient()
