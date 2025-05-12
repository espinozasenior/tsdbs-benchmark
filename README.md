# TSDBs

## QuestDB - Airbus

QuestDB is the fastest growing open-source time-series database offering **blazingly fast, high throughput ingestion** and **dynamic, low-latency SQL queries**. The entire high-performance codebase is built from the ground up in Java, C++ and Rust with no dependencies and zero garbage collection.

We achieve high performance via a column-oriented storage model, parallelized vector execution, SIMD instructions, and low-latency techniques. In addition, QuestDB is hardware efficient, with quick setup and operational efficiency.

https://questdb.com/download/

https://github.com/questdb/questdb

https://questdb.com/blog/2024/02/26/questdb-versus-influxdb/

**Docker deployment**

```bash
docker run -p 9000:9000 \
 -p 9009:9009 \
 -p 8812:8812 \
 -p 9003:9003 \
 -v "$(pwd):/root/.questdb/" questdb/questdb
```

**Homebrew installation**

```bash
brew install questdb
# To start questdb now and restart at login:
brew services start questdb
# Or, if you don't want/need a background service you can just run:
/opt/homebrew/opt/questdb/bin/questdb start -d /opt/homebrew/var/questdb -n -f
```

## Cassandra
Apache Cassandra is a highly scalable, fault-tolerant, partitioned, distributed, multi-model database designed to handle large amounts of structured and semi-structured data across many commodity servers.

https://github.com/apache/cassandra
https://github.com/Anant/awesome-cassandra
https://cassandra.link/post/advanced-time-series-with-cassandra
https://cassandra.link/post/apache-cassandra-data-partitioning
https://www.ksolves.com/blog/big-data/optimizing-cassandra-for-time-series-data

**Docker deployment**
```bash
docker run --name cassandra -d -e CASSANDRA_BROADCAST_ADDRESS=127.0.0.1 -p 9042:9042 cassandra:latest
```

## TimeScaleDB
TimescaleDB is an open source time-series database optimized for fast, scalable querying and analytical processing of time-series data. It extends the PostgreSQL database, adding functionality specifically for time-series data, while maintaining the familiar SQL query language and user interface.
htScaleDB

https://docs.timescale.com/getting-started/latest/services/
https://www.timescale.com/blog/cassandra-vs-timescaledb
https://github.com/timescale/timescaledb


```bash
docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password timescale/timescaledb-ha:pg17
```


# OLAP

## DuckDB  (In-memory database)

