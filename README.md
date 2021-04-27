# Network Alligator
![alligator](alligator.png)

**Alligator sounds a lot like Allocator**

Chalice/SAM serverless service that provides an IAM authenticated REST inferface to an IP Network Allocation stored in DynamoDB.

# Developing

## Prerequisites
* python3.8
* docker

## Setup

Satisfy python requirements:
```
pip3 install -r dev_requirements.txt
```

**Note: requirements.txt is used by Chalic for the dist bundle, so use dev_requirements.txt for development**

Run local dynamodb server:

```
docker-compose up -d
```

## Ensure tests all run successfully
```
py.test -srxP tests/test_app.py
```

## Development workflow
An environment variable, `ALLIGATOR_TEST` can be set to `1` to ensure all dynamodb access is made against the local dynamodb running under docker.

You can populate the local dynamodb database with:

```
ALLIGATOR_TEST=1 ./deploy.py init
```

The following can be used to run the service on localhost:8000 for interactive use (IAM authorization is automatically disabled in this case):

```
ALLIGATOR_TEST=1 chalice local
```

The local dynamodb database can be easily destroyed by deleting `docker/shared-local-instance.db`

Typical workflow is to test code changes iteratively with TDD by running the tests under `tests/test_app.py`

# Additional CFN resources
`resources.py` contains additional CFN resources that Chalice will merge with its own. These are written using Troposphere and the respective CFN template is generated during the build process.

# Deployment
`build.sh` generates `resources.json` (it needs to be JSON, there are currently
syntax errors with the generated YAML and IAM auth) and runs `chalice package` which creates artifacts under `dist/` ready for deployment.

`deploy.py` script assumed a multi-account control-tower environment with a master account and a workload account named `alligator`. Executing `deploy.py` as the master account will assume role into the `alligator` account and deploy the the contents of `dist/`

Common pattern is:

```
./build.sh && ./deploy.sh
```

It is also possible to create some sample data in the production environment based of the test fixtures. The below should probably only be run in production once, or possibly not at all in favour of manually allocating production data.

```
./deploy init
```

