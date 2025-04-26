terraform {
  # required_version = "~> 1.9.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95.0"  
    }
    opensearch = {
      source  = "opensearch-project/opensearch"
      version = "~> 2.0"
    }
    # random = {
    #   source  = "hashicorp/random"
    #   version = "~> 3.5.1"
    # }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "random" {}

provider "opensearch" {
  url       = data.aws_opensearchserverless_collection.existing_collection.collection_endpoint
  insecure = true 
}

provider "aws" {
  alias  = "waf"
  region = "us-east-1"
}