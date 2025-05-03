# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "hackathon-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "OPTIONS"]
    allow_headers     = ["*"]
    expose_headers    = ["*"]
    allow_credentials = true
    max_age           = 7200
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 5000
    throttling_rate_limit  = 5000
  }
}

######################################################
######### API Gateway integration and routes #########
######################################################

resource "aws_apigatewayv2_integration" "render_frontend" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri    = aws_lambda_function.render_frontend.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "complete" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri    = aws_lambda_function.complete.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "doc_process" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri    = aws_lambda_function.doc_process.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "presigned_url" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.presigned_url.invoke_arn
  integration_method = "POST"
}

#################################################
########## API Gateway routes ###################
#################################################
resource "aws_apigatewayv2_route" "render_frontend" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /render"
  target    = "integrations/${aws_apigatewayv2_integration.render_frontend.id}"
}

resource "aws_apigatewayv2_route" "render_frontend_detail" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /render/{run_id}"
  target    = "integrations/${aws_apigatewayv2_integration.render_frontend.id}"
}

resource "aws_apigatewayv2_route" "complete" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /complete"
  target    = "integrations/${aws_apigatewayv2_integration.complete.id}"
}

resource "aws_apigatewayv2_route" "doc_process" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /process"
  target    = "integrations/${aws_apigatewayv2_integration.doc_process.id}"
}

resource "aws_apigatewayv2_route" "presigned_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /presigned"
  target    = "integrations/${aws_apigatewayv2_integration.presigned_url.id}"
}


#################################################
##### Lambda permissions for API Gateway #######
#################################################
resource "aws_lambda_permission" "render_frontend" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.render_frontend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "complete" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.complete.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "doc_process" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.doc_process.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
} 

resource "aws_lambda_permission" "presigned_url" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.presigned_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}