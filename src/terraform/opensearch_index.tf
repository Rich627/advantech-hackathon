# ##########################################################
# # repair-reports 向量索引，一次性建立
# ##########################################################
# resource "opensearch_index" "repair_reports" {
#   name = "repair-reports"

#   settings = jsonencode({
#     "index" = {
#       "knn" = "true"
#     }
#   })

#   mappings = jsonencode({
#     "properties" = {
#       "report_id" = { "type" = "keyword" },
#       "chunk"     = { "type" = "text" },
#       "vector"    = {
#         "type"      = "knn_vector",
#         "dimension" = 768,           # Titan v2 輸出 768 維
#         "method"    = {
#           "name"       = "hnsw",
#           "space_type" = "cosinesimil"
#         }
#       }
#     }
#   })

#   # 讓 Terraform 知道：必須等 collection 建好才能建 index
#   depends_on = [data.aws_opensearchserverless_collection.existing_collection]
# }