"""
Schema Store - Stores and manages database schema information
for RAG retrieval
"""
from typing import List, Dict, Optional
import logging

from app.db.executor import sql_executor

logger = logging.getLogger(__name__)


class SchemaStore:
    """Manages database schema information for RAG"""
    
    def __init__(self):
        self._schema_cache: Optional[Dict] = None
    
    def get_all_tables(self) -> List[Dict]:
        """Get all tables in the database"""
        sql = """
            SELECT 
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        success, data, error = sql_executor.execute(sql)
        if success:
            return data or []
        logger.error(f"Failed to get tables: {error}")
        return []
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Get detailed information about a table"""
        # Get columns
        columns_sql = f"""
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE 
                    WHEN pk.column_name IS NOT NULL THEN true 
                    ELSE false 
                END as is_primary_key
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.table_name, ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
            ) pk ON c.table_name = pk.table_name 
                AND c.column_name = pk.column_name
            WHERE c.table_name = '{table_name}'
            ORDER BY c.ordinal_position
        """
        
        success, data, error = sql_executor.execute(columns_sql)
        if not success:
            logger.error(f"Failed to get table info: {error}")
            return None
        
        # Get foreign keys
        fk_sql = f"""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = '{table_name}'
        """
        
        fk_success, fk_data, _ = sql_executor.execute(fk_sql)
        foreign_keys = fk_data if fk_success else []
        
        return {
            "table_name": table_name,
            "columns": data or [],
            "foreign_keys": foreign_keys
        }
    
    def get_schema_context(self) -> str:
        """
        Get formatted schema context for LLM
        This is a simple version. In production, use embeddings + vector store
        """
        if self._schema_cache:
            return self._schema_cache.get("formatted", "")
        
        tables = self.get_all_tables()
        schema_parts = []
        
        for table in tables:
            table_name = table["table_name"]
            table_info = self.get_table_info(table_name)
            
            if not table_info:
                continue
            
            # Format table description
            parts = [f"Table: {table_name}"]
            parts.append("Columns:")
            
            for col in table_info["columns"]:
                col_desc = f"  - {col['column_name']} ({col['data_type']})"
                if col.get("is_primary_key"):
                    col_desc += " [PRIMARY KEY]"
                if col.get("is_nullable") == "NO":
                    col_desc += " [NOT NULL]"
                parts.append(col_desc)
            
            # Add foreign keys
            if table_info["foreign_keys"]:
                parts.append("Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    parts.append(
                        f"  - {fk['column_name']} -> "
                        f"{fk['foreign_table_name']}.{fk['foreign_column_name']}"
                    )
            
            schema_parts.append("\n".join(parts))
        
        formatted_schema = "\n\n".join(schema_parts)
        
        self._schema_cache = {
            "formatted": formatted_schema,
            "tables": tables
        }
        
        return formatted_schema
    
    def clear_cache(self):
        """Clear schema cache"""
        self._schema_cache = None
        logger.info("Schema cache cleared")


# Global schema store instance
schema_store = SchemaStore()
