
"""
    This code has to be used in case the switch doesn't accept when the controller starts the conversations, for
       example, when using OVS-OFCTL.

    Procedure Loop:
        1 - [Once switch connects] delete all OPenFlows entries
        2 - Open .flows file
        3 - Create a FlowMod per entry in the .flows file (below)
        4 - Run tcpreplay
        5 - sleep VARIABLE
        6 - Send STAT_REQ for Flows
        7 - Receive STAT_RES
        8 - Convert STAT_RES to format of ovs-ofctl (below)
        9 - Run validate code

    Files:

      .flow
         cookie=0x1f4,table=0,tcp,nw_src=173.212.38.112,nw_dst=187.197.245.104,tp_src=6385,tp_dst=722,,send_flow_rem,idle_timeout=0,hard_timeout=0,actions=output:4
      flow-dumps
         cookie=0x0, duration=615897.181s, table=0, n_packets=2975, n_bytes=190400, in_port=97 actions=output:97

"""

from ryu import utils
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto.ofproto_v1_0_parser import OFPPhyPort


# The server ethernet port connected to the switch
SENDER_OUTPUT_INTF="eth2"
# The switch OpenFlow port_no connected to the sink server
OF_SINK_PORT=4
# Actions to be used in all flow mods
ACTIONS="output:%s" % OF_SINK_PORT
# MAX Repetitions
MAX_REP = 40
# MAX Sleeping Time
MAX_SLEEPING = 25


class TmaController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TmaController, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
            FeatureReply - For each new switch that connects, add to the
            node_list array. This array will be used for sending packetOut
            and generate topology and colors
            Args:
                ev: event triggered
        """

        self.delete_flows(ev)
        return

        sleeping = 1
        while sleeping <= MAX_SLEEPING:
            print sleeping

            reps = 1
            while reps <= MAX_REP:
                print reps
                # print 'flow-del'
                self.delete_flows(ev)
                print 'add-flow'

                print 'tcpreplay'

                print 'dump-flows'

                print 'validate'

                reps += 1

            sleeping += 1

    def delete_flows(self, node):
        """
            Remove all flows from the node
            Args:
                node: node to be removed
        """
        datapath = node.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        op = ofproto.OFPP_CONTROLLER
        actions = [datapath.ofproto_parser.OFPActionOutput(op)]
        match = parser.OFPMatch()

        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=0,
                        table_id=255, out_port=4294967295,
                        flags=0, out_group=4294967295,
                        command=ofproto.OFPFC_DELETE, priority=32768)

        datapath.send_msg(mod)
        datapath.send_barrier()
        return

    def add_flow(self, node):
        datapath = node.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parse

        with open(newfile, 'r') as infile:
            for line in infile:




    @staticmethod
    def push_flow(datapath, cookie, priority, command, match, actions, flags=1):
        """
             Send the FlowMod to datapath. Send BarrierReq after to confirm
             Args:
                 datapath: switch class
                 cookie: cookie to be used on the flow
                 priority: flow priority
                 command: action (Add, Delete, modify)
                 match: flow match
                 actions: flow action
        """
        if flags is not 0:
            flags = datapath.ofproto.OFPFF_SEND_FLOW_REM

        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=cookie,
                                out_port=datapath.ofproto.OFPP_CONTROLLER,
                                flags=flags,
                                command=command, priority=priority,
                                actions=actions)
        # DEBUG:
        # print mod

        datapath.send_msg(mod)
        datapath.send_barrier()

