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
  apache/airflow:2.6.3 \
  standalone

sudo docker exec -it airflow airflow users delete --username admin

sudo docker exec -it airflow airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com