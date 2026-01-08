"""
Chat Service - Orchestrates the entire chat flow
"""
from typing import Optional, Dict, Any
import logging

from app.rag.retriever import schema_retriever
from app.rag.schema_store import schema_store
from app.llm.chains import SQLGenerationChain, AnswerSummarizationChain
from app.llm.question_refiner import question_refiner
from app.llm.gemini_response_formatter import response_formatter
from app.llm.question_classifier import question_classifier
from app.llm.general_question_handler import general_question_handler
from app.llm.query_intent import query_intent_detector
from app.llm.sensitive_question_detector import sensitive_question_detector
from app.services.statistical_analysis import statistical_analysis_service
from app.services.visualization_service import visualization_service
from app.db.executor import sql_executor
from app.utils.error_messages import get_professional_error_message
from app.config import settings

logger = logging.getLogger(__name__)


class ChatService:
    """Main service for handling chat requests"""
    
    def __init__(self):
        try:
            self.sql_chain = SQLGenerationChain()
            self.summarization_chain = AnswerSummarizationChain()
        except ValueError as e:
            logger.warning(f"LLM chains not initialized: {e}")
            self.sql_chain = None
            self.summarization_chain = None
    
    def handle_question(self, question: str) -> Dict[str, Any]:
        """
        Handle a user question and return answer
        
        Flow:
        1. Get complete database schema (all tables and columns)
        2. Refine question using Gemini (with complete schema)
        3. Retrieve relevant schema context (RAG - top_k)
        4. Generate SQL query (LLM - using refined question)
        5. Validate SQL (Security)
        6. Execute SQL (DAL) - returns data as table/array
        7. Format response using Gemini (professional formatting with data structure)
        
        Returns:
            {
                "success": bool,
                "answer": str,  # Professional response in user's language
                "sql_query": str,
                "data": list/dict,  # Structured data (array or dictionary)
                "needs_visualization": bool,  # True if user wants charts/graphs
                "visualization_type": str,  # chart/graph/table/none
                "error": Optional[str],
                "metadata": Dict
            }
        """
        if not self.sql_chain or not self.summarization_chain:
            return {
                "success": False,
                "answer": None,
                "sql_query": None,
                "error": "LLM service is not available. Please configure OPENAI_API_KEY.",
                "metadata": {}
            }
        
        metadata = {
            "question": question,
            "steps": []
        }
        
        try:
            # Step 0: Check if question is asking for sensitive information
            logger.info(f"Processing question: {question[:100]}")
            is_sensitive, sensitive_reason = sensitive_question_detector.check(question)
            
            if is_sensitive:
                logger.warning(
                    f"Sensitive question detected",
                    extra={
                        "question": question[:100],
                        "reason": sensitive_reason
                    }
                )
                metadata["steps"].append("sensitive_question_detected")
                return {
                    "success": False,
                    "answer": sensitive_reason,
                    "sql_query": None,
                    "data": None,
                    "needs_visualization": False,
                    "visualization_type": "none",
                    "is_database_related": True,
                    "error": sensitive_reason,
                    "metadata": metadata
                }
            
            metadata["steps"].append("sensitive_check_passed")
            
            # Step 1: Classify question (database-related or general)
            classify_success, is_database_related, classify_error = question_classifier.classify(question)
            
            metadata["steps"].append("question_classified")
            metadata["is_database_related"] = is_database_related
            
            # If general question, handle it directly with Gemini
            if not is_database_related:
                logger.info("Question is general, handling with Gemini")
                handle_success, answer, handle_error = general_question_handler.handle(question)
                
                if handle_success:
                    metadata["steps"].append("general_question_answered")
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": None,
                        "data": None,
                        "needs_visualization": False,
                        "visualization_type": "none",
                        "is_database_related": False,
                        "error": None,
                        "metadata": metadata
                    }
                else:
                    return {
                        "success": False,
                        "answer": None,
                        "sql_query": None,
                        "error": f"Failed to handle general question: {handle_error}",
                        "metadata": metadata
                    }
            
            # Step 1: Get complete schema context (all tables and columns)
            # Clear cache to ensure fresh data
            schema_store.clear_cache()
            # Get complete schema (all tables, not just top_k)
            complete_schema_context = schema_store.get_schema_context()
            metadata["steps"].append("schema_retrieved")
            
            # Step 2: Refine question using Gemini (with complete schema)
            refine_success, refined_question, refine_error = question_refiner.refine(
                question,
                complete_schema_context
            )
            
            if refine_success and refined_question:
                logger.info(f"Question refined: {question[:50]} -> {refined_question[:50]}")
                metadata["original_question"] = question
                metadata["refined_question"] = refined_question
                question_to_use = refined_question
            else:
                logger.warning(f"Question refinement failed, using original: {refine_error}")
                question_to_use = question
            
            metadata["steps"].append("question_refined")
            
            # Step 3: Detect query intent (for better SQL generation)
            intent = query_intent_detector.detect(question_to_use)
            metadata["query_intent"] = intent
            metadata["steps"].append("intent_detected")
            
            # Step 4: Retrieve relevant schema for SQL generation (top_k for efficiency)
            # Note: Full schema is already cached from Step 1, RAG uses cached embeddings
            relevant_schema_context = schema_retriever.retrieve(
                question_to_use, 
                top_k=settings.RAG_TOP_K
            )
            
            # Step 5: Generate SQL using refined question + intent
            # Enhance schema context with intent information
            enhanced_schema_context = self._enhance_schema_with_intent(
                relevant_schema_context,
                intent
            )
            
            sql_success, sql_query, sql_error = self.sql_chain.generate(
                question_to_use, 
                enhanced_schema_context
            )
            
            if not sql_success:
                # Generate professional error message
                error_message = get_professional_error_message(
                    question=question,
                    error_type="sql_generation",
                    technical_error=sql_error
                )
                
                logger.warning(
                    f"SQL generation failed",
                    extra={
                        "question": question[:100],
                        "technical_error": sql_error
                    }
                )
                
                return {
                    "success": False,
                    "answer": error_message,
                    "sql_query": None,
                    "data": None,
                    "needs_visualization": False,
                    "visualization_type": "none",
                    "is_database_related": True,
                    "error": error_message,
                    "metadata": metadata
                }
            
            metadata["steps"].append("sql_generated")
            metadata["sql_query"] = sql_query
            
            # Step 5 & 6: Execute SQL (validation happens inside executor)
            exec_success, data, exec_error = sql_executor.execute(sql_query)
            
            if not exec_success:
                # Determine error type
                error_type = "incomplete_query" if "incomplete" in str(exec_error).lower() else "sql_execution"
                
                # Generate professional error message
                error_message = get_professional_error_message(
                    question=question,
                    error_type=error_type,
                    technical_error=exec_error
                )
                
                logger.warning(
                    f"SQL execution failed",
                    extra={
                        "question": question[:100],
                        "sql_query": sql_query[:200] if sql_query else None,
                        "technical_error": exec_error
                    }
                )
                
                return {
                    "success": False,
                    "answer": error_message,
                    "sql_query": sql_query,
                    "data": None,
                    "needs_visualization": False,
                    "visualization_type": "none",
                    "is_database_related": True,
                    "error": error_message,
                    "metadata": metadata
                }
            
            metadata["steps"].append("sql_executed")
            metadata["rows_returned"] = len(data) if data else 0
            
            # Step 7: Statistical Analysis (NEW - Convert data to insights)
            statistical_analysis = statistical_analysis_service.analyze(
                data=data or [],
                intent=intent,
                question=question
            )
            
            metadata["statistical_analysis"] = statistical_analysis
            metadata["steps"].append("statistical_analysis")
            
            # Step 8: Format response using Gemini (professional formatting with insights)
            # Send complete data + statistical analysis to Gemini for professional response
            format_success, formatted_response, format_error = response_formatter.format_response(
                user_question=question,  # Original question in user's language
                sql_query=sql_query,
                query_results=data or [],
                statistical_analysis=statistical_analysis  # NEW: Include insights
            )
            
            if format_success and formatted_response:
                # Use Gemini formatted response
                answer = formatted_response.get("response", "")
                formatted_data = formatted_response.get("data", data or [])
                needs_visualization = formatted_response.get("needs_visualization", False)
                visualization_type = formatted_response.get("visualization_type", "none")
                
                metadata["steps"].append("response_formatted")
                metadata["needs_visualization"] = needs_visualization
                metadata["visualization_type"] = visualization_type
                
                # If user/LLM explicitly requested visualization, use the suggested type
                # or determine best type based on data and intent
                if needs_visualization:
                    if statistical_analysis.get("has_analysis"):
                        suggested_viz = statistical_analysis.get("visualization_type", "none")
                        metadata["suggested_visualization_type"] = suggested_viz
                        # Use suggested type if it's valid, otherwise use LLM's choice
                        if suggested_viz != "none" and suggested_viz:
                            visualization_type = suggested_viz
                    
                    # If visualization_type is still generic "chart", determine specific type
                    if visualization_type in ["chart", "graph", "none"]:
                        # Determine best chart type based on intent and data
                        if intent.get("type") in ["aggregate", "comparison"] or "top" in question.lower() or "أعلى" in question.lower():
                            visualization_type = "bar"
                        elif intent.get("type") == "trend":
                            visualization_type = "line"
                        else:
                            visualization_type = "bar"  # Default to bar for rankings
                else:
                    # Check if user explicitly asked for chart but LLM didn't detect it
                    chart_keywords = ["رسم بياني", "مخطط", "chart", "graph", "visualize", "plot"]
                    if any(keyword in question.lower() for keyword in chart_keywords):
                        needs_visualization = True
                        visualization_type = "bar"  # Default for rankings/top N
                        logger.info(f"User explicitly requested chart, enabling visualization")
                
                # Generate chart if visualization is needed (NEW - PandasAI)
                chart_result = None
                if needs_visualization and visualization_type != "none" and visualization_type != "table":
                    chart_result = visualization_service.generate_chart(
                        data=data or [],
                        visualization_type=visualization_type,
                        intent=intent,
                        statistical_insights=statistical_analysis.get("statistical_result", {})
                    )
                    
                    if chart_result.get("success"):
                        metadata["chart_generated"] = True
                        metadata["chart_type"] = visualization_type
                        metadata["chart_url"] = chart_result.get("chart", {}).get("url")
                    else:
                        logger.warning(
                            f"Chart generation failed: {chart_result.get('error')}",
                            extra={"visualization_type": visualization_type}
                        )
                
                # Only include statistical interpretation in the answer if the user asked for analysis/statistics/visualization.
                if self._user_requested_analysis(question) and statistical_analysis.get("has_analysis") and statistical_analysis.get("interpretation"):
                    insight = statistical_analysis["interpretation"]
                    answer = f"{insight}\n\n{answer}"
                
                return {
                    "success": True,
                    "answer": answer,
                    "sql_query": sql_query if settings.SHOW_SQL_TO_USER else None,
                    "data": formatted_data,  # Structured data (array or dict)
                    "needs_visualization": needs_visualization,
                    "visualization_type": visualization_type,
                    "statistical_insights": statistical_analysis.get("statistical_result", {}),
                    "chart": chart_result.get("chart") if chart_result and chart_result.get("success") else None,  # NEW
                    "is_database_related": True,
                    "error": None,
                    "metadata": metadata
                }
            else:
                # Fallback: Use traditional summarization
                logger.warning(f"Gemini formatting failed, using fallback: {format_error}")
                summary_success, answer, summary_error = self.summarization_chain.summarize(
                    question,
                    sql_query,
                    data or []
                )
                
                if not summary_success:
                    answer = f"Query executed successfully. Results: {data}"
                    logger.warning(f"Summarization failed, using fallback: {summary_error}")
                
                # Use statistical analysis visualization suggestion if available
                if statistical_analysis.get("has_analysis"):
                    suggested_viz = statistical_analysis.get("visualization_type", "none")
                    metadata["suggested_visualization_type"] = suggested_viz
                    if needs_visualization:
                        visualization_type = suggested_viz
                else:
                    # Fallback: Check for visualization needs (simple keyword detection)
                    question_lower = question.lower()
                    viz_keywords = ["رسم", "مخطط", "رسم بياني", "chart", "graph", "plot", "visualize", "diagram"]
                    needs_visualization = any(keyword in question_lower for keyword in viz_keywords)
                    visualization_type = "chart" if needs_visualization else "none"
                
                # Generate chart if visualization is needed (NEW - PandasAI)
                chart_result = None
                if needs_visualization and visualization_type != "none" and visualization_type != "table":
                    chart_result = visualization_service.generate_chart(
                        data=data or [],
                        visualization_type=visualization_type,
                        intent=intent,
                        statistical_insights=statistical_analysis.get("statistical_result", {})
                    )
                    
                    if chart_result.get("success"):
                        metadata["chart_generated"] = True
                        metadata["chart_type"] = visualization_type
                        metadata["chart_url"] = chart_result.get("chart", {}).get("url")
                    else:
                        logger.warning(
                            f"Chart generation failed: {chart_result.get('error')}",
                            extra={"visualization_type": visualization_type}
                        )
                
                # Only include statistical interpretation in the answer if the user asked for analysis/statistics/visualization.
                if self._user_requested_analysis(question) and statistical_analysis.get("has_analysis") and statistical_analysis.get("interpretation"):
                    insight = statistical_analysis["interpretation"]
                    answer = f"{insight}\n\n{answer}"
                
                metadata["steps"].append("answer_generated")
                metadata["needs_visualization"] = needs_visualization
                metadata["visualization_type"] = visualization_type
                
                return {
                    "success": True,
                    "answer": answer,
                    "sql_query": sql_query if settings.SHOW_SQL_TO_USER else None,
                    "data": data or [],  # Raw data as fallback
                    "needs_visualization": needs_visualization,
                    "visualization_type": visualization_type,
                    "statistical_insights": statistical_analysis.get("statistical_result", {}),
                    "chart": chart_result.get("chart") if chart_result and chart_result.get("success") else None,  # NEW
                    "is_database_related": True,
                    "error": None,
                    "metadata": metadata
                }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Chat service error: {error_msg}",
                extra={"question": question[:100]},
                exc_info=True
            )
            
            # Generate professional error message
            error_message = get_professional_error_message(
                question=question,
                error_type="general_error",
                technical_error=error_msg
            )
            
            return {
                "success": False,
                "answer": error_message,
                "sql_query": None,
                "data": None,
                "needs_visualization": False,
                "visualization_type": "none",
                "is_database_related": True,
                "error": error_message,
                "metadata": metadata
            }
    
    def _user_requested_analysis(self, question: str) -> bool:
        """
        Heuristic: only show statistical interpretation in the answer when user asked for it explicitly.
        """
        q = (question or "").lower()
        keywords = [
            # Arabic
            "تحليل", "إحصائ", "احصائ", "مقارنة", "اتجاه", "ترند", "ارتباط", "علاقة",
            "رسم", "مخطط", "رسم بياني", "بياني", "visual",
            # English
            "analysis", "statistics", "statistical", "compare", "comparison", "trend", "correlation",
            "chart", "graph", "plot", "visualize", "visualisation", "visualization",
        ]
        return any(k in q for k in keywords)

    def _enhance_schema_with_intent(self, schema_context: str, intent: Dict) -> str:
        """
        Enhance schema context with intent information for better SQL generation
        """
        intent_hint = f"\n\nQuery Intent: {intent['type']}"
        if intent.get('entities'):
            intent_hint += f"\nRelevant Entities: {', '.join(intent['entities'])}"
        if intent.get('metrics'):
            intent_hint += f"\nRequested Metrics: {', '.join(intent['metrics'])}"
        
        return schema_context + intent_hint
    
    def _determine_visualization(self, data: list, intent: Dict, llm_suggestion: bool) -> tuple[bool, str]:
        """
        Determine visualization needs using code-based logic + LLM suggestion
        
        Returns:
            (needs_visualization, visualization_type)
        """
        if not data:
            return False, "none"
        
        # Code-based heuristics
        row_count = len(data)
        
        # Check if data has numeric columns
        has_numeric = False
        if data and isinstance(data[0], dict):
            for value in data[0].values():
                if isinstance(value, (int, float)):
                    has_numeric = True
                    break
        
        # Determine visualization type based on intent
        if intent.get('type') in ['comparison', 'trend', 'correlation']:
            if row_count > 1 and has_numeric:
                return True, "chart"
        
        if intent.get('type') == 'aggregate':
            if row_count > 1:
                return True, "bar" if has_numeric else "table"
        
        # If LLM suggested visualization and we have data
        if llm_suggestion and row_count > 1:
            return True, "chart"
        
        # Default: no visualization needed
        return False, "none"


# Global service instance
chat_service = ChatService()
