import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import socket

# Create streaming environment
env = StreamExecutionEnvironment.get_execution_environment()
env.enable_checkpointing(6000)

settings = EnvironmentSettings.new_instance() \
    .in_streaming_mode() \
    .build()

# Create table environment
table_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                          environment_settings=settings)

def get_container_ip(container_name):
    try:
        # Use gethostbyname to find IP on container
        ip_address = socket.gethostbyname(container_name)
        return ip_address
    except socket.error as e:
        return f"Error: Unable to resolve IP for {container_name}. {e}"

def create_ref_catalog(catalog_name, s3_address):
    """
    Create a flink catalog that is tied to a specific ref.

    In order to create the catalog we have to first create the branch
    """
    # type - tell Flink to use Iceberg as the catalog
    # catalog-impl - which Iceberg catalog to use, in this case we want Nessie
    # uri - the location of the nessie server.
    # ref - the Nessie ref/branch we want to use (defaults to main)
    # warehouse - the location this catalog should store its data
    # s3.endpoint: Endpoint of the MinIO server; used by clients to connect. 
    # You need to provide the actual IP address of the MinIO machine here so DNS resolution can happen (if accessed outside of the network context).
    # (ip-address) is real IP of your machine
    table_env.execute_sql(
        f"""
            CREATE CATALOG {catalog_name} WITH (
                'type'='iceberg',
                'catalog-impl'='org.apache.iceberg.nessie.NessieCatalog',
                'io-impl'='org.apache.iceberg.aws.s3.S3FileIO',
                'uri'='http://catalog:19120/api/v1',
                'authentication.type'='none',
                'client.assume-role.region'='us-east-1',
                'warehouse'='s3://warehouse/',
                's3.endpoint'='http://{s3_address}:9000'
            )
        """
    )
    print(f"Created catalog: {catalog_name}")

# Get address of Minio
s3_address = get_container_ip("storage")

#######################################################################
# Create CATALOG
#######################################################################
create_ref_catalog("nessie_catalog", s3_address)

#######################################################################
# Create DATABASE
#######################################################################
table_env.execute_sql("CREATE DATABASE IF NOT EXISTS nessie_catalog.db")

#######################################################################
# Create Kafka Source Table with DDL
#######################################################################
src_ddl = """
    CREATE TABLE cdc_src (
        before ROW<id int, col_a STRING, col_b STRING, col_c STRING>,
        after ROW<id int, col_a STRING, col_b STRING, col_c STRING>,
        op STRING
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'cdc.public.demo',
        'properties.bootstrap.servers' = 'broker:29092',
        'properties.group.id' = 'flink_connector',
        'scan.startup.mode'='earliest-offset',
        'format' = 'json'
    )
"""
table_env.execute_sql(src_ddl)
print("Created CDC Kafka Source Table")

###############################################################
# Create Sink Table Iceberg
###############################################################
sink_ddl = """
    CREATE TABLE IF NOT EXISTS nessie_catalog.db.demo_sink (
        id int, 
        col_a VARCHAR,
        col_b VARCHAR,
        col_c VARCHAR,
        op VARCHAR,
        ppn_time timestamp(6)
    ) 
"""
table_env.execute_sql(sink_ddl)
print("Created Iceberg Sink Table")

###############################################################
# Insert into Sink Table Iceberg
###############################################################
insert_sql = """
    INSERT INTO nessie_catalog.db.demo_sink
    SELECT 
        CASE 
            WHEN op = 'd' THEN before.id 
            ELSE after.id 
        END AS id,
        CASE 
            WHEN op = 'd' THEN before.col_a 
            ELSE after.col_a 
        END AS col_a,
        CASE 
            WHEN op = 'd' THEN before.col_b 
            ELSE after.col_b 
        END AS col_b,
        CASE 
            WHEN op = 'd' THEN before.col_c 
            ELSE after.col_c 
        END AS col_c,
        op,
        CURRENT_TIMESTAMP AS ppn_time
    FROM default_catalog.default_database.cdc_src
    WHERE op IN ('c', 'u', 'd');
"""

table_env.execute_sql(insert_sql).wait()
print("Processed INSERT operations")
