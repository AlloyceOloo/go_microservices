FROM bitnami/spark:3.5

USER root

# Download JDBC drivers into /opt/spark/jars (bitnami puts jars here)
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar" \
    -o /opt/bitnami/spark/jars/mysql-connector-j-8.3.0.jar && \
    curl -fsSL \
    "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar" \
    -o /opt/bitnami/spark/jars/postgresql-42.7.3.jar

WORKDIR /app

COPY jobs/ ./jobs/

USER 1001

ENTRYPOINT ["spark-submit", \
    "--master", "local[2]", \
    "--driver-memory", "256m", \
    "--executor-memory", "384m", \
    "/app/jobs/aggregate_orders.py"]
