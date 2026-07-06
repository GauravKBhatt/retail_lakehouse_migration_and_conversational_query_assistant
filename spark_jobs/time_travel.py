from pyspark.sql import Row, SparkSession

from spark_jobs.spark_session import get_spark

NEW_ROW = """
    INSERT INTO nessie.retail.fact_sales
    VALUES (8888888, CAST('2024-07-01' AS DATE), 2, 2, 2, 1, 99.99, 99.99, 0.05)
"""

COUNT_SUM_QUERY = "SELECT COUNT(*) AS row_count, SUM(total_amount) AS total FROM nessie.retail.fact_sales"


def list_snapshots(spark: SparkSession) -> None:
    """Print every snapshot recorded for fact_sales, oldest first."""
    spark.sql(
        "SELECT snapshot_id, committed_at, summary FROM nessie.retail.fact_sales.snapshots ORDER BY committed_at"
    ).show(truncate=False)


def get_earliest_snapshot(spark: SparkSession) -> Row:
    """Return the full row (snapshot_id, committed_at) of the first snapshot.

    This is the state of the table before this script makes any changes,
    used as the baseline for the time travel comparison.
    """
    return spark.sql(
        "SELECT snapshot_id, committed_at FROM nessie.retail.fact_sales.snapshots ORDER BY committed_at LIMIT 1"
    ).collect()[0]


def insert_new_row(spark: SparkSession) -> None:
    """Insert a new fact_sales row, creating a new snapshot (SNAP_AFTER)."""
    spark.sql(NEW_ROW)
    print("Inserted order_id=8888888 with discount_pct=0.05")


def get_latest_snapshot_id(spark: SparkSession, table: str = "nessie.retail.fact_sales") -> int:
    """Return the snapshot_id of the most recent commit on a table."""
    row: Row = spark.sql(
        f"SELECT snapshot_id FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1"
    ).collect()[0]
    return row["snapshot_id"]


def query_current_state(spark: SparkSession) -> None:
    """Run COUNT(*) / SUM(total_amount) against the latest snapshot."""
    print("=== CURRENT (latest snapshot) ===")
    spark.sql(COUNT_SUM_QUERY).show()


def query_as_of_snapshot(spark: SparkSession, snapshot_id: int) -> None:
    """Run the same COUNT(*) / SUM(total_amount) query as of a past snapshot.

    Uses Iceberg's VERSION AS OF syntax to read the table exactly as it
    existed at snapshot_id, proving snapshots are real immutable history
    and not just metadata bookkeeping.
    """
    print(f"=== AS OF SNAP_BEFORE (snapshot {snapshot_id}) ===")
    spark.sql(f"""
        SELECT COUNT(*) AS row_count, SUM(total_amount) AS total
        FROM nessie.retail.fact_sales
        VERSION AS OF {snapshot_id}
    """).show()


def query_as_of_timestamp(spark: SparkSession, timestamp: str) -> None:
    """Run a COUNT(*) query as of a specific commit timestamp.

    TIMESTAMP AS OF is the second valid time travel syntax alongside
    VERSION AS OF, resolving to whichever snapshot was current at that
    point in time. Note this travels by commit wall-clock time, not by
    any date column inside the data (e.g. order_date).
    """
    print(f"=== AS OF TIMESTAMP {timestamp} ===")
    spark.sql(f"""
        SELECT COUNT(*) AS row_count
        FROM nessie.retail.fact_sales
        TIMESTAMP AS OF '{timestamp}'
    """).show()


def demonstrate_time_travel(spark: SparkSession) -> None:
    """Run the full time travel demo end to end."""
    print("=== SNAPSHOT HISTORY BEFORE CHANGE ===")
    list_snapshots(spark)

    snap_before_row = get_earliest_snapshot(spark)
    snap_before = snap_before_row["snapshot_id"]
    snap_before_committed_at = snap_before_row["committed_at"]
    print(f"SNAP_BEFORE={snap_before}")

    insert_new_row(spark)

    snap_after = get_latest_snapshot_id(spark)
    print(f"SNAP_AFTER={snap_after}")

    query_current_state(spark)
    query_as_of_snapshot(spark, snap_before)
    query_as_of_timestamp(spark, str(snap_before_committed_at))


if __name__ == "__main__":
    spark = get_spark("TimeTravel")

    demonstrate_time_travel(spark)

    spark.stop()