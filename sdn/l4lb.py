# from ryu.base import app_manager
# from ryu.controller import ofp_event
# from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
# from ryu.controller.handler import set_ev_cls
# from ryu.ofproto import ofproto_v1_4
# from ryu.lib.packet import packet
# from ryu.lib.packet import ethernet
# from ryu.lib.packet import in_proto
# from ryu.lib.packet import arp
# from ryu.lib.packet import ipv4
# from ryu.lib.packet import tcp
# from ryu.lib.packet.tcp import TCP_SYN
# from ryu.lib.packet.tcp import TCP_FIN
# from ryu.lib.packet.tcp import TCP_RST
# from ryu.lib.packet.tcp import TCP_ACK
# from ryu.lib.packet.ether_types import ETH_TYPE_IP, ETH_TYPE_ARP

# class L4Lb(app_manager.RyuApp):
#     OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

#     def __init__(self, *args, **kwargs):
#         super(L4Lb, self).__init__(*args, **kwargs)
#         self.ht = {} # {(<sip><vip><sport><dport>): out_port, ...}
#         self.vip = '10.0.0.10'
#         self.dips = ('10.0.0.2', '10.0.0.3')
#         self.dmacs = ('00:00:00:00:00:02', '00:00:00:00:00:03')
#         #
#         # write your code here, if needed
#         #
#         self.next_server = 2
#         self.client = '10.0.0.1'
#         self.cmac = '00:00:00:00:00:01'

#     def _send_packet(self, datapath, port, pkt):
#         ofproto = datapath.ofproto
#         parser = datapath.ofproto_parser
#         pkt.serialize()
#         data = pkt.data
#         actions = [parser.OFPActionOutput(port=port)]
#         out = parser.OFPPacketOut(datapath=datapath,
#                                   buffer_id=ofproto.OFP_NO_BUFFER,
#                                   in_port=ofproto.OFPP_CONTROLLER,
#                                   actions=actions,
#                                   data=data)
#         return out

#     @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
#     def features_handler(self, ev):
#         dp = ev.msg.datapath
#         ofp, psr = (dp.ofproto, dp.ofproto_parser)
#         acts = [psr.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
#         self.add_flow(dp, 0, psr.OFPMatch(), acts)

#     def add_flow(self, dp, prio, match, acts, buffer_id=None):
#         ofp, psr = (dp.ofproto, dp.ofproto_parser)
#         bid = buffer_id if buffer_id is not None else ofp.OFP_NO_BUFFER
#         ins = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acts)]
#         mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
#                                 match=match, instructions=ins)
#         dp.send_msg(mod)

