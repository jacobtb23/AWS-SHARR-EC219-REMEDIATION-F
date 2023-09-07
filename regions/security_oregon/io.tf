variable "account_id" {
  type        = string
  description = "AWS account ID"
  default     = "558283493208"
}

variable "account_profile" {
  type        = string
  description = "AWS account [SSO] "
  default     = "security"
}

variable "region" {
  type        = string
  description = "The default AWS region."
  default     = "us-west-2"
}