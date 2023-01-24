import json
from yaramo.model import Topology, Node, Edge, SignalDirection


class Exporter:
    def __init__(self, topology: Topology) -> None:
        self.topology = topology

    def export_topology(self) -> dict:

        edges = {
            edge.uuid: {
                "anschlussA": None,
                "anschlussB": None,
                "id": edge.uuid,
                "knotenA": None,
                "knotenB": None,
                "laenge": int(edge.length) if edge.length else None,
            }
            for edge in self.topology.edges.values()
        }

        signals = {
            signal.uuid: {
                "art": str(signal.kind),
                "edge": signal.edge.uuid,
                "funktion": str(signal.function),
                "id": signal.uuid,
                "name": signal.name or "",
                "offset": signal.distance_edge,
                "rastaId": None,
                "wirkrichtung": "normal"
                if signal.direction == SignalDirection.IN
                else "reverse",
            }
            for signal in self.topology.signals.values()
        }

        points = {
            point.uuid: {
                "id": point.uuid,
                "name": point.name or "",
                "node": "",
                "rastaId": None,
            }
            for point in self.topology.nodes.values()
            if None
            not in [
                point.connected_on_head,
                point.connected_on_left,
                point.connected_on_right,
            ]
        }

        # Find "node" ids by concatenating edge ids for each node that connects them
        edges_per_node = self.__group_edges_per_node(self.topology.edges.values())
        edge_combinations = []
        for _edges in edges_per_node.values():
            if len(_edges) > 1:
                for i, _ in enumerate(_edges):
                    for j in range(i + 1, len(_edges)):
                        edge_combinations.append(f"{_edges[i].uuid}.{_edges[j].uuid}")
        nodes = {
            edge_combination: {"id": edge_combination}
            for edge_combination in edge_combinations
        }

        # Add extra axlecountingheads for edges with nodes that don't have further connections
        axleCountingHeads = {}
        for _edges in edges_per_node.values():
            if len(_edges) > 2:
                continue
            for _edge in _edges:
                tmp = Node()
                head = {
                    "edge": _edge.uuid,
                    "id": tmp.uuid,
                    "limits": [],
                    "name": "",
                    "position": 0.1,
                }
                axleCountingHeads[tmp.uuid] = head

        return {
            "edges": edges,
            "nodes": nodes,
            "points": points,
            "signals": signals,
            "axleCountingHeads": axleCountingHeads,
            "drivewaySections": {},
            "trackVacancySections": {},
        }

    def export_placement(self) -> dict:
        self.__ensure_nodes_orientations()

        points = {}
        visited_edges = {
            f"{edge.node_a.uuid}.{edge.node_b.uuid}": edge.uuid
            for edge in self.topology.edges.values()
        }
        visited_edges = {
            **visited_edges,
            **{
                f"{edge.node_b.uuid}.{edge.node_a.uuid}": edge.uuid
                for edge in self.topology.edges.values()
            },
        }
        get_edge_from_nodes = lambda a, b: visited_edges.get(f"{a}.{b}")
        for node in self.topology.nodes.values():
            if not self.__is_point(node):
                continue
            diverting = (
                get_edge_from_nodes(node.uuid, node.connected_on_left)
                if node.__dict__.get("orientation") == "Left"
                else get_edge_from_nodes(node.uuid, node.connected_on_right)
            )
            through = (
                get_edge_from_nodes(node.uuid, node.connected_on_right)
                if node.__dict__.get("orientation") == "Left"
                else get_edge_from_nodes(node.uuid, node.connected_on_left)
            )

            point = {
                "toe": get_edge_from_nodes(node.uuid, node.connected_on_head.uuid)
                if node.connected_on_head
                else "",
                "diverting": diverting,
                "through": through,
                "divertsInDirection": node.__dict__.get("divertsInDirection"),
                "orientation": node.__dict__.get("orientation"),
            }
            points[node.uuid] = point

        edges = {}
        for edge in self.topology.edges.values():
            items = [edge.node_a.uuid] if self.__is_point(edge.node_a) else []
            items += (
                [
                    signal.uuid
                    for signal in sorted(edge.signals, key=lambda x: x.distance_edge)
                ]
                if len(edge.signals) > 0
                else []
            )
            items += [edge.node_b.uuid] if self.__is_point(edge.node_b) else []
            edges[edge.uuid] = {"items": items, "orientation": "normal"}

        return {"points": points, "edges": edges}

    def __ensure_nodes_orientations(self):
        # find nodes that mark topology ends
        visited_nodes = self.__group_edges_per_node(self.topology.edges.values())
        visited_nodes_length = {
            node: len(items) for node, items in visited_nodes.items()
        }

        # Use one of the ends as start for a graph traversal
        start_node = self.topology.nodes.get(
            min(visited_nodes_length, key=visited_nodes_length.get)
        )
        start_diversion_direction = (
            "normal"
            if start_node.connected_nodes[0].connected_on_head == start_node
            else "reverse"
        )
        self.__set_node_orientation(
            start_node.connected_nodes[0], "Left", start_diversion_direction
        )

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

    def __set_node_orientation(
        self, node: Node, orientation: str, divertsInDirection: str
    ):
        if orientation:
            setattr(node, "orientation", orientation)
        if divertsInDirection:
            setattr(node, "divertsInDirection", divertsInDirection)

        # Try to go in a straight line first, to ensure an orientation for all those nodes,
        # which can than be used to find an orientation for all the diverting ones.
        next_node_order = [node.connected_on_head] if node.connected_on_head else []
        if orientation == "Left":
            if node.connected_on_right:
                next_node_order.append(node.connected_on_right)
            if node.connected_on_left:
                next_node_order.append(node.connected_on_left)
        else:
            if node.connected_on_left:
                next_node_order.append(node.connected_on_left)
            if node.connected_on_right:
                next_node_order.append(node.connected_on_right)

        for connected_node in next_node_order:
            # Set divertionDirection
            if not connected_node.__dict__.get("divertsInDirection"):
                next_node_diverting_direction = divertsInDirection

                if (
                    connected_node.connected_on_head == node
                    and node.connected_on_head == connected_node
                ) or (
                    connected_node.connected_on_head != node
                    and node.connected_on_head != connected_node
                ):
                    next_node_diverting_direction = (
                        "reverse" if divertsInDirection == "normal" else "normal"
                    )

            # Do not overwrite orientation
            if (
                not connected_node.__dict__.get("orientation")
            ):
                next_node_orientation = None

                if(connected_node.connected_on_head == node):
                    next_node_orientation = self.__get_node_orientation_based_on_neighbours(connected_node, divertsInDirection)

                if next_node_orientation == None:
                    if (
                        connected_node.connected_on_left == node
                        and node.connected_on_left == connected_node
                    ):
                        next_node_orientation = "Left"
                    elif (
                        connected_node.connected_on_right == node
                        and node.connected_on_right == connected_node
                    ):
                        next_node_orientation = "Right"
                    elif (
                        connected_node.connected_on_left == node
                        and node.connected_on_right == connected_node
                    ):
                        next_node_orientation = "Right"
                    elif (
                        connected_node.connected_on_right == node
                        and node.connected_on_left == connected_node
                    ):
                        next_node_orientation = "Left"
                    else:
                        # Default
                        next_node_orientation = "Left" if orientation == "normal" else "Right"

                self.__set_node_orientation(
                    connected_node, next_node_orientation, next_node_diverting_direction
                )

    def __is_point(self, node: Node):
        return len(node.connected_nodes) == 3

    def __get_node_orientation_based_on_neighbours(self, node: Node, divertsInDirection: str):
        head = node.connected_on_head
        head_connection = None if not head else self.__get_connected_on_neighbour_orientation(node, head)
        left = node.connected_on_left 
        left_connection = None if not left else self.__get_connected_on_neighbour_orientation(node, left)
        right = node.connected_on_right
        right_connection = None if not right else self.__get_connected_on_neighbour_orientation(node, right)

        if head_connection == 'Head':
            if left_connection == 'Left' or 'Right':
                return left_connection
            if right_connection == 'Left' or 'Right':
                return right_connection
        else:
            if right_connection == 'Right':
                return 'Right' if right.__dict__.get('orienation') == 'Right' else 'Left'
            if left_connection == 'Left':
                return 'Left' if left.__dict__.get('orienation') == 'Left' else 'Right'
        return None

    def __get_connected_on_neighbour_orientation(self, node: Node, neighbour: Node):
        if neighbour.connected_on_head == node:
            return 'Head'
        if neighbour.connected_on_right == node:
            return 'Right'
        if neighbour.connected_on_left == node:
            return 'Left'
        return None
