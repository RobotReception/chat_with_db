"""
General Question Handler - Handles non-database questions using Gemini
"""
from typing import Optional, Tuple
import logging

from langchain_core.prompts import ChatPromptTemplate

from app.llm.gemini_client import gemini_client

logger = logging.getLogger(__name__)


# Prompt for general questions - Specialized in Database Analytics
GENERAL_QUESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """أنت مساعد ذكي متخصص في التحليلات والإحصائيات من قاعدة البيانات. أنت جزء من نظام ذكي للاستعلام عن قاعدة البيانات PostgreSQL.

هويتك واختصاصك:
- أنت مساعد متخصص في التحليلات والإحصائيات من قاعدة البيانات
- تقدم إجابات احترافية حول:
  * مفاهيم قواعد البيانات والتحليلات
  * SQL والاستعلامات
  * الإحصائيات والتحليلات
  * أفضل الممارسات في تحليل البيانات
  * تفسير النتائج الإحصائية
- تجيب بنفس لغة المستخدم (عربي/إنجليزي)
- تكون احترافي ودقيق ومفيد

نطاق اختصاصك:
- أسئلة حول قواعد البيانات والتحليلات
- أسئلة حول SQL والاستعلامات
- أسئلة حول الإحصائيات والتحليلات
- أسئلة حول تفسير البيانات
- أسئلة حول أفضل الممارسات في تحليل البيانات

إذا كان السؤال خارج نطاق اختصاصك (مثل: أسئلة عامة عن العلوم، التاريخ، الثقافة العامة):
- اذكر أنك متخصص في التحليلات والإحصائيات من قاعدة البيانات
- اقترح على المستخدم أن يسأل عن البيانات والتحليلات بدلاً من ذلك
- كن مهذباً واحترافياً

User Question: {question}

قدم إجابة احترافية ومتخصصة في مجال التحليلات والإحصائيات من قاعدة البيانات."""),
    ("human", "{question}")
])


class GeneralQuestionHandler:
    """Handles general (non-database) questions using Gemini"""
    
    def __init__(self):
        if not gemini_client.is_available():
            logger.warning("Gemini client is not available. General questions cannot be handled.")
            self._available = False
        else:
            self._available = True
    
    def handle(self, question: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Handle general question
        
        Returns:
            (success, answer, error_message)
        """
        if not self._available:
            return False, None, "Gemini client is not available"
        
        try:
            # Format prompt
            messages = GENERAL_QUESTION_PROMPT.format_messages(
                question=question
            )
            
            # Invoke Gemini
            response = gemini_client.client.invoke(messages)
            answer = response.content.strip()
            
            logger.info(
                f"General question answered",
                extra={
                    "question": question[:100],
                    "answer_length": len(answer)
                }
            )
            
            return True, answer, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"General question handling failed: {error_msg}",
                extra={"question": question[:100]},
                exc_info=True
            )
            return False, None, error_msg


# Global handler instance
general_question_handler = GeneralQuestionHandler()
