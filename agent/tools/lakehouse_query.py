from typing import Any, Dict, List

from pyspark.sql import SparkSession

from api_backend.guard import is_safe_query  # stub for now, real guard in Phase 4
from spark_jobs.spark_session import get_spark

SYSTEM_PROMPT = """
You are a retail analytics assistant. You have access to these Iceberg tables:
- nessie.retail.fact_sales (order_id, order_date, product_id, store_id, customer_id, quantity, unit_price, total_amount, discount_pct)
- nessie.retail.dim_product (product_id, name, category, subcategory, brand, cost_price)
- nessie.retail.dim_store (store_id, name, city, state, region, store_type)
- nessie.retail.dim_customer (customer_id, segment, join_date, lifetime_value_bucket)
- nessie.retail.dim_date (date_id, full_date, year, quarter, month, week, day_of_week)
Always generate standard Spark SQL. Never use INSERT, UPDATE, DELETE, or DROP.
Limit results to 100 rows unless the user asks for aggregates.
"""

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


def execute_query(sql: str) -> Dict[str, Any]:
    """Run a SQL query against the lakehouse and return rows as plain data.

    Rejects the query up front if it fails the safety guard. Results are
    capped at 100 rows and every value is stringified so the result is
    safe to serialize back to the model as a function response.
    """
    if not is_safe_query(sql):
        return {"error": "Query rejected by safety guard"}

    spark = get_or_create_spark()
    df = spark.sql(sql)
    rows: List = df.limit(100).collect()

    return {
        "columns": df.columns,
        "rows": [[str(value) for value in row] for row in rows],
        "row_count": len(rows),
    }