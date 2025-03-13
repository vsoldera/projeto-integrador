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
  region = "us-west-2"
}

resource "aws_s3_bucket" "bucket" {
  bucket = "yellow-taxi-group-5"    
}

resource "null_resource" "upload_files" {
  depends_on = [aws_s3_bucket.bucket]

  provisioner "local-exec" {
    command = <<EOT
      curl -o yellow_tripdata_2024-12.parquet https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-12.parquet
      curl -o taxi_zone_lookup.csv https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
      aws s3 cp yellow_tripdata_2024-12.parquet s3://${aws_s3_bucket.bucket.id}/
      aws s3 cp taxi_zone_lookup.csv s3://${aws_s3_bucket.bucket.id}/
    EOT
  }
}