import networkx as nx
import json
import matplotlib.pyplot as plt

#hosts, links and network devices returned by ryu rest api

hosts = {}
links = {} 
switches = {}

probe_result = {}


def generate_graph(hosts, switches, links):
    G = nx.Graph()

    for sw in switches:
        sw_name = f"s{int(sw['dpid'], 16)}"
        G.add_node(sw_name, node_type="switch", dpid=sw["dpid"])

    for host in hosts:
        h_name = f"h{int(host['mac'].split(':')[-1], 16)}"
        sw_name = f"s{int(host['port']['dpid'], 16)}"
        G.add_node(h_name, node_type="host", ip=host["ipv4"][0])
        G.add_edge(h_name, sw_name, port=int(host["port"]["port_no"], 16))

    for link in links:
        u = f"s{int(link['src']['dpid'], 16)}"
        v = f"s{int(link['dst']['dpid'], 16)}"
        G.add_edge(u, v)

    return G

def draw_graph(G, probe_result, filename, source=None, target=None):
    pos = nx.spring_layout(G, seed=67)

    switches = [n for n, attr in G.nodes(data=True) if attr.get("node_type") == "switch"]
    hosts = [n for n, attr in G.nodes(data=True) if attr.get("node_type") == "host"]

    nx.draw_networkx_nodes(G, pos, nodelist=switches, node_color="#0000ff", node_shape="s", node_size=220, label="Switches")
    nx.draw_networkx_nodes(G, pos, nodelist=hosts, node_color="#409040", node_shape="o", node_size=220, label="Hosts")
    nx.draw_networkx_edges(G, pos, edge_color="#cccccc", width=1)
    nx.draw_networkx_labels(G, pos, font_weight="bold", font_color="white")

    if source is not None and target is not None:
        active_path = nx.shortest_path(G, source="h1", target="h2")
        path_edges = list(zip(active_path[:-1], active_path[1:]))

        path_color = "#ff0000" if probe_result["loss_pct"] > 10.0 else "#2ECC71"
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color=path_color, width=4)

        plt.title(f"Path: {' -> '.join(active_path)} | RTT: {probe_result['rtt_avg_ms']} ms | Loss: {probe_result['loss_pct']}%")

    plt.legend()
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)