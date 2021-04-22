import ipaddress
from chalice import Chalice, NotFoundError
from database import get_database

app = Chalice(app_name='alligator')


def to_payload(data):
    def cast_value(value):
        return value
    return {k:cast_value(v) for k,v in data.items()}


@app.route('/networks')
def networks():
    networks = get_database().scan(TableName='network_table')['Items']
    return [
        to_payload(net)
        for net in networks
    ]


@app.route('/networks', methods=['POST'], content_types=['application/json'])
def allocate():
    prefixlen = int(app.current_request.json_body.get('prefixlen', 24))


@app.route('/networks/{network}/{prefixlen}')
def network(network, prefixlen):
    cidr = ipaddress.ip_network(f'{network}/{prefixlen}')

    network_integer = int(cidr.network_address)
    prefix_length = cidr.prefixlen

    network = get_database().get_item(
        TableName='network_table',
        Key=dict(
            network_integer=dict(N=str(network_integer)),
            prefix_length=dict(N=str(prefix_length))
        )
    )

    if 'Item' not in network:
        raise NotFoundError(f'Network {cidr} not found')

    return to_payload(network['Item'])



