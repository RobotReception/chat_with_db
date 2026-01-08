"""
LangChain Chains for SQL Generation and Answer Processing
"""
from typing import Optional, Tuple
import logging
import re

from langchain_core.output_parsers import StrOutputParser

from app.llm.client import llm_client
from app.llm.prompts import SQL_GENERATION_PROMPT, ANSWER_SUMMARIZATION_PROMPT

logger = logging.getLogger(__name__)


class SQLGenerationChain:
    """Chain for generating SQL from natural language"""
    
    def __init__(self):
        if not llm_client.is_available():
            raise ValueError("LLM client is not available")
        
        self.chain = (
            SQL_GENERATION_PROMPT
            | llm_client.client
            | StrOutputParser()
        )
    
    def generate(self, question: str, schema_context: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate SQL query from question
        
        Returns:
            (success, sql_query, error_message)
        """
        try:
            # Format prompt
            messages = SQL_GENERATION_PROMPT.format_messages(
                schema_context=schema_context,
                question=question
            )
            
            # Invoke chain
            response = llm_client.client.invoke(messages)
            
            # Extract SQL from response
            sql = self._extract_sql(response.content)
            
            if not sql:
                return False, None, "Failed to extract SQL from LLM response"
            
            # Validate SQL completeness
            validation_error = self._validate_sql_completeness(sql)
            if validation_error:
                logger.warning(
                    f"SQL validation failed: {validation_error}",
                    extra={
                        "question": question[:100],
                        "sql": sql[:200]
                    }
                )
                return False, None, f"Generated SQL is incomplete: {validation_error}"
            
            logger.info(
                f"SQL generated successfully",
                extra={
                    "question": question[:100],
                    "sql": sql[:200]
                }
            )
            
            return True, sql, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"SQL generation failed: {error_msg}",
                extra={"question": question[:100]},
                exc_info=True
            )
            return False, None, error_msg
    
    # def _extract_sql(self, text: str) -> Optional[str]:
    #     """
    #     Extract SQL query from LLM response
    #     Handles cases where LLM adds explanations
    #     """
    #     # Remove markdown code blocks if present
    #     text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
    #     text = re.sub(r'```\s*', '', text)
        
    #     # Remove any text after semicolon (explanations, notes, etc.)
    #     if ';' in text:
    #         text = text.split(';')[0] + ';'
        
    #     # Find SQL statement (SELECT ...) - stop at first non-SQL text
    #     # Look for SELECT and capture until we hit a line that doesn't look like SQL
    #     lines = text.split('\n')
    #     sql_lines = []
    #     in_sql = False
        
    #     for line in lines:
    #         line_stripped = line.strip()
    #         if not line_stripped:
    #             if in_sql:
    #                 sql_lines.append('')
    #             continue
            
    #         # Check if this looks like SQL
    #         sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 
    #                       'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'AND', 'OR']
            
    #         if any(line_stripped.upper().startswith(kw) for kw in sql_keywords):
    #             in_sql = True
    #             sql_lines.append(line_stripped)
    #         elif in_sql and (line_stripped.startswith('--') or 
    #                        any(kw in line_stripped.upper() for kw in ['PLEASE', 'NOTE', 'NOTE:', 'REPLACE'])):
    #             # Stop at comments or explanatory text
    #             break
    #         elif in_sql:
    #             # Continue SQL if it looks like part of the query
    #             if any(char in line_stripped for char in [',', '(', ')', '=', '<', '>', "'", '"']):
    #                 sql_lines.append(line_stripped)
    #             else:
    #                 # Might be explanation, but check if it's a valid SQL continuation
    #                 if line_stripped.upper() in ['AS', 'ON', 'IN', 'IS', 'NULL', 'NOT']:
    #                     sql_lines.append(line_stripped)
    #                 else:
    #                     break
        
    #     if sql_lines:
    #         sql = ' '.join(sql_lines).strip().rstrip(';')
    #         # Clean up multiple spaces
    #         sql = re.sub(r'\s+', ' ', sql)
    #         if sql.upper().startswith('SELECT'):
    #             return sql
        
    #     # Fallback: try simple pattern matching
    #     match = re.search(r'(SELECT.*?)(?:LIMIT\s+\d+)?;?', text, re.IGNORECASE | re.DOTALL)
    #     if match:
    #         sql = match.group(1).strip()
    #         # Remove any trailing non-SQL text (explanations, notes, etc.)
    #         sql = re.sub(r'\s+Please.*$', '', sql, flags=re.IGNORECASE | re.DOTALL)
    #         sql = re.sub(r'\s+Note.*$', '', sql, flags=re.IGNORECASE | re.DOTALL)
    #         sql = re.sub(r'\s+If.*$', '', sql, flags=re.IGNORECASE | re.DOTALL)
    #         sql = re.sub(r'\s+This.*$', '', sql, flags=re.IGNORECASE | re.DOTALL)
    #         sql = re.sub(r'\s+You.*$', '', sql, flags=re.IGNORECASE | re.DOTALL)
    #         # Remove anything after a line break that doesn't look like SQL
    #         lines = sql.split('\n')
    #         clean_lines = []
    #         for line in lines:
    #             line = line.strip()
    #             if not line:
    #                 continue
    #             # Stop if we hit explanatory text
    #             if any(word in line.upper() for word in ['PLEASE', 'NOTE', 'IF YOU', 'THIS WILL', 'YOU WOULD']):
    #                 break
    #             clean_lines.append(line)
    #         sql = ' '.join(clean_lines).strip()
    #         sql = sql.rstrip(';').strip()
    #         if sql.upper().startswith('SELECT'):
    #             return sql
        
    #     return None
    
    
    def _extract_sql(self, text: str) -> Optional[str]:
        # Remove markdown blocks
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        
        # Extract from SELECT to LIMIT
        match = re.search(
            r"(SELECT\s.+?\sLIMIT\s+\d+)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if match:
            sql = match.group(1)
            sql = re.sub(r"\s+", " ", sql).strip()
            return sql

        return None

    def _validate_sql_completeness(self, sql: str) -> Optional[str]:
        """
        Validate that SQL query is complete and executable
        
        Returns:
            Error message if incomplete, None if valid
        """
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return "Query must start with SELECT"
        
        # Must have FROM clause
        if 'FROM' not in sql_upper:
            return "Query missing FROM clause"
        
        # Check if FROM has a table name after it
        from_index = sql_upper.find('FROM')
        if from_index >= 0:
            after_from = sql_upper[from_index + 4:].strip()
            # Check if there's something after FROM (table name or JOIN)
            if not after_from or after_from.startswith('LIMIT'):
                return "Query missing table name after FROM clause"
            
            # If it starts with LIMIT, it's incomplete
            if after_from.startswith('LIMIT'):
                return "Query has LIMIT directly after FROM - missing table name"
        
        # If LIMIT exists, it should be at the end
        if 'LIMIT' in sql_upper:
            limit_index = sql_upper.find('LIMIT')
            # Check if there's anything after LIMIT that looks like SQL (shouldn't be)
            after_limit = sql_upper[limit_index + 5:].strip()
            if after_limit and not after_limit.replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '').strip():
                # If there's non-numeric content after LIMIT, it might be incomplete
                pass
        
        # Basic syntax check: FROM should not be immediately followed by LIMIT
        if re.search(r'FROM\s+LIMIT', sql_upper):
            return "Query has LIMIT immediately after FROM - missing table name or JOIN clause"
        
        return None


class AnswerSummarizationChain:
    """Chain for summarizing query results into natural language"""
    
    def __init__(self):
        if not llm_client.is_available():
            raise ValueError("LLM client is not available")
        
        self.chain = (
            ANSWER_SUMMARIZATION_PROMPT
            | llm_client.client
            | StrOutputParser()
        )
    
    def summarize(self, question: str, sql_query: str, results: list) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Summarize query results into natural language
        
        Returns:
            (success, answer, error_message)
        """
        try:
            # Format results
            if not results:
                results_text = "No results found."
            elif len(results) == 1:
                results_text = str(results[0])
            else:
                # Check if question asks for a list (show all results)
                question_lower = question.lower()
                list_keywords = ['list', 'show all', 'display all', 'all', 'كل', 'جميع', 'عرض', 'أعرض', 'قائمة']
                is_list_request = any(keyword in question_lower for keyword in list_keywords)
                
                # For list requests, show all results (up to 100)
                # For other requests, limit to 20 for prompt efficiency
                max_display = 100 if is_list_request else 20
                
                if len(results) <= max_display:
                    # Show all results
                    results_text = f"Found {len(results)} result(s):\n"
                    # Format results nicely
                    formatted_results = []
                    for i, row in enumerate(results, 1):
                        if isinstance(row, dict):
                            # If it's a dict with one key, show just the value
                            if len(row) == 1:
                                value = list(row.values())[0]
                                formatted_results.append(f"{i}. {value}")
                            else:
                                formatted_results.append(f"{i}. {row}")
                        else:
                            formatted_results.append(f"{i}. {row}")
                    results_text += "\n".join(formatted_results)
                else:
                    # Show first max_display results
                    display_results = results[:max_display]
                    results_text = f"Found {len(results)} result(s). Showing first {max_display}:\n"
                    formatted_results = []
                    for i, row in enumerate(display_results, 1):
                        if isinstance(row, dict):
                            if len(row) == 1:
                                value = list(row.values())[0]
                                formatted_results.append(f"{i}. {value}")
                            else:
                                formatted_results.append(f"{i}. {row}")
                        else:
                            formatted_results.append(f"{i}. {row}")
                    results_text += "\n".join(formatted_results)
                    results_text += f"\n... and {len(results) - max_display} more results."
            
            # Format prompt
            messages = ANSWER_SUMMARIZATION_PROMPT.format_messages(
                question=question,
                sql_query=sql_query,
                query_results=results_text
            )
            
            # Invoke chain
            response = llm_client.client.invoke(messages)
            answer = response.content.strip()
            
            logger.info(
                f"Answer summarized successfully",
                extra={
                    "question": question[:100],
                    "answer_length": len(answer)
                }
            )
            
            return True, answer, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Answer summarization failed: {error_msg}",
                extra={"question": question[:100]},
                exc_info=True
            )
            return False, None, error_msg
