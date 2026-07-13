import uuid
from datetime import datetime

from spark_jobs.spark_session import get_spark


def log_interaction(user_role, model, question, sql, snapshot_id,
                    execution_time_ms, answer):
    spark = get_spark()
    from pyspark.sql import Row

    row = Row(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        user_role=user_role,
        model=model,
        question=question,
        generated_sql=sql,
        snapshot_id=snapshot_id,
        execution_time_ms=execution_time_ms,
        answer=answer,
    )
    spark.createDataFrame([row]).writeTo("nessie.retail.audit_log").append()