################################################
####### OpenSearch Serverless Configuration ####
################################################

# OpenSearch Serverless encryption policy
resource "aws_opensearchserverless_security_policy" "vdb_encryption_policy" {
  name        = "icam-vdb-encryption"
  type        = "encryption"
  policy      = jsonencode({
    Rules = [{
      ResourceType = "collection",
      Resource = ["collection/icam-vectors"]
    }],
    AWSOwnedKey = true
  })
}

# OpenSearch Serverless collection
resource "aws_opensearchserverless_collection" "vdb_collection" {
  name        = "icam-vectors"
  type        = "VECTORSEARCH"
  description = "vector search collection for equipment management system"
  
  depends_on = [aws_opensearchserverless_security_policy.vdb_encryption_policy]
}

# OpenSearch Serverless data access policy for search and write
resource "aws_opensearchserverless_access_policy" "vdb_data_access_policy" {
  name        = "icam-vdb-data-access"
  type        = "data"
  policy      = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource    = ["collection/icam-vectors"],
          Permission  = [
            "aoss:CreateCollectionItems", 
            "aoss:DeleteCollectionItems", 
            "aoss:UpdateCollectionItems", 
            "aoss:DescribeCollectionItems",
            "aoss:ReadDocument",         
            "aoss:SearchCollectionItems" 
          ]
        },
        {
          ResourceType = "index",
          Resource    = ["index/icam-vectors/*"],
          Permission  = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ],
      Principal = [
        aws_iam_role.lambda_exec.arn,
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  ])

  depends_on = [aws_opensearchserverless_collection.vdb_collection]
}

# OpenSearch Serverless network policy
resource "aws_opensearchserverless_security_policy" "vdb_network_policy" {
  name   = "icam-vdb-network"
  type   = "network"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource    = ["collection/icam-vectors"]
        }
      ],
      # public access allowed, but only services/roles with permissions from other policies can access
      AllowFromPublic = true
    #   AllowFromPublic = false,
    #   SourceVPCEs = [var.vpc_endpoint_id]
    }
  ])

  depends_on = [aws_opensearchserverless_collection.vdb_collection]
}


############################################
### IAM policy for OpenSearch Serverless ###
############################################
resource "aws_iam_policy" "opensearch_index_management" {
  name        = "opensearch_index_management"
  description = "Allow creating and managing OpenSearch indexes"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "aoss:CreateIndex",
          "aoss:UpdateIndex",
          "aoss:DeleteIndex",
          "aoss:ListIndices"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "opensearch_index_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.opensearch_index_management.arn
}