#     @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
#     def _packet_in_handler(self, ev):
#         msg = ev.msg
#         in_port, pkt = (msg.match['in_port'], packet.Packet(msg.data))
#         dp = msg.datapath
#         ofp, psr, did = (dp.ofproto, dp.ofproto_parser, format(dp.id, '016d'))
#         eth = pkt.get_protocols(ethernet.ethernet)[0]
#         #
#         # write your code here, if needed
#         #
#         iph = pkt.get_protocols(ipv4.ipv4)
#         tcph = pkt.get_protocols(tcp.tcp)
#         arph = pkt.get_protocols(arp.arp)
#         #
#         # write your code here
#         #
#         if len(iph) > 0 and len(tcph) > 0:
#             # Find SYN FIN RST flags
#             sport = tcph[0].src_port
#             dport = tcph[0].dst_port
#             sip = iph[0].src
#             dip = iph[0].dst
#             flow_key = (sip, dip, sport, dport)
#             if dport != ofp.OFPP_FLOOD:
#                 if in_port == 1:
#                     trans_dip = self.dips[self.next_server - 2]
#                     flow_key = (sip, self.vip, sport, dport)
#                     acts = []
#                     if flow_key not in self.ht:
#                         self.ht[flow_key] = self.next_server, self.dips[self.next_server - 2], self.dmacs[self.next_server - 2]
#                         self.next_server = 3 if self.next_server == 2 else 2
#                     server, ht_dip, ht_dmac = self.ht[flow_key]
#                     if self.next_server == 2:
#                         acts = [psr.OFPActionOutput(2), psr.OFPActionSetField(ipv4_dst=self.dips[0]), psr.OFPActionSetField(eth_dst=self.dmacs[0])]
#                         self.next_server = 3
#                     else:
#                         acts = [psr.OFPActionOutput(3), psr.OFPActionSetField(ipv4_dst=self.dips[1]), psr.OFPActionSetField(eth_dst=self.dmacs[1])]
#                         self.next_server = 2
#                     acts = [psr.OFPActionOutput(server), psr.OFPActionSetField(ipv4_dst=ht_dip), psr.OFPActionSetField(eth_dst=ht_dmac)]
#                     mtc = psr.OFPMatch(in_port=1, eth_type=eth.ethertype,
#                                     ipv4_src=sip, ipv4_dst=ht_dip)
#                     self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
#                     if msg.buffer_id != ofp.OFP_NO_BUFFER:
#                         return
#                 else:
#                     flow_key_reverse = (dip, self.vip, dport, sport)
#                     if flow_key_reverse in self.ht:
#                         out_port = self.ht[flow_key_reverse]
#                         acts = [psr.OFPActionOutput(1), psr.OFPActionSetField(ipv4_src=self.vip)]
#                         mtc = psr.OFPMatch(in_port=in_port, eth_type=eth.ethertype,
#                                         ipv4_src=sip, ipv4_dst=dip)
#                         self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
#                     else:
#                         acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]
#                     if msg.buffer_id != ofp.OFP_NO_BUFFER:
#                         return 
#         elif len(arph) > 0:
#             # arp
#             if in_port == 1:
#                 pkt_json = pkt.to_jsondict()
#                 for proto_pkt in pkt_json['Packet']['protocols']:
#                     if 'arp' in proto_pkt:
#                         proto_pkt['arp']['src_ip'] = self.vip
#                         proto_pkt['arp']['dst_ip'] = self.client
#                         proto_pkt['arp']['src_mac'] = self.dmacs[self.next_server - 2]
#                         proto_pkt['arp']['dst_mac'] = self.cmac 
#                         self.next_server = 2 if self.next_server == 3 else 3
#                 pkt = packet.Packet.from_jsondict(pkt_json['Packet'])
#                 out = self._send_packet(dp, self.next_server, pkt)
#                 dp.send_msg(out)
#                 self.next_server = 3 if self.next_server == 2 else 2
#             else:
#                 pkt_json = pkt.to_jsondict()
#                 for proto_pkt in pkt_json['Packet']['protocols']:
#                     if 'arp' in proto_pkt:
#                         proto_pkt['arp']['dst_ip'] = proto_pkt['arp']['src_ip']
#                         proto_pkt['arp']['src_ip'] = self.client
#                         proto_pkt['arp']['dst_mac'] = proto_pkt['arp']['src_mac']  
#                         proto_pkt['arp']['src_mac'] = self.cmac
#                         self.next_server = 2 if self.next_server == 3 else 3
#                 pkt = packet.Packet.from_jsondict(pkt_json['Packet'])
#                 out = self._send_packet(dp, 1, pkt)
#                 dp.send_msg(out)
#             return
#         else:
#             # print(in_port, eth.src)
#             if in_port == 1:
#                 acts = [psr.OFPActionOutput(self.next_server)]
#                 self.next_server = 3 if self.next_server == 2 else 2
#             else:
#                 acts = [psr.OFPActionOutput(in_port)]
#         data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
#         out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
#                                in_port=in_port, actions=acts, data=data)
#         dp.send_msg(out)


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import in_proto
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet.tcp import TCP_SYN
from ryu.lib.packet.tcp import TCP_FIN
from ryu.lib.packet.tcp import TCP_RST
from ryu.lib.packet.tcp import TCP_ACK
from ryu.lib.packet.ether_types import ETH_TYPE_IP, ETH_TYPE_ARP

