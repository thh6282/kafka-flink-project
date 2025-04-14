
# Installation and Testing Guide for the Data Lakehouse Architecture

This guide provides step-by-step instructions to set up and test the above Data Lakehouse architecture using Docker. Follow these instructions carefully to ensure everything is configured and tested properly.

---

## **Step 1: Build the Docker Images**
- Navigate to the directory containing your `Dockerfile`.
- Build the Docker images. You can modify the configurations or add additional libraries for Flink if required.
  ```bash
  docker build -t flink-custom ./docker/flink
  ```

---

## **Step 2: Start the Docker Containers**
- Use the provided `docker-compose` file to spin up all the components in the architecture.
- Run the following command from the `./docker` directory:
  ```bash
  docker-compose -f docker-compose.yaml up -d
  ```
- This will initialize and start all the required services, including PostgreSQL, Debezium, Kafka, Flink, MinIO, Nessie, Iceberg, and Trino.

---

## **Step 3: Verify PostgreSQL Setup**
- Once all the components are up and running, connect to the PostgreSQL container to check the source table:
  ```bash
  docker exec -it postgres psql -U postgres
  ```
- Inside the PostgreSQL shell, run the following command to verify the `demo` table:
  ```sql
  select * from demo;
  ```

---

## **Step 4: Verify Trino Setup**
- Connect to the Trino container and check the sink table:
  ```bash
  docker exec -it trino trino
  ```
- Run the following SQL query to inspect the data in the Iceberg sink table:
  ```sql
  select * from nessie_catalog.db.demo_sink;
  ```

---

## **Step 5: Update and Test Data Flow**
- Update the `demo` table in PostgreSQL by inserting, updating, or deleting records.
  ```sql
  insert into demo (id, name, value) values (1, 'test', 100);
  ```
- Revisit the sink table in Trino to confirm that the data has flowed through the pipeline and is now available in Iceberg:
  ```sql
  select * from nessie_catalog.db.demo_sink;
  ```

---

## **Notes:**
- Make sure all containers are running correctly before proceeding with any testing. You can check container statuses using:
  ```bash
  docker ps
  ```
- If any container fails, inspect the logs for errors:
  ```bash
  docker logs <container_name>
  ```

By following these steps, you will successfully verify the functionality of the entire Data Lakehouse architecture, from data ingestion in PostgreSQL to real-time analytics in Trino.
