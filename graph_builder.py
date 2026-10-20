import networkx as nx
import json
import matplotlib.pyplot as plt

#create networkx graph using ryu api data
def generate_graph(hosts, switches, links):
    G = nx.Graph()

    for sw in switches:
        sw_name = f"s{int(sw['dpid'], 16)}" #convert base 16 string to human readable (0000000000000001 becomes s1)
        G.add_node(sw_name, node_type="switch", dpid=sw["dpid"])

    for host in hosts:
        h_name = f"h{int(host['mac'].split(':')[-1], 16)}" #last section of MAC address corresponds to host in Mininet 
                                                            #(00:00:00:00:00:01 corresponds to h1)
        sw_name = f"s{int(host['port']['dpid'], 16)}"

        G.add_node(h_name, node_type="host", ip=host["ipv4"][0])
        G.add_edge(h_name, sw_name, port=int(host["port"]["port_no"], 16))

    for link in links:
        u = f"s{int(link['src']['dpid'], 16)}"
        v = f"s{int(link['dst']['dpid'], 16)}"
        G.add_edge(u, v)

    return G

#draw the created graph using matplotlib, if source and taraget are specified, highlight a path from source to target
#show possible link outages, suggest alternate paths in merged output if source and target are specified
def draw_graph(G, probe_result, filename):
    #create graph layout
    pos = nx.spring_layout(G, seed=67)

    #separate switches and hosts from networkx graph
    switches = [n for n, attr in G.nodes(data=True) if attr.get("node_type") == "switch"]
    hosts = [n for n, attr in G.nodes(data=True) if attr.get("node_type") == "host"]

    #add elements to graph
    nx.draw_networkx_nodes(G, pos, nodelist=switches, node_color="#0000ff", node_shape="s", node_size=250, label="Switches")
    nx.draw_networkx_nodes(G, pos, nodelist=hosts, node_color="#409040", node_shape="o", node_size=250, label="Hosts")
    nx.draw_networkx_edges(G, pos, edge_color="#cccccc", width=1)
    nx.draw_networkx_labels(G, pos,font_color=(0.663, 0.663, 0.663))

    #path finding utility built into networkx, in this case, uses dijkstra's algorithm to find shortest path between source and target
    active_path = nx.shortest_path(G, source=probe_result["src"], target=probe_result["dst"])

    #create list of edges by zipping everything except the last node, and everything except the first node
    #if active path is ["h1", "s1", "s2", "s4", "h2"], zip ["h1", "s1", "s2", "s4"] and ["s1", "s2", "s4", "h2"] to get
    #[("h1", "s1"), ("s1", "s2"), ("s2", "s4"), ("s4", "h2")], which are the path edges
    path_edges = list(zip(active_path[:-1], active_path[1:]))

    #ignore hosts to provide path with only switches, so if path is ["h1", "s1", "s2", "s4", "h2"], 
    #switch_path is ["s1", "s2", "s4"]
    all_switch_paths = [p[1:-1] for p in nx.all_simple_paths(G, source=probe_result["src"], target=probe_result["dst"])]

    #drawing links
    path_color = "#ff0000" if probe_result["loss_pct"] > 10.0 else "#2ECC71"
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color=path_color, width=4)

    #draw path details
    plt.title(f"Path: {' -> '.join(active_path)} | RTT: {probe_result['rtt_avg_ms']} ms | Loss: {probe_result['loss_pct']}%")

    plt.legend()
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)

    

    #provide alternate paths to probed output
    merged_output = {
        "src": probe_result["src"],
        "dst": probe_result["dst"],
        "path": active_path[1:-1],
        "alternative_paths": [p for p in all_switch_paths if p != active_path[1:-1]],
        "rtt_avg_ms": probe_result["rtt_avg_ms"],
        "loss_pct": probe_result["loss_pct"],
    }

    print(json.dumps(merged_output, indent=2))