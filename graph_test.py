import graph_builder

switches = [
    {
        "dpid": "0000000000000001",
        "ports": [
            {"dpid": "0000000000000001", "port_no": "00000001", "hw_addr": "0a:b1:00:00:01:01", "name": "s1-eth1"},
            {"dpid": "0000000000000001", "port_no": "00000002", "hw_addr": "0a:b1:00:00:01:02", "name": "s1-eth2"},
            {"dpid": "0000000000000001", "port_no": "00000003", "hw_addr": "0a:b1:00:00:01:03", "name": "s1-eth3"},
        ],
    },
    {
        "dpid": "0000000000000002",
        "ports": [
            {"dpid": "0000000000000002", "port_no": "00000001", "hw_addr": "0a:b1:00:00:02:01", "name": "s2-eth1"},
            {"dpid": "0000000000000002", "port_no": "00000002", "hw_addr": "0a:b1:00:00:02:02", "name": "s2-eth2"},
        ],
    },
    {
        "dpid": "0000000000000003",
        "ports": [
            {"dpid": "0000000000000003", "port_no": "00000001", "hw_addr": "0a:b1:00:00:03:01", "name": "s3-eth1"},
            {"dpid": "0000000000000003", "port_no": "00000002", "hw_addr": "0a:b1:00:00:03:02", "name": "s3-eth2"},
        ],
    },
    {
        "dpid": "0000000000000004",
        "ports": [
            {"dpid": "0000000000000004", "port_no": "00000001", "hw_addr": "0a:b1:00:00:04:01", "name": "s4-eth1"},
            {"dpid": "0000000000000004", "port_no": "00000002", "hw_addr": "0a:b1:00:00:04:02", "name": "s4-eth2"},
            {"dpid": "0000000000000004", "port_no": "00000003", "hw_addr": "0a:b1:00:00:04:03", "name": "s4-eth3"},
        ],
    },
]

links = [
    {
        "src": {"dpid": "0000000000000001", "port_no": "00000002", "hw_addr": "0a:b1:00:00:01:02", "name": "s1-eth2"},
        "dst": {"dpid": "0000000000000002", "port_no": "00000001", "hw_addr": "0a:b1:00:00:02:01", "name": "s2-eth1"},
    },
    {
        "src": {"dpid": "0000000000000002", "port_no": "00000002", "hw_addr": "0a:b1:00:00:02:02", "name": "s2-eth2"},
        "dst": {"dpid": "0000000000000004", "port_no": "00000001", "hw_addr": "0a:b1:00:00:04:01", "name": "s4-eth1"},
    },
    {
        "src": {"dpid": "0000000000000001", "port_no": "00000003", "hw_addr": "0a:b1:00:00:01:03", "name": "s1-eth3"},
        "dst": {"dpid": "0000000000000003", "port_no": "00000001", "hw_addr": "0a:b1:00:00:03:01", "name": "s3-eth1"},
    },
    {
        "src": {"dpid": "0000000000000003", "port_no": "00000002", "hw_addr": "0a:b1:00:00:03:02", "name": "s3-eth2"},
        "dst": {"dpid": "0000000000000004", "port_no": "00000002", "hw_addr": "0a:b1:00:00:04:02", "name": "s4-eth2"},
    },
]

hosts = [
    {
        "mac": "00:00:00:00:00:01",
        "ipv4": ["10.0.0.1"],
        "ipv6": [],
        "port": {"dpid": "0000000000000001", "port_no": "00000001", "hw_addr": "0a:b1:00:00:01:01", "name": "s1-eth1"},
    },
    {
        "mac": "00:00:00:00:00:02",
        "ipv4": ["10.0.0.2"],
        "ipv6": [],
        "port": {"dpid": "0000000000000004", "port_no": "00000003", "hw_addr": "0a:b1:00:00:04:03", "name": "s4-eth3"},
    },
]

probe_result = {
    "src": "h1",
    "dst": "h2",
    "sent": 100,
    "recv": 97,
    "loss_pct": 15.0,
    "rtt_min_ms": 9.8,
    "rtt_avg_ms": 12.4,
    "rtt_max_ms": 19.1,
    "jitter_ms": 1.6,
}

G = graph_builder.generate_graph(hosts, switches, links)
graph_builder.draw_graph(G, probe_result, "test2.png")

