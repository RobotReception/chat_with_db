"""
Question Classifier - Determines if question is database-related or general
"""
from typing import Tuple, Optional
import logging

from langchain_core.prompts import ChatPromptTemplate

from app.llm.gemini_client import gemini_client

logger = logging.getLogger(__name__)


# Prompt for question classification - Professional and Accurate
QUESTION_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert question classifier specialized in database analytics. Your task is to accurately determine if a user's question requires querying a database to get specific data.

CRITICAL CLASSIFICATION RULES:

**DATABASE-RELATED (requires database query):**
A question is database-related if it:
1. Asks for SPECIFIC DATA from tables:
   - "Show me...", "List...", "Display...", "اعرض...", "أظهر..."
   - "How many...", "كم عدد...", "ما عدد..."
   - "Find...", "Search...", "ابحث عن..."
   - "What are...", "ما هي..."
   - "Which...", "أي..."

2. Asks for ANALYSIS or COMPARISON of actual data:
   - "Compare...", "قارن..."
   - "Which has more...", "أي له أكثر..."
   - "What is the relationship between...", "ما العلاقة بين..."
   - "Analyze...", "حلل..."
   - "Calculate...", "احسب..."

3. Asks for STATISTICS or AGGREGATIONS on real data:
   - "Total revenue...", "إجمالي الإيرادات..."
   - "Average...", "متوسط..."
   - "Highest...", "Lowest...", "أعلى...", "أقل..."
   - "Most...", "Least...", "الأكثر...", "الأقل..."

4. Asks about SPECIFIC RECORDS or ENTITIES:
   - "Who...", "من..."
   - "When...", "متى..."
   - "Where...", "أين..."

5. Questions about CORRELATIONS or TRENDS in data:
   - "Does X affect Y?", "هل يؤثر X على Y?"
   - "What is the trend...", "ما هو الاتجاه..."
   - "Relationship between...", "العلاقة بين..."

Examples of DATABASE-RELATED:
- "اعرض جميع الفئات"
- "كم عدد الأفلام في كل فئة؟"
- "ما هي الأفلام الأكثر إيراداً؟"
- "هل الأفلام المرتفعة السعر تحقق إيرادات أعلى؟"
- "قارن بين إيرادات الأفلام حسب الفئة"
- "ما هو متوسط سعر الإيجار للأفلام؟"

**GENERAL (does NOT require database query):**
A question is general if it:
1. Asks for CONCEPTUAL EXPLANATIONS:
   - "What is SQL?", "ما هو SQL?"
   - "How does JOIN work?", "كيف يعمل JOIN?"
   - "Explain normalization", "اشرح التطبيع"

2. Asks for BEST PRACTICES or THEORY:
   - "What are best practices...", "ما هي أفضل الممارسات..."
   - "How to optimize...", "كيفية تحسين..."

3. Asks about GENERAL KNOWLEDGE:
   - "What is Python?", "ما هو Python?"
   - "How does AI work?", "كيف يعمل الذكاء الاصطناعي?"

4. Asks for DEFINITIONS or MEANINGS:
   - "What does X mean?", "ماذا يعني X?"
   - "Define...", "عرّف..."

Examples of GENERAL:
- "ما هو الفرق بين COUNT و SUM؟"
- "كيف يعمل JOIN في SQL؟"
- "ما هي أفضل الممارسات في تحليل البيانات؟"
- "اشرح مفهوم قاعدة البيانات"

**IMPORTANT:**
- If the question asks about ACTUAL DATA VALUES → DATABASE
- If the question asks about CONCEPTS/THEORY → GENERAL
- When in doubt, classify as DATABASE if it mentions specific entities (customers, films, orders, etc.)

User Question: {question}

Analyze carefully and classify. Return ONLY "database" or "general" - no explanations."""),
    ("human", "{question}")
])


class QuestionClassifier:
    """Classifies questions as database-related or general"""
    
    def __init__(self):
        if not gemini_client.is_available():
            logger.warning("Gemini client is not available. All questions will be treated as database-related.")
            self._available = False
        else:
            self._available = True
    
    def classify(self, question: str) -> Tuple[bool, bool, Optional[str]]:
        """
        Classify question as database-related or general
        
        Returns:
            (success, is_database_related, error_message)
            is_database_related: True if database-related, False if general
        """
        if not self._available:
            # Default: assume database-related
            return True, True, None
        
        try:
            # Format prompt
            messages = QUESTION_CLASSIFICATION_PROMPT.format_messages(
                question=question
            )
            
            # Invoke Gemini
            response = gemini_client.client.invoke(messages)
            classification = response.content.strip().lower()
            
            # Parse response - more robust and professional parsing
            classification_lower = classification.lower().strip()
            
            # Remove common prefixes/suffixes
            classification_lower = classification_lower.replace("the answer is", "").replace("classification:", "").strip()
            
            # Check for explicit database indicators
            database_indicators = ["database", "db", "data query", "query data", "retrieve data", "requires database"]
            general_indicators = ["general", "concept", "explain", "theory", "definition", "conceptual"]
            
            # Count matches
            db_matches = sum(1 for indicator in database_indicators if indicator in classification_lower)
            gen_matches = sum(1 for indicator in general_indicators if indicator in classification_lower)
            
            # Determine classification with priority logic
            if db_matches > gen_matches:
                is_database_related = True
            elif gen_matches > db_matches:
                is_database_related = False
            else:
                # Check first word or exact match
                first_word = classification_lower.split()[0] if classification_lower.split() else ""
                if first_word in ["database", "db"]:
                    is_database_related = True
                elif first_word == "general":
                    is_database_related = False
                else:
                    # Default to database if unclear (safer for data queries)
                    # This ensures we try to query database rather than miss data requests
                    is_database_related = True
            
            logger.info(
                f"Question classified",
                extra={
                    "question": question[:100],
                    "is_database_related": is_database_related,
                    "classification": classification,
                    "db_matches": db_matches,
                    "gen_matches": gen_matches
                }
            )
            
            return True, is_database_related, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Question classification failed: {error_msg}",
                extra={"question": question[:100]},
                exc_info=True
            )
            # Default: assume database-related
            return True, True, f"Classification failed, defaulting to database: {error_msg}"


# Global classifier instance
question_classifier = QuestionClassifier()
