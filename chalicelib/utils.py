import ipaddress
from collections import OrderedDict
from .database import get_database


def to_payload(data):
    def cast_value(value):
        if 'N' in value:
            return int(value['N'])
        else:
            return value['S']
    return {k:cast_value(v) for k,v in data.items()}


def boundary(address, prefixlen):
     bitprefixlen = (2**32-1) & ~ (2 ** (32-prefixlen)-1)
     return ipaddress.ip_network(
         str(ipaddress.ip_address(int(address) & bitprefixlen)) + f'/{prefixlen}')


def next_boundary(address, prefixlen):
    network_boundary_int = int(boundary(address, prefixlen).network_address)
    cidr = str(ipaddress.ip_address(network_boundary_int + 2 ** (32 - prefixlen))) + f'/{prefixlen}'
    return ipaddress.ip_network(cidr)


def walk_tree(tree):
    for network, children in sorted(tree.items(), key=lambda item: ipaddress.ip_network(item[0]).prefixlen, reverse=True):
        yield from walk_tree(children)
        yield (network, children)


def find_parent(tree, subnet):
    for network, children in tree.items():
        parent = find_parent(children, subnet)
        if parent is not None:
            return parent
        ip_network = ipaddress.ip_network(network)
        if subnet.subnet_of(ip_network):
            return children


def get_all_networks():
    networks = get_database().scan(TableName='network_table')['Items']
    return [to_payload(network) for network in networks]


def make_tree(networks, tree=OrderedDict()):
    for network in [ipaddress.ip_network('{network_string}/{prefix_length}'.format(**net)) for net in networks]:
        parent = find_parent(tree, network)
        if parent is not None:
            parent[str(network)] = OrderedDict()
        else:
            tree[str(network)] = OrderedDict()
    return tree


def print_gap(start, end):
    hosts = end - start
    start = ipaddress.ip_address(start)
    end = ipaddress.ip_address(end)
    print(f'{start} - {end}: {hosts} hosts')


def find_free(tree, prefixlen):
    seen = {}
    def _find_free(tree, prefixlen):
        required_size = 2 ** (32 - prefixlen)
        for network, subnets in walk_tree(tree):
            if network in seen:
                continue
            seen[network] = True
            network = ipaddress.ip_network(network)
            if network.prefixlen < prefixlen:
                yield from _find_free(subnets, prefixlen)
                offset = int(network.network_address)
                for subnet in subnets:
                    subnet = ipaddress.ip_network(subnet)
                    start = int(subnet.network_address)
                    gap = start - offset
                    if gap >= required_size:
                        # print_gap(offset, start)
                        yield next_boundary(ipaddress.ip_address(offset + 1), prefixlen)
                    offset = int(subnet.broadcast_address)
                start = int(network.broadcast_address)
                gap =  start - offset
                if gap >= required_size:
                    # print_gap(offset, start)
                    yield  next_boundary(ipaddress.ip_address(offset + 1), prefixlen)
    return list(_find_free(tree, prefixlen))