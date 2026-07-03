from pyspark.sql import DataFrame, SparkSession

from spark_jobs.spark_session import get_spark

DIM_TABLES = ["dim_product", "dim_date", "dim_store", "dim_customer"]

DATA_DIR = "data"


def read_csv(spark: SparkSession, path: str) -> DataFrame:
    """Read a CSV file with header and inferred schema."""
    return spark.read.option("header", True).option("inferSchema", True).csv(path)


def load_dimensions(spark: SparkSession, dims: list[str] = DIM_TABLES) -> None:
    """Load each dimension CSV and overwrite the corresponding Iceberg table.

    Dimensions are small, so a full overwrite on every run is cheap and
    keeps the job idempotent without needing merge logic.
    """
    for dim in dims:
        df = read_csv(spark, f"{DATA_DIR}/{dim}.csv")
        df.writeTo(f"nessie.retail.{dim}").overwritePartitions()
        print(f"Loaded {dim}")


def load_fact_sales(spark: SparkSession, path: str = f"{DATA_DIR}/fact_sales.csv") -> None:
    """Load fact_sales.csv into Iceberg using MERGE INTO on order_id.

    Only rows with an order_id not already present get inserted, so
    re-running this job does not create duplicate rows.
    """
    fact_df = read_csv(spark, path)
    fact_df.createOrReplaceTempView("fact_staging")

    spark.sql("""
        MERGE INTO nessie.retail.fact_sales t
        USING fact_staging s
        ON t.order_id = s.order_id
        WHEN NOT MATCHED THEN INSERT *
    """)

    print("Loaded fact_sales")


def get_latest_snapshot_id(spark: SparkSession, table: str = "nessie.retail.fact_sales") -> int:
    """Return the snapshot_id of the most recent commit on a table.

    Used to capture a snapshot reference for the time-travel demo in Task 7.
    """
    snap = spark.sql(
        f"SELECT snapshot_id FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1"
    )
    return snap.collect()[0][0]


def run_ingest(spark: SparkSession) -> int:
    """Run the full ingest job and return the latest fact_sales snapshot_id."""
    load_dimensions(spark)
    load_fact_sales(spark)
    return get_latest_snapshot_id(spark)


if __name__ == "__main__":
    spark = get_spark("RetailIngest")

    snapshot_id = run_ingest(spark)
    print(f"SNAPSHOT_ID={snapshot_id}")

    spark.sql("SELECT COUNT(*) FROM nessie.retail.fact_sales").show()

    spark.stop()