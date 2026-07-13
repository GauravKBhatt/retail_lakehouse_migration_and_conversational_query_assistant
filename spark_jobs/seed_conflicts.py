"""Seed the commit_conflicts metadata table with a synthetic record.

Run once to populate the table so the agent's get_commit_conflicts tool
has data to retrieve:

    .venv/Scripts/python -m spark_jobs.seed_conflicts
"""

from spark_jobs.spark_session import get_spark

spark = get_spark("SeedConflicts")

spark.sql("""
    CREATE TABLE IF NOT EXISTS nessie.retail.commit_conflicts (
        job_id INT,
        error  STRING
    ) USING iceberg
""")

spark.sql("""
    INSERT INTO nessie.retail.commit_conflicts
    VALUES (1, 'CommitFailedException: Table nessie.retail.fact_sales modified by
    another transaction while this commit was in progress. Conflicting partition:
    order_date=2024-01-15')
""")

print("Seeded 1 conflict record into nessie.retail.commit_conflicts")
spark.sql("SELECT * FROM nessie.retail.commit_conflicts").show(truncate=False)
