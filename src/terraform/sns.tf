################################################
########## SNS Topic Configuration #############
################################################

resource "aws_sns_topic" "alert_topic" {
  name = "equipment_alert_topic"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.alert_topic.arn
  protocol  = "email"
  endpoint  = var.email_address
}
