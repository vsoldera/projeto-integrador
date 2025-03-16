#!/bin/bash
sudo yum update -y
sudo amazon-linux-extras enable python3.8
sudo yum install python3.8 python3-pip -y

pip3 install apache-airflow

airflow db init

airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin

airflow webserver -p 8080 -D
airflow scheduler -D
