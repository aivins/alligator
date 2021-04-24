import ipaddress
import logging
from collections import OrderedDict
from chalice import Chalice, NotFoundError
from chalicelib.database import get_database
from chalicelib.utils import (
    to_payload,
    get_all_networks,
    make_tree,
    find_free,
    find_parent
)


app = Chalice(app_name='alligator')
app.log.setLevel(logging.DEBUG)


@app.route('/networks')
def networks():
    networks = get_all_networks()
    return [
        to_payload(net)
        for net in networks
    ]


@app.route('/networks/free')
def free():
    prefixlen = int(app.current_request.query_params.get('prefixlen', 24))
    parent_prefixlen = int(app.current_request.query_params.get('parent_prefixlen', 20))
    networks = get_all_networks()
    tree = make_tree(networks)
    free = list(find_free(tree, prefixlen))
    return [str(f) for f in free]


@app.route('/networks', methods=['POST'], content_types=['application/json'])
def allocate():
    network = ipaddress.ip_network(app.current_request.json_body.get('network'))
    networks = get_all_networks()
    tree = make_tree(networks)
    parent = find_parent(tree, network)
    import json
    print(json.dumps(tree, indent=2))
    import ipdb; ipdb.set_trace()
    return free



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



