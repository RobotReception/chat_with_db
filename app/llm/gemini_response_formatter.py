"""
Gemini Response Formatter - Formats SQL results into professional responses
"""
from typing import Optional, Tuple, Dict, Any, List
import logging
import json

from langchain_core.prompts import ChatPromptTemplate

from app.llm.gemini_client import gemini_client
from app.utils.data_summarizer import DataSummarizer
from app.utils.json_sanitizer import sanitize_for_json
import re

logger = logging.getLogger(__name__)


# Prompt template for professional response formatting
RESPONSE_FORMATTING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert data analyst assistant. Your task is to format database query results into professional, user-friendly responses.

You will receive:
1. The user's original question (in their language)
2. The SQL query that was executed
3. A SAMPLE of the query results (first 10 rows) - to understand data structure

Your job is to:
- Analyze the user's question and understand their intent
- Format the response professionally in the SAME LANGUAGE as the user's question
- If the user asked for a list/table, present ALL data clearly
- If the user asked for statistics/summary, provide a clear summary
- Detect if the user wants to visualize data (charts, graphs, plots) - return true/false
- If user asks for "رسم بياني", "مخطط", "chart", "graph", "visualization", "plot" → set needs_visualization=true
- Be very attentive to visualization requests - if user explicitly asks for a chart/graph, ALWAYS set needs_visualization=true
- Return data in a structured format (array or dictionary)
- Make the response clear, professional, and helpful

CRITICAL SECURITY RULES - MUST FOLLOW STRICTLY:
- ⚠️ NEVER mention database table names (e.g., "customer", "payment", "product", "order")
- ⚠️ NEVER mention column names (e.g., "customer_id", "amount", "price", "total")
- ⚠️ NEVER mention database structure, schema, or technical details
- ✅ Use generic business terms instead:
  * "العملاء" / "clients" instead of "customer table"
  * "المدفوعات" / "payments" instead of "payment table"  
  * "المبلغ" / "amount" instead of "amount column"
  * "رقم العميل" / "client number" instead of "customer_id"
- ✅ Focus on the data content and business meaning, NOT technical database terminology
- ✅ The response should read naturally as if talking about business insights, NOT database structure
- ✅ If you see table/column names in the SQL query or data, translate them to business terms in your response