class L4Lb(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L4Lb, self).__init__(*args, **kwargs)
        self.ht = {} # {(<sip><vip><sport><dport>): out_port, ...}
        self.vip = '10.0.0.10'
        self.dips = ('10.0.0.2', '10.0.0.3')
        self.dmacs = ('00:00:00:00:00:02', '00:00:00:00:00:03')
        #
        # write your code here, if needed
        #
        self.cmac = '00:00:00:00:00:01'
        self.next_server = 2

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        return out

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        acts = [psr.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, psr.OFPMatch(), acts)

    def add_flow(self, dp, prio, match, acts, buffer_id=None):
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        bid = buffer_id if buffer_id is not None else ofp.OFP_NO_BUFFER
        ins = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acts)]
        mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
                                match=match, instructions=ins)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        in_port, pkt = (msg.match['in_port'], packet.Packet(msg.data))
        dp = msg.datapath
        ofp, psr, did = (dp.ofproto, dp.ofproto_parser, format(dp.id, '016d'))
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        #
        # write your code here, if needed
        #
        iph = pkt.get_protocols(ipv4.ipv4)
        tcph = pkt.get_protocols(tcp.tcp)
        #
        # write your code here
        #
        if eth.ethertype == ETH_TYPE_IP:
            src_ip = iph[0].src 
            dst_ip = iph[0].dst
            src_port = tcph[0].src_port
            dst_port = tcph[0].dst_port
            if in_port == 1:
                flow = (src_ip, dst_ip, src_port, dst_port)
                if flow not in self.ht:
                    self.ht[flow] = self.next_server, self.dips[self.next_server - 2], self.dmacs[self.next_server - 2]
                    self.next_server = 5 - self.next_server
                out_port, ht_dst_ip, ht_dmac = self.ht[flow]
                acts = [psr.OFPActionOutput(out_port), psr.OFPActionSetField(ipv4_dst=ht_dst_ip), psr.OFPActionSetField(eth_dst=ht_dmac)]
                mtc = psr.OFPMatch(in_port=in_port, eth_type=ETH_TYPE_IP, ipv4_src=src_ip, ipv4_dst=ht_dst_ip, ip_proto=in_proto.IPPROTO_TCP, tcp_src=src_port, tcp_dst=dst_port)
            else:
                out_port = 1
                acts = [psr.OFPActionOutput(out_port), psr.OFPActionSetField(ipv4_src=self.vip)]
                mtc = psr.OFPMatch(in_port=in_port, eth_type=ETH_TYPE_IP, ipv4_src=src_ip, ipv4_dst=dst_ip, ip_proto=in_proto.IPPROTO_TCP, tcp_src=src_port, tcp_dst=dst_port)
            self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
            if msg.buffer_id == ofp.OFP_NO_BUFFER:
                return
        elif eth.ethertype == ETH_TYPE_ARP:
            arph = pkt.get_protocols(arp.arp)[0]
            src_ip = arph.src_ip
            dst_ip = arph.dst_ip
            smac = arph.src_mac
            if in_port == 1:
                dmac = self.dmacs[self.next_server - 2]
                self.next_server = 5 - self.next_server 
            else:
                dmac = self.cmac
            eh = ethernet.ethernet(dst=smac, src=dmac, ethertype=ETH_TYPE_ARP)
            ah = arp.arp(arp.ARP_REQUEST, src_mac=dmac, src_ip=dst_ip, dst_mac=smac, dst_ip=src_ip)
            pk = packet.Packet()
            pk.add_protocol(eh)
            pk.add_protocol(ah)
            dp.send_msg(self._send_packet(dp, in_port, pk))
            return 
        else:
            out_port = self.next_server + 2 if in_port == 1 else 1
            self.next_server = 5 - self.next_server
            acts = [psr.OFPActionOutput(out_port)]
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)

