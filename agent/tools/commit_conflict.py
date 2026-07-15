from typing import Any, Dict, List
from pyspark.sql import SparkSession
from spark_jobs.spark_session import get_spark, _spark_lock
from api_backend.logger import log_event

CONFLICT_TOOL = {
    "function_declarations": [
        {
            "name": "get_commit_conflicts",
            "description": (
                "Retrieve recent Iceberg commit conflicts. Use this when the user "
                "asks why a write job failed or mentions commit errors."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    ]
}

def get_or_create_spark() -> SparkSession:
    """Get or create a Spark session."""
    return SparkSession.getActiveSession() or get_spark()

def get_conflicts() -> List[Dict[str, Any]]:
    """Get recent commit conflicts."""
    log_event("get_commit_conflicts", {})
    spark = get_or_create_spark()
    with _spark_lock:
        try:
            rows = spark.sql(
                'SELECT * FROM nessie.retail.commit_conflicts ORDER BY job_id DESC LIMIT 10'
            ).collect()
        except Exception as e:
            log_event("get_commit_conflicts_error", {"error": str(e)})
            return []
    conflicts = [{'job_id': r['job_id'], 'error': r['error']} for r in rows]
    log_event("get_commit_conflicts_result", {"count": len(conflicts)})
    return conflicts