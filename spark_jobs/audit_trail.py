from spark_jobs.spark_session import get_spark


def audit_trail(spark) -> None:
    # Database
    spark.sql("""
    CREATE TABLE IF NOT EXISTS nessie.retail.audit_log (
        event_id STRING,
        timestamp TIMESTAMP,
        user_role STRING,
        model STRING,
        question STRING,
        generated_sql STRING,
        snapshot_id BIGINT,
        execution_time_ms LONG,
        answer STRING
    ) USING iceberg
    PARTITIONED BY (days(timestamp))
    """)

if __name__ == "__main__":
    spark = get_spark()

    audit_trail(spark)
    spark.stop()