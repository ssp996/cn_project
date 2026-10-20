"""
diag_controller.py - Ryu app for CN mini project PS13 (Person B)

- Loop-free forwarding on the diamond WITHOUT STP:
    * broadcast / unknown-unicast is sent by the controller ONLY to host-facing
      (edge) ports, never between switches -> no broadcast storm
    * known unicast gets flows installed along a BFS shortest path
- Any link add/delete clears installed flows, so traffic re-routes over the
  surviving path (this is how a failed path shows up).
- Extra REST endpoint:  GET /v1.0/diag/paths  -> path each host pair really uses
"""
import json
from collections import deque

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, DEAD_DISPATCHER,
                                    MAIN_DISPATCHER, set_ev_cls)
from ryu.lib.packet import arp, ether_types, ethernet, ipv4, packet
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology.api import get_link, get_switch
from webob import Response

FLOW_COOKIE = 0xD1A6
OFP_PORT_MAX = 0xffffff00


class DiagController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(DiagController, self).__init__(*args, **kwargs)
        self.datapaths = {}      # dpid -> datapath
        self.adj = {}            # dpid -> {neighbour dpid: out port}
        self.inter_ports = {}    # dpid -> set(port_no) that face other switches
        self.host_loc = {}       # mac -> (dpid, port)
        self.host_ip = {}        # mac -> ip
        self.active_paths = {}   # (src_mac, dst_mac) -> [dpid, ...]
        kwargs['wsgi'].register(DiagRest, {'diag_app': self})

    # ------------------------------------------------------------ switches
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        dp = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[dp.id] = dp
        elif ev.state == DEAD_DISPATCHER:
            self.datapaths.pop(dp.id, None)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self._add_flow(dp, 0, match, actions, 0)          # table-miss -> controller

    # ------------------------------------------------------------ topology
    @set_ev_cls([event.EventSwitchEnter, event.EventSwitchLeave,
                 event.EventLinkAdd, event.EventLinkDelete])
    def topology_change_handler(self, ev):
        adj, inter = {}, {}
        for sw in get_switch(self, None):
            adj.setdefault(sw.dp.id, {})
            inter.setdefault(sw.dp.id, set())
        for link in get_link(self, None):
            s, d = link.src, link.dst
            adj.setdefault(s.dpid, {})[d.dpid] = s.port_no
            inter.setdefault(s.dpid, set()).add(s.port_no)
            inter.setdefault(d.dpid, set()).add(d.port_no)
        self.adj, self.inter_ports = adj, inter
        self._clear_flows()
        self.logger.info('topology changed: %s',
                         {'s%d' % k: sorted('s%d' % n for n in v) for k, v in adj.items()})

    def _shortest_path(self, src, dst):
        if src == dst:
            return [src]
        prev = {src: None}
        queue = deque([src])
        while queue:
            node = queue.popleft()
            for nbr in sorted(self.adj.get(node, {})):
                if nbr in prev:
                    continue
                prev[nbr] = node
                if nbr == dst:
                    path = [dst]
                    while prev[path[-1]] is not None:
                        path.append(prev[path[-1]])
                    return path[::-1]
                queue.append(nbr)
        return None

    # ------------------------------------------------------------ packet-in
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype in (ether_types.ETH_TYPE_LLDP, ether_types.ETH_TYPE_IPV6):
            return                                   # LLDP is ryu.topology's job
        if in_port >= OFP_PORT_MAX:
            return
        if in_port in self.inter_ports.get(dp.id, ()):
            return                                   # loop guard
        if not any(self.adj.values()):
            return                                   # topology not discovered yet

        src, dst = eth.src, eth.dst
        self.host_loc[src] = (dp.id, in_port)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if arp_pkt and arp_pkt.src_ip != '0.0.0.0':
            self.host_ip[src] = arp_pkt.src_ip
        elif ip_pkt and ip_pkt.src != '0.0.0.0':
            self.host_ip[src] = ip_pkt.src

        is_multicast = int(dst.split(':')[0], 16) & 1
        if not is_multicast and dst in self.host_loc:
            self._route(dp, in_port, msg.data, src, dst)
        else:
            self._flood_edge_ports(dp.id, in_port, msg.data)

    def _route(self, dp, in_port, data, src, dst):
        s_dpid, s_port = self.host_loc[src]
        d_dpid, d_port = self.host_loc[dst]
        path = self._shortest_path(s_dpid, d_dpid)
        if path is None:
            self.logger.warning('NO PATH %s -> %s', src, dst)
            return
        self._install_path(path, src, dst, d_port)
        self._install_path(path[::-1], dst, src, s_port)
        self.active_paths[(src, dst)] = path
        self.active_paths[(dst, src)] = path[::-1]
        self.logger.info('path %s -> %s : %s', src, dst, ['s%d' % d for d in path])
        out_port = d_port if len(path) == 1 else self.adj[path[0]][path[1]]
        self._packet_out(dp, in_port, out_port, data)

    def _install_path(self, path, src_mac, dst_mac, last_port):
        for i in reversed(range(len(path))):          # last hop first
            dp = self.datapaths.get(path[i])
            if dp is None:
                continue
            out_port = last_port if i == len(path) - 1 else self.adj[path[i]][path[i + 1]]
            parser = dp.ofproto_parser
            match = parser.OFPMatch(eth_src=src_mac, eth_dst=dst_mac)
            self._add_flow(dp, 10, match, [parser.OFPActionOutput(out_port)], FLOW_COOKIE)

    def _flood_edge_ports(self, src_dpid, in_port, data):
        for sw in get_switch(self, None):
            dp = self.datapaths.get(sw.dp.id)
            if dp is None:
                continue
            skip = self.inter_ports.get(sw.dp.id, set())
            for p in sw.ports:
                if p.port_no >= OFP_PORT_MAX or p.port_no in skip:
                    continue
                if sw.dp.id == src_dpid and p.port_no == in_port:
                    continue
                self._packet_out(dp, dp.ofproto.OFPP_CONTROLLER, p.port_no, data)

    # ------------------------------------------------------------ helpers
    def _add_flow(self, dp, priority, match, actions, cookie):
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(parser.OFPFlowMod(datapath=dp, cookie=cookie, priority=priority,
                                      match=match, instructions=inst))

    def _clear_flows(self):
        for dp in list(self.datapaths.values()):
            ofp = dp.ofproto
            parser = dp.ofproto_parser
            dp.send_msg(parser.OFPFlowMod(
                datapath=dp, cookie=FLOW_COOKIE, cookie_mask=0xffffffffffffffff,
                table_id=ofp.OFPTT_ALL, command=ofp.OFPFC_DELETE,
                out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
                match=parser.OFPMatch()))
        self.active_paths.clear()

    def _packet_out(self, dp, in_port, out_port, data):
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        dp.send_msg(parser.OFPPacketOut(
            datapath=dp, buffer_id=ofp.OFP_NO_BUFFER, in_port=in_port,
            actions=[parser.OFPActionOutput(out_port)], data=data))


class DiagRest(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(DiagRest, self).__init__(req, link, data, **config)
        self.app = data['diag_app']

    @route('diag_paths', '/v1.0/diag/paths', methods=['GET'])
    def list_paths(self, req, **kwargs):
        out = []
        for (src, dst), path in sorted(self.app.active_paths.items()):
            out.append({'src_mac': src, 'dst_mac': dst,
                        'src_ip': self.app.host_ip.get(src),
                        'dst_ip': self.app.host_ip.get(dst),
                        'path': ['s%d' % d for d in path],
                        'path_dpids': path})
        return Response(content_type='application/json',
                        body=json.dumps(out, indent=2).encode('utf-8'))
