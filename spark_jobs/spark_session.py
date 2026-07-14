import glob
import os
from dotenv import load_dotenv
load_dotenv()

# JVM is launched by py4j at getorcreate() and .config(memory) happens later thus, the java heap memory size remains the same. thus, setting the memory as a environment setting. 
os.environ["PYSPARK_SUBMIT_ARGS"] = "--driver-memory 4g --executor-memory 4g pyspark-shell"

from pyspark.sql import SparkSession

JAR_DIR = os.environ.get("SPARK_JAR_DIR", os.environ.get("JAR_DIR", os.path.expanduser("~/.ivy2/jars")))
NESSIE_URL = os.environ.get("NESSIE_URL", "http://localhost:19120/api/v1")
WAREHOUSE_DIR = os.environ.get("WAREHOUSE_DIR", "file:///D:/retail_lakehouse_migration_and_conversational_query_assistant/iceberg_warehouse")


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
    """Build (or fetch) a SparkSession wired up with Iceberg and Nessie."""
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.driver.memory", "4g")
        .config("spark.driver.maxResultSize", "2g")
        .config("spark.jars", _resolve_jars())
        .config(
            "spark.sql.extensions",
            ",".join([
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
                "org.projectnessie.spark.extensions.NessieSparkSessionExtensions"
            ])
        )
        .config(
            "spark.sql.catalog.nessie",
            "org.apache.iceberg.spark.SparkCatalog"
        )
        .config(
            "spark.sql.catalog.nessie.catalog-impl",
            "org.apache.iceberg.nessie.NessieCatalog"
        )
        .config(
            "spark.sql.catalog.nessie.uri",
            NESSIE_URL
        )
        .config(
            "spark.sql.catalog.nessie.ref",
            "main"
        )
        .config(
            "spark.sql.catalog.nessie.warehouse",
            WAREHOUSE_DIR
        )
        .getOrCreate()
    )


if __name__ == "__main__":
    spark = get_spark()
    print(spark.version)
    spark.stop()
