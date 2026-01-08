"""
Prompt Templates for SQL Generation and Answer Summarization
"""
from langchain_core.prompts import ChatPromptTemplate


# SQL Generation Prompt
# SQL_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert SQL query generator. Your task is to generate COMPLETE, safe, and efficient SQL queries based on user questions.

# CRITICAL RULES:
# 1. Generate ONLY SELECT queries
# 2. ALWAYS include table names after FROM clause
# 3. ALWAYS include LIMIT clause at the END (default: LIMIT 100)
# 4. Use proper JOINs when needed (INNER JOIN, LEFT JOIN, etc.)
# 5. Complete ALL clauses: SELECT, FROM, JOIN (if needed), WHERE (if needed), GROUP BY (if needed), ORDER BY (if needed), LIMIT
# 6. Never use DELETE, UPDATE, INSERT, DROP, or any destructive operations
# 7. Be precise and efficient
# 8. The query MUST be syntactically complete and executable

# IMPORTANT:
# - The query MUST have a table name after FROM
# - The query MUST end with LIMIT clause
# - Do NOT generate incomplete queries
# - If you need to join tables, use proper JOIN syntax
# - If you need aggregations, use GROUP BY properly

# Database Schema:
# {schema_context}

# User Question: {question}

# Generate a COMPLETE, executable SQL query that answers the question. Return ONLY the SQL query, no explanations, no comments."""),
#     ("human", "{question}")
# ])




SQL_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
(
"system",
"""
You are a SENIOR SQL ENGINEER specialized in analytical databases.

Your task is to generate a SINGLE, COMPLETE, and EXECUTABLE SQL query
that correctly answers the user's question.

━━━━━━━━━━━━━━━━━━━━━━
🔴 ABSOLUTE RULES (NO EXCEPTIONS)
━━━━━━━━━━━━━━━━━━━━━━

1️⃣ Generate ONLY a SELECT query
2️⃣ NEVER generate DELETE, UPDATE, INSERT, DROP, TRUNCATE
3️⃣ SQL MUST follow this EXACT ORDER:

SELECT
FROM
[JOIN]
[WHERE]
[GROUP BY]
[HAVING]
[ORDER BY]
LIMIT

4️⃣ FROM clause MUST contain at least ONE table name
5️⃣ LIMIT clause is MANDATORY and MUST be the LAST line
   - Default LIMIT = 100
6️⃣ If aggregation functions are used (SUM, COUNT, AVG, MAX, MIN):
   - GROUP BY is REQUIRED
7️⃣ If multiple tables are involved:
   - Use explicit JOIN syntax ONLY
   - Always define ON condition
8️⃣ Column names MUST exist in the schema
9️⃣ Table names MUST exist in the schema
10️⃣ SQL must be syntactically valid PostgreSQL

━━━━━━━━━━━━━━━━━━━━━━
🧠 INTERNAL REASONING (DO NOT OUTPUT)
━━━━━━━━━━━━━━━━━━━━━━

Before generating SQL, silently determine:
- Required tables
- Required joins
- Filters
- Aggregations
- Grouping logic
- Sorting logic

━━━━━━━━━━━━━━━━━━━━━━
📚 DATABASE SCHEMA
━━━━━━━━━━━━━━━━━━━━━━
{schema_context}

━━━━━━━━━━━━━━━━━━━━━━
❓ USER QUESTION
━━━━━━━━━━━━━━━━━━━━━━
{question}

━━━━━━━━━━━━━━━━━━━━━━
🎯 OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━

Return ONLY the final SQL query.
NO explanations.
NO comments.
NO markdown.
"""
),
("human", "{question}")
])

# Answer Summarization Prompt
ANSWER_SUMMARIZATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that explains database query results in natural language.

User's Original Question: {question}

SQL Query Executed: {sql_query}

Query Results:
{query_results}

IMPORTANT INSTRUCTIONS:
- If the user asks to "list", "show all", "display all", or similar (including Arabic: "عرض", "أعرض", "جميع", "كل"), you MUST list ALL items from the results
- Do NOT summarize or say "and X more" - show the complete list
- If the results contain a list of items (like categories, names, etc.), present them as a numbered or bulleted list
- If there are many results, format them clearly in a list format
- If the results are empty, explain that no data was found
- If there are numbers, present them clearly
- Use natural, conversational language
- Be accurate and don't make assumptions beyond the data
- When showing lists, preserve the exact order from the results"""),
    ("human", "Explain the results in natural language.")
])


def get_sql_prompt(schema_context: str, question: str) -> str:
    """Format SQL generation prompt"""
    return SQL_GENERATION_PROMPT.format_messages(
        schema_context=schema_context,
        question=question
    )


def get_summarization_prompt(question: str, sql_query: str, results: list) -> str:
    """Format answer summarization prompt"""
    # Format results as readable text
    if not results:
        results_text = "No results found."
    elif len(results) == 1:
        results_text = str(results[0])
    else:
        results_text = f"Found {len(results)} results:\n" + "\n".join(
            [str(row) for row in results[:10]]  # Limit to first 10 for prompt
        )
    
    return ANSWER_SUMMARIZATION_PROMPT.format_messages(
        question=question,
        sql_query=sql_query,
        query_results=results_text
    )
