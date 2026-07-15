import uuid
from datetime import datetime

from spark_jobs.spark_session import get_spark, _spark_lock


def log_interaction(user_role, model, question, sql, snapshot_id,
                    execution_time_ms, answer):
    spark = get_spark()

    event_id = str(uuid.uuid4())
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    snapshot_val = str(snapshot_id) if snapshot_id is not None else "NULL"
    exec_val = str(execution_time_ms) if execution_time_ms is not None else "NULL"

    # Escape single quotes in string values
    def esc(val):
        if val is None:
            return "NULL"
        return "'" + str(val).replace("'", "''") + "'"

    insert_sql = f"""
        INSERT INTO nessie.retail.audit_log VALUES (
            {esc(event_id)},
            TIMESTAMP '{ts}',
            {esc(user_role)},
            {esc(model)},
            {esc(question)},
            {esc(sql)},
            {snapshot_val},
            {exec_val},
            {esc(answer)}
        )
    """
    try:
        with _spark_lock:
            spark.sql(insert_sql)
    except Exception:
        pass  # audit_log table not yet created
