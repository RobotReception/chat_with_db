"""
RAG Retriever - Retrieves relevant schema information
for the user's question
"""
from typing import List, Optional
import logging

from app.rag.schema_store import schema_store
from app.rag.semantic_keywords import SEMANTIC_KEYWORDS

logger = logging.getLogger(__name__)


class SchemaRetriever:
    """
    Database-agnostic schema retriever based on column semantics.
    """

    def retrieve(self, question: str, top_k: int = 15) -> str:
        question_lower = question.lower()
        all_tables = schema_store.get_all_tables()

        table_scores = {}

        # 1️⃣ Score tables by column semantic match
        for table in all_tables:
            table_name = table["table_name"]
            table_info = schema_store.get_table_info(table_name)
            if not table_info:
                continue

            score = 0
            for col in table_info["columns"]:
                col_name = col["column_name"].lower()

                for concept, keywords in SEMANTIC_KEYWORDS.items():
                    if any(k in question_lower for k in keywords):
                        if any(k in col_name for k in keywords):
                            score += 3  # strong signal

                # Weak signal: direct column name match
                if col_name in question_lower:
                    score += 2

            if score > 0:
                table_scores[table_name] = score

        # 2️⃣ Sort tables by relevance
        sorted_tables = sorted(
            table_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        selected_tables = [t[0] for t in sorted_tables[:top_k]]

        # 3️⃣ Fallback: minimal schema
        if not selected_tables:
            selected_tables = [t["table_name"] for t in all_tables[:top_k]]

        # 4️⃣ Expand via foreign keys (relationships)
        expanded_tables = set(selected_tables)
        for table_name in selected_tables:
            table_info = schema_store.get_table_info(table_name)
            for fk in table_info.get("foreign_keys", []):
                expanded_tables.add(fk["foreign_table_name"])

        # 5️⃣ Build schema context
        context_parts = []
        for table_name in expanded_tables:
            table_info = schema_store.get_table_info(table_name)
            if not table_info:
                continue

            parts = [f"Table: {table_name}", "Columns:"]
            for col in table_info["columns"]:
                col_desc = f"  - {col['column_name']} ({col['data_type']})"
                if col.get("is_primary_key"):
                    col_desc += " [PRIMARY KEY]"
                parts.append(col_desc)

            if table_info["foreign_keys"]:
                parts.append("Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    parts.append(
                        f"  - {fk['column_name']} → "
                        f"{fk['foreign_table_name']}.{fk['foreign_column_name']}"
                    )

            context_parts.append("\n".join(parts))

        context = "\n\n".join(context_parts)

        logger.info(
            "Retrieved schema context (DB-agnostic)",
            extra={
                "question": question[:100],
                "tables": list(expanded_tables),
                "tables_count": len(expanded_tables)
            }
        )

        return context


# Global retriever instance
schema_retriever = SchemaRetriever()
