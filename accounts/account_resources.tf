data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Account wide roles
resource "aws_iam_role" "sharr_member_role" {
  name                = "SO0111-Remediate-SC-2.0.0-EC2.19" #Role name. Uniform across all accounts.
  assume_role_policy  = templatefile("${path.module}/../docs/member_account_role.json", { account = data.aws_caller_identity.current.account_id , admin_account = var.admin_account_id})
  managed_policy_arns = [aws_iam_policy.lambda_permissions.arn, aws_iam_policy.base_member_account_role.arn]
}

resource "aws_iam_policy" "lambda_permissions" {
  name   = "SHARR-ASFB-EC219-Permissions"
  policy = templatefile("${path.module}/../docs/lambda_permission_policy.json", { account = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_policy" "base_member_account_role" {
  name   = "RemediationRoleSO0111-Remediate-AFSBP-1.0.0-EC2.19MemberBasePolicy"
  policy = templatefile("${path.module}/../docs/member_account_sharr_policy.json", { account = data.aws_caller_identity.current.account_id })
}