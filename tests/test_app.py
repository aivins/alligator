import os
import json
import ipaddress
from chalice.test import Client
from pytest import fixture
from app import app
import resources
from .networks import networks
from chalicelib.database import get_database
from chalicelib.utils import boundary, next_boundary


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


def test_network_boundary_detection():
    assert str(boundary(ipaddress.ip_address(
        '192.168.1.99'), 24)) == '192.168.1.0/24'
    assert str(boundary(ipaddress.ip_address(
        '172.16.31.56'), 23)) == '172.16.30.0/23'


def test_network_next_boundary():
    assert str(next_boundary(ipaddress.ip_address(
        '192.168.1.0'), 24)) == '192.168.2.0/24'
    assert str(next_boundary(ipaddress.ip_address(
        '10.0.0.0'), 16)) == '10.1.0.0/16'


# def test_local_dynamodb():
#     response = db.describe_limits()
#     assert 'AccountMaxReadCapacityUnits' in response


# def test_get_all_networks(client, test_data):
#     result = client.http.get('/networks')
#     assert len(result.json_body) == len(networks)


# def test_get_network(client, test_data):
#     result = client.http.get('/networks/192.168.0.0/24')
#     assert result.json_body == {
#         'network_integer': 3232235520,
#         'network_string': '192.168.0.0',
#         'prefix_length': 24
#     }


# def test_network_not_found(client, test_data):
#     result = client.http.get('/networks/192.168.90.0/24')
#     assert result.status_code == 404


def test_network_free(client, test_data):
    result = client.http.get('/networks/free?prefixlen=28')
    assert result.json_body == ['192.168.1.16/28', '192.168.0.16/28',
                                '192.168.0.144/28', '192.168.1.16/28',
                                '0.0.0.16/28', '192.168.16.16/28']



# def test_network_allocate(client, test_data):
#     result = client.http.post('/networks', body=json.dumps(dict(prefixlen=24)),
#                               headers={'Content-Type': 'application/json'})
#     assert '192.168.0.0/24' in result.json_body
