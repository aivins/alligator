import os
from functools import lru_cache
import boto3


@lru_cache
def get_database(session=None):
    test = bool(os.environ.get('ALLIGATOR_TEST', False))
    if not session:
        session = boto3.Session()
    if test:
        db = session.client('dynamodb', endpoint_url='http://localhost:8000')
    else:
        db = session.client('dynamodb')
    return db
