from typing import Any, Dict, List

from pyspark.errors.exceptions.captured import AnalysisException
from pyspark.sql import SparkSession

from api_backend.guard import is_safe_query  
from governance.masking import get_masked_columns, rewrite_query_with_masks
from spark_jobs.spark_session import get_spark
from api_backend.logger import log_event

SYSTEM_PROMPT = '''
You are a retail analytics assistant. You have access to these Iceberg tables in the nessie.retail schema:
- fact_sales (order_id, order_date, product_id, store_id, customer_id, quantity, unit_price, total_amount)
- dim_product (product_id, name, category, subcategory, brand, cost_price)
- dim_store (store_id, name, city, state, region, store_type)
- dim_customer (customer_id, segment, join_date, lifetime_value_bucket)
- dim_date (date_id, full_date, year, quarter, month, week, day_of_week)

IMPORTANT: Always use the exact table names above. Do NOT use variations.
Always qualify table names with the schema: nessie.retail.table_name
Examples: nessie.retail.fact_sales, nessie.retail.dim_product

Column type hints:
- dim_date.month is an INTEGER (1-12), NOT a string. Use month = 2 for February, month = 12 for December.
- dim_date.year is an INTEGER (e.g., 2023, 2024).
- fact_sales.order_date is a STRING in 'yyyy-MM-dd' format. To filter by month, JOIN with dim_date on full_date = order_date.

IMPORTANT: Do NOT query information_schema or any system tables. They do not exist in this Spark environment.
To list tables, use: SHOW TABLES IN nessie.retail

Limit results to 100 rows unless the user asks for aggregates.

You also have access to an audit_log table:
- nessie.retail.audit_log (event_id, timestamp, user_role, model, question, generated_sql, snapshot_id, execution_time_ms, answer)
Use the run_audit_query tool to answer questions about past interactions.
'''


# Gemini function-calling tool declaration (equivalent of Claude's tool schema).
LAKEHOUSE_QUERY_TOOL = {
    "function_declarations": [
        {
            "name": "run_lakehouse_query",
            "description": "Run a read-only SQL query against the retail Iceberg lakehouse and return results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Plain-English explanation of what this query does",
                    },
                },
                "required": ["sql", "explanation"],
            },
        }
    ]
}


def get_or_create_spark() -> SparkSession:
    """Return the active SparkSession, creating one if none exists."""
    return SparkSession.getActiveSession() or get_spark()


def execute_query(sql: str, user_role: str = "analyst") -> Dict[str, Any]:
    """Run a SQL query against the lakehouse and return rows as plain data.

    Rejects the query up front if it fails the safety guard. Results are
    capped at 100 rows and every value is stringified so the result is
    safe to serialize back to the model as a function response.
    Rejects the query up front if it fails the safety guard. Applies
    column-level masking via OPA before execution. Results are capped at
    100 rows and every value is stringified so the result is safe to
    serialize back to the model as a function response.
    """

    safe, reason = is_safe_query(sql)
    if not safe:
        return {"error": reason}   

    masked_cols = get_masked_columns(user_role)
    if masked_cols:
        sql = rewrite_query_with_masks(sql, masked_cols)
        log_event("query_masking", {"role": user_role, "masked": masked_cols, "sql": sql})

    log_event("sql_execution", {"sql": sql})

    spark = get_or_create_spark()
    try:
        df = spark.sql(sql)
    except AnalysisException as e:
        return {
            "error": f"Query failed — table or view not found. Details: {e}"
        }
    rows: List = df.limit(100).collect()

    result = {
        "columns": df.columns,
        "rows": [[str(value) for value in row] for row in rows],
        "row_count": len(rows),
    }

    log_event("sql_result", {
        "sql": sql,
        "row_count": len(rows),
        "columns": df.columns,
    })
    return result
