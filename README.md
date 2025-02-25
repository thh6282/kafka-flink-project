# KAFKA-FLINK

## Set up kafka cluster
### Install Strimzi operator
Before deploying the Strimzi cluster operator, create a namespace called kafka:

```bash
kubectl create namespace kafka
```
Apply the Strimzi install files, including ClusterRoles, ClusterRoleBindings and some Custom Resource Definitions (CRDs). The CRDs define the schemas used for the custom resources (CRs, such as Kafka, KafkaTopic and so on) you will be using to manage Kafka clusters, topics and users.

``` bash
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
```
The YAML files for ClusterRoles and ClusterRoleBindings downloaded from strimzi.io contain a default namespace of myproject. The query parameter namespace=kafka updates these files to use kafka instead. By specifying -n kafka when running kubectl create, the definitions and configurations without a namespace reference are also installed in the kafka namespace. If there is a mismatch between namespaces, then the Strimzi cluster operator will not have the necessary permissions to perform its operations.

### Create an Apache Kafka cluster

Create a new Kafka custom resource to get a Apache Kafka cluster:

Apply the `Kafka` Cluster yaml file
```bash
kubectl apply -f kafka-ephemeral.yaml -n kafka 
```

Install kafka ui: UI for Apache Kafka wraps major functions of Apache Kafka with an intuitive user interface.
```bash
kubectl apply -f kafka-ui.yaml -n kafka 
```

## Flink
Stateful Computations over Data Streams
Apache Flink is a framework and distributed processing engine for stateful computations over unbounded and bounded data streams. Flink has been designed to run in all common cluster environments, perform computations at in-memory speed and at any scale.

