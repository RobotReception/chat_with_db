"""
Data Summary Layer - Code-based data analysis before LLM formatting
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataSummarizer:
    """Summarizes query results using code-based analysis"""
    
    def summarize(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Generate structured summary of query results
        
        Returns:
            {
                "row_count": int,
                "column_count": int,
                "has_numeric": bool,
                "has_text": bool,
                "top_values": dict,
                "numeric_stats": dict,
                "sample": list
            }
        """
        if not data:
            return {
                "row_count": 0,
                "column_count": 0,
                "has_numeric": False,
                "has_text": False,
                "top_values": {},
                "numeric_stats": {},
                "sample": []
            }
        
        # Basic stats
        row_count = len(data)
        column_count = len(data[0].keys()) if data and isinstance(data[0], dict) else 0
        
        # Analyze data types
        has_numeric = False
        has_text = False
        numeric_stats = {}
        top_values = {}
        
        if data and isinstance(data[0], dict):
            for col_name, value in data[0].items():
                if isinstance(value, (int, float)):
                    has_numeric = True
                    # Calculate stats for numeric columns
                    numeric_values = [row.get(col_name) for row in data if isinstance(row.get(col_name), (int, float))]
                    if numeric_values:
                        numeric_stats[col_name] = {
                            "min": min(numeric_values),
                            "max": max(numeric_values),
                            "sum": sum(numeric_values),
                            "avg": sum(numeric_values) / len(numeric_values) if numeric_values else 0
                        }
                elif isinstance(value, str):
                    has_text = True
                    # Get top values for text columns
                    text_values = [row.get(col_name) for row in data if row.get(col_name)]
                    if text_values:
                        from collections import Counter
                        top_values[col_name] = dict(Counter(text_values).most_common(5))
        
        # Sample (first 5 rows)
        sample = data[:5] if len(data) > 5 else data
        
        summary = {
            "row_count": row_count,
            "column_count": column_count,
            "has_numeric": has_numeric,
            "has_text": has_text,
            "top_values": top_values,
            "numeric_stats": numeric_stats,
            "sample": sample
        }
        
        logger.debug(f"Data summarized: {row_count} rows, {column_count} columns")
        
        return summary
