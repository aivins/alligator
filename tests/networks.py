import ipaddress
from chalicelib.utils import network_to_keys

networks = [
  network_to_keys(ipaddress.ip_network(network))
  for network in
  [
    '192.168.0.0/20',
    '192.168.0.0/24',
    '192.168.1.0/24',
    '192.168.0.0/25',
    '10.0.0.0/8',
  ]
]
