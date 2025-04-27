resource "aws_dynamodb_table" "reports" {
  name           = "issues"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "risk_level"
    type = "S"
  }

  global_secondary_index {
    name            = "TimestampIndex"
    hash_key        = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "RiskLevelIndex"
    hash_key        = "risk_level"
    projection_type = "ALL"
  }
}
