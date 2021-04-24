import ipaddress

networks = [
  dict(
    network_integer=dict(N=str(int(ipaddress.ip_address(network)))),
    network_string=dict(S=network),
    prefix_length=dict(N=str(prefixlen))
  ) for (network, prefixlen) in
  [
    ('0.0.0.0', 0),
    ('192.168.0.0', 20),
    ('192.168.0.0', 24),
    ('192.168.1.0', 24),
    ('192.168.0.0', 25)
  ]
]