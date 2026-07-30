"""
aggregate_orders.py — JUMO Data Platform
Reads completed orders from MySQL ambassador DB,
aggregates revenue metrics, writes to PostgreSQL warehouse.
"""

import os
import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def get_env(key: str, fallback: str = "") -> str:
    return os.environ.get(key, fallback)


def build_mysql_url() -> str:
    host = get_env("MYSQL_HOST", "ambassador_db")
    port = get_env("MYSQL_PORT", "3306")
    db   = get_env("MYSQL_DB",   "ambassador")
    return f"jdbc:mysql://{host}:{port}/{db}?useSSL=false&allowPublicKeyRetrieval=true"


def build_pg_url() -> str:
    host = get_env("WAREHOUSE_HOST", "warehouse_db")
    port = get_env("WAREHOUSE_PORT", "5432")
    db   = get_env("WAREHOUSE_DB",   "warehouse")
    return f"jdbc:postgresql://{host}:{port}/{db}"


def mysql_props() -> dict:
    return {
        "user":   get_env("MYSQL_USER", "root"),
        "password": get_env("MYSQL_PASS", "root"),
        "driver": "com.mysql.cj.jdbc.Driver",
    }


def pg_props() -> dict:
    return {
        "user":   get_env("WAREHOUSE_USER", "warehouse"),
        "password": get_env("WAREHOUSE_PASS", "warehouse"),
        "driver": "org.postgresql.Driver",
    }


def main():
    spark = (
        SparkSession.builder
        .appName("jumo-aggregate-orders")
        .config("spark.sql.shuffle.partitions", "4")   # low for small data on i3
        .config("spark.executor.memory", "384m")
        .config("spark.driver.memory", "256m")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    mysql_url   = build_mysql_url()
    pg_url      = build_pg_url()
    mysql_opts  = mysql_props()
    pg_opts     = pg_props()

    print("Reading orders and order_items from MySQL…")

    orders = (
        spark.read
        .format("jdbc")
        .option("url", mysql_url)
        .option("dbtable", "orders")
        .options(**mysql_opts)
        .load()
        .filter(F.col("complete") == True)
    )

    order_items = (
        spark.read
        .format("jdbc")
        .option("url", mysql_url)
        .option("dbtable", "order_items")
        .options(**mysql_opts)
        .load()
    )

    # Join orders → items, add window_date from orders.created_at
    joined = (
        order_items
        .join(orders.select("id", "ambassador_email", "created_at"),
              order_items.order_id == orders.id, "inner")
        .withColumn("window_date", F.to_date(F.col("created_at")))
    )

    # ── 1. Revenue by ambassador ──────────────────────────────────────────────
    rev_by_ambassador = (
        joined
        .groupBy("ambassador_email", "window_date")
        .agg(
            F.round(F.sum("ambassador_revenue"), 2).alias("total_revenue"),
            F.countDistinct("order_id").alias("order_count"),
        )
    )

    # ── 2. Revenue by product ─────────────────────────────────────────────────
    rev_by_product = (
        joined
        .groupBy("product_title", "window_date")
        .agg(
            F.round(F.sum(F.col("price") * F.col("quantity")), 2).alias("total_revenue"),
            F.sum("quantity").cast("integer").alias("units_sold"),
        )
    )

    # ── 3. Daily order summary ────────────────────────────────────────────────
    daily_summary = (
        joined
        .groupBy("window_date")
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.round(F.sum("admin_revenue"), 2).alias("total_admin_revenue"),
            F.round(F.sum("ambassador_revenue"), 2).alias("total_ambassador_revenue"),
        )
    )

    # ── Write to PostgreSQL warehouse ─────────────────────────────────────────
    def write_pg(df, table: str):
        print(f"Writing {df.count()} rows to {table}…")
        (
            df.write
            .format("jdbc")
            .option("url", pg_url)
            .option("dbtable", table)
            .options(**pg_opts)
            .mode("overwrite")   # full refresh per run
            .save()
        )

    write_pg(rev_by_ambassador, "revenue_by_ambassador")
    write_pg(rev_by_product,    "revenue_by_product")
    write_pg(daily_summary,     "daily_order_summary")

    # ── Update pipeline metadata ──────────────────────────────────────────────
    # Write last_run timestamp as a single-row dataframe
    metadata = spark.createDataFrame(
        [("last_spark_run", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))],
        schema=["key", "value"],
    )
    (
        metadata.write
        .format("jdbc")
        .option("url", pg_url)
        .option("dbtable", "pipeline_metadata")
        .options(**pg_opts)
        .mode("append")
        .save()
    )

    print("Aggregation complete.")
    spark.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
