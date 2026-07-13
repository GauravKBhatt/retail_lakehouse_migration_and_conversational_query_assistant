"""Simulate an Iceberg optimistic-concurrency conflict on Windows.

PySpark's threading and multiprocessing both crash on Windows when two
threads/processes share the same JVM or try to write to Iceberg concurrently.

The fix: launch a *subprocess* (separate Python process via ``subprocess.Popen``)
so each writer gets its own SparkSession and JVM. The conflict happens at the
Nessie catalog level — two Nessie commits to the same branch at the same time.
"""

import subprocess
import sys
import time
from spark_jobs.spark_session import get_spark

ERRORS = []

# Competitor code that runs in a separate process.
# Uses SQL INSERT (not DataFrame) to avoid the Python worker crash
# that plagues PySpark DataFrame writes on Windows.
COMPETITOR_SCRIPT = """\
import sys, time
sys.path.insert(0, "{project_root}")
from spark_jobs.spark_session import get_spark

spark = get_spark("CompetitorWriter")

# Build 50 rows so the commit takes longer, widening the conflict window.
rows = []
for i in range(2, 52):
    rows.append("(900%06d, DATE '2024-01-15', 1, 1, 1, 1, 9.99, 9.99)" % i)
values = ",".join(rows)

time.sleep(0.1)  # let the main process start its commit first

try:
    spark.sql("INSERT INTO nessie.retail.fact_sales VALUES " + values)
    print("COMPETITOR_COMMITTED")
except Exception as e:
    print("COMPETITOR_FAILED: " + str(e))
"""


def run_competitor(project_root: str) -> subprocess.Popen:
    """Launch a separate Python process that writes to the same partition."""
    code = COMPETITOR_SCRIPT.format(project_root=project_root)
    return subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


if __name__ == "__main__":
    import pathlib

    project_root = str(pathlib.Path(__file__).resolve().parent.parent)

    # Start the competitor — spins up its own Spark session,
    # then inserts 50 rows into the same January 2024 partition.
    competitor = run_competitor(project_root)

    # Brief pause so the competitor's Spark session is initialising,
    # then we also write to the same partition.
    time.sleep(0.05)

    try:
        spark = get_spark("MainWriter")
        spark.sql(
            "INSERT INTO nessie.retail.fact_sales "
            "VALUES (9000001, DATE '2024-01-15', 1, 1, 1, 1, 9.99, 9.99)"
        )
        print("Main writer committed successfully")
    except Exception as exc:
        ERRORS.append({"job_id": 1, "error": str(exc)})
        print(f"Main writer FAILED: {exc}")

    # Collect competitor result
    stdout, stderr = competitor.communicate(timeout=60)
    print(f"Competitor output:\n{stdout.strip()}")
    if stderr.strip():
        print(f"Competitor stderr:\n{stderr.strip()}")

    if "COMPETITOR_FAILED" in stdout:
        ERRORS.append({"job_id": 2, "error": stdout.strip()})

    # Persist any conflicts
    if ERRORS:
        spark = get_spark("ConflictRecorder")
        err_df = spark.createDataFrame(ERRORS)
        err_df.writeTo("nessie.retail.commit_conflicts").createOrReplace()
        print(f"Persisted {len(ERRORS)} conflict(s) to nessie.retail.commit_conflicts")
    else:
        print("No conflicts detected — both writes committed successfully.")
        print("Try reducing the delay or increasing write size for more overlap.")
