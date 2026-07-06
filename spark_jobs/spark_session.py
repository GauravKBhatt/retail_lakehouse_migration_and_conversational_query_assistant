import glob
import os
from dotenv import load_dotenv
load_dotenv()

# JVM is launched by py4j at getorcreate() and .config(memory) happens later thus, the java heap memory size remains the same. thus, setting the memory as a environment setting. 
os.environ["PYSPARK_SUBMIT_ARGS"] = "--driver-memory 4g --executor-memory 4g pyspark-shell"

from pyspark.sql import SparkSession

# this is for not lettings the spark download jars again and again. it can be skipped but spark will re-download jars everytime
JAR_DIR = os.environ.get(
    "SPARK_JAR_DIR",
    os.path.expanduser(os.environ["JAR_DIR"]),
)


def _resolve_jars(jar_dir: str = JAR_DIR) -> str:
    """Return a comma-separated list of all jar files found under jar_dir.

    Used to point spark.jars at locally cached jars instead of letting
    Spark re-resolve spark.jars.packages from Maven on every run.
    """
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

    Loads jars from local disk instead of Maven, and points the nessie
    catalog at the local Nessie server and a durable Iceberg warehouse
    directory.
    """
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
            "http://localhost:19120/api/v1"
        )
        .config(
            "spark.sql.catalog.nessie.ref",
            "main"
        )
        .config(
            "spark.sql.catalog.nessie.warehouse",
            "file:///D:/retail_lakehouse_migration_and_conversational_query_assistant/iceberg_warehouse"
        )
        .getOrCreate()
    )


if __name__ == "__main__":
    spark = get_spark()
    print(spark.version)
    spark.stop()