IMPORTANT:
- Preserve the original language of the user's question
- Be concise and answer the question directly
- Do NOT add statistical/analysis boilerplate unless the user explicitly asked for analysis, statistics, insights, trends, comparison, or visualization
- The "response" MUST be short (1-3 sentences) and MUST NOT include:
  - Markdown tables
  - Code fences (```), JSON blocks, or raw JSON
  - Full lists of rows/records
  - Table names or column names
- If the user asked to "show/list/display" results, acknowledge and summarize briefly.
  The actual records will be returned separately in the API response (data/download), not inside "response".
- You will receive a SAMPLE of the data (first 10 rows) to understand the structure
- The complete dataset will be available in the API response
- Format numbers and dates clearly
- Use appropriate formatting for tables/lists
- Note: The sample shown is just for understanding structure - mention total count if different

User's Question: {user_question}

SQL Query Executed: {sql_query}

Query Results (JSON):
{query_results}

{statistical_insights}

Analyze the question and format a professional response. Also determine if the user wants data visualization.

VISUALIZATION DETECTION:
- If user asks for "رسم بياني", "مخطط", "chart", "graph", "visualize", "plot" → needs_visualization MUST be true
- If user asks about "أعلى", "top", "ranking", "مقارنة", "comparison" with data → consider needs_visualization=true
- visualization_type should be "bar" for rankings/comparisons, "line" for trends, "scatter" for correlations

If statistical insights are provided, incorporate them naturally into your response."""),
    ("human", """Please provide your response as a valid JSON object with these exact keys:
- "response": professional response text in the user's language (brief, 1-3 sentences)
- "data": the data as an array or object
- "needs_visualization": true if user asked for chart/graph/visualization, false otherwise
- "visualization_type": "bar" for rankings/comparisons, "line" for trends, "scatter" for correlations, "chart" for general, or "none"

IMPORTANT: If user explicitly asked for "رسم بياني" or "chart" or "graph", you MUST set needs_visualization=true and choose appropriate visualization_type.

Return ONLY valid JSON, no additional text.""")
])


class GeminiResponseFormatter:
    """Formats SQL results into professional responses using Gemini"""
    
    def __init__(self):
        if not gemini_client.is_available():
            logger.warning("Gemini client is not available. Response formatting will be skipped.")
            self._available = False
        else:
            self._available = True
        
        self.data_summarizer = DataSummarizer()
    
    def format_response(
        self, 
        user_question: str, 
        sql_query: str, 
        query_results: List[Dict],
        statistical_analysis: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Format query results into professional response
        
        Args:
            user_question: Original user question
            sql_query: SQL query that was executed
            query_results: Complete query results as list of dicts
        
        Returns:
            (success, formatted_response, error_message)
            formatted_response contains:
                - response: Professional text response
                - data: Formatted data (array or dict)
                - needs_visualization: bool
                - visualization_type: str
        """
        if not self._available:
            # Fallback: return simple format
            return self._fallback_format(user_question, sql_query, query_results)
        
        try:
            # Step 1: Generate code-based summary (reduces hallucination)
            data_summary = self.data_summarizer.summarize(query_results)
            
            # Step 2: Send only a sample to Gemini (first 5-10 rows) to avoid overloading
            # But keep all data for API response
            sample_size = min(10, len(query_results)) if query_results else 0
            sample_data = query_results[:sample_size] if query_results else []
            
            # Format sample results as JSON string for Gemini
            sample_json = json.dumps(
                sanitize_for_json(sample_data),
                ensure_ascii=False,
                indent=2
            )
            
            # Combine summary + sample for Gemini
            summary_text = f"""Data Summary:
- Total rows: {data_summary['row_count']}
- Columns: {data_summary['column_count']}
- Has numeric data: {data_summary['has_numeric']}
- Has text data: {data_summary['has_text']}
"""
            if data_summary.get('numeric_stats'):
                summary_text += f"\nNumeric Statistics:\n{json.dumps(sanitize_for_json(data_summary['numeric_stats']), indent=2)}"
            if data_summary.get('top_values'):
                summary_text += f"\nTop Values:\n{json.dumps(sanitize_for_json(data_summary['top_values']), indent=2)}"
            
            if len(query_results) > sample_size:
                sample_info = f"{summary_text}\n\nSample Data ({sample_size} of {len(query_results)} rows):\n{sample_json}"
            else:
                sample_info = f"{summary_text}\n\nData:\n{sample_json}"
            
            # Prepare statistical insights text
            insights_text = ""
            if statistical_analysis and statistical_analysis.get("has_analysis"):
                insights_text = f"\n\nStatistical Analysis:\n{statistical_analysis.get('interpretation', '')}\n"
                if statistical_analysis.get("statistical_result"):
                    insights_text += f"Results: {json.dumps(sanitize_for_json(statistical_analysis['statistical_result']), indent=2)}"
            
            # Format prompt with sample data + insights
            messages = RESPONSE_FORMATTING_PROMPT.format_messages(
                user_question=user_question,
                sql_query=sql_query,
                query_results=sample_info,
                statistical_insights=insights_text
            )
            
            # Invoke Gemini
            response = gemini_client.client.invoke(messages)
            response_text = response.content.strip()
            
            # Parse JSON response
            formatted_response = self._parse_response(response_text)
            formatted_response = self._enforce_concise_response(
                formatted_response=formatted_response,
                user_question=user_question,
                sql_query=sql_query,
                query_results=query_results,
                data_summary=data_summary,
            )
            
            # Add complete data to response (not just sample)
            formatted_response["data"] = query_results  # All data, not just sample
            
            logger.info(
                f"Response formatted successfully",
                extra={
                    "question": user_question[:100],
                    "needs_visualization": formatted_response.get("needs_visualization", False),
                    "total_rows": len(query_results),
                    "sample_sent_to_gemini": sample_size
                }
            )
            
            return True, formatted_response, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Response formatting failed: {error_msg}",
                extra={"question": user_question[:100]},
                exc_info=True
            )
            # Fallback to simple format
            return self._fallback_format(user_question, sql_query, query_results)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response and extract JSON"""
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        text = response_text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Try to find JSON object
        try:
            # Find JSON object boundaries
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, try to extract parts manually
        # If it looks like JSON but is malformed/truncated, try to extract "response" field.
        extracted = self._extract_response_field(text)
        if extracted:
            return {
                "response": extracted,
                "data": [],
                "needs_visualization": False,
                "visualization_type": "none",
            }
        return self._extract_manual(response_text)

    def _extract_response_field(self, text: str) -> Optional[str]:
        """
        Best-effort extraction of the "response" string from a JSON-like payload.
        Handles cases where the model returns a JSON object but it's not valid JSON.
        """
        if not text:
            return None
        # Look for: "response": "...."
        m = re.search(r'"response"\s*:\s*"(.*?)"\s*,\s*"(data|needs_visualization|visualization_type)"', text, re.DOTALL)
        if not m:
            m = re.search(r'"response"\s*:\s*"(.*?)"\s*[,}]', text, re.DOTALL)
        if not m:
            return None
        raw = m.group(1)
        # Unescape common JSON escapes safely
        try:
            return json.loads(f"\"{raw}\"")
        except Exception:
            return raw.replace("\\n", "\n").replace("\\t", "\t").strip()

    def _enforce_concise_response(
        self,
        formatted_response: Dict[str, Any],
        user_question: str,
        sql_query: str,
        query_results: List[Dict],
        data_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Hard guardrail: never return large JSON/tables/code blocks in the "response" field.
        If the model output violates constraints, replace with a concise, professional summary.
        """
        resp = (formatted_response.get("response") or "").strip()

        def _looks_like_payload(s: str) -> bool:
            if not s:
                return False
            if "```" in s:
                return True
            if s.lstrip().startswith("{") and ("\"data\"" in s or "\"response\"" in s):
                return True
            # markdown table
            if "|" in s and "\n|" in s:
                return True
            return False

        too_long = len(resp) > 400
        if _looks_like_payload(resp) or too_long:
            row_count = data_summary.get("row_count", len(query_results))
            # Try to mention a top value if present
            top_hint = ""
            if query_results and isinstance(query_results[0], dict):
                # pick a likely numeric metric
                metric_key = None
                for k in ["total", "amount", "total_payments", "count", "sum", "avg", "max"]:
                    if any(k in col.lower() for col in query_results[0].keys()):
                        metric_key = next(col for col in query_results[0].keys() if k in col.lower())
                        break
                if metric_key and metric_key in query_results[0]:
                    top_hint = f" أعلى نتيجة في الصف الأول: {metric_key}={query_results[0].get(metric_key)}."

            formatted_response["response"] = (
                f"تم تنفيذ الاستعلام بنجاح وإرجاع {row_count} صف."
                f"{top_hint}"
                f" يمكنك عرض التفاصيل في حقل data أو تنزيلها عبر export_to_excel."
            )
        return formatted_response
    
    def _extract_manual(self, text: str) -> Dict[str, Any]:
        """Manually extract response components if JSON parsing fails"""
        result = {
            "response": text,
            "data": [],
            "needs_visualization": False,
            "visualization_type": "none"
        }
        
        # Check for visualization keywords
        viz_keywords = ["رسم", "مخطط", "رسم بياني", "chart", "graph", "plot", "visualize", "diagram"]
        text_lower = text.lower()
        result["needs_visualization"] = any(keyword in text_lower for keyword in viz_keywords)
        
        if result["needs_visualization"]:
            if any(kw in text_lower for kw in ["chart", "رسم بياني", "مخطط"]):
                result["visualization_type"] = "chart"
            elif any(kw in text_lower for kw in ["graph", "رسم"]):
                result["visualization_type"] = "graph"
            elif any(kw in text_lower for kw in ["table", "جدول"]):
                result["visualization_type"] = "table"
        
        return result
    
    def _fallback_format(
        self, 
        user_question: str, 
        sql_query: str, 
        query_results: List[Dict]
    ) -> Tuple[bool, Dict[str, Any], None]:
        """Fallback formatting when Gemini is not available"""
        # Simple text response
        if not query_results:
            response_text = "لا توجد نتائج."
        elif len(query_results) == 1:
            response_text = f"النتيجة: {query_results[0]}"
        else:
            response_text = f"تم العثور على {len(query_results)} نتيجة."
        
        # Check for visualization needs
        question_lower = user_question.lower()
        viz_keywords = ["رسم", "مخطط", "رسم بياني", "chart", "graph", "plot", "visualize"]
        needs_viz = any(keyword in question_lower for keyword in viz_keywords)
        
        return True, {
            "response": response_text,
            "data": query_results,
            "needs_visualization": needs_viz,
            "visualization_type": "chart" if needs_viz else "none"
        }, None


# Global formatter instance
response_formatter = GeminiResponseFormatter()
