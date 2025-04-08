#!/bin/bash
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo yum install docker -y

sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

EC2_UID=$(id -u ec2-user)

AIRFLOW_DIR="/home/ec2-user/airflow"
mkdir -p ${AIRFLOW_DIR}/{dags,logs,plugins}
sudo chown -R ${EC2_UID}:0 ${AIRFLOW_DIR} 
sudo chmod -R g+w ${AIRFLOW_DIR}

sudo docker run -d \
  --name airflow \
  -p 8080:8080 \
  -v ${AIRFLOW_DIR}/dags:/opt/airflow/dags \
  -v ${AIRFLOW_DIR}/logs:/opt/airflow/logs \
  -v ${AIRFLOW_DIR}/plugins:/opt/airflow/plugins \
  --user ${EC2_UID}:0 \
  -e AIRFLOW__CORE__LOAD_EXAMPLES=False \
  -e _AIRFLOW_WWW_USER_USERNAME=admin \
  -e _AIRFLOW_WWW_USER_PASSWORD=admin \
  apache/airflow:2.6.3 \
  standalone

sleep 60

until sudo docker exec airflow airflow db check; do
  echo "Waiting for Airflow database to be ready..."
  sleep 5
done


sudo amazon-linux-extras install java-openjdk11 -y

# Download and install Spark
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar xvf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark
sudo chown -R ec2-user:ec2-user /opt/spark

# Configure environment variables
echo 'export SPARK_HOME=/opt/spark' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
echo 'export PYTHONPATH=$SPARK_HOME/python:$PYTHONPATH' >> ~/.bashrc

# Add PostgreSQL JDBC driver to Spark jars
sudo wget -P /opt/spark/jars https://jdbc.postgresql.org/download/postgresql-42.5.1.jar

# Apply environment variables
source ~/.bashrc

echo "Creating Airflow admin user..."
sudo docker exec -it airflow airflow users delete --username admin || true
sudo docker exec -it airflow airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com

