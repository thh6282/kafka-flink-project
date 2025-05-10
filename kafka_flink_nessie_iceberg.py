import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.table.expressions import lit
# from pynessie import init

# Create streaming environment
env = StreamExecutionEnvironment.get_execution_environment()
env.enable_checkpointing(6000)

settings = EnvironmentSettings.new_instance()\
                .in_streaming_mode()\
                .build()

# create table environment
table_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                    environment_settings=settings)

def create_ref_catalog(catalog_name):
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
                's3.endpoint'='http://(ip-address):9000'
            )
        """
    )
    print(f"Create successful catalog: {catalog_name}")

#######################################################################
# Create CATALOG
#######################################################################
create_ref_catalog("nessie_catalog")

#######################################################################
# Create DATABASE
#######################################################################
table_env.execute_sql("CREATE DATABASE IF NOT EXISTS nessie_catalog.db")

#######################################################################
# Create Kafka Source Table with DDL
#######################################################################
src_ddl = """
    CREATE TABLE sales_usd_src (
        seller_id VARCHAR,
        amount_usd DOUBLE,
        sale_ts BIGINT
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'sales-usd',
        'properties.bootstrap.servers' = 'broker:29092',
        'properties.group.id' = 'sales-usd',
        'scan.startup.mode'='earliest-offset',
        'format' = 'json'
    )
"""
table_env.execute_sql(src_ddl)
print("Create table from kafka successful")

###############################################################
# Create Sink Table Iceberg
###############################################################
sink_ddl = """
    CREATE TABLE IF NOT EXISTS nessie_catalog.db.sales_usd_sink (
        seller_id VARCHAR,               
        amount_usd DOUBLE,          
        sale_ts bigint         
    )
"""
# Execute the SQL to create the Iceberg sink table
table_env.execute_sql(sink_ddl)
print("Iceberg sink table created successfully")

###############################################################
# Insert into Sink Table Iceberg
###############################################################
insert_sql = """
    INSERT INTO nessie_catalog.db.sales_usd_sink
    SELECT * FROM default_catalog.default_database.sales_usd_src
"""
table_env.execute_sql(insert_sql).wait()
