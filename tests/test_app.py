from chalice.test import Client
from app import app

def test_networks_function():
    with Client(app) as client:
        result = client.lambda_.invoke('networks')
        assert result.payload == {'hello': 'world'}

