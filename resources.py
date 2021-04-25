from troposphere import (
    Template,
    Ref,
    Sub,
    Parameter,
    dynamodb,
    serverless,
    iam
)

from awacs.aws import (
    PolicyDocument,
    Statement,
    Allow,
    Principal,
    Action,
)

import awacs.dynamodb
import awacs.logs
import awacs.sts




class UnvalidatedAWSObject:
    def _validate_props(self):
        pass

    def validate(self):
        pass


class UnvalidatedFunction(UnvalidatedAWSObject, serverless.Function):
    pass


class UnvalidatedRole(UnvalidatedAWSObject, iam.Role):
    pass


t = Template('Network Allocator Resources')

code_bucket = t.add_parameter(
    Parameter(
        'CodeBucket',
        Description='S3 bucket name for ZIP bundle',
        Type='String'
    )
)

code_key = t.add_parameter(
    Parameter(
        'CodeKey',
        Description='S3 path of ZIP bundle',
        Type='String'
    )
)


network_table = t.add_resource(
    dynamodb.Table(
        'NetworkTable',
        TableName='network_table',
        BillingMode='PAY_PER_REQUEST',
        AttributeDefinitions=[
            dynamodb.AttributeDefinition(
                AttributeName='network_integer',
                AttributeType='N'
            ),
            dynamodb.AttributeDefinition(
                AttributeName='prefix_length',
                AttributeType='N'
            )
        ],
        KeySchema=[
            dynamodb.KeySchema(
                AttributeName='network_integer',
                KeyType='HASH'
            ),
            dynamodb.KeySchema(
                AttributeName='prefix_length',
                KeyType='RANGE'
            )
        ]
    )
)


t.add_resource(
    UnvalidatedFunction(
        'APIHandler',
        CodeUri=serverless.S3Location(
            Bucket=Ref(code_bucket),
            Key=Ref(code_key)
        ),
        Environment=serverless.Environment(
            Variables=dict(
                NETWORK_TABLE=Ref(network_table)
            )
        )
    )
)


t.add_resource(
    iam.Role(
        'DefaultRole',
        AssumeRolePolicyDocument=PolicyDocument(
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[awacs.sts.AssumeRole],
                    Principal=Principal(
                        'Service', ['lambda.amazonaws.com']
                    )
                )
            ],
        ),
        Policies=[
            iam.Policy(
                PolicyName='NetworkTableAccess',
                PolicyDocument=PolicyDocument(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[awacs.dynamodb.Action('*')],
                            Resource=['arn:aws:dynamodb:*:*:table/network_table']
                        )
                    ]
                )
            ),
            # This policy is designed to be identical to the one produced by Chalic
            # Merging the Policies key above during build overwrites it, so it has
            # to be included here to make it into the final sam.yaml
            iam.Policy(
                PolicyName='DefaultRolePolicy',
                PolicyDocument=PolicyDocument(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[
                                awacs.logs.CreateLogGroup,
                                awacs.logs.CreateLogStream,
                                awacs.logs.PutLogEvents
                            ],
                            Resource=['arn:*:logs:*:*:*']
                        )
                    ],
                )
            )
        ]
    )
)


if __name__ == '__main__':
    print(t.to_yaml())