from typing import Any, Dict

from pyspark.errors.exceptions.captured import AnalysisException
from pyspark.sql import SparkSession

from governance.masking import get_masked_columns, rewrite_query_with_masks
from spark_jobs.spark_session import get_spark

AUDIT_TOOL = {
    "function_declarations": [
        {
            "name": "run_audit_query",
            "description": "Query the audit_log table to see past interactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query against nessie.retail.audit_log",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "What this audit query does",
                    },
                },
                "required": ["sql", "explanation"],
            },
        }
    ]
}

def execute_audit_query(sql: str) -> Dict[str, Any]:
    spark = SparkSession.getActiveSession() or get_spark()
    try:
        df = spark.sql(sql)
    except AnalysisException as e:
        return {"error": str(e)}
    rows = df.limit(100).collect()
    return {
        "columns": df.columns,
        "rows": [[str(v) for v in row] for row in rows],
        "row_count": len(rows),
    }