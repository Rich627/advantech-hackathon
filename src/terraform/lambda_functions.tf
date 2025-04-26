# # Lambda functions IAM role
# resource "aws_iam_role" "api_lambda_role" {
#   name = "hackathon-api-lambda-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "lambda.amazonaws.com"
#         }
#       }
#     ]
#   })
# }

# # Basic Lambda execution policy
# resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
#   role       = aws_iam_role.api_lambda_role.name
# }

# # Lambda functions
# resource "aws_lambda_function" "render_frontend" {
#   function_name = "hackathon-render-frontend"
#   role          = aws_iam_role.api_lambda_role.arn
#   package_type  = "Image"
#   image_uri     = "${var.ecr_repository_url}/render-frontend:latest"

#   memory_size = 128
#   timeout     = 30
# }

# resource "aws_lambda_function" "complete" {
#   function_name = "hackathon-complete"
#   role          = aws_iam_role.api_lambda_role.arn
#   package_type  = "Image"
#   image_uri     = "${var.ecr_repository_url}/complete:latest"

#   memory_size = 128
#   timeout     = 30
# }

# resource "aws_lambda_function" "doc_process" {
#   function_name = "hackathon-doc-process"
#   role          = aws_iam_role.api_lambda_role.arn
#   package_type  = "Image"
#   image_uri     = "${var.ecr_repository_url}/doc-process:latest"

#   memory_size = 128
#   timeout     = 30
# } 