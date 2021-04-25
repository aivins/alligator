import os
import json
import ipaddress
from chalice.test import Client
from pytest import fixture
from app import app
import resources
from .networks import networks
from chalicelib.database import get_database
from chalicelib.utils import (
    boundary,
    next_boundary,
    to_payload,
    make_tree,
    find_parent,
    get_all_networks
)


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
    return_value = []
    for network in networks:
        db.put_item(
            TableName='network_table',
            Item=network
        )
        return_value.append(to_payload(network))
    return sorted(return_value, key=lambda net: net['network_integer'])


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


def test_make_tree(test_data):
    expected_tree = {
        '0.0.0.0/0': {
            '10.0.0.0/8': {},
            '192.168.0.0/20': {
                '192.168.0.0/24': {
                    '192.168.0.0/25': {}
                },
                '192.168.1.0/24': {}
            }
        }
    }

    tree1 = make_tree(test_data)
    assert tree1 == expected_tree

    networks = get_all_networks()
    tree2 = make_tree(networks)
    assert tree2 == expected_tree


def test_find_parent(test_data):
    tree = make_tree(test_data)

    (parent, _) = find_parent(tree, ipaddress.ip_network('192.168.0.0/28'))
    assert parent == ipaddress.ip_network('192.168.0.0/25')

    (parent, _) = find_parent(tree, ipaddress.ip_network('11.0.0.0/8'))
    assert parent == ipaddress.ip_network('0.0.0.0/0')

    (parent, _) = find_parent(tree, ipaddress.ip_network('10.0.0.0/8'))
    assert parent == ipaddress.ip_network('0.0.0.0/0')


def test_get_all_networks(client, test_data):
    result = client.http.get('/networks')
    assert len(result.json_body) == len(networks)


def test_get_network(client, test_data):
    result = client.http.get('/networks/192.168.0.0/24')
    assert result.json_body == {
        'network_integer': 3232235520,
        'network_string': '192.168.0.0',
        'prefix_length': 24
    }


def test_network_not_found(client, test_data):
    result = client.http.get('/networks/192.168.90.0/24')
    assert result.status_code == 404


def test_network_free(client, test_data):
    result = client.http.get('/networks/free?prefixlen=28')
    assert result.json_body == ['192.168.0.16/28', '192.168.0.144/28', '192.168.1.16/28',
                                '192.168.2.16/28', '10.0.0.16/28', '0.0.0.16/28',
                                '11.0.0.16/28', '192.168.16.16/28']


def test_network_allocate(client, test_data):
    result = client.http.post('/networks', body=json.dumps(dict(network='11.0.0.0/8')),
                              headers={'Content-Type': 'application/json'})
    assert result.status_code == 200
    result = client.http.post('/networks', body=json.dumps(dict(network='11.0.0.0/8')),
                              headers={'Content-Type': 'application/json'})
    assert result.status_code == 409


def test_network_allocate_next(client, test_data):
    result = client.http.post('/networks', body=json.dumps(dict(prefixlen='28')),
                              headers={'Content-Type': 'application/json'})
    assert result.status_code == 200
    assert result.json_body == {'network_integer': 3232235536,
                                'network_string': '192.168.0.16', 'prefix_length': 28}
