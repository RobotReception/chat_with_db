"""
SQL Security & Validation Layer
Critical for Production Safety
"""
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class SQLSecurityValidator:
    """Validates and secures SQL queries"""
    
    def __init__(self):
        self.allowed_operations = set(settings.SQL_ALLOWED_OPERATIONS)
        self.blocked_keywords = {
            "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE",
            "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC",
            "EXECUTE", "CALL", "MERGE", "COPY"
        }
    
    def validate(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety
        
        Returns:
            (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"
        
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql.strip())
            if not parsed:
                return False, "Invalid SQL syntax"
            
            statement = parsed[0]
            
            # Check for blocked operations
            for token in statement.tokens:
                if token.ttype is DML:
                    operation = token.value.upper().strip()
                    if operation not in self.allowed_operations:
                        return False, f"Operation '{operation}' is not allowed. Only SELECT queries are permitted."
                
                if token.ttype is Keyword:
                    keyword = token.value.upper().strip()
                    if keyword in self.blocked_keywords:
                        return False, f"Keyword '{keyword}' is not allowed for security reasons."
            
            # Ensure SELECT statement
            if not self._is_select_only(statement):
                return False, "Only SELECT statements are allowed"
            
            # Check for LIMIT clause (recommended but not enforced)
            if not self._has_limit(sql):
                logger.warning(f"Query missing LIMIT clause: {sql[:100]}")
            
            return True, None
            
        except Exception as e:
            logger.error(f"SQL validation error: {e}", exc_info=True)
            return False, f"SQL validation failed: {str(e)}"
    
    def _is_select_only(self, statement: Statement) -> bool:
        """Check if statement is SELECT only"""
        for token in statement.tokens:
            if token.ttype is DML:
                return token.value.upper().strip() == "SELECT"
        return False
    
    def _has_limit(self, sql: str) -> bool:
        """Check if SQL has LIMIT clause"""
        sql_upper = sql.upper()
        return "LIMIT" in sql_upper
    
    def sanitize(self, sql: str) -> str:
        """
        Sanitize SQL query (add LIMIT if missing)
        Note: This is a simple implementation. Production should be more robust.
        """
        sql = sql.strip().rstrip(";")
        
        # Add LIMIT if missing and query doesn't end with LIMIT
        if not self._has_limit(sql):
            sql = f"{sql} LIMIT {settings.SQL_MAX_ROWS}"
        
        return sql


# Global validator instance
sql_validator = SQLSecurityValidator()
