import time
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.topo import Topo

SERVER_PYTHON_FILE = ""


class MyTopo(Topo):
    def build(self):
        h1 = self.addHost("h1", ip="10.0.0.1/24")
        h2 = self.addHost("h2", ip="10.0.0.2/24")

        s1 = self.addSwitch("s1")
        self.addLink(h1, s1)
        self.addLink(h2, s1)


class StandaloneSwitch(OVSSwitch):
    def __init__(self, name, **params):
        params["failMode"] = "standalone"
        super().__init__(name, **params)


net = Mininet(
    topo=MyTopo(),
    switch=StandaloneSwitch,
    controller=None
)

net.start()

try:
    h1 = net.get("h1")
    h2 = net.get("h2")

    h2.cmd(
        "python3 server.py"
        "> /tmp/server.log 2>&1 &"
    )

    time.sleep(0.5)

    output = h1.cmd(
        "python3 client.py"
    )

    print(output)
    print(h2.cmd("cat /tmp/server.log"))

finally:
    net.stop()

