variable "account_id" {
  type        = string
  description = "AWS account Id"
  default     = ""
}

variable "admin_account_id" {
  type        = string
  description = "SecHub Admin AWS account ID"
  default     = ""
}

variable "account_profile" {
  type        = string
  description = "AWS account profile [SSO]"
  default     = "audit"
}

variable "region" {
  type        = string
  description = "Default AWS region"
  default     = "us-west-2"
}