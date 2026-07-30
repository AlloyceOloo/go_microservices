"""
test_aggregate_orders.py — smoke test for the Spark aggregation logic.
Runs entirely in-memory; no MySQL or PostgreSQL required.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType,
    IntegerType, BooleanType, TimestampType,
)
from datetime import datetime


@pytest.fixture(scope="session")
def spark():
    return (
        SparkSession.builder
        .master("local[1]")
        .appName("test-aggregate-orders")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.driver.memory", "256m")
        .getOrCreate()
    )


def make_orders(spark):
    schema = StructType([
        StructField("id",               IntegerType(), False),
        StructField("ambassador_email", StringType(),  True),
        StructField("complete",         BooleanType(), False),
        StructField("created_at",       TimestampType(), True),
    ])
    ts = datetime(2024, 1, 15, 10, 0, 0)
    data = [
        (1, "alice@test.com", True,  ts),
        (2, "bob@test.com",   True,  ts),
        (3, "alice@test.com", False, ts),   # incomplete — should be excluded
    ]
    return spark.createDataFrame(data, schema)


def make_order_items(spark):
    schema = StructType([
        StructField("order_id",           IntegerType(), False),
        StructField("product_title",      StringType(),  True),
        StructField("price",              FloatType(),   True),
        StructField("quantity",           IntegerType(), True),
        StructField("ambassador_revenue", FloatType(),   True),
        StructField("admin_revenue",      FloatType(),   True),
    ])
    data = [
        (1, "Widget A", 100.0, 2, 20.0, 180.0),
        (1, "Widget B", 50.0,  1,  5.0,  45.0),
        (2, "Widget A", 100.0, 1, 10.0,  90.0),
    ]
    return spark.createDataFrame(data, schema)


def test_revenue_by_ambassador(spark):
    orders      = make_orders(spark).filter(F.col("complete") == True)
    order_items = make_order_items(spark)

    joined = (
        order_items
        .join(orders.select("id", "ambassador_email", "created_at"),
              order_items.order_id == orders.id, "inner")
        .withColumn("window_date", F.to_date(F.col("created_at")))
    )

    result = (
        joined
        .groupBy("ambassador_email", "window_date")
        .agg(F.round(F.sum("ambassador_revenue"), 2).alias("total_revenue"))
        .orderBy("ambassador_email")
        .collect()
    )

    emails = [r.ambassador_email for r in result]
    assert "alice@test.com" in emails
    assert "bob@test.com"   in emails

    alice = next(r for r in result if r.ambassador_email == "alice@test.com")
    # orders 1 only (order 3 is incomplete): 20 + 5 = 25
    assert float(alice.total_revenue) == pytest.approx(25.0)

    bob = next(r for r in result if r.ambassador_email == "bob@test.com")
    assert float(bob.total_revenue) == pytest.approx(10.0)


def test_daily_summary_excludes_incomplete(spark):
    orders      = make_orders(spark).filter(F.col("complete") == True)
    order_items = make_order_items(spark)

    joined = (
        order_items
        .join(orders.select("id", "ambassador_email", "created_at"),
              order_items.order_id == orders.id, "inner")
        .withColumn("window_date", F.to_date(F.col("created_at")))
    )

    summary = (
        joined
        .groupBy("window_date")
        .agg(F.countDistinct("order_id").alias("total_orders"))
        .collect()
    )

    # Only 2 complete orders (order 3 was incomplete)
    assert summary[0].total_orders == 2


def test_revenue_by_product(spark):
    orders      = make_orders(spark).filter(F.col("complete") == True)
    order_items = make_order_items(spark)

    joined = (
        order_items
        .join(orders.select("id", "ambassador_email", "created_at"),
              order_items.order_id == orders.id, "inner")
        .withColumn("window_date", F.to_date(F.col("created_at")))
    )

    result = (
        joined
        .groupBy("product_title", "window_date")
        .agg(
            F.round(F.sum(F.col("price") * F.col("quantity")), 2).alias("total_revenue"),
            F.sum("quantity").cast("integer").alias("units_sold"),
        )
        .orderBy("product_title")
        .collect()
    )

    widget_a = next(r for r in result if r.product_title == "Widget A")
    # orders 1 (qty 2) + order 2 (qty 1) = 3 units, revenue 100*2 + 100*1 = 300
    assert widget_a.units_sold == 3
    assert float(widget_a.total_revenue) == pytest.approx(300.0)
