import os
import json
from chalice.test import Client
from pytest import fixture
from app import app
import resources
from .networks import networks
from database import get_database


os.environ['ALLIGATOR_TEST'] = "1"


tables = dict(
    network_table=resources.network_table.to_dict()['Properties']
)

db = get_database()


def init_tables(db):
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


@fixture
def client():
    with Client(app) as client:
        yield client


@fixture
def test_data():
    print("Creating test data...")
    init_tables(db)
    for network in networks:
        db.put_item(
            TableName='network_table',
            Item=network
        )
    return networks


def test_local_dynamodb():
    response = db.describe_limits()
    assert 'AccountMaxReadCapacityUnits' in response


def test_get_all_networks(client, test_data):
    result = client.http.get('/networks')
    assert len(result.json_body) == len(networks)


def test_get_network(client, test_data):
    result = client.http.get('/networks/192.168.0.0/24')
    assert result.json_body == {
        'network_integer': {'N': '3232235520'},
        'network_string': {'S': '192.168.0.0'},
        'prefix_length': {'N': '24'}
    }


def test_network_not_found(client, test_data):
    result = client.http.get('/networks/192.168.90.0/24')
    assert result.status_code == 404


def test_network_allocate(client, test_data):
    result = client.http.post('/networks', body=json.dumps(dict(prefixlen=24)),
                              headers={'Content-Type': 'application/json'})
