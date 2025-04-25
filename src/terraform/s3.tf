################################################
### AWS S3 Bucket for History Report Storage ###
################################################
resource "aws_s3_bucket" "history_report_bucket" {
  bucket = "${var.history_report_bucket_name}-${random_string.bucket_suffix.result}"
}

resource "aws_iam_policy" "history_s3_access" {
  name = "history_s3_access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.history_report_bucket.arn,
          "${aws_s3_bucket.history_report_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "history_s3_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.history_s3_access.arn
}

##################################################
### AWS S3 Bucket for Image from icam Storage ####
##################################################
resource "aws_s3_bucket" "image_bucket" {
  bucket = "${var.bucket_name}-${random_string.bucket_suffix.result}"
}

# When the image is uploaded to the S3 bucket, it will trigger the Lambda function
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.image_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.llm_advise_handler.arn
    events             = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
