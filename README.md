# TSDBs

## QuestDB - Airbus

QuestDB is the fastest growing open-source time-series database offering **blazingly fast, high throughput ingestion** and **dynamic, low-latency SQL queries**. The entire high-performance codebase is built from the ground up in Java, C++ and Rust with no dependencies and zero garbage collection.

We achieve high performance via a column-oriented storage model, parallelized vector execution, SIMD instructions, and low-latency techniques. In addition, QuestDB is hardware efficient, with quick setup and operational efficiency.

https://questdb.com/download/

https://github.com/questdb/questdb

https://questdb.com/blog/2024/02/26/questdb-versus-influxdb/

**Docker deployment**

```json
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

![image.png](attachment:e755a6e1-43fd-4591-86bd-e2d5a7ac194a:image.png)

| **Database** | **Type** | **API - Tools - Access Methods** | **Language** | **Queries** | **Distributed system compatibility** | **Deployment** |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **QuestDB** | Time Series DBMS | [Grafana-native plugin](https://questdb.io/docs/third-party-tools/grafana/)
[Webview](https://demo.questdb.io/index.html)
API REST for bulk imports and exports | Java (low latency, zero-GC), C++ | SQL | Good with Kafka, Flink, Spark | EASY |  |
| **InfluxDB** | Time Series DBMS | HTTP API (including InfluxDB Line Protocol), JSON over UDP | Go | InfluxQL Flux |  | N/A |  |
| **DuckDB** |  |  |  | SQL |  | VERY EASY |  |
| **StarRocks** |  |  |  | SQL (MYSQL connector) |  | EASY |  |