################################
###### API Gateway settings ######
################################
resource "aws_api_gateway_rest_api" "main" {
  name        = "equipment-management-api"
  description = "API for equipment management system"
}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  
  depends_on = [
    aws_api_gateway_integration.doc_process_integration,
    aws_api_gateway_integration.render_frontend_integration,
    aws_api_gateway_integration.complete_integration,
    aws_api_gateway_integration.presigned_url_integration
  ]
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"
}

#####################################
###### API Gateway API settings ######
#####################################
resource "aws_api_gateway_resource" "doc_process_resource" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "document"
}

resource "aws_api_gateway_resource" "render_frontend_resource" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "frontend"
}

resource "aws_api_gateway_resource" "complete_resource" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "complete"
}

resource "aws_api_gateway_resource" "presigned_url_resource" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "presigned"
}

#########################################
###### API Gateway Method settings ######
#########################################
resource "aws_api_gateway_method" "doc_process_method" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.doc_process_resource.id
  http_method   = "POST"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "render_frontend_method" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.render_frontend_resource.id
  http_method   = "GET"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "complete_method" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.complete_resource.id
  http_method   = "POST"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "presigned_url_method" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = "GET"
  authorization_type = "NONE"
}

#####################################
###### API Gateway Integration ######
#####################################
resource "aws_api_gateway_integration" "doc_process_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.doc_process_resource.id
  http_method             = aws_api_gateway_method.doc_process_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.doc_process.invoke_arn
}

resource "aws_api_gateway_integration" "render_frontend_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.render_frontend_resource.id
  http_method             = aws_api_gateway_method.render_frontend_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.render_frontend.invoke_arn
}

resource "aws_api_gateway_integration" "complete_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.complete_resource.id
  http_method             = aws_api_gateway_method.complete_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.complete.invoke_arn
}

resource "aws_api_gateway_integration" "presigned_url_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.presigned_url_resource.id
  http_method             = aws_api_gateway_method.presigned_url_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.presigned_url.invoke_arn
}

#####################################
####### Lambda Permissions ##########
#####################################
resource "aws_lambda_permission" "doc_process_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.doc_process.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "render_frontend_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.render_frontend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "complete_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.complete.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "presigned_url_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.presigned_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}