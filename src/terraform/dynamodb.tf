resource "aws_dynamodb_table" "synthesis_reports" {
  name           = "issues"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "issue_id"

  # === Attributes ===
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

  attribute {
    name = "location"
    type = "S"
  }

  attribute {
    name = "crack_type"
    type = "S"
  }

  # 注意：length_cm 和 depth_cm 屬於數值類型，但 DynamoDB 中只能用 S (string), N (number), B (binary)
  attribute {
    name = "length_cm"
    type = "N"
  }

  attribute {
    name = "depth_cm"
    type = "N"
  }

  attribute {
    name = "image_url"
    type = "S"
  }

  # === Global Secondary Indexes (GSI) ===
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

  global_secondary_index {
    name            = "LocationIndex"
    hash_key        = "location"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "EngineerIndex"
    hash_key        = "engineer"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "CrackTypeIndex"
    hash_key        = "crack_type"
    projection_type = "ALL"
  }
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.synthesis_reports.name
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.synthesis_reports.arn
}