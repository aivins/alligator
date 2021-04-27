#!/usr/bin/env python

import sys
import os
from awscli.customizations.s3uploader import S3Uploader
from chalicelib.assume_role import aws_account
from chalicelib.database import get_database
from tests.networks import networks
import resources

STACK_NAME = 'NetworkAlligator'
ASSUME_ROLE = 'AWSControlTowerExecution'
WORKLOAD_ACCOUNT = 'alligator'
DEPLOY_BUCKET = 'alligator-deployment-bucket'


test = bool(os.environ.get('ALLIGATOR_TEST', False))


def init_tables(db):
    tables = dict(
        network_table=resources.network_table.to_dict()['Properties']
    )
    for table_name, definition in tables.items():
        try:
            db.delete_table(TableName=table_name)
            waiter = db.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name)
        except db.exceptions.ResourceNotFoundException:
            pass
        db.create_table(
            **definition
        )


@aws_account(ASSUME_ROLE, WORKLOAD_ACCOUNT)
def init_db(context):
    print('Initializing network_table...')
    session = context.session
    db = get_database(session)
    if test:
        init_tables(db)
    for network in networks:
        print(network)
        db.put_item(
            TableName='network_table',
            Item=network
        )
    print('done!')


@aws_account(ASSUME_ROLE, WORKLOAD_ACCOUNT)
def deploy(context):
    session = context.session

    with open('dist/sam.json', 'r') as template_file:
        template_body = template_file.read()

    s3 = session.client('s3')
    try:
        s3.create_bucket(
            Bucket=DEPLOY_BUCKET,
            CreateBucketConfiguration={
                'LocationConstraint': session.region_name,
            },
        )
    except (s3.exceptions.BucketAlreadyExists, s3.exceptions.BucketAlreadyOwnedByYou):
        pass

    uploader = S3Uploader(
        s3,
        DEPLOY_BUCKET,
    )
    code_uri = uploader.upload_with_dedup('dist/deployment.zip')
    code_key = code_uri.split(f'{DEPLOY_BUCKET}/')[1]
    print(f'\nCODE_URI={code_uri}\nCODE_KEY={code_key}')

    cfn = session.client('cloudformation')

    stack_exists = False
    stacks = cfn.list_stacks()['StackSummaries']
    for stack in stacks:
        if stack['StackStatus'] == 'DELETE_COMPLETE':
            continue
        if STACK_NAME == stack['StackName']:
            stack_exists = True

    if stack_exists:
        print('Updating stack...')
        operation = cfn.update_stack
        waiter = cfn.get_waiter('stack_update_complete')
    else:
        print('Creating stack...')
        operation = cfn.create_stack
        waiter = cfn.get_waiter('stack_create_complete')

    operation(
        StackName=STACK_NAME,
        TemplateBody=template_body,
        Capabilities=[
            'CAPABILITY_IAM',
            'CAPABILITY_AUTO_EXPAND'
        ],
        Parameters=[
            dict(ParameterKey='CodeBucket', ParameterValue=DEPLOY_BUCKET),
            dict(ParameterKey='CodeKey', ParameterValue=code_key)
        ]
    )

    waiter.wait(
        StackName=STACK_NAME
    )

    response = cfn.describe_stacks(StackName=STACK_NAME)
    print(response)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_db()
    else:
        deploy()
