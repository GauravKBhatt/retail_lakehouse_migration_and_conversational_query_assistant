import glob
import os
from dotenv import load_dotenv
load_dotenv()
from pyspark.sql import SparkSession

# this is for not lettings the spark download jars again and again. it can be skipped but spark will re-download jars everytime
JAR_DIR = os.environ.get(
    "SPARK_JAR_DIR",
    os.path.expanduser(os.environ["JAR_DIR"]),
)


def _resolve_jars(jar_dir: str = JAR_DIR) -> str:
    jars = glob.glob(os.path.join(jar_dir, "**", "*.jar"), recursive=True)
    if not jars:
        raise FileNotFoundError(
            f"No jars found under {jar_dir!r}. Run get_spark() once with "
            "spark.jars.packages configured (or download the jars manually) "
            "before switching to spark.jars."
        )
    return ",".join(jars)


def get_spark(app_name: str = "RetailLakehouse") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
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
            "file:///tmp/iceberg_warehouse"
        )
        .getOrCreate()
    )


if __name__ == "__main__":
    spark = get_spark()
    print(spark.version)
    spark.stop()