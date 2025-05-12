import duckdb
from questdb.ingress import Sender, TimestampNanos
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, SimpleStatement
from cassandra.io.libevreactor import LibevConnection
import random
import uuid
import pandas as pd
import time
import random
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.schema import Table, MetaData, Column
from sqlalchemy.types import Integer, TIMESTAMP, Float, String

# --- Configuration ---
NUM_RECORDS = 10_000_000  # Number of records to generate
DUCKDB_TABLE_NAME = 'benchmark_table_duckdb'
QUESTDB_TABLE_NAME = 'benchmark_table_questdb'
STARROCKS_TABLE_NAME = 'benchmark_table_starrocks'
CASSANDRA_TABLE_NAME = 'benchmark_table_cassandra'
QUESTDB_HOST = '127.0.0.1'
QUESTDB_ILP_PORT = 9009
STARROCKS_HOST = '127.0.0.1'
STARROCKS_PORT = 9030
STARROCKS_USER = 'root'
STARROCKS_PASSWORD = ''
STARROCKS_DB = 'example_db'
CASSANDRA_KEYSPACE = 'iot_benchmark'
CASSANDRA_HOSTS = ['127.0.0.1']

# --- Data Generation ---
def generate_data(num_records):
    print(f"Generating {num_records} records...")
    data = []
    start_time = datetime(2023, 1, 1)
    for i in range(num_records):
        ts = start_time + timedelta(seconds=i)
        value1 = random.uniform(0, 100)
        value2 = f'category_{random.choice(["A", "B", "C", "D", "E"])}'
        data.append({'id': i, 'ts': ts, 'value1': value1, 'value2': value2})
    df = pd.DataFrame(data)
    print("Data generation complete.")
    return df

# --- DuckDB Functions ---
def setup_duckdb():
    print("Setting up DuckDB...")
    con = duckdb.connect(database=':memory:', read_only=False)
    # Or use a file: duckdb.connect(database='duckdb_benchmark.db', read_only=False)
    try:
        con.execute(f"DROP TABLE IF EXISTS {DUCKDB_TABLE_NAME}")
        con.execute(f"""
            CREATE TABLE {DUCKDB_TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                ts TIMESTAMP,
                value1 DOUBLE,
                value2 VARCHAR
            )
        """)
        print("DuckDB setup complete.")
    except Exception as e:
        print(f"Error setting up DuckDB: {e}")
        raise
    return con

def load_data_duckdb(con, df):
    print(f"Loading data into DuckDB table {DUCKDB_TABLE_NAME}...")
    start_time = time.time()
    try:
        con.register('source_df', df)
        con.execute(f"INSERT INTO {DUCKDB_TABLE_NAME} SELECT * FROM source_df")
        # For very large data, consider using con.execute(f"COPY source_df TO '{DUCKDB_TABLE_NAME}' (FORMAT PARQUET)") if df is saved as parquet
        # Or insert in chunks if memory is an issue with register
    except Exception as e:
        print(f"Error loading data into DuckDB: {e}")
        raise
    end_time = time.time()
    load_time = end_time - start_time
    print(f"DuckDB data loading complete. Time taken: {load_time:.2f} seconds.")
    return load_time

def query_duckdb(con):
    print("Querying DuckDB...")
    queries = {
        "count_all": f"SELECT COUNT(*) FROM {DUCKDB_TABLE_NAME}",
        "avg_value1": f"SELECT AVG(value1) FROM {DUCKDB_TABLE_NAME}",
        "filter_and_count": f"SELECT COUNT(*) FROM {DUCKDB_TABLE_NAME} WHERE value1 > 50 AND value2 = 'category_A'",
        "group_by_value2": f"SELECT value2, AVG(value1) FROM {DUCKDB_TABLE_NAME} GROUP BY value2",
        "time_window_query": f"SELECT COUNT(*) FROM {DUCKDB_TABLE_NAME} WHERE ts >= '2023-01-01 00:00:00' AND ts < '2023-01-01 01:00:00'"
    }
    results = {}
    for name, query_sql in queries.items():
        print(f"  Executing query '{name}': {query_sql}")
        start_time = time.time()
        try:
            result = con.execute(query_sql).fetchall()
            # print(f"    Result: {result}") # Optional: print query result
        except Exception as e:
            print(f"    Error executing query '{name}': {e}")
            result = None
        end_time = time.time()
        results[name] = end_time - start_time
        print(f"    Query '{name}' time: {results[name]:.4f} seconds.")
    print("DuckDB querying complete.")
    return results

