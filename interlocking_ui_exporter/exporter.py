import json
from yaramo.model import Topology, Node


class Exporter:
    def __init__(self, topology: Topology) -> None:
        self.topology = topology

    def export_topology(self) -> str:
        pass

    def export_placement(self) -> str:
        # find edge that marks topology end
        visited_nodes = {}
        visited_edges = {}
        for edge in self.topology.edges.values():
            if visited_nodes.get(edge.node_a.uuid):
                visited_nodes[edge.node_a.uuid] += 1
            else:
                visited_nodes[edge.node_a.uuid] = 1

            if visited_nodes.get(edge.node_b.uuid):
                visited_nodes[edge.node_b.uuid] += 1
            else:
                visited_nodes[edge.node_b.uuid] = 1

            visited_edges[f"{edge.node_a.uuid}.{edge.node_b.uuid}"] = edge
            visited_edges[f"{edge.node_b.uuid}.{edge.node_a.uuid}"] = edge

        start_node = self.topology.nodes.get(min(visited_nodes, key=visited_nodes.get))
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
