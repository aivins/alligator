import sys
import os
import json
import ipaddress
from chalice.test import Client
from pytest import fixture
from app import app
from .networks import networks
from deploy import init_tables
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
db = get_database()

boring_fields = {
    'class': '',
    'group': '',
    'description': '',
    'account': ''
}


@fixture
def client():
    with Client(app) as client:
        yield client


@fixture(scope='session')
def test_data(request):
    sys.stdout.write(
        "\nLoading test data once for this entire run (scope='session')...")
    sys.stdout.flush()
    init_tables(db)
    return_value = []
    for network in networks:
        db.put_item(
            TableName='network_table',
            Item=network
        )
        return_value.append(to_payload(network))
    data = sorted(return_value, key=lambda net: net['network_integer'])
    sys.stdout.write('done!\n')
    sys.stdout.flush()
    return data


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
    expected_tree = [
        '0.0.0.0/0',
        '10.248.0.0/17',
        '10.248.32.0/20',
        '10.248.40.0/23'
    ]

    def assert_tree(tree):
        ref = tree
        for net in expected_tree:
            assert net in ref
            ref = ref[net]

    tree1 = make_tree(test_data)
    assert_tree(tree1)

    networks = get_all_networks()
    tree2 = make_tree(networks)
    assert_tree(tree2)


def test_find_parent(test_data):
    tree = make_tree(test_data)

    (parent, _) = find_parent(tree, ipaddress.ip_network('10.249.80.0/24'))
    assert parent == ipaddress.ip_network('10.249.80.0/20')

    (parent, _) = find_parent(tree, ipaddress.ip_network('11.0.0.0/8'))
    assert parent == ipaddress.ip_network('0.0.0.0/0')

    (parent, _) = find_parent(tree, ipaddress.ip_network('10.0.0.0/8'))
    assert parent == ipaddress.ip_network('0.0.0.0/0')


def test_get_all_networks(client, test_data):
    result = client.http.get('/')
    # 0.0.0.0/0 is implicit and we also added one in another test
    assert len(result.json_body) >= len(networks)


def test_get_network(client, test_data):
    result = client.http.get('/10.248.42.0/23')
    assert result.json_body['network_integer'] == 184035840
    assert result.json_body['prefix_length'] == 23
    assert result.json_body['network_string'] == '10.248.42.0/23'


def test_network_not_found(client, test_data):
    result = client.http.get('/192.168.90.0/24')
    assert result.status_code == 404


def test_network_free(client, test_data):
    result = client.http.get('/free?prefixlen=28')
    assert len(result.json_body) > 0


def test_network_allocate(client, test_data):
    result = client.http.post('/', body=json.dumps(dict(network='11.0.0.0/8')),
                              headers={'Content-Type': 'application/json'})
    assert result.status_code == 200
    result = client.http.post('/', body=json.dumps(dict(network='11.0.0.0/8')),
                              headers={'Content-Type': 'application/json'})
    assert result.status_code == 409


def test_network_allocate_next(client, test_data):
    result = client.http.post('/', body=json.dumps(dict(prefixlen='28')),
                              headers={'Content-Type': 'application/json'})
    assert result.status_code == 200
    assert result.json_body['network_integer'] == 172200464
    assert result.json_body['prefix_length'] == 28
