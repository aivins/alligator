from troposphere import (
    Template,
    Ref,
    Parameter,
    dynamodb,
    serverless
)




class UnvalidatedAWSObject:
    def _validate_props(self):
        pass

    def validate(self):
        pass


class UnvalidatedFunction(UnvalidatedAWSObject, serverless.Function):
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
        BillingMode='PAY_PER_REQUEST',
        AttributeDefinitions=[
            dynamodb.AttributeDefinition(
                AttributeName='NetworkInteger',
                AttributeType='N'
            ),
            dynamodb.AttributeDefinition(
                AttributeName='NetworkString',
                AttributeType='S'
            )
        ],
        KeySchema=[
            dynamodb.KeySchema(
                AttributeName='NetworkInteger',
                KeyType='HASH'
            ),
            dynamodb.KeySchema(
                AttributeName='NetworkString',
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


if __name__ == '__main__':
    print(t.to_yaml())