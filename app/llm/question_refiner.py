"""
Question Refinement using Gemini
Improves user questions before sending to SQL generation
"""
from typing import Optional, Tuple
import logging

from langchain_core.prompts import ChatPromptTemplate

from app.llm.gemini_client import gemini_client

logger = logging.getLogger(__name__)


# # Prompt template for question refinement
# QUESTION_REFINEMENT_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert SQL query assistant. Your task is to refine and improve user questions to make them more precise and SQL-friendly.

# You will receive:
# 1. Complete database schema (all tables and their columns)
# 2. The user's original question

# Your job is to:
# - Analyze the user's question
# - Understand what data they need
# - Refine the question to be more specific and clear
# - Make it easier to generate accurate SQL queries
# - Keep the original intent and meaning
# - Use proper terminology based on the schema

# IMPORTANT RULES:
# - Do NOT generate SQL queries
# - Only refine and improve the question
# - Keep the question in the same language as the original
# - Make it more specific if needed
# - Add context from the schema if helpful
# - Return ONLY the refined question, no explanations

# Database Schema:
# {schema_context}

# Original User Question: {original_question}

# Refine this question to be more precise and SQL-friendly:"""),
#     ("human", "{original_question}")
# ])


QUESTION_REFINEMENT_PROMPT = ChatPromptTemplate.from_messages([
(
"system",
"""
You are a SENIOR DATA ANALYST assisting a database-powered chatbot.

Your task is to rewrite the user's question into a CLEAR, PRECISE,
and DATABASE-AGNOSTIC analytical instruction written in ENGLISH.

━━━━━━━━━━━━━━━━━━━━━━
🎯 OBJECTIVE
━━━━━━━━━━━━━━━━━━━━━━

Rewrite the question so it clearly states:
- What entities or records are being analyzed
- What metrics or outcomes are being examined
- What comparison, aggregation, or grouping is required (if any)

━━━━━━━━━━━━━━━━━━━━━━
🧠 CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━

1️⃣ Output MUST be in ENGLISH  
2️⃣ Do NOT generate SQL  
3️⃣ Do NOT mention column names unless explicitly stated by the user  
4️⃣ Do NOT assume how metrics are calculated  
5️⃣ Do NOT define thresholds (e.g., averages, ranges, percentiles)  
6️⃣ Do NOT ask follow-up questions  
7️⃣ Preserve the original intent EXACTLY  
8️⃣ If the question is analytical:
    - Rewrite it as a DATA ANALYSIS INSTRUCTION
    - NOT as a yes/no question

━━━━━━━━━━━━━━━━━━━━━━
📌 EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━

User: "هل الأفلام مرتفعة السعر تحقق إيرادات أعلى؟"
Rewrite as:
"Compare total revenue between higher-priced items and lower-priced items."

User: "ما هي المنتجات الأكثر مبيعًا؟"
Rewrite as:
"List items ordered by total sales volume from highest to lowest."

━━━━━━━━━━━━━━━━━━━━━━
📚 DATABASE SCHEMA (FOR CONTEXT ONLY)
━━━━━━━━━━━━━━━━━━━━━━
{schema_context}

━━━━━━━━━━━━━━━━━━━━━━
❓ ORIGINAL QUESTION
━━━━━━━━━━━━━━━━━━━━━━
{original_question}

━━━━━━━━━━━━━━━━━━━━━━
✍️ OUTPUT
━━━━━━━━━━━━━━━━━━━━━━

Return ONLY the rewritten question in ENGLISH.
"""
),
("human", "{original_question}")
])



class QuestionRefiner:
    """Refines user questions using Gemini before SQL generation"""
    
    def __init__(self):
        if not gemini_client.is_available():
            logger.warning("Gemini client is not available. Question refinement will be skipped.")
            self._available = False
        else:
            self._available = True
    
    def refine(self, original_question: str, schema_context: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Refine user question using Gemini
        
        Args:
            original_question: User's original question
            schema_context: Complete database schema (tables + columns)
        
        Returns:
            (success, refined_question, error_message)
        """
        if not self._available:
            # If Gemini is not available, return original question
            logger.info("Gemini not available, using original question")
            return True, original_question, None
        
        try:
            # Format prompt
            messages = QUESTION_REFINEMENT_PROMPT.format_messages(
                schema_context=schema_context,
                original_question=original_question
            )
            
            # Invoke Gemini
            response = gemini_client.client.invoke(messages)
            refined_question = response.content.strip()
            
            # Clean up the response (remove any extra text)
            refined_question = self._clean_response(refined_question)
            
            logger.info(
                f"Question refined successfully",
                extra={
                    "original": original_question[:100],
                    "refined": refined_question[:100]
                }
            )
            
            return True, refined_question, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Question refinement failed: {error_msg}",
                extra={"original_question": original_question[:100]},
                exc_info=True
            )
            # Fallback: return original question
            return True, original_question, f"Refinement failed, using original: {error_msg}"
    
    def _clean_response(self, text: str) -> str:
        """Clean Gemini response to extract only the refined question"""
        # Remove common prefixes
        prefixes = [
            "Refined question:",
            "Improved question:",
            "Here's the refined question:",
            "The refined question is:",
        ]
        
        text = text.strip()
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        
        # Remove quotes if present
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        
        # Take first line if multiple lines (usually the refined question is first)
        lines = text.split('\n')
        if len(lines) > 1:
            # Check if first line looks like a question
            first_line = lines[0].strip()
            if any(q in first_line for q in ['?', 'what', 'how', 'show', 'list', 'find', 'get', 'كم', 'ما', 'ماذا']):
                text = first_line
        
        return text.strip()


# Global refiner instance
question_refiner = QuestionRefiner()
