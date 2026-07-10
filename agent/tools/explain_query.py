import re
from typing import Any, Dict

from pyspark.sql import SparkSession

from spark_jobs.spark_session import get_spark
from api_backend.logger import log_event

EXPLAIN_TOOL = {
    "function_declarations": [
        {
            "name": "explain_query_plan",
            "description": (
                "Get a plain-English explanation of how a query will execute: "
                "which partition files will be scanned, which will be skipped, and why."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The SQL query to explain"},
                },
                "required": ["sql"],
            },
        }
    ]
}


def get_or_create_spark() -> SparkSession:
    return SparkSession.getActiveSession() or get_spark()


def explain_plan(sql: str) -> Dict[str, Any]:
    log_event("explain_query",{"sql":sql})

    spark = get_or_create_spark()
    plan = spark.sql(f"EXPLAIN EXTENDED {sql}").collect()[0][0]

    selected = re.search(r"SelectedPartitions\s*:\s*(\d+)", plan)
    total = re.search(r"TotalPartitions\s*:\s*(\d+)", plan)
    files = re.search(r"FilesRead\s*:\s*(\d+)", plan)

    result = {
        "selected_partitions": selected.group(1) if selected else "unknown",
        "total_partitions": total.group(1) if total else "unknown",
        "files_read": files.group(1) if files else "unknown",
        "raw_plan_excerpt": plan[:800],
    }
    
    log_event("explain_query",{"result":result})
    
    return result
