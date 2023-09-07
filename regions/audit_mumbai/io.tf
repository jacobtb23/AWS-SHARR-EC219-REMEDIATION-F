variable "account_id" {
  type        = string
  description = "AWS account ID"
  default     = "376658174654"
}

variable "account_profile" {
  type        = string
  description = "AWS account profile [SSO]"
  default     = "audit"
}

variable "region" {
  type        = string
  description = "Default AWS Region"
  default     = "ap-south-1"
}