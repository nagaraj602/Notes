terraform {
  required_version = ">= 1.15.0"


  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.51.0"
    }
  }
}


backend "s3" {
  bucket = "remote-backend-s3-jan2026-nagaraj-29-07-2026"
  key    = "simple-terraform-Jenkins-pipeline/terraform.tfstate"
  region = "us-east-1"
  use_lockfile = true
}


provider "aws" {
  region = "us-east-1"
}
