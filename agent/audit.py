import uuid
from datetime import datetime

from pyspark.sql.types import StructType, StructField, StringType, TimestampType, LongType
from spark_jobs.spark_session import get_spark

SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("user_role", StringType(), True),
    StructField("model", StringType(), True),
    StructField("question", StringType(), True),
    StructField("generated_sql", StringType(), True),
    StructField("snapshot_id", LongType(), True),
    StructField("execution_time_ms", LongType(), True),
    StructField("answer", StringType(), True),
])


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
    spark.createDataFrame([row], schema=SCHEMA).writeTo("nessie.retail.audit_log").append()