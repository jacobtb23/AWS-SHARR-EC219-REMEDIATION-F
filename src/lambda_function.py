import json
import requests
import boto3 

def lambda_handler(event, context):
    print('INPUT EVENT:')
    print(event)
    json_str = json.dumps(event)
    event_formatted = json.loads(json_str)
    SG_ID = str(event_formatted['GroupId'][0])
    Account = event_formatted['RemediationAccount']
    Region = event_formatted['RemediationRegion']
    #Create EC2 boto3 client
    ec2_client = ClientSetup()
    #Get SG details
    SGR_Details = GetSGRs(ec2_client, SG_ID)
    Non_Compliant_SGRs = ID_Illegal_Rules(SGR_Details, SG_ID, Account, Region)
    Execute_Remediations(ec2_client,Non_Compliant_SGRs, SG_ID, Account)

def Execute_Remediations(client, Non_Compliant_SGRs, SG_ID, Account): #DELETE OFFENDING RULES
    print('REMEDIATING THE FOLLOWING SGRs IN SECURITY GROUP %s: ' % SG_ID)
    if (Non_Compliant_SGRs):
        for sgr in Non_Compliant_SGRs:
            print('   - ' + sgr)
        try:
            response = client.revoke_security_group_ingress(
                GroupId = SG_ID,
                SecurityGroupRuleIds = Non_Compliant_SGRs)
            print(' - SGRs have been successfully deleted.')
            message = 'Non Compliant SGRs in %s have been successfully deleted!' % SG_ID
            SendCompletionMessage(message)
        except Exception as e:
            print(' - ERROR: %s' % e)
            message = 'ERROR: %s' % e
            SendCompletionMessage(message)
    else:
        print(' --- No SGRs were marked for deletion.')

def ID_Illegal_Rules(SGR_Details, SG_ID, Account, Region):
    SGRs = SGR_Details['SecurityGroupRules'] # Extract SGR's
    #STATIC Vars
    RISKY_PORTS = [20,21,22,25,110,135,143,445,1433,1434,3000,3306,3389,4333,5000,5432,5500,5601,8080,8888,9200,9300]
    ILLEGAL_IPV4_CIDR = '0.0.0.0/0'
    ILLEGAL_IPV6_CIDR = '::/0'
    SGRs_To_Remediate = []
    Slack_Message_List = []
    
    #Loop through SGR's
    count = 0
    for sgr in SGRs:
        count = count + 1
        print('--------------------------------')
        print('Security Group Rule ' + str(count) + ':')
        print(sgr)

        try: #SET PORT VARIABLES...
            start_port = sgr['FromPort'] #if err
            end_port = sgr['ToPort']
        except KeyError:
            print('Fields FromPort and ToPort are not specified. Assigning value as N/A.')
            start_port = 'N/A'
            end_port = 'N/A'


        try: #SET IPv4 CIDR RANGE VARIABLES...
            IPv4_CIDR_Range = sgr['CidrIpv4']
            print('IPv4 Range: ' + str(IPv4_CIDR_Range))
        except KeyError:
            IPv4_CIDR_Range = 'N/A'
            print('No IPv4 range specified. Assigning value as N/A.')
        try: #SET IPv6 CIDR RANGE VARIABLES...
            IPv6_CIDR_Range = sgr['CidrIpv6']
            print('IPv6 Range: ' + str(IPv6_CIDR_Range))
        except KeyError:
            IPv6_CIDR_Range = 'N/A'
            print('No IPv6 range specified. Assigning value as N/A.')


        #SET IP PROTOCOL
        IpProtocol = sgr['IpProtocol']
        if (CheckForDeleteProtectionTag(sgr) == False):
            if (sgr['IsEgress'] == False): # Check if we are dealing with outbound rule. If so continue.
                # FIND RISKY RULES...
                if (start_port == 0) & (end_port == 65535):
                    if (IPv4_CIDR_Range == ILLEGAL_IPV4_CIDR) | (IPv6_CIDR_Range == ILLEGAL_IPV6_CIDR):
                        print('ALERT: RISKY PORTS 0-65535 ALLOWED')
                        print('REMEDIATE SG RULE %s' % sgr['SecurityGroupRuleId'])
                        SGRs_To_Remediate.append(sgr['SecurityGroupRuleId'])
                        message = '--- [DELETION] - Rule %s has been slated for deletion [ 0-65536 open to 0.0.0.0/0 ].' % sgr['SecurityGroupRuleId']
                        Slack_Message_List.append(message)
                    else:
                        print('LEGAL RULE, but is open to a large number of portsx.')
                        message = '--- [LEGAL] - Rule %s not slated for deletion, but is very open and should be reviewed.' % sgr['SecurityGroupRuleId']
                        Slack_Message_List.append(message)
                elif (IpProtocol == '-1'):
                    if (IPv4_CIDR_Range == ILLEGAL_IPV4_CIDR) | (IPv6_CIDR_Range == ILLEGAL_IPV6_CIDR):
                        print('ALERT: ALL PORTS ALLOWED')
                        SGRs_To_Remediate.append(sgr['SecurityGroupRuleId'])
                        print('REMEDIATE SG RULE %s' % sgr['SecurityGroupRuleId'])
                        message = '--- [DELETION] - Rule %s has been slated for deletion [ ALL ports open to 0.0.0.0/0 ].' % sgr['SecurityGroupRuleId']
                        Slack_Message_List.append(message)
                    else:
                        print('LEGAL RULE, but is open to all ports.')
                        message = '--- [LEGAL] - Rule %s not slated for deletion, but is very open and should be reviewed.' % sgr['SecurityGroupRuleId']
                        Slack_Message_List.append(message)
                elif (start_port in RISKY_PORTS) | (end_port in RISKY_PORTS) & (start_port == end_port):
                    if (IPv4_CIDR_Range == ILLEGAL_IPV4_CIDR) | (IPv6_CIDR_Range == ILLEGAL_IPV6_CIDR):
                        print("ALERT: RISKY PORT %i ALLOWED" % start_port)
                        SGRs_To_Remediate.append(sgr['SecurityGroupRuleId'])
                        print('REMEDIATE SG RULE %s' % sgr['SecurityGroupRuleId'])
                        message = '--- [DELETION] - Rule %s has been slated for deletion [ Port %s open to 0.0.0.0/0 ].' % (sgr['SecurityGroupRuleId'], start_port)
                        Slack_Message_List.append(message)
                    else:
                        print('LEGAL RULE')
                else: # RANGE of PORTS. Check to see if any include risky ports.
                    RISKY_RANGE_PORTS = []
                    for Risky_Port in RISKY_PORTS:
                        if (Risky_Port in range(start_port, end_port)):
                            if (IPv4_CIDR_Range == ILLEGAL_IPV4_CIDR) | (IPv6_CIDR_Range == ILLEGAL_IPV6_CIDR):
                                RISKY_RANGE_PORTS.append(Risky_Port)
                    if(RISKY_RANGE_PORTS): #If list is NOT empty...
                        print('ALERT for ports: %s' % str(RISKY_RANGE_PORTS))
                        SGRs_To_Remediate.append(sgr['SecurityGroupRuleId'])
                        print('REMEDIATE SG RULE %s' % sgr['SecurityGroupRuleId'])
                        message = '--- [DELETION] Rule %s has been slated for deletion [ Ports %s are open to 0.0.0.0/0 ].' % (sgr['SecurityGroupRuleId'], str(RISKY_RANGE_PORTS))
                        Slack_Message_List.append(message)
                    else:
                        print('LEGAL RULES, but group is very open.')
                        message = '--- [LEGAL] - Rule %s not slated for deletion, but is very open and should be reviewed.' % sgr['SecurityGroupRuleId']
                        Slack_Message_List.append(message)
                print('--------------------------------')
            else:
                print('--- [LEGAL] - Outbound Rule %s' % sgr['SecurityGroupRuleId'])
                message = '--- [LEGAL] - Outbound Rule %s' % sgr['SecurityGroupRuleId']
                Slack_Message_List.append(message)
        else:
            print('--- DELETION PROTECTION APPLIED on SGR rule %s' % sgr['SecurityGroupRuleId'])
            message = '--- [PROTECTED] deletion protection applied on SGR rule %s' % sgr['SecurityGroupRuleId']
            Slack_Message_List.append(message)
    #RETURN SGR ID's for remediation...
    SendSlackMessage(Slack_Message_List, ['Dummy', 'Data'], Account, SG_ID, Region)
    return SGRs_To_Remediate

