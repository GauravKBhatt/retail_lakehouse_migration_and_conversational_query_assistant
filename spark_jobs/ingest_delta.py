import sys
from pyspark.sql import SparkSession
from spark_jobs.spark_session import get_spark


def ingest_batch(batch_num: int) -> None:
    spark = get_spark("IngestDelta")
    path = f"data/delta_batch_{batch_num}.csv"

    df = spark.read.option("header", True).option("inferSchema", True).csv(path)
    df.createOrReplaceTempView("delta_staging")

    spark.sql("""
        MERGE INTO nessie.retail.fact_sales t
        USING delta_staging s
        ON t.order_id = s.order_id
        WHEN NOT MATCHED THEN INSERT *
    """)

    count = spark.sql("SELECT COUNT(*) FROM nessie.retail.fact_sales").collect()[0][0]
    snaps = spark.sql(
        "SELECT snapshot_id, committed_at FROM nessie.retail.fact_sales.snapshots ORDER BY committed_at"
    ).collect()

    print(f"Batch {batch_num} ingested. Total rows: {count}")
    for s in snaps:
        print(f"  snap={s['snapshot_id']}  at={s['committed_at']}")

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m spark_jobs.ingest_delta <batch_number>")
        sys.exit(1)
    ingest_batch(int(sys.argv[1]))
