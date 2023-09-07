variable "account_id" {
  type        = string
  description = "AWS account ID"
  default     = "558283493208"
}

variable "account_profile" {
  type        = string
  description = "AWS account profile [SSO]"
  default     = "security"
}

variable "region" {
  type        = string
  description = "Default AWS Region"
  default     = "us-east-2"
} 