# --- QuestDB Functions ---
# Note: QuestDB Python client typically uses InfluxDB Line Protocol (ILP).
# Ensure QuestDB is running and accessible on QUESTDB_HOST:QUESTDB_ILP_PORT.

def setup_questdb():
    # For QuestDB, table creation can happen implicitly on first data write with ILP if auto-create is enabled,
    # or explicitly via SQL (e.g., using requests library to hit the HTTP API on port 9000).
    # For simplicity with ILP, we'll rely on auto-creation or assume table exists.
    # To explicitly create/drop table, you'd use SQL via HTTP endpoint:
    # import requests
    requests.post(f'http://{QUESTDB_HOST}:9000/exec', params={'query': f'DROP TABLE IF EXISTS {QUESTDB_TABLE_NAME}'})
    requests.post(f'http://{QUESTDB_HOST}:9000/exec', params={'query': f'CREATE TABLE IF NOT EXISTS {QUESTDB_TABLE_NAME} (id LONG, ts TIMESTAMP, value1 DOUBLE, value2 SYMBOL) timestamp(ts) PARTITION BY DAY'})
    print(f"QuestDB setup: Table '{QUESTDB_TABLE_NAME}' will be written to. Ensure QuestDB is running.")
    # No explicit connection object needed for this ILP sender style, but we check connectivity conceptually.
    try:
        conf = (
            f"tcp::addr={QUESTDB_HOST}:{QUESTDB_ILP_PORT};"
            f"auto_flush_bytes=1024;"      # Flush if the internal buffer exceeds 1KiB
            f"auto_flush_rows=off;"        # Disable auto-flushing based on row count
            f"auto_flush_interval=5000;")  # Flush if last flushed more than 5s ago
        with Sender.from_conf(conf) as sender: # Use Sender.from_conf
            pass # Just to check if connection can be initiated
        print("QuestDB ILP sender can be initialized.")
    except Exception as e:
        print(f"Error initializing QuestDB ILP Sender (check if QuestDB is running on {QUESTDB_HOST}:{QUESTDB_ILP_PORT}): {e}")
        raise

def load_data_questdb(df):
    print(f"Loading data into QuestDB table {QUESTDB_TABLE_NAME} via ILP...")
    start_time = time.time()
    try:
        conf = (
            f"tcp::addr={QUESTDB_HOST}:{QUESTDB_ILP_PORT};"
            f"auto_flush_bytes=1024;"      # Flush if the internal buffer exceeds 1KiB
            f"auto_flush_rows=off;"        # Disable auto-flushing based on row count
            f"auto_flush_interval=5000;")  # Flush if last flushed more than 5s ago
        with Sender.from_conf(conf) as sender: # Use Sender.from_conf
            for index, row in df.iterrows():
                sender.row(
                    QUESTDB_TABLE_NAME,
                    symbols={'value2': str(row['value2'])}, # Ensure value2 is string for SYMBOL type
                    columns={'id': int(row['id']), 'value1': float(row['value1'])},
                    at=row['ts']
                )
                if (index + 1) % 10000 == 0:
                    sender.flush()
                    print(f"  {index + 1}/{len(df)} records sent to QuestDB...")
            sender.flush() # Final flush
    except Exception as e:
        print(f"Error loading data into QuestDB: {e}")
        raise
    end_time = time.time()
    load_time = end_time - start_time
    print(f"QuestDB data loading complete. Time taken: {load_time:.2f} seconds.")
    return load_time

def query_questdb():
    print("Querying QuestDB (via HTTP API). Ensure QuestDB HTTP is enabled on port 9000.")
    import requests # Using requests for SQL queries as official client is ILP focused
    questdb_http_port = 9000
    queries = {
        "count_all": f"SELECT COUNT() FROM {QUESTDB_TABLE_NAME}",
        "avg_value1": f"SELECT AVG(value1) FROM {QUESTDB_TABLE_NAME}",
        "filter_and_count": f"SELECT COUNT() FROM {QUESTDB_TABLE_NAME} WHERE value1 > 50 AND value2 = 'category_A'",
        "group_by_value2": f"SELECT value2, AVG(value1) FROM {QUESTDB_TABLE_NAME} GROUP BY value2",
        "time_window_query": f"SELECT COUNT() FROM {QUESTDB_TABLE_NAME} WHERE ts >= '2023-01-01T00:00:00.000000Z' AND ts < '2023-01-01T01:00:00.000000Z'"
    }
    results = {}
    for name, query_sql in queries.items():
        print(f"  Executing query '{name}': {query_sql}")
        start_time = time.time()
        try:
            response = requests.get(f'http://{QUESTDB_HOST}:{questdb_http_port}/exec', params={'query': query_sql})
            response.raise_for_status() # Raise an exception for HTTP errors
            query_result_json = response.json()
            # print(f"    Result: {query_result_json['dataset']}") # Optional: print query result
        except Exception as e:
            print(f"    Error executing query '{name}': {e}")
            query_result_json = None
        end_time = time.time()
        results[name] = end_time - start_time
        print(f"    Query '{name}' time: {results[name]:.4f} seconds.")
    print("QuestDB querying complete.")
    return results

# --- StarRocks Functions --- (New Section)
def setup_starrocks():
    print("Setting up StarRocks...")
    db_name = STARROCKS_DB # Use STARROCKS_DB directly as the database name

    # Step 1: Connect to the StarRocks server to create the target database.
    # First, try connecting to the server root (like `mysql -h host -P port -u user`).
    engine_admin_url = f'starrocks://{STARROCKS_USER}:{STARROCKS_PASSWORD}@{STARROCKS_HOST}:{STARROCKS_PORT}/'
    engine_admin = create_engine(engine_admin_url)
    db_created_successfully = False

    try:
        with engine_admin.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
            connection.commit()
            print(f"Database '{db_name}' ensured using URL: {engine_admin_url}")
            db_created_successfully = True
    except Exception as e_db_create_root:
        print(f"Error creating database '{db_name}' using root URL '{engine_admin_url}': {e_db_create_root}")
        # If root connection failed for DB creation, try via 'default_catalog'
        # This assumes 'default_catalog' exists and allows DB creation from its context.
        print("Attempting database creation via 'default_catalog'...")
        if 'engine_admin' in locals():
            engine_admin.dispose() # Dispose previous engine
        
        engine_admin_url_fallback = f'starrocks://{STARROCKS_USER}:{STARROCKS_PASSWORD}@{STARROCKS_HOST}:{STARROCKS_PORT}/default_catalog'
        engine_admin = create_engine(engine_admin_url_fallback)
        try:
            with engine_admin.connect() as connection_fallback:
                connection_fallback.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
                connection_fallback.commit()
                print(f"Database '{db_name}' ensured using fallback URL: {engine_admin_url_fallback}")
                db_created_successfully = True
        except Exception as e_db_create_fallback:
            print(f"Error creating database '{db_name}' using fallback URL '{engine_admin_url_fallback}': {e_db_create_fallback}")
            # If both attempts fail, re-raise the last error.
            if 'engine_admin' in locals():
                engine_admin.dispose()
            raise e_db_create_fallback
    finally:
        if 'engine_admin' in locals():
            engine_admin.dispose()

    if not db_created_successfully:
        # This case should ideally be caught by the exceptions above, but as a safeguard:
        raise Exception(f"Failed to create database '{db_name}' after all attempts.")

    # Step 2: Connect directly to the newly ensured database
    engine_db_url = f'starrocks://{STARROCKS_USER}:{STARROCKS_PASSWORD}@{STARROCKS_HOST}:{STARROCKS_PORT}/{db_name}'
    engine = create_engine(engine_db_url)

    try:
        with engine.connect() as connection:
            # Now operating within the context of `db_name`
            connection.execute(text(f"DROP TABLE IF EXISTS {STARROCKS_TABLE_NAME}"))
            # Table name is now just STARROCKS_TABLE_NAME as we are connected to the db_name
            create_table_sql = f"""
            CREATE TABLE {STARROCKS_TABLE_NAME} (
                id INT,
                ts DATETIME,
                value1 DOUBLE,
                value2 VARCHAR(255)
            )
            ENGINE=OLAP
            PRIMARY KEY(id)
            DISTRIBUTED BY HASH(id)
            PROPERTIES(
                "replication_num" = "1"
            )
            """
            connection.execute(text(create_table_sql))
            connection.commit() # Ensure DDL is committed
        print(f"StarRocks setup complete. Table '{STARROCKS_TABLE_NAME}' created in database '{db_name}'.")
    except Exception as e:
        # This error is for connection to db_name or table operations within it.
        print(f"Error setting up StarRocks table '{STARROCKS_TABLE_NAME}' in database '{db_name}' using URL '{engine_db_url}': {e}")
        if 'engine' in locals():
            engine.dispose()
        raise # Re-raise the primary exception for table setup
    return engine

