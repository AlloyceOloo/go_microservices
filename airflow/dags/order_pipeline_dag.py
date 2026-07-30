"""
order_pipeline_dag.py — JUMO Data Platform
Daily pipeline: Spark aggregation → data quality checks → email report.

Schedule: 01:00 UTC every day.

Task graph:
  run_spark_job
      │
      ├─ check_order_counts
      │       │
      └─ check_revenue_totals
              │
        send_quality_report
"""

import os
from datetime import datetime, timedelta

import pymysql
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.exceptions import AirflowException

# ── Connection helpers ────────────────────────────────────────────────────────

def _mysql_conn():
    return pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASS"],
        database=os.environ["MYSQL_DB"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def _pg_conn():
    return psycopg2.connect(
        host=os.environ["WAREHOUSE_HOST"],
        port=int(os.environ.get("WAREHOUSE_PORT", "5432")),
        dbname=os.environ["WAREHOUSE_DB"],
        user=os.environ["WAREHOUSE_USER"],
        password=os.environ["WAREHOUSE_PASS"],
    )


# ── Task callables ────────────────────────────────────────────────────────────

def check_order_counts(**context):
    """
    Compare count of complete orders in MySQL vs total_orders in warehouse.
    Fails if the absolute difference is > 1% of the MySQL count.
    Pushes results to XCom for the email report.
    """
    with _mysql_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE complete = 1")
            mysql_count = cur.fetchone()["cnt"]

    with _pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(SUM(total_orders), 0) FROM daily_order_summary")
            wh_count = int(cur.fetchone()[0])

    delta = abs(mysql_count - wh_count)
    threshold = max(1, int(mysql_count * 0.01))   # 1% tolerance, min 1

    result = {
        "mysql_count": mysql_count,
        "warehouse_count": wh_count,
        "delta": delta,
        "passed": delta <= threshold,
    }
    context["ti"].xcom_push(key="order_count_result", value=result)

    if not result["passed"]:
        raise AirflowException(
            f"Order count mismatch: MySQL={mysql_count}, warehouse={wh_count}, "
            f"delta={delta} exceeds 1% threshold ({threshold})"
        )


def check_revenue_totals(**context):
    """
    Compare SUM of (admin_revenue + ambassador_revenue) in MySQL order_items
    vs SUM in warehouse daily_order_summary.
    Fails if delta > $0.01.
    """
    with _mysql_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ROUND(SUM(oi.admin_revenue + oi.ambassador_revenue), 2) AS total
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.complete = 1
                """
            )
            row = cur.fetchone()
            mysql_total = float(row["total"] or 0)

    with _pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ROUND(COALESCE(SUM(total_admin_revenue + total_ambassador_revenue), 0), 2) "
                "FROM daily_order_summary"
            )
            wh_total = float(cur.fetchone()[0])

    delta = abs(mysql_total - wh_total)
    result = {
        "mysql_total": mysql_total,
        "warehouse_total": wh_total,
        "delta": round(delta, 2),
        "passed": delta <= 0.01,
    }
    context["ti"].xcom_push(key="revenue_result", value=result)

    if not result["passed"]:
        raise AirflowException(
            f"Revenue mismatch: MySQL=${mysql_total:.2f}, warehouse=${wh_total:.2f}, "
            f"delta=${delta:.2f} exceeds $0.01"
        )


def build_report(**context):
    """Assembles XCom results into an HTML email body, pushes to XCom."""
    ti = context["ti"]
    order_res   = ti.xcom_pull(task_ids="check_order_counts",   key="order_count_result")  or {}
    revenue_res = ti.xcom_pull(task_ids="check_revenue_totals", key="revenue_result")       or {}
    run_date    = context["ds"]

    def badge(passed):
        colour = "#22c55e" if passed else "#ef4444"
        label  = "PASS" if passed else "FAIL"
        return f'<span style="background:{colour};color:#fff;padding:2px 8px;border-radius:4px">{label}</span>'

    html = f"""
    <h2>JUMO Data Quality Report — {run_date}</h2>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse">
      <tr><th>Check</th><th>Source</th><th>Warehouse</th><th>Delta</th><th>Result</th></tr>
      <tr>
        <td>Order count</td>
        <td>{order_res.get('mysql_count', 'n/a')}</td>
        <td>{order_res.get('warehouse_count', 'n/a')}</td>
        <td>{order_res.get('delta', 'n/a')}</td>
        <td>{badge(order_res.get('passed', False))}</td>
      </tr>
      <tr>
        <td>Revenue total ($)</td>
        <td>{order_res.get('mysql_total', revenue_res.get('mysql_total', 'n/a'))}</td>
        <td>{revenue_res.get('warehouse_total', 'n/a')}</td>
        <td>{revenue_res.get('delta', 'n/a')}</td>
        <td>{badge(revenue_res.get('passed', False))}</td>
      </tr>
    </table>
    <p style="color:#6b7280;font-size:12px">Generated by Airflow · JUMO Data Platform</p>
    """
    context["ti"].xcom_push(key="report_html", value=html)
    return html


# ── DAG definition ────────────────────────────────────────────────────────────

default_args = {
    "owner":            "data-engineering",
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,   # handled by send_quality_report task
    "email_on_retry":   False,
}

with DAG(
    dag_id="order_pipeline",
    description="Spark aggregation → DQ checks → email report",
    schedule_interval="0 1 * * *",   # 01:00 UTC daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["jumo", "data-quality", "pipeline"],
) as dag:

    run_spark = DockerOperator(
        task_id="run_spark_job",
        image="jumo-spark-job:latest",          # built by cd-docker-push.yml
        container_name="airflow_spark_run",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="ambassador_network",
        environment={
            "MYSQL_HOST":      os.environ.get("MYSQL_HOST",      "ambassador_db"),
            "MYSQL_USER":      os.environ.get("MYSQL_USER",      "root"),
            "MYSQL_PASS":      os.environ.get("MYSQL_PASS",      "root"),
            "MYSQL_DB":        os.environ.get("MYSQL_DB",        "ambassador"),
            "WAREHOUSE_HOST":  os.environ.get("WAREHOUSE_HOST",  "warehouse_db"),
            "WAREHOUSE_PORT":  os.environ.get("WAREHOUSE_PORT",  "5432"),
            "WAREHOUSE_DB":    os.environ.get("WAREHOUSE_DB",    "warehouse"),
            "WAREHOUSE_USER":  os.environ.get("WAREHOUSE_USER",  "warehouse"),
            "WAREHOUSE_PASS":  os.environ.get("WAREHOUSE_PASS",  "warehouse"),
        },
    )

    t_order_counts = PythonOperator(
        task_id="check_order_counts",
        python_callable=check_order_counts,
        provide_context=True,
    )

    t_revenue = PythonOperator(
        task_id="check_revenue_totals",
        python_callable=check_revenue_totals,
        provide_context=True,
    )

    t_build_report = PythonOperator(
        task_id="build_report",
        python_callable=build_report,
        provide_context=True,
        trigger_rule="all_done",   # run even if checks fail
    )

    t_send_report = EmailOperator(
        task_id="send_quality_report",
        to=os.environ.get("DQ_ALERT_EMAIL", "admin@admin.com"),
        subject=f"JUMO DQ Report — {{{{ ds }}}}",
        html_content="{{ task_instance.xcom_pull(task_ids='build_report', key='report_html') }}",
        trigger_rule="all_done",
    )

    # run_spark → [check_order_counts, check_revenue_totals] → build_report → send
    run_spark >> [t_order_counts, t_revenue] >> t_build_report >> t_send_report
