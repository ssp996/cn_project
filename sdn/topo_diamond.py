#!/usr/bin/env python3
"""
topo_diamond.py - diamond topology for CN mini project PS13 (Person B)

              s2   (upper path, 5 ms per link)
            /    \
  h1 -- s1        s4 -- h2
            \    /
              s3   (lower path, 20 ms per link)

h1 = 10.0.0.1/24 (00:00:00:00:00:01)   h2 = 10.0.0.2/24 (00:00:00:00:00:02)
Switch sN has dpid N (s1 = 0000000000000001).  Controller: 127.0.0.1:6653
"""
import json
import os
import sys
import time
import urllib.request
from functools import partial

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo

REST = 'http://127.0.0.1:8080'


class DiamondTopo(Topo):
    def build(self):
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        self.addLink(h1, s1)               # s1-eth1
        self.addLink(h2, s4)               # s4-eth1
        self.addLink(s1, s2, delay='5ms')  # s1-eth2 <-> s2-eth1
        self.addLink(s2, s4, delay='5ms')  # s2-eth2 <-> s4-eth2
        self.addLink(s1, s3, delay='20ms') # s1-eth3 <-> s3-eth1
        self.addLink(s3, s4, delay='20ms') # s3-eth2 <-> s4-eth3


def wait_for_topology(expected_links=8, timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(REST + '/v1.0/topology/links', timeout=2) as r:
                if len(json.loads(r.read().decode())) >= expected_links:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main():
    if os.geteuid() != 0:
        sys.exit('Run with sudo:  sudo python3 topo_diamond.py')
    setLogLevel('info')
    net = Mininet(topo=DiamondTopo(),
                  switch=partial(OVSSwitch, protocols='OpenFlow13'),
                  controller=None, link=TCLink, autoSetMacs=True, build=False)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    try:
        net.start()
        net.waitConnected(timeout=20)
        info('*** Waiting for Ryu topology discovery (8 directed links)\n')
        if not wait_for_topology():
            info('!!! topology not fully discovered - check logs/ryu.log\n')
        h1, h2 = net.get('h1', 'h2')
        info('*** Warm-up ping so Ryu learns the hosts\n')
        for _ in range(5):
            if net.ping([h1, h2], timeout='2') == 0:
                break
            time.sleep(1)
        info('\n*** READY  REST: %s/v1.0/topology/{switches,links,hosts}  '
             'and  %s/v1.0/diag/paths\n\n' % (REST, REST))
        CLI(net)
    finally:
        net.stop()


if __name__ == '__main__':
    main()