An analytics **in-process** SQL database. Think SQLite, but for analytics. Unlike other popular analytics databases, there is no DBMS server to install, update or maintain. All data is stored in a persistent, ****single-file database. DuckDB does not run as a separate process and can query Pandas data directly without importing or copying any data or query foreign data (csv, parquet, json files) without copying [[1]](https://duckdb.org/why_duckdb.html#duckdbissimple)

https://duckdb.org/

https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=macos&download_method=direct

https://github.com/davidgasquez/awesome-duckdb

https://github.com/apecloud/myduckserver

https://github.com/quackscience/duckdb-extension-httpserver

https://medium.com/@octavianzarzu/build-and-deploy-apps-with-duckdb-and-streamlit-in-under-one-hour-852cd31cccce

**Homebrew installation**

```bash
brew install duckdb
```

## StarRocks - AirBnb / Coinbase

StarRocks is a next-gen, high-performance analytical data warehouse that enables real-time, multi-dimensional, and highly concurrent data analysis. StarRocks has an MPP architecture and is equipped with a fully vectorized execution engine, a columnar storage engine that supports real-time updates, and is powered by a rich set of features including a fully-customized cost-based optimizer (CBO), intelligent materialized view and more. StarRocks supports real-time and batch data ingestion from a variety of data sources.

https://www.starrocks.io/blog/webinar_220315

https://github.com/StarRocks/StarRocks

https://celerdata.com/hubfs/Airbnb_Case_Study.pdf?hsLang=en

Benchmark: https://www.starrocks.io/blog/benchmark-test

**Docker deployment**

```json
docker run -p 9030:9030 -p 8030:8030 -p 8040:8040 -itd \
--name quickstart starrocks/allin1-ubuntu
```

## Ares DB - Uber

https://eng.uber.com/aresdb/

https://github.com/uber/aresdb?tab=readme-ov-file

## Apache Pinot - LinkedIn

https://pinot.apache.org/

https://github.com/apache/pinot?tab=readme-ov-file

# Resources

https://db-engines.com/en/ranking/time+series+dbms

# Testing

We are choosing **QuestDB, DuckDB, Cassandra and StarRocks**. Following the next criteria:

- **Easy deployment and configuration**: Docker, amount of parts to production ready
- **Plugins, tools and connectors**: Prometeo, Grafana, webviews, etc.
- **Query difficulty**: SQL-like query or self query.
- **Use cases and support**: community, implementations, production cases.
- **Time responses:** How fast are writing and query high scale data.
- **Cost effective**: How expensive are the resources in a production environment, self-hosted and cloud-hosted.

## Instance

**Amazon type t2.2xlarge: 32 RAM - 8vcpu**
We have build a **[Python script](https://github.com/espinozasenior/tsdbs-benchmark)** to write and query 10 millions of rows in my local computer to test how complex is the installation, connection and query building.

**First try** ⏲

<img width="632" alt="image-20250512-210259" src="https://github.com/user-attachments/assets/30788cf7-4c72-4bd6-9f49-9064923fa91a" />


**Second try** ⏲

<img width="641" alt="image" src="https://github.com/user-attachments/assets/7f51c7b7-82e9-4a55-b9a8-5391b79e1e43" />


## 🔄 Comparative: DuckDB, StarRocks, Cassandra, QuestDB, TimescaleDB

| **Criteria** | **DuckDB** | **StarRocks** | **Cassandra** | **QuestDB** | **TimescaleDB** |
| --- | --- | --- | --- | --- | --- |
| **Database Type** | Embedded OLAP | Distributed OLAP | Distributed NoSQL | Native Time-Series DB | Time-Series DB on RDBMS |
| **Core Engine** | C++ | C++ | Java | Java + C | PostgreSQL (C) |
| **Full SQL Support** | ✅ Yes | ✅ Yes | ⚠️ Partial (CQL) | ✅ Yes (Extended) | ✅ Yes (PostgreSQL-based) |
| **Real-Time Write Performance** | ⚠️ Limited | ✅ Yes | ✅ Yes | ✅ Excellent | ✅ Yes |
| **Read Performance** | ✅ Excellent | ✅ Excellent | ⚠️ Moderate | ✅ Excellent | ✅ Excellent |
| **Time-Series Optimization** | ❌ No | ⚠️ Partial | ⚠️ Possible, not ideal | ✅ Yes | ✅ Yes |
| **Horizontal Scalability** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes (Enterprise only) |
| **Grafana Integration** | ⚠️ Indirect | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Kafka Integration** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Ideal Use Case** | Local data analysis | Large-scale dashboards | High write availability | IoT/Financial TS data | TS data with full SQL |
| **Deployment** | Easiest | Easy | Medium (need nodes and some config for time serie optimization) | Very easy | Easy (some config for production optimization) |
| **API - Tools** | DuckDB-Wasm Pandas direct integration | Data lakes integrations Kafka S3 / GCS / HDFS BI: Superset, Power BI, Grafana | **Kafka**, **Spark**, **Flink**BI tools (indirect): via **Trino/Presto**, **Spark SQL** Monitoring: **Grafana**, **Prometheus**, **OpsCenter** | [Grafana-native plugin](https://questdb.io/docs/third-party-tools/grafana/) [Webview](https://demo.questdb.io/index.html) API REST for bulk imports and exports | Telegraf, Kafka Connect, Prometheus, Timescale Forge **Data ingestion**: REST, MQTT (indirecto), ingestion through COPY/INSERT/Batch Multinode clustering |
