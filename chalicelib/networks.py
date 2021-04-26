import ipaddress
from chalice import Blueprint, NotFoundError, ConflictError, BadRequestError
from chalicelib.database import get_database
from chalicelib.utils import (
    to_payload,
    get_all_networks,
    make_tree,
    find_free,
    find_parent,
    network_to_keys
)


endpoint = Blueprint(__name__)
networks_endpoint = endpoint


@endpoint.route('/')
def networks():
    networks = get_all_networks()
    return [
        to_payload(net)
        for net in networks
    ]


@endpoint.route('/free')
def free():
    params = endpoint.current_request.query_params or {}
    prefixlen = int(params.get('prefixlen', 24))
    parent_prefixlen = int(params.get('parent_prefixlen', 20))
    networks = get_all_networks()
    tree = make_tree(networks)
    free = list(find_free(tree, prefixlen))
    return [str(f) for f in free]


@endpoint.route('/', methods=['POST'], content_types=['application/json'])
def allocate():
    network = endpoint.current_request.json_body.get('network')
    prefixlen = endpoint.current_request.json_body.get('prefixlen')

    if network is not None and prefixlen is not None:
        raise BadRequestError('cannot provide both network and prefixlen')

    networks = get_all_networks()
    tree = make_tree(networks)

    if network:
        network = ipaddress.ip_network(network)
        (parent, children) = find_parent(tree, network)
        if str(network) not in children:
            item = network_to_keys(network)
            get_database().put_item(
                TableName='network_table',
                Item=item
            )
            return to_payload(item)
        else:
            raise ConflictError(f'{network} is already allocated')
    elif prefixlen:
        prefixlen = int(prefixlen)
        free = next(find_free(tree, prefixlen))
        if not free:
            raise BadRequestError(
                f'Unable to allocate /{prefixlen} network, not enough free space in parent')
        item = network_to_keys(free)
        get_database().put_item(
            TableName='network_table',
            Item=item
        )
        return to_payload(item)

    else:
        raise BadRequestError('network or prefixlen required')


@endpoint.route('/{network}/{prefixlen}')
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
