from typing import Any, Dict, Optional

from pyspark.sql import SparkSession

from api_backend.guard import is_safe_query
from spark_jobs.spark_session import get_spark

# Gemini function-calling tool declaration for time travel queries.
TIME_TRAVEL_TOOL = {
    "function_declarations": [
        {
            "name": "run_time_travel_query",
            "description": (
                "Query the lakehouse as it existed at a specific date or snapshot ID. "
                'Use this whenever the user asks about historical data, e.g. "last week", '
                '"three days ago", "as of January 5th".'
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"},
                    "as_of_date": {
                        "type": "string",
                        "description": "ISO date string, e.g. 2024-01-15",
                    },
                    "snapshot_id": {
                        "type": "integer",
                        "description": "Exact Iceberg snapshot ID (optional — use as_of_date if unknown)",
                    },
                },
                "required": ["sql"],
            },
        }
    ]
}


def get_or_create_spark() -> SparkSession:
    """Return the active SparkSession, creating one if none exists."""
    return SparkSession.getActiveSession() or get_spark()


def resolve_snapshot(as_of_date: Optional[str], snapshot_id: Optional[int]) -> Optional[int]:
    """Resolve a snapshot_id from either an explicit ID or a natural date.

    An explicit snapshot_id always wins. Otherwise, as_of_date is matched
    to the latest snapshot committed on or before the end of that day.
    Returns None if neither is provided or no matching snapshot exists.
    """
    if snapshot_id:
        return snapshot_id

    if as_of_date:
        spark = get_or_create_spark()
        row = spark.sql(f"""
            SELECT snapshot_id FROM nessie.retail.fact_sales.snapshots
            WHERE committed_at <= TIMESTAMP '{as_of_date} 23:59:59'
            ORDER BY committed_at DESC LIMIT 1
        """).collect()
        return row[0][0] if row else None

    return None


def execute_time_travel_query(
    sql: str,
    as_of_date: Optional[str] = None,
    snapshot_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Run a SQL query as of a resolved historical snapshot.

    Rewrites the fact_sales reference to pin it to VERSION AS OF the
    resolved snapshot, so the same query the model would normally run
    reads historical state instead of the current one.
    """
    if not is_safe_query(sql):
        return {"error": "Query rejected by safety guard"}

    snap_id = resolve_snapshot(as_of_date, snapshot_id)

    if snap_id is None:
        return {"error": "Could not resolve a snapshot for the given date/snapshot_id"}

    sql = sql.replace(
        "nessie.retail.fact_sales",
        f"nessie.retail.fact_sales VERSION AS OF {snap_id}",
    )

    spark = get_or_create_spark()
    df = spark.sql(sql)
    rows = df.limit(100).collect()

    return {
        "snapshot_id": snap_id,
        "columns": df.columns,
        "rows": [[str(value) for value in row] for row in rows],
    }