from spark_jobs.spark_session import get_spark


def create_tables(spark) -> None:
    # Database
    spark.sql("CREATE DATABASE IF NOT EXISTS nessie.retail")

    # Step 1: Dimension tables (small, no partitioning)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.retail.dim_product (
            product_id BIGINT,
            name STRING,
            category STRING,
            subcategory STRING,
            brand STRING,
            cost_price DOUBLE
        ) USING iceberg
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.retail.dim_date (
            date_id BIGINT,
            full_date DATE,
            year INT,
            quarter INT,
            month INT,
            week INT,
            day_of_week STRING
        ) USING iceberg
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.retail.dim_store (
            store_id BIGINT,
            name STRING,
            city STRING,
            state STRING,
            region STRING,
            store_type STRING
        ) USING iceberg
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.retail.dim_customer (
            customer_id BIGINT,
            segment STRING,
            join_date DATE,
            lifetime_value_bucket STRING
        ) USING iceberg
    """)

    # Step 2: Fact table, hidden partitioning on order_date 

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.retail.fact_sales (
            order_id BIGINT,
            order_date DATE,
            product_id BIGINT,
            store_id BIGINT,
            customer_id BIGINT,
            quantity INT,
            unit_price DOUBLE,
            total_amount DOUBLE
        ) USING iceberg
        PARTITIONED BY (days(order_date))
    """)


if __name__ == "__main__":
    spark = get_spark()

    create_tables(spark)

    # Step 3: Verify table creation
    spark.sql("SHOW TABLES IN nessie.retail").show()

    spark.stop()