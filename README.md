# Network Diagnostic and Path Analysis Tool (Project 13)

    sockets/       UDP echo server + probe client (RTT, jitter, loss -> JSON)
    sdn/           Mininet diamond topology + Ryu controller (topology + diag REST)
    integration/   graph builder + analyze.py (probe JSON + Ryu data -> path, graph)
    results/       probe.json, merged.json, topology_path.png
    test/          early standalone socket/mininet tests

## Setup
- Ryu venv at ~/ryuenv (or set RYU_VENV)
- pip install networkx matplotlib (for integration/)

## Run
Terminal 1 (Ryu + Mininet, from repo root):

    ./sdn/run_all.sh

Mininet CLI:

    mininet> h2 python3 sockets/server.py --port 5005 &
    mininet> h1 python3 sockets/client.py --dst 10.0.0.2 --count 100 --out results/probe.json

Terminal 2 (normal shell, repo root):

    python3 sdn/check_rest.py
    cd integration && python3 analyze.py --probe ../results/probe.json --out ../results/topology_path.png > ../results/merged.json

analyze.py prints the merged JSON (path, alternative paths, RTT, loss, utilization) to stdout and saves the topology graph with the active path highlighted.
