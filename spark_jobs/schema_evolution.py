from pyspark.sql import SparkSession

from spark_jobs.spark_session import get_spark

NEW_ROW = """
    INSERT INTO nessie.retail.fact_sales
    VALUES (9999999, CAST('2024-06-15' AS DATE), 1, 1, 1, 2, 49.99, 99.98, 0.10)
"""


def print_current_schema(spark: SparkSession) -> None:
    """Print the fact_sales schema and a few rows before any changes.

    Baseline snapshot for comparing against the schema after evolution.
    """
    print("=== SCHEMA BEFORE CHANGE ===")
    spark.sql("DESCRIBE nessie.retail.fact_sales").show()

    print("=== SAMPLE ROWS BEFORE CHANGE ===")
    spark.sql("SELECT * FROM nessie.retail.fact_sales LIMIT 5").show()


def add_discount_column(spark: SparkSession) -> None:
    """Add discount_pct to fact_sales via ALTER TABLE.

    Iceberg assigns this column a new Field ID rather than a position,
    so existing data files aren't rewritten and old rows just report
    NULL for it.
    """
    spark.sql("ALTER TABLE nessie.retail.fact_sales ADD COLUMN discount_pct DOUBLE")
    print("Added column discount_pct")


def show_old_rows_after_change(spark: SparkSession) -> None:
    """Query old rows and confirm discount_pct comes back NULL.

    This is the actual proof that Iceberg maps columns by Field ID: old
    data files have no discount_pct column at all, yet the query still
    resolves cleanly instead of erroring or misreading a column by position.
    """
    print("=== OLD ROWS AFTER SCHEMA CHANGE ===")
    df = spark.sql(
        "SELECT order_id, total_amount, discount_pct FROM nessie.retail.fact_sales LIMIT 10"
    )
    df.show()


def insert_row_with_discount(spark: SparkSession) -> None:
    """Insert a new row that populates discount_pct."""
    spark.sql(NEW_ROW)
    print("Inserted order_id=9999999 with discount_pct=0.10")


def compare_old_and_new_rows(spark: SparkSession) -> None:
    """Query an old row and the new row side by side.

    order_id=1 should show NULL discount_pct, order_id=9999999 should
    show 0.10 — proving old and new rows coexist under one evolved schema.
    """
    print("=== OLD VS NEW ROW ===")
    spark.sql(
        "SELECT order_id, discount_pct FROM nessie.retail.fact_sales WHERE order_id IN (1, 9999999)"
    ).show()


def demonstrate_schema_evolution(spark: SparkSession) -> None:
    """Run the full schema evolution demo end to end."""
    print_current_schema(spark)
    add_discount_column(spark)
    show_old_rows_after_change(spark)
    insert_row_with_discount(spark)
    compare_old_and_new_rows(spark)


if __name__ == "__main__":
    spark = get_spark("SchemaEvolution")

    demonstrate_schema_evolution(spark)

    spark.stop()