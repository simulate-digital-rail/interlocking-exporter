import asyncio
import websockets
from http.client import OK
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import json
from cli_importer.cli import CLI
from interlocking_ui_exporter.exporter import Exporter
from yaramo.model import (
    Topology,
    Node,
    Edge,
    Signal,
    SignalDirection,
    SignalFunction,
    SignalKind,
)


class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Content-Type', 'application/json')
        if self.path == "/topology":
            self.wfile.write(topology_json.encode('utf-8'))
        if self.path == "/placement":
            self.wfile.write(placement_json.encode('utf-8'))
        return


#      ----
#     /    \
# a--b-----f--g

topology_json = None
placement_json = None


if __name__ == "__main__":

    topology = Topology()
    node_a = Node(name="a", uuid="a")
    node_b = Node(name="b", uuid="b")
    node_f = Node(name="f", uuid="f")
    node_g = Node(name="g", uuid="g")

    node_a.set_connection_head(node_b)
    node_b.set_connection_head(node_a)
    node_b.set_connection_right(node_f)
    node_b.set_connection_left(node_f)
    node_f.set_connection_left(node_b)
    node_f.set_connection_head(node_g)
    node_f.set_connection_right(node_b)
    node_g.set_connection_head(node_f)

    edge_1 = Edge(node_a, node_b, uuid="a-b", length=100)
    edge_2 = Edge(node_b, node_f, uuid="b-f-up", length=101)
    edge_3 = Edge(node_b, node_f, uuid="b-f-straight", length=102)
    edge_4 = Edge(node_f, node_g, uuid="f-g", length=103)
    signal_A = Signal(
        edge_1,
        0.2,
        SignalDirection.IN,
        SignalFunction.Block_Signal,
        SignalKind.Hauptsignal,
        uuid="A",
    )
    signal_T1 = Signal(
        edge_2,
        0.2,
        SignalDirection.IN,
        SignalFunction.Block_Signal,
        SignalKind.Hauptsignal,
        uuid="T1",
    )
    signal_T2 = Signal(
        edge_3,
        0.2,
        SignalDirection.IN,
        SignalFunction.Block_Signal,
        SignalKind.Hauptsignal,
        uuid="T2",
    )
    signal_P = Signal(
        edge_4,
        0.9,
        SignalDirection.IN,
        SignalFunction.Block_Signal,
        SignalKind.Hauptsignal,
        uuid="P",
    )
    signal_N = Signal(
        edge_1,
        0.1,
        SignalDirection.GEGEN,
        SignalFunction.Block_Signal,
        SignalKind.Hauptsignal,
        uuid="N",
    )
    signal_S = Signal(
        edge_4,
        0.8,
        SignalDirection.GEGEN,
        SignalFunction.Block_Signal,
        SignalKind.Hauptsignal,
        uuid="S",
    )

    edge_1.signals.append(signal_A)
    edge_1.signals.append(signal_N)
    edge_4.signals.append(signal_P)
    edge_4.signals.append(signal_S)
    edge_2.signals.append(signal_T1)
    edge_3.signals.append(signal_T2)

    topology.nodes = {
        node.uuid: node
        for node in [
            node_a,
            node_b,
            node_f,
            node_g,
        ]
    }
    topology.edges = {edge.uuid: edge for edge in [edge_1, edge_2, edge_3, edge_4]}
    topology.signals = {
        signal.uuid: signal
        for signal in [signal_A, signal_P, signal_N, signal_S, signal_T1, signal_T2]
    }

    exporter = Exporter(topology)
    topology = exporter.export_topology()
    placement = exporter.export_placement()

    # async def handler(websocket, path):
    #     if path == '/topology':
    #         data = await websocket.recv()
    #         reply = json.dumps(topology)
    #     if path == '/placement':
    #         data = await websocket.recv()
    #         reply = json.dumps(placement)
    #     else:
    #         reply = f'Wrong path!'
    #     await websocket.send(reply)
    class HTTPRequestHandler(BaseHTTPRequestHandler):

        def do_HEAD(self):
            return
            
        def do_GET(self):
            self.respond()
            
        def do_POST(self):
            self.respond()
            
        def handle_http(self, status, content_type):
            response = bytes()
            if self.path == '/topology':
                response = json.dumps(topology).encode('utf-8')
            if self.path == '/placement':
                response = json.dumps(placement).encode('utf-8')
            
            self.send_response(status)
            self.send_header('Content-type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return response
    
        def respond(self):
            content = self.handle_http(200, 'application/json')
            self.wfile.write(content)
        
    url = 'localhost'
    port = 8888
    httpd = HTTPServer((url, port), HTTPRequestHandler)
    try:
        print('Starting server ...')
        httpd.serve_forever()
    except Exception:
        pass
    finally:
        httpd.shutdown()