def GetSGRs(ec2_client, SG_ID):
    #Get SG details
    try:
        response = ec2_client.describe_security_group_rules(
            Filters=[{'Name': 'group-id','Values': [SG_ID]}]
        )
        return response
    except Exception as e:
        print('ERRO %s: Could not describe security group rules for security group %s' % (e,SG_ID))

def CheckForDeleteProtectionTag(sgr):
    for tag in sgr['Tags']:
        if (tag['Key'] == 'BlockProtection') & (tag['Value'] == 'True'):
            return True
    return False

def ClientSetup():
    #EC2 SDK client
    client = boto3.client('ec2')
    return client

def SendSlackMessage(message_list, Non_Compliant_SGRs, Account, SG_ID, Region): # MESSAGE TYPE codes: {0 - Deletion Failure, 1 or Other - Standard, 2 - Deletion Success}
    #Define parameters for slack message
    slack_webhook_url = ''
    slack_data = ''
    protected_count = 0
    deletion_count = 0
    for message in message_list:
        if message[0:15] == "--- [PROTECTED]":
            print(message[0:15])
            protected_count = protected_count + 1
            print(protected_count)
        elif message[0:14] == "--- [DELETION]":
            deletion_count = deletion_count + 1
            print(message[0:14])
            print(deletion_count)
    if deletion_count == 0 and protected_count > 0:
        return "Notification Aborted"
    else:
        try:
            formatted_message = ''
            formatted_message = formatted_message + '[EC2.19 REMEDIATION LAMBDA EXECUTED] %s in %s account %s has been flagged as NON-COMPLIANT. As a result offending SG rules will be deleted: ' % (SG_ID, Region, Account)
            for message in message_list:
                formatted_message = formatted_message + '\n' + message
            slack_data = {'text': formatted_message}

            #POST message to channel.
            response = requests.post(
            slack_webhook_url, data=json.dumps(slack_data), 
            headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            print('ERROR sending message. Please check logs for details: %s' % e)
    
def SendCompletionMessage(Message):
    slack_data = {'text': Message}
    try:
        slack_webhook_url = ''
        #POST message to channel.
        response = requests.post(
        slack_webhook_url, data=json.dumps(slack_data), 
        headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        print('ERROR sending message. Please check logs for details: %s' % e)
