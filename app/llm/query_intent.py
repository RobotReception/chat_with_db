"""
Query Intent Detection - Analyzes user question to determine intent type
"""
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class QueryIntentDetector:
    """Detects query intent from user question"""
    
    # Intent patterns
    LIST_PATTERNS = [
        r'عرض|أعرض|اعرض|عرض جميع|أظهر|أظهر جميع|show|list|display|get all',
        r'جميع|كل|all|every',
        r'ما هي|ما هم|what are|what is'
    ]
    
    AGGREGATE_PATTERNS = [
        r'كم|عدد|count|how many|total|sum|average|avg|متوسط|إجمالي',
        r'أكثر|أقل|most|least|highest|lowest|الأكثر|الأقل',
        r'أعلى|أقل|top|bottom|maximum|minimum'
    ]
    
    COMPARISON_PATTERNS = [
        r'قارن|مقارنة|compare|comparison|versus|vs|مقارنة بين',
        r'أفضل|أسوأ|better|worse|best|worst',
        r'أكثر من|أقل من|more than|less than|greater|smaller'
    ]
    
    TREND_PATTERNS = [
        r'اتجاه|اتجاهات|trend|trends|تطور|تطورات',
        r'بمرور الوقت|over time|over the years|خلال|during',
        r'نمو|انخفاض|growth|decline|increase|decrease'
    ]
    
    CORRELATION_PATTERNS = [
        r'علاقة|ارتباط|relationship|correlation|correlate',
        r'هل يؤثر|does.*affect|impact|تأثير',
        r'يرتبط|related|linked|connected'
    ]
    
    def detect(self, question: str) -> Dict[str, any]:
        """
        Detect query intent from question
        
        Returns:
            {
                "type": "list" | "aggregate" | "comparison" | "trend" | "correlation" | "unknown",
                "entities": ["film", "category", ...],
                "metrics": ["revenue", "count", ...],
                "confidence": 0.0-1.0
            }
        """
        question_lower = question.lower()
        
        # Detect intent type
        intent_type = self._detect_intent_type(question_lower)
        
        # Extract entities (table names mentioned)
        entities = self._extract_entities(question_lower)
        
        # Extract metrics
        metrics = self._extract_metrics(question_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent_type, question_lower)
        
        # Determine if statistical analysis is required
        analysis_required = intent_type in ["correlation", "comparison", "trend", "aggregate"]
        analysis_type = "statistical" if analysis_required else None
        
        result = {
            "type": intent_type,
            "entities": entities,
            "metrics": metrics,
            "confidence": confidence,
            "analysis_required": analysis_required,  # NEW: Indicates if analysis is mandatory
            "analysis_type": analysis_type  # NEW: Type of analysis needed
        }
        
        logger.info(
            f"Query intent detected",
            extra={
                "question": question[:100],
                "intent": result
            }
        )
        
        return result
    
    def _detect_intent_type(self, question: str) -> str:
        """Detect primary intent type"""
        # Check patterns in order of specificity
        if any(re.search(pattern, question, re.IGNORECASE) for pattern in self.CORRELATION_PATTERNS):
            return "correlation"
        elif any(re.search(pattern, question, re.IGNORECASE) for pattern in self.TREND_PATTERNS):
            return "trend"
        elif any(re.search(pattern, question, re.IGNORECASE) for pattern in self.COMPARISON_PATTERNS):
            return "comparison"
        elif any(re.search(pattern, question, re.IGNORECASE) for pattern in self.AGGREGATE_PATTERNS):
            return "aggregate"
        elif any(re.search(pattern, question, re.IGNORECASE) for pattern in self.LIST_PATTERNS):
            return "list"
        else:
            return "unknown"
    
    def _extract_entities(self, question: str) -> List[str]:
        """Extract entity/table names from question"""
        # Common table names in dvdrental
        known_tables = [
            'film', 'category', 'actor', 'customer', 'rental', 'payment',
            'store', 'staff', 'inventory', 'address', 'city', 'country',
            'language', 'film_actor', 'film_category'
        ]
        
        entities = []
        for table in known_tables:
            # Check for Arabic or English variations
            patterns = [
                rf'\b{table}\b',
                rf'{table}s',  # plural
                rf'{table}es',  # plural
            ]
            
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    entities.append(table)
                    break
        
        return list(set(entities))  # Remove duplicates
    
    def _extract_metrics(self, question: str) -> List[str]:
        """Extract metrics from question"""
        metrics = []
        
        metric_keywords = {
            'revenue': [r'إيراد|revenue|income|money|مبلغ'],
            'count': [r'عدد|count|number|quantity'],
            'price': [r'سعر|price|cost|تكلفة'],
            'rate': [r'معدل|rate|rating|تقييم'],
            'amount': [r'مبلغ|amount|value|قيمة']
        }
        
        for metric, patterns in metric_keywords.items():
            if any(re.search(pattern, question, re.IGNORECASE) for pattern in patterns):
                metrics.append(metric)
        
        return metrics
    
    def _calculate_confidence(self, intent_type: str, question: str) -> float:
        """Calculate confidence score"""
        if intent_type == "unknown":
            return 0.3
        
        # Count pattern matches
        pattern_counts = {
            "list": len([p for p in self.LIST_PATTERNS if re.search(p, question, re.IGNORECASE)]),
            "aggregate": len([p for p in self.AGGREGATE_PATTERNS if re.search(p, question, re.IGNORECASE)]),
            "comparison": len([p for p in self.COMPARISON_PATTERNS if re.search(p, question, re.IGNORECASE)]),
            "trend": len([p for p in self.TREND_PATTERNS if re.search(p, question, re.IGNORECASE)]),
            "correlation": len([p for p in self.CORRELATION_PATTERNS if re.search(p, question, re.IGNORECASE)])
        }
        
        matches = pattern_counts.get(intent_type, 0)
        
        # Confidence based on matches
        if matches >= 2:
            return 0.9
        elif matches == 1:
            return 0.7
        else:
            return 0.5


# Global instance
query_intent_detector = QueryIntentDetector()
