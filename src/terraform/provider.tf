terraform {
  required_version = "~> 1.9.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95.0"  
    }
    opensearch = {
      source  = "opensearch-project/opensearch"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "random" {}

provider "opensearch" {
  url       = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
  aws_sigv4 = true          # Serverless 一定要 SigV4
  region    = var.aws_region
}