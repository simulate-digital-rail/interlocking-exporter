from cli_importer.cli import CLI
from interlocking_ui_exporter.exporter import Exporter
from yaramo.model import Topology, Node, Edge

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
    edge_2 = Edge(node_b, node_b)
    edge_3 = Edge(node_b, node_d)
    edge_4 = Edge(node_c, node_b)
    edge_5 = Edge(node_c, node_g)
    edge_6 = Edge(node_d, node_b)
    edge_7 = Edge(node_d, node_e)
    edge_8 = Edge(node_d, node_f)
    edge_9 = Edge(node_e, node_d)
    edge_10 = Edge(node_f, node_g)
    edge_11 = Edge(node_f, node_d)
    edge_12 = Edge(node_d, node_c)
    edge_13 = Edge(node_d, node_f)
    edge_14 = Edge(node_d, node_e)
    edge_15 = Edge(node_e, node_g)

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
