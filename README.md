# AWS-SHARR-EC219-REMEDIATION-TF
Extension of AWS SHARR solution for EC2.19 security control.

Summary:
The EC2.19 remediation is a custom extension of the AWS Security Hub Automatic Remediation (SHARR) solution. This particular extension of the solution remediates illegally configured security groups open to 0.0.0.0/0. Security Hub aggregates all findings in the audit account. When EC2.19 alerts are generated SHARR takes action and will remediate the misconfiguration in the origin account and notify the security team. 

Deployment:
The solution as a whole can be deployed by following the document linked below: https://docs.aws.amazon.com/solutions/latest/automated-security-response-on-aws/solution-overview.html. The custom solutions are aggregated to the existing solution by mirroring the permissions and SSM documents found in the out of the box solution. In the case of added accounts or regions, the terraform in the custom remediation repo should be modified to deploy resources to the new accounts and regions.

In order for this solution to work you will need to modify the IAM role 'SO0111-SHARR_Orchestrator' in the Security Hub admin account. In the 'sts:AssumeRole' section you will need to add the ARN of your newly created remediation role to the resource section. It will follow the pattern 'arn:aws:iam::*:role/SO0111-Remediate-SC-2.0.0-<new-control-id>'. As seen below (Be sure to replace <control_id> with your actual control_id):
```		
        {
			"Action": "sts:AssumeRole",
			"Resource": [
				"arn:aws:iam::*:role/SO0111-SHARR-Orchestrator-Member",
				"arn:aws:iam::*:role/SO0111-Remediate-SC-2.0.0-EC2.19",
				"arn:aws:iam::*:role/SO0111-Remediate-SC-2.0.0-EC2.18",
                "arn:aws:iam::*:role/SO0111-Remediate-SC-2.0.0-<control-id>"
			],
			"Effect": "Allow"
		},
```

This allows for the SHARR admin roles in the security hub admin account to assume the IAM role across our AWS accounts.

You can now create a custom Eventbridge rule in the aggregation region of the security hub admin account. This is where the security hub solution aggregates all findings. The rule should be disabled initially and be named after the following convention 'SC_2.0.0_<control-id>_AutoTrigger'. The event should be formatted as follows (Be sure to replace <control_id> with your actual control_id):
```
{
  "detail-type": ["Security Hub Findings - Imported"],
  "source": ["aws.securityhub"],
  "detail": {
    "findings": {
      "Compliance": {
        "Status": ["FAILED"]
      },
      "GeneratorId": ["security-control/<control_id>"],
      "RecordState": ["ACTIVE"],
      "Workflow": {
        "Status": ["NEW"]
      }
    }
  }
}
```
This will create a rule that triggers your solution whenever a finding of that type appears in security hub.
Once this is complete the solution can be deployed and tested. 

Workflow:
The solution works by monitoring the security hub administrative account aggregation region for any finding of the type EC2.19. Once a finding is matched by an event-bridge trigger, the finding details are sent to a SSM document in the target member account. The finding details are parsed and fed into the remediation lambda which deletes all offending rules within the security group. Once that is completed successfully, the lambda can notify a slack channel for triage.

Exceptions:
Security rules can be protected from deletion by adding the following tag:
```
{
'key' : 'BlockProtection',
'value' : 'True' 
}
```


