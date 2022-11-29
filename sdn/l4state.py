from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet.ether_types import ETH_TYPE_IP

class L4State14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L4State14, self).__init__(*args, **kwargs)
        self.ht = set()

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
        import pdb; pdb.set_trace()
        #
        # write your code here
        tcp_header = pkt.get_protocol(tcp.tcp)
        ip_header = pkt.get_protocol(ipv4.ipv4)
        is_tcp_over_ipv4 = tcp_header is not None and ip_header is not None
        if not is_tcp_over_ipv4:
            if in_port == 1:
                acts = [psr.OFPActionOutput(2)]
            else:
                acts = [psr.OFPActionOutput(1)]
        else:
            # Find SYN FIN RST flags
            SYN_set = tcp_header.bits & 0x02
            FIN_set = tcp_header.bits & 0x01
            RST_set = tcp_header.bits & 0x04
            # ports and ips
            sport = tcp_header.src_port
            dport = tcp_header.dst_port
            src_ip = ip_header.src
            dst_ip = ip_header.dst
            flow_key = (src_ip, dst_ip, sport, dport)
            flow_key_reverse = (dst_ip, src_ip, dport, sport)
            if dport != ofp.OFPP_FLOOD:
                if in_port == 1:
                    if flow_key not in self.ht:
                        self.ht.add(flow_key)
                    # check flags
                    if (SYN_set and FIN_set) or (SYN_set and RST_set) or (not (SYN_set or FIN_set or RST_set)):
                        acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]
                    else:
                        acts = [psr.OFPActionOutput(2)]
                        mtc = psr.OFPMatch(in_port=1, eth_type=eth.ethertype,
                                        ipv4_src=src_ip, ipv4_dst=dst_ip,
                                        ip_proto=in_proto.IPPROTO_TCP,
                                        tcp_src=sport, tcp_dst=dport)
                        self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
                        if msg.buffer_id != ofp.OFP_NO_BUFFER:
                            return 
                else:
                    if flow_key_reverse in self.ht:
                        acts = [psr.OFPActionOutput(1)]
                        mtc = psr.OFPMatch(in_port=2, eth_type=eth.ethertype,
                                             ipv4_src=src_ip, ipv4_dst=dst_ip,
                                                ip_proto=in_proto.IPPROTO_TCP,
                                                tcp_src=sport, tcp_dst=dport)
                        self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
                        if msg.buffer_id != ofp.OFP_NO_BUFFER:
                            return  
                    else:
                        acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]  
        #
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)
