terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_key_pair" "airflow_key" {
  key_name   = "airflow-key"
  public_key = file("~/.ssh/airflow-key.pub")
}


resource "aws_security_group" "airflow_sg" {
  name        = "airflow_sg"
  description = "Allow SSH and Web UI access"
  
  ingress {
    from_port   = 22  # SSH
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "airflow" {
  ami             = data.aws_ami.amazon_linux.id
  instance_type   = "t3.medium"
  key_name        = aws_key_pair.airflow_key.key_name
  security_groups = [aws_security_group.airflow_sg.name]

  user_data = file("user-data.sh")

  tags = {
    Name = "Airflow-EC2"
  }
}
