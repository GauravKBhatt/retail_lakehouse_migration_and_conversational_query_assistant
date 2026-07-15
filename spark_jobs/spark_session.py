import glob
import os
import threading
from dotenv import load_dotenv
load_dotenv()

# Container-safe JVM options:
#   -XX:+UseContainerSupport   -> respect cgroup memory limits
#   -XX:MaxRAMPercentage=50    -> cap heap at 50% of container memory
#   -XX:+UseG1GC               -> low-pause GC for interactive workloads
# JAVA_TOOL_OPTIONS is read by the JVM at startup, before Py4J launches it,
# so these flags take effect even though .config(memory) comes later.
os.environ.setdefault(
    "JAVA_TOOL_OPTIONS",
    "-XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0 -XX:+UseG1GC",
)
os.environ["PYSPARK_SUBMIT_ARGS"] = "--driver-memory 2g --executor-memory 2g pyspark-shell"

from pyspark.sql import SparkSession

JAR_DIR = os.environ.get("SPARK_JAR_DIR", os.environ.get("JAR_DIR", os.path.expanduser("~/.ivy2/jars")))
NESSIE_URL = os.environ.get("NESSIE_URL", "http://localhost:19120/api/v1")
WAREHOUSE_DIR = os.environ.get("WAREHOUSE_DIR", "file:///D:/retail_lakehouse_migration_and_conversational_query_assistant/iceberg_warehouse")

# Module-level lock: protects session creation AND query execution.
# PySpark's SparkSession is not thread-safe for concurrent sql() calls.
_spark_lock = threading.Lock()
_spark_session: SparkSession | None = None


def _resolve_jars(jar_dir: str = JAR_DIR) -> str:
    """Return a comma-separated list of all jar files found under jar_dir."""
    jars = glob.glob(os.path.join(jar_dir, "**", "*.jar"), recursive=True)
    if not jars:
        raise FileNotFoundError(
            f"No jars found under {jar_dir!r}. Run get_spark() once with "
            "spark.jars.packages configured (or download the jars manually) "
            "before switching to spark.jars."
        )
    return ",".join(jars)


def get_spark(app_name: str = "RetailLakehouse") -> SparkSession:
    """Build (or fetch) a SparkSession wired up with Iceberg and Nessie.

    Thread-safe: the session is created once and reused across requests.
    """
    global _spark_session
    if _spark_session is not None:
        try:
            _spark_session.sparkContext.status
            return _spark_session
        except Exception:
            _spark_session = None

    with _spark_lock:
        if _spark_session is not None:
            try:
                _spark_session.sparkContext.status
                return _spark_session
            except Exception:
                _spark_session = None

        _spark_session = (
            SparkSession.builder
            .appName(app_name)
            .config("spark.driver.memory", "2g")
            .config("spark.driver.maxResultSize", "1g")
            .config("spark.jars", _resolve_jars())
            .config(
                "spark.sql.extensions",
                ",".join([
                    "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
                    "org.projectnessie.spark.extensions.NessieSparkSessionExtensions",
                ]),
            )
            .config("spark.sql.catalog.nessie",
                    "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.nessie.catalog-impl",
                    "org.apache.iceberg.nessie.NessieCatalog")
            .config("spark.sql.catalog.nessie.uri", NESSIE_URL)
            .config("spark.sql.catalog.nessie.ref", "main")
            .config("spark.sql.catalog.nessie.warehouse", WAREHOUSE_DIR)
            .getOrCreate()
        )
        return _spark_session


def run_sql(sql: str, app_name: str = "RetailLakehouse"):
    """Execute a SQL string under the Spark lock.

    Returns the Spark DataFrame result. Callers must call .collect(),
    .show(), etc. *before* releasing the lock (i.e. within the same
    ``with _spark_lock`` block), or simply use this helper which already
    holds the lock for the spark.sql() call.
    """
    spark = get_spark(app_name)
    return spark.sql(sql)


if __name__ == "__main__":
    spark = get_spark()
    print(spark.version)
    spark.stop()
