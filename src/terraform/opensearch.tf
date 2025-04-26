# ################################################
# ####### OpenSearch Serverless Configuration ####
# ################################################
data "aws_opensearchserverless_collection" "existing_collection" {
  name = "report-vector"
}

# # OpenSearch Serverless data access policy for search and write
# resource "aws_opensearchserverless_access_policy" "vdb_data_access_policy" {
#   name        = "icam-vdb-data-access"
#   type        = "data"
#   policy      = jsonencode([
#     {
#       Rules = [
#         {
#           ResourceType = "collection",
#           Resource    = ["collection/report-vector"],
#           Permission  = [
#             "aoss:CreateCollectionItems", 
#             "aoss:DeleteCollectionItems", 
#             "aoss:UpdateCollectionItems", 
#             "aoss:DescribeCollectionItems",
#             "aoss:ReadDocument",         
#             "aoss:SearchCollectionItems" 
#           ]
#         },
#         {
#           ResourceType = "index",
#           Resource    = ["index/report-vector/*"],
#           Permission  = [
#             "aoss:CreateIndex",
#             "aoss:DeleteIndex",
#             "aoss:UpdateIndex",
#             "aoss:DescribeIndex",
#             "aoss:ReadDocument",
#             "aoss:WriteDocument"
#           ]
#         }
#       ],
#       Principal = [
#         aws_iam_role.lambda_exec.arn,
#         "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
#       ]
#     }
#   ])

#   depends_on = [data.aws_opensearchserverless_collection.existing_collection]
# }

# # OpenSearch Serverless network policy
# resource "aws_opensearchserverless_security_policy" "vdb_network_policy" {
#   name   = "icam-vdb-network"
#   type   = "network"
#   policy = jsonencode([
#     {
#       Rules = [
#         {
#           ResourceType = "collection",
#           Resource    = ["collection/report-vector"]
#         }
#       ],
#       # public access allowed, but only services/roles with permissions from other policies can access
#       AllowFromPublic = true
#     }
#   ])

#   depends_on = [data.aws_opensearchserverless_collection.existing_collection]
# }


# ############################################
# ### IAM policy for OpenSearch Serverless ###
# ############################################
# resource "aws_iam_policy" "opensearch_index_management" {
#   name        = "opensearch_index_management"
#   description = "Allow creating and managing OpenSearch indexes"
  
#   policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Effect = "Allow",
#         Action = [
#           "aoss:CreateIndex",
#           "aoss:UpdateIndex",
#           "aoss:DeleteIndex",
#           "aoss:ListIndices"
#         ],
#         Resource = "*"
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy_attachment" "opensearch_index_attachment" {
#   role       = aws_iam_role.lambda_exec.name
#   policy_arn = aws_iam_policy.opensearch_index_management.arn
# }