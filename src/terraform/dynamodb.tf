resource "aws_dynamodb_table" "synthesis_reports" {
  name           = "issues"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "issue_id"

  attribute {
    name = "issue_id"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  attribute {
    name = "risk_level"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "DateIndex"
    hash_key        = "date"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "RiskLevelIndex"
    hash_key        = "risk_level"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
}
