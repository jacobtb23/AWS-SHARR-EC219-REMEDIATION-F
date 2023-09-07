variable "account_id" {
  type        = string
  description = "AWS account ID"
  default     = ""
}

variable "admin_account_id" {
  type        = string
  description = "SecHub Admin AWS account ID"
  default     = ""
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