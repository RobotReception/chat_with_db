"""
SQL Execution Layer
Executes validated SQL queries safely
"""
from sqlalchemy import text
from typing import Any, Optional
import logging
import time

from app.db.connection import db_manager
from app.db.security import sql_validator
from app.config import settings

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Executes SQL queries with safety checks"""
    
    def execute(self, sql: str) -> tuple[bool, Optional[list[dict]], Optional[str]]:
        """
        Execute SQL query safely
        
        Returns:
            (success, data, error_message)
            data: List of dictionaries (rows as dicts)
        """
        # Validate SQL
        is_valid, error = sql_validator.validate(sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {error}")
            return False, None, error
        
        # Sanitize SQL
        safe_sql = sql_validator.sanitize(sql)
        
        start_time = time.time()
        
        try:
            # Log which database we're connecting to
            db_name = settings.POSTGRESQL_URL.split("/")[-1] if settings.POSTGRESQL_URL else settings.DB_NAME
            logger.debug(f"Executing SQL on database: {db_name}")
            
            with db_manager.get_session() as session:
                result = session.execute(text(safe_sql))
                
                # Convert to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                data = [dict(zip(columns, row)) for row in rows]
                
                execution_time = time.time() - start_time
                
                logger.info(
                    f"SQL executed successfully",
                    extra={
                        "sql": safe_sql[:200],  # Log first 200 chars
                        "rows_returned": len(data),
                        "execution_time_ms": round(execution_time * 1000, 2)
                    }
                )
                
                return True, data, None
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(
                f"SQL execution failed: {error_msg}",
                extra={
                    "sql": safe_sql[:200],
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "error": error_msg
                },
                exc_info=True
            )
            
            return False, None, error_msg
    
    def get_table_schema(self, table_name: str) -> Optional[dict]:
        """Get schema information for a table"""
        sql = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        
        success, data, error = self.execute(sql)
        if success:
            return {"columns": data}
        return None


# Global executor instance
sql_executor = SQLExecutor()
