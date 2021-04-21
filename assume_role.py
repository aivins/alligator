#!/usr/bin/env python3

from dataclasses import dataclass
from functools import wraps
import boto3



WORKLOAD_ACCOUNT = 'alligator'
IAM_ROLE='AWSControlTowerExecution'


@dataclass
class Context:
    account: dict
    session: object


def get_boto3_sts_session(aws_access_key_id, aws_secret_access_key, aws_session_token):
    return boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )


def assume_role(session, account_id, iam_role):
    sts = session.client('sts')
    role_arn = f'arn:aws:iam::{account_id}:role/{iam_role}'
    sts_creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=iam_role
    )
    return get_boto3_sts_session(
        sts_creds['Credentials']['AccessKeyId'],
        sts_creds['Credentials']['SecretAccessKey'],
        sts_creds['Credentials']['SessionToken']
    )


def assume_role_for_account(role, account_name):
    session = boto3.Session()
    orgs = session.client('organizations')
    accounts = orgs.list_accounts()['Accounts']
    for account in accounts:
        if account['Name'].lower() == account_name.lower():
            assumed_session = assume_role(session, account['Id'], role)
            return Context(account=account, session=assumed_session)



def aws_account(role, account_name):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            context = assume_role_for_account(role, account_name)
            return f(context, *args, **kwargs)
        return wrapped
    return wrapper
