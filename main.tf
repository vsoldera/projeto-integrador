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

data "aws_vpc" "default" {
  default = true
}

variable "bucket_name" {
  type = string
}

resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name
  force_destroy = true
}



resource "aws_security_group" "rds_sg" {
  name        = "rds-sg"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5432
    to_port     = 5432
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

resource "aws_db_instance" "default" {
  allocated_storage    = 10
  db_name              = "taxilookupdb"
  engine               = "postgres"
  engine_version       = "11"
  instance_class       = "db.t3.micro"
  username             = "foo"
  password             = "foobarbaz"
  parameter_group_name = "default.postgres11"
  skip_final_snapshot  = true
  publicly_accessible  = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

resource "null_resource" "upload_files" {
  depends_on = [aws_s3_bucket.bucket]

  provisioner "local-exec" {
    command = "/bin/bash download-files.sh ${aws_s3_bucket.bucket.id}"
  }
}