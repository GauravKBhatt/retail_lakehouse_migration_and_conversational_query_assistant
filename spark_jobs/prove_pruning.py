from pyspark.sql import SparkSession

from spark_jobs.spark_session import get_spark

FULL_SCAN_QUERY = "SELECT SUM(total_amount) FROM nessie.retail.fact_sales"

PRUNED_QUERY = """
    SELECT SUM(total_amount) FROM nessie.retail.fact_sales
    WHERE order_date BETWEEN '2024-01-01' AND '2024-01-31'
"""


def run_full_scan(spark: SparkSession) -> None:
    """Run the unfiltered query and print its explain plan.

    No predicate on order_date, so Iceberg has to read every day-partition.
    This is the baseline to compare pruning against.
    """
    df_full = spark.sql(FULL_SCAN_QUERY)
    print("=== FULL SCAN (no filter) ===")
    df_full.explain(extended=True)


def run_pruned_scan(spark: SparkSession) -> None:
    """Run the date-filtered query and print its explain plan.

    order_date is a hidden partition column (days(order_date)), so Iceberg
    should resolve the BETWEEN filter down to a handful of day-partitions.
    """
    df_pruned = spark.sql(PRUNED_QUERY)
    print("=== PRUNED (January 2024 only) ===")
    df_pruned.explain(extended=True)


def print_file_counts(spark: SparkSession) -> None:
    """Print total data files vs files touched by the January 2024 filter.

    explain() shows the pushed-down filter but not concrete file counts, so
    this queries Iceberg's own metadata table (fact_sales.files) to get the
    real SelectedPartitions-style numbers for the README.
    """
    print("=== FILE COUNTS (from Iceberg metadata) ===")

    total_files = spark.sql(
        "SELECT COUNT(*) AS total_files FROM nessie.retail.fact_sales.files"
    )
    total_files.show()

    pruned_files = spark.sql("""
        SELECT COUNT(*) AS pruned_files
        FROM nessie.retail.fact_sales.files
        WHERE partition.order_date_day BETWEEN date('2024-01-01') AND date('2024-01-31')
    """)
    pruned_files.show()


def prove_pruning(spark: SparkSession) -> None:
    """Run both queries back to back so their explain plans can be diffed."""
    run_full_scan(spark)
    run_pruned_scan(spark)
    print_file_counts(spark)


if __name__ == "__main__":
    spark = get_spark("ProvePruning")

    prove_pruning(spark)

    spark.stop()