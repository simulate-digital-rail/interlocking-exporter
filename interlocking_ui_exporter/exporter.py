import json
from yaramo.model import Topology, Node, Edge


class Exporter:
    def __init__(self, topology: Topology) -> None:
        self.topology = topology

    def export_topology(self) -> str:
        topology = {
            "axleCountingHeads": {},
            "drivewaySections": {},
            "edges": {},
            "nodes": {},
            "points": {},
            "signals": {},
            "trackVacancySections": {},
            "trackVacancySections": {},
        }

        edges = {edge.uuid: {
            "anschlussA": None,
			"anschlussB": None,
			"id": edge.uuid,
			"knotenA": None,
			"knotenB": None,
			"laenge": int(edge.length) if edge.length else None
        } for edge in self.topology.edges.values()}

        points = {point.uuid: {
			"id": point.uuid,
			"name": point.name,
			"node": None,
            "orientation": "FOO",
			"rastaId": None
        } for point in self.topology.points.values()}

        # Find "node" ids by concatenating edge ids for each node that connects them
        edges_per_node = self.__group_edges_per_node(self.topology.edges.values())
        edge_combinations = []
        for edges in edges_per_node.values():
            if len(edges) > 1:
                for i, _ in enumerate(edges):
                    for j in range(i+1, len(edges)):
                        edge_combinations.append(f"{edges[i].uuid}.{edges[j].uuid}")
        nodes = {edge_combination: {
			"id": edge_combination
        } for edge_combination in edge_combinations}



        return json.dumps({"edges": edges, "nodes": nodes})

    def export_placement(self) -> str:
        # find node that marks topology end
        visited_nodes = self.__group_edges_per_node(self.topology.edges.values())
        visited_nodes_length = {node: len(items) for node, items in visited_nodes.items()}
        start_node = self.topology.nodes.get(min(visited_nodes_length, key=visited_nodes_length.get))
        start_direction = "normal" if not start_node.connected_on_head else "reverse"

        self.__traverse_nodes(start_node, start_direction)

        points = {}
        for node in self.topology.nodes.values():
            point = {
                "head": node.connected_on_head.uuid if node.connected_on_head else None,
                "diverting": node.connected_on_right.uuid
                if node.connected_on_right
                else None
                if node.maximum_speed_on_left
                and node.maximum_speed_on_right
                and node.maximum_speed_on_left > node.connected_on_right
                else node.connected_on_left.uuid
                if node.connected_on_left
                else None,
                "through": node.connected_on_right.uuid
                if node.connected_on_right
                else None
                if node.maximum_speed_on_left
                and node.maximum_speed_on_right
                and node.maximum_speed_on_left > node.connected_on_right
                else node.connected_on_left.uuid
                if node.connected_on_left
                else None,
                "divertsInDirection": node.__dict__.get("direction"),
                "orientation": "Left"
                if node.__dict__.get("direction") == "normal"
                else "Right",
            }
            points[node.uuid] = point

        edges = {}
        for edge in self.topology.edges.values():
            items = [edge.node_a.uuid]
            items += [signal.uuid for signal in sorted(edge.signals, key=lambda x: x.distance_edge)] if len(edge.signals) > 0 else []
            items += [edge.node_b.uuid]
            edges[edge.uuid] = {"items": items, "orientation": "normal"}

        return json.dumps({"points": points, "edges": edges})

    def __group_edges_per_node(self, edges: list[Edge]) -> dict[Node, list[Edge]]:
        visited_nodes = {}
        for edge in edges:
            for node in [edge.node_a, edge.node_b]:
                uuid = node.uuid
                if visited_nodes.get(uuid):
                    visited_nodes.get(uuid).append(edge)
                else:
                    visited_nodes[uuid] = [edge]
        return visited_nodes

    def __traverse_nodes(self, node: Node, direction: str):
        setattr(node, "direction", direction)
        # node["direction"] = direction

        for connected_node in node.connected_nodes:
            if not connected_node.__dict__.get("direction"):
                next_node_direction = "normal"
                if (
                    connected_node.connected_on_left == node
                    or connected_node.connected_on_right == node
                ):
                    next_node_direction = (
                        "reverse" if direction == "normal" else "normal"
                    )
                if connected_node.connected_on_head == node:
                    next_node_direction = (
                        "normal" if direction == "normal" else "reverse"
                    )

                # flip direction if connected node is connected on the head of this node
                next_node_direction = (
                    "reverse" if next_node_direction == "normal" else "normal"
                )

                self.__traverse_nodes(connected_node, next_node_direction)
