from cli_importer.cli import CLI
from interlocking_ui_exporter.exporter import Exporter
from yaramo.model import Topology, Node, Edge, Signal, SignalDirection, SignalFunction, SignalKind

#   e--d--f  
#     /   \
# a--b--c--g--e


if __name__ == '__main__':
    # _cli = CLI()
    # _cli.run()
    topology = Topology()
    node_a = Node(name='a')
    node_b = Node(name='b')
    node_c = Node(name='c')
    node_d = Node(name='d')
    node_e = Node(name='e')
    node_f = Node(name='f')
    node_g = Node(name='g')
    node_h = Node(name='h')
    node_i = Node(name='i')

    node_a.set_connection_head(node_b)
    node_b.set_connection_head(node_a)
    node_b.set_connection_left(node_d)
    node_b.set_connection_right(node_c)
    node_c.set_connection_left(node_b)
    node_c.set_connection_head(node_g)
    node_d.set_connection_left(node_b)
    node_d.set_connection_right(node_e)
    node_d.set_connection_head(node_f)
    node_e.set_connection_head(node_d)
    node_f.set_connection_right(node_g)
    node_f.set_connection_head(node_d)
    node_d.set_connection_left(node_c)
    node_d.set_connection_right(node_f)
    node_d.set_connection_head(node_e)
    node_e.set_connection_head(node_g)

    edge_1 = Edge(node_a, node_b)
    signal_1 = Signal(edge_1, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_12 = Signal(edge_1, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_1.signals = [signal_1, signal_12] 
    edge_2 = Edge(node_b, node_c)
    signal_2 = Signal(edge_2, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_22 = Signal(edge_2, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_2.signals = [signal_2, signal_22] 
    edge_3 = Edge(node_b, node_d)
    signal_3 = Signal(edge_3, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_32 = Signal(edge_3, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_3.signals = [signal_3, signal_32] 
    edge_4 = Edge(node_c, node_b)
    signal_4 = Signal(edge_4, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_42 = Signal(edge_4, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_4.signals = [signal_4, signal_42] 
    edge_5 = Edge(node_c, node_g)
    signal_5 = Signal(edge_5, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_52 = Signal(edge_5, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_5.signals = [signal_5, signal_52] 
    edge_6 = Edge(node_d, node_b)
    signal_6 = Signal(edge_6, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_62 = Signal(edge_6, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_6.signals = [signal_6, signal_62] 
    edge_7 = Edge(node_d, node_e)
    signal_7 = Signal(edge_7, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_72 = Signal(edge_7, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_7.signals = [signal_7, signal_72] 
    edge_8 = Edge(node_d, node_f)
    signal_8 = Signal(edge_8, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_82 = Signal(edge_8, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_8.signals = [signal_8, signal_82] 
    edge_9 = Edge(node_e, node_d)
    signal_9 = Signal(edge_9, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal_92 = Signal(edge_9, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_9.signals = [signal_9, signal_92] 
    edge_10 = Edge(node_f, node_g)
    signal10 = Signal(edge_10, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal102 = Signal(edge_10, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_10.signals = [signal10, signal102] 
    edge_11 = Edge(node_f, node_d)
    signal11 = Signal(edge_11, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal112 = Signal(edge_11, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_11.signals = [signal11, signal112] 
    edge_12 = Edge(node_d, node_c)
    signal12 = Signal(edge_12, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal122 = Signal(edge_12, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_12.signals = [signal12, signal122] 
    edge_13 = Edge(node_d, node_f)
    signal13 = Signal(edge_13, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal132 = Signal(edge_13, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_13.signals = [signal13, signal132] 
    edge_14 = Edge(node_d, node_e)
    signal14 = Signal(edge_14, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal142 = Signal(edge_14, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_14.signals = [signal14, signal142] 
    edge_15 = Edge(node_e, node_g)
    signal15 = Signal(edge_15, 0.2, SignalDirection.IN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    signal152 = Signal(edge_15, 0.9, SignalDirection.GEGEN, SignalFunction.Block_Signal, SignalKind.Hauptsignal)
    edge_15.signals = [signal15, signal152] 

    topology.nodes = {node.uuid: node for node in [
        node_a,
        node_b,
        node_c,
        node_d,
        node_e,
        node_f,
        node_g,
        node_h,
        node_i
    ]}
    topology.edges = {edge.uuid: edge for edge in [
        edge_1,
        edge_2,
        edge_3,
        edge_4,
        edge_5,
        edge_6,
        edge_7,
        edge_8,
        edge_9,
        edge_10,
        edge_11,
        edge_12,
        edge_13,
        edge_14,
        edge_15
    ]}
    
    exporter = Exporter(topology)
    print(exporter.export_placement())