def load_data_starrocks(engine, df):
    # engine is now connected to the specific database (e.g., example_db from STARROCKS_DB)
    db_name = STARROCKS_DB
    print(f"Loading data into StarRocks table {STARROCKS_TABLE_NAME} in database {db_name}...")
    start_time = time.time()
    try:
        # StarRocks SQLAlchemy connector might not support df.to_sql efficiently for very large datasets
        # or might have specific ways to handle it. Pandas to_sql is generic.
        # For large data, INSERT from SELECT or stream loading (e.g. Stream Load HTTP API) is preferred in StarRocks.
        # For this benchmark, df.to_sql should work for moderate NUM_RECORDS.
        # Ensure 'ts' is in a format StarRocks understands (e.g., 'YYYY-MM-DD HH:MM:SS')
        df_copy = df.copy()
        df_copy['ts'] = df_copy['ts'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # The table object for SQLAlchemy needs to be defined correctly, matching the one in StarRocks
        # We can reflect it or define it. For simplicity, let's use to_sql with table name string.
        # Since the engine is connected directly to the database (e.g., 'test_db'),
        # the 'schema' parameter for to_sql should ideally be None or not specified.
        # However, some database dialects/drivers might still expect it.
        # The starrocks-connector documentation for pandas to_sql implies schema might be needed if table is in a different db than connection.
        # Since we are connected to the target DB, schema=None is the most standard SQLAlchemy approach.
        # If issues arise, explicitly passing db_name (e.g., STARROCKS_DB.split('.')[1]) could be a fallback.
        df_copy.to_sql(STARROCKS_TABLE_NAME, engine, schema=None, if_exists='append', index=False, chunksize=10000)
        # Note: `if_exists='append'` because we created the table in setup.
        # `chunksize` is good for memory management.
    except Exception as e:
        print(f"Error loading data into StarRocks: {e}")
        raise
    end_time = time.time()
    load_time = end_time - start_time
    print(f"StarRocks data loading complete. Time taken: {load_time:.2f} seconds.")
    return load_time

def query_starrocks(engine):
    # Engine is now connected to the specific database (e.g., example_db from STARROCKS_DB)
    # So, table references can be direct (STARROCKS_TABLE_NAME) without catalog.db prefix.
    db_name = STARROCKS_DB
    print(f"Querying StarRocks table {STARROCKS_TABLE_NAME} in database {db_name}...")
    queries = {
        "count_all": f"SELECT COUNT(*) FROM {STARROCKS_TABLE_NAME}",
        "avg_value1": f"SELECT AVG(value1) FROM {STARROCKS_TABLE_NAME}",
        "filter_and_count": f"SELECT COUNT(*) FROM {STARROCKS_TABLE_NAME} WHERE value1 > 50 AND value2 = 'category_A'",
        "group_by_value2": f"SELECT value2, AVG(value1) FROM {STARROCKS_TABLE_NAME} GROUP BY value2 ORDER BY value2",
        "time_window_query": f"SELECT COUNT(*) FROM {STARROCKS_TABLE_NAME} WHERE ts >= '2023-01-01 00:00:00' AND ts < '2023-01-01 01:00:00'"
    }
    results = {}
    try:
        with engine.connect() as connection:
            for name, query_sql in queries.items():
                print(f"  Executing query '{name}': {query_sql}")
                start_query_time = time.time()
                try:
                    result_proxy = connection.execute(text(query_sql))
                    query_result = result_proxy.fetchall()
                    # print(f"    Result: {query_result}") # Optional
                    connection.commit() # For some operations or configurations, a commit might be needed after select.
                except Exception as e_query:
                    print(f"    Error executing query '{name}': {e_query}")
                    query_result = None
                end_query_time = time.time()
                results[name] = end_query_time - start_query_time
                print(f"    Query '{name}' time: {results[name]:.4f} seconds.")
    except Exception as e:
        print(f"Error during StarRocks querying: {e}")
        # If connection fails, all query times will be 0 or not set, handle this in reporting
    print("StarRocks querying complete.")
    return results

# --- Cassandra Functions --- (New Section)
def setup_cassandra():
    print("Setting up Cassandra...")
    try:
        cluster = Cluster(CASSANDRA_HOSTS)
        session = cluster.connect()
        session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
            WITH REPLICATION = {{ 'class' : 'SimpleStrategy', 'replication_factor' : 1 }}
        """)
        session.set_keyspace(CASSANDRA_KEYSPACE)
        session.execute(f"DROP TABLE IF EXISTS {CASSANDRA_TABLE_NAME}")
        session.execute(f"""
            CREATE TABLE {CASSANDRA_TABLE_NAME} (
                id INT PRIMARY KEY,
                ts TIMESTAMP,
                value1 DOUBLE,
                value2 TEXT
            )
        """)
        print(f"Cassandra setup complete. Keyspace '{CASSANDRA_KEYSPACE}' and table '{CASSANDRA_TABLE_NAME}' are ready.")
        return session, cluster
    except Exception as e:
        print(f"Error setting up Cassandra: {e}")
        raise

def load_data_cassandra(session, df):
    print(f"Loading data into Cassandra table {CASSANDRA_TABLE_NAME}...")
    start_time = time.time()
    try:
        prepared = session.prepare(f"""
            INSERT INTO {CASSANDRA_TABLE_NAME} (id, ts, value1, value2)
            VALUES (?, ?, ?, ?)
        """)
        batch = BatchStatement()
        batch_size = 300 # Adjust batch size as needed (failed me with higher value)
        for i, row in df.iterrows():
            # Ensure 'ts' is a Python datetime object for Cassandra driver
            timestamp_val = row['ts'].to_pydatetime() if isinstance(row['ts'], pd.Timestamp) else row['ts']
            batch.add(prepared, (int(row['id']), timestamp_val, float(row['value1']), str(row['value2'])))
            if (i + 1) % batch_size == 0:
                session.execute(batch)
                batch.clear()
                print(f"  {i + 1}/{len(df)} records sent to Cassandra...")
        if batch:
            session.execute(batch) # Send remaining records
    except Exception as e:
        print(f"Error loading data into Cassandra: {e}")
        raise
    end_time = time.time()
    load_time = end_time - start_time
    print(f"Cassandra data loading complete. Time taken: {load_time:.2f} seconds.")
    return load_time

def query_cassandra(session):
    print("Querying Cassandra...")
    queries = {
        "count_all": f"SELECT COUNT(*) FROM {CASSANDRA_TABLE_NAME}",
        "avg_value1": f"SELECT AVG(value1) FROM {CASSANDRA_TABLE_NAME}", # Note: AVG might be slow without proper indexing/SAI
        "filter_and_count": f"SELECT COUNT(*) FROM {CASSANDRA_TABLE_NAME} WHERE value1 > 50 AND value2 = 'category_A' ALLOW FILTERING",
        "group_by_value2": f"SELECT value2, AVG(value1) FROM {CASSANDRA_TABLE_NAME} GROUP BY value2 ALLOW FILTERING", # Note: GROUP BY can be resource-intensive
        "time_window_query": f"SELECT COUNT(*) FROM {CASSANDRA_TABLE_NAME} WHERE ts >= '2023-01-01 00:00:00+0000' AND ts < '2023-01-01 01:00:00+0000' ALLOW FILTERING"
    }
    results = {}
    for name, query_cql in queries.items():
        print(f"  Executing query '{name}': {query_cql}")
        start_time = time.time()
        try:
            result_set = session.execute(query_cql)
            # For count queries, result_set.one()[0] gives the count
            # For other queries, you might iterate through result_set
            # print(f"    Result: {[row for row in result_set]}") # Optional: print query result
        except Exception as e:
            print(f"    Error executing query '{name}': {e}")
            result_set = None
        end_time = time.time()
        results[name] = end_time - start_time
        print(f"    Query '{name}' time: {results[name]:.4f} seconds.")
    print("Cassandra querying complete.")
    return results


def main():
    # Generate data
    data_df = generate_data(NUM_RECORDS)

    # --- Cassandra Benchmark --- (New Section)
    print("\n--- Starting Cassandra Benchmark ---")
    cassandra_session = None
    cassandra_cluster = None
    cassandra_load_time = float('nan')
    cassandra_query_times = {}
    try:
        cassandra_session, cassandra_cluster = setup_cassandra()
        cassandra_load_time = load_data_cassandra(cassandra_session, data_df.copy())
        print("Waiting a few seconds for Cassandra to process data before querying...")
        time.sleep(5) # Optional: wait if needed, though Cassandra writes are typically available quickly
        cassandra_query_times = query_cassandra(cassandra_session)
    except Exception as e:
        print(f"Cassandra benchmark failed: {e}")
    finally:
        if cassandra_session:
            cassandra_session.shutdown()
        if cassandra_cluster:
            cassandra_cluster.shutdown()
            print("Cassandra connection closed.")

    # --- QuestDB Benchmark ---
    print("\n--- Starting QuestDB Benchmark ---")
    questdb_load_time = float('nan')
    questdb_query_times = {}
    try:
        setup_questdb() # Checks ILP sender, table creation is implicit or via HTTP
        questdb_load_time = load_data_questdb(data_df.copy())
        # Wait a bit for data to be fully committed and queryable in QuestDB
        print("Waiting a few seconds for QuestDB to commit data before querying...")
        time.sleep(5) 
        questdb_query_times = query_questdb()
    except Exception as e:
        print(f"QuestDB benchmark failed: {e}")

    # --- DuckDB Benchmark ---
    print("\n--- Starting DuckDB Benchmark ---")
    duckdb_conn = None
    duckdb_load_time = float('nan')
    duckdb_query_times = {}
    try:
        duckdb_conn = setup_duckdb()
        duckdb_load_time = load_data_duckdb(duckdb_conn, data_df.copy()) # Use copy to avoid issues if df is modified
        duckdb_query_times = query_duckdb(duckdb_conn)
    except Exception as e:
        print(f"DuckDB benchmark failed: {e}")
    finally:
        if duckdb_conn:
            duckdb_conn.close()
            print("DuckDB connection closed.")

    # --- StarRocks Benchmark --- (New Section)
    print("\n--- Starting StarRocks Benchmark ---")
    starrocks_engine = None
    starrocks_load_time = float('nan')
    starrocks_query_times = {}
    try:
        starrocks_engine = setup_starrocks()
        starrocks_load_time = load_data_starrocks(starrocks_engine, data_df.copy())
        # Wait a bit for data to be fully available for querying, if necessary
        print("Waiting a few seconds for StarRocks to process data before querying...")
        time.sleep(5)
        starrocks_query_times = query_starrocks(starrocks_engine)
    except Exception as e:
        print(f"StarRocks benchmark failed: {e}")
    finally:
        if starrocks_engine:
            starrocks_engine.dispose()
            print("StarRocks engine disposed.")

    # --- Results Summary ---
    print("\n--- Benchmark Results Summary ---")
    print(f"Generated {NUM_RECORDS} records.")
    print("\nLoad Times:")
    print(f"  DuckDB: {duckdb_load_time:.2f} seconds")
    print(f"  QuestDB: {questdb_load_time:.2f} seconds")
    print(f"  StarRocks: {starrocks_load_time:.2f} seconds") # New
    print(f"  Cassandra: {cassandra_load_time:.2f} seconds") # New

    print("\nQuery Times (seconds):")
    header = f"{'Query':<20} | {'DuckDB':<10} | {'QuestDB':<10} | {'StarRocks':<10} | {'Cassandra':<10}" # New
    print(header)
    print("-" * len(header))

    # Assuming all query sets have the same keys if successful
    # Get query names from one of the results, e.g., duckdb_query_times, or define a standard list
    query_names = list(duckdb_query_times.keys()) # Or define explicitly if one might fail
    if not query_names and questdb_query_times: query_names = list(questdb_query_times.keys())
    if not query_names and starrocks_query_times: query_names = list(starrocks_query_times.keys())
    if not query_names: # Fallback if all failed before querying
        query_names = ["count_all", "avg_value1", "filter_and_count", "group_by_value2", "time_window_query"]

    for name in query_names:
        d_time = duckdb_query_times.get(name, float('nan'))
        q_time = questdb_query_times.get(name, float('nan'))
        s_time = starrocks_query_times.get(name, float('nan'))
        c_time = cassandra_query_times.get(name, float('nan'))
        print(f"{name:<20} | {d_time:<10.4f} | {q_time:<10.4f} | {s_time:<10.4f} | {c_time:<10.4f}") # New

    print("\nBenchmark finished.")

if __name__ == "__main__":
    main()
