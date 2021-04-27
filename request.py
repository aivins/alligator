#!/usr/bin/env python3

import sys
from urllib.parse import urlparse
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth


# Script to test IAM authorization works
# eg. request.py https://68uh616kt0.execute-api.ap-southeast-2.amazonaws.com/api/free


url = sys.argv[1]
host = urlparse(url)[1]

auth = BotoAWSRequestsAuth(aws_host=host,
                           aws_region='ap-southeast-2',
                           aws_service='execute-api')


response = requests.get(url, auth=auth)

print(response.json())
