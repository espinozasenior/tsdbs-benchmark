# tsdbs-benchmark
History repository for stress testing of multiple time series database (TSDB) and online analytical processing (OLAP) database options

# Testing

We are choosing **QuestDB, DuckDB, Cassandra and StarRocks**. Following the next criteria:

- **Easy deployment and configuration**: Docker, amount of parts to production ready
- **Plugins, tools and connectors**: Prometeo, Grafana, webviews, etc.
- **Query difficulty**: SQL-like query or self query.
- **Use cases and support**: community, implementations, production cases.
- **Time responses:** How fast are writing and query high scale data.
- **Cost effective**: How expensive are the resources in a production environment, self-hosted and cloud-hosted.

## Localhost test

I’d build a Python script to load a 1.6 billion of NY's taxi trips records from 

### DuckDB

```
brew install duckdb
```
### QuestDB
**Docker deployment**
```
docker run -p 9000:9000 \
 -p 9009:9009 \
 -p 8812:8812 \
 -p 9003:9003 \
 -v "$(pwd):/root/.questdb/" questdb/questdb
```

### StarRocks
```
docker run -p 9030:9030 -p 8030:8030 -p 8040:8040 -itd \
--name quickstart starrocks/allin1-ubuntu
```