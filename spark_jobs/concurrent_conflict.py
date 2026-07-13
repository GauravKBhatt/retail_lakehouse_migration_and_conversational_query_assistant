import multiprocessing
import time
from datetime import date 
from pyspark.sql import Row
from spark_jobs.spark_session import get_spark

def writer(job_id: int = 0, delay: float = 0.0, errors_list=None) -> bool:
    """
    Append a single sales record to the Iceberg table after an optional delay.

    Args:
        job_id: Identifier used to generate a unique order ID.
        delay: Number of seconds to wait before writing.
        errors_list: Shared list for collecting errors across processes.

    Returns:
        True if the write succeeds, otherwise False. On failure, the exception
        details are appended to the shared errors list.
    """
    time.sleep(delay)

    try:
        spark = get_spark()
        rows = [
            Row(
                order_id=9_000_000 + job_id,
                order_date=date(2024,1,15),
                product_id=1,
                store_id=1,
                customer_id=1,
                quantity=1,
                unit_price=9.99,
                total_amount=9.99,
            )
        ]

        spark.createDataFrame(rows).writeTo(
            "nessie.retail.fact_sales"
        ).append()

        print(f"Job {job_id} committed successfully")
        return True

    except Exception as exc:
        if errors_list is not None:
            errors_list.append({"job_id": job_id, "error": str(exc)})
        print(f"Job {job_id} FAILED: {exc}")
        return False

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    errors = manager.list()

    p1 = multiprocessing.Process(target=writer, args=(1, 0, errors))
    p2 = multiprocessing.Process(target=writer, args=(2, 0.05, errors))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    if errors:
        spark = get_spark()
        err_df = spark.createDataFrame(list(errors))
        err_df.writeTo('nessie.retail.commit_conflicts').createOrReplace()
        print(f'Persisted {len(errors)} conflict(s) to nessie.retail.commit_conflicts')