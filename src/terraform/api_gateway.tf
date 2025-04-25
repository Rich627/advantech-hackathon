# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "hackathon-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}

# API Gateway integrations
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

# API Gateway routes
resource "aws_apigatewayv2_route" "render_frontend" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /render"
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

# Lambda permissions for API Gateway
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