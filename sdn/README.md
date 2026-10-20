# SDN part (Mininet + Ryu)

CN Mini Project PS13 - Network Diagnostic and Path Analysis Tool.
This folder has the topology, the Ryu controller and the REST API used by the integration part.

## Files
- `topo_diamond.py` - Mininet diamond topology
- `diag_controller.py` - Ryu app (loop-free routing + `/v1.0/diag/paths`)
- `run_all.sh` - starts Ryu and Mininet together
- `check_rest.py` - tests the REST API

## Topology
```
              s2  (5 ms per link)
            /    \
  h1 -- s1        s4 -- h2
            \    /
              s3  (20 ms per link)
```
- h1 = 10.0.0.1, h2 = 10.0.0.2
- sN has dpid N
- upper path RTT ~20 ms, lower path ~80 ms

## Setup
Ryu needs Python 3.9 (breaks on 3.10+), so it runs in a venv. Mininet uses system python3.

```bash
sudo apt update
sudo apt install -y software-properties-common git curl net-tools build-essential \
    python3-setuptools mininet openvswitch-switch
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3.9-dev

python3.9 -m venv ~/ryuenv
source ~/ryuenv/bin/activate
python -m pip install "setuptools==58.2.0" wheel pbr
python -m pip install "dnspython==1.16.0" "eventlet==0.30.2"
python -m pip install --no-build-isolation "ryu==4.34"
deactivate
```
`setuptools==58.2.0` and `--no-build-isolation` are needed, otherwise the ryu install fails.

## Run
```bash
cd sdn
./run_all.sh
```
Second terminal: `python3 check_rest.py`

## REST (http://127.0.0.1:8080)
- `/v1.0/topology/switches` - 4 switches
- `/v1.0/topology/links` - 8 entries (4 links x 2 directions)
- `/v1.0/topology/hosts` - filled after the first ping
- `/v1.0/diag/paths` - actual path used by each host pair, e.g. `"path": ["s1","s2","s4"]`

Use `/diag/paths` for the real path. Both paths have equal hop count, so networkx can pick the wrong one.

## Loop handling
No STP. Broadcast/unknown packets go only to host ports (controller sends them), unicast gets flows on the BFS shortest path. Any link up/down clears the flows, so traffic re-routes.

## Tests
Failed path (at the `mininet>` prompt):
```
h1 ping -c 3 h2
link s1 s2 down
h1 ping -c 3 h2        # now goes via s3
link s1 s2 up
```
Packet loss (second terminal, use `replace` not `add`):
```bash
sudo tc qdisc replace dev s1-eth2 root netem delay 5ms loss 20%
sudo tc qdisc replace dev s1-eth2 root netem delay 5ms
```
Link interfaces: s1-s2 = `s1-eth2`, s2-s4 = `s2-eth2`, s1-s3 = `s1-eth3`, s3-s4 = `s3-eth2`.

## Common problems
- `ryu-manager not found` - recreate the venv
- `address already in use` - `pkill -f ryu-manager; sudo mn -c`
- hosts empty - run `pingall` in Mininet
