import json
from yaramo.model import Topology, Node, Edge, SignalDirection


class Exporter:
    def __init__(self, topology: Topology) -> None:
        self.topology = topology
        self.__ensure_nodes_orientations()

    def export_topology(self) -> dict:
        """Export the topology as a dict containing attributes needed by the Interlocking-UI.
        This can optinally add extra AxleCountingHeads on edges that contain no further items."""
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
                "rastaId": 1234567890,
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

        # Find node ids by concatenating edge ids for each node that connects them
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

        axleCountingHeads = {}

        return {
            "edges": edges,
            "nodes": nodes,
            "points": points,
            "signals": signals,
            "axleCountingHeads": axleCountingHeads,
            "routes": {},
            "trackVacancySections": {},
        }

    def export_placement(self) -> dict:
        """Export the placement of points and edges as a dict containing attributes needed by the Interlocking-UI"""
        points = {}
        visited_edges = self.__map_connected_nodes_to_edge(self.topology.edges.values())
        get_edges_from_nodes = lambda a, b: visited_edges.get((a, b))

        # Determine for each point the connected edges and to which branch the connect to
        for node in self.topology.nodes.values():
            if not self.__is_point(node):
                continue

            edges_right = get_edges_from_nodes(node, node.connected_on_right)
            edges_left = get_edges_from_nodes(node, node.connected_on_left)

            # We found two points being connected by two edges
            if edges_right and edges_left and edges_right == edges_left:
                # We already connected them once
                other_nodes_right_edge = None
                if node.connected_on_left.__dict__.get("right_edge"):
                    # Assign edges to match previous assignment
                    other_nodes_right_edge = node.connected_on_left.__dict__.get(
                        "right_edge"
                    )
                    other_nodes_left_edge = (
                        edges_right[0]
                        if edges_right[0] != other_nodes_right_edge
                        else edges_right[1]
                    )

                    diverting = (
                        other_nodes_right_edge
                        if node.__dict__.get("orientation") == "Left"
                        else other_nodes_left_edge
                    )
                    through = (
                        other_nodes_right_edge
                        if node.__dict__.get("orientation") == "Right"
                        else other_nodes_left_edge
                    )
                # We see them the first time
                else:
                    # Choose randomly
                    diverting = edges_left[0]
                    through = edges_left[1]

                    node.__dict__["right_edge"] = (
                        diverting
                        if node.__dict__.get("orientation") == "Right"
                        else through
                    )
            else:
                # There are different edges and they are only singular
                diverting = (
                    get_edges_from_nodes(node, node.connected_on_left)[0]
                    if node.__dict__.get("orientation") == "Left"
                    else get_edges_from_nodes(node, node.connected_on_right)[0]
                )
                through = (
                    get_edges_from_nodes(node, node.connected_on_right)[0]
                    if node.__dict__.get("orientation") == "Left"
                    else get_edges_from_nodes(node, node.connected_on_left)[0]
                )

            point = {
                "toe": get_edges_from_nodes(node, node.connected_on_head)[0]
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
        """Make sure that each node has the attributes 'orientation' and 'divertsInDirection' set correctly"""
        # Find nodes that mark topology ends
        visited_nodes = self.__group_edges_per_node(self.topology.edges.values())
        visited_nodes_length = {
            node: len(items) for node, items in visited_nodes.items()
        }

        # Use one of the ends as start for a graph traversal
        start_node = self.topology.nodes.get(
            min(visited_nodes_length, key=visited_nodes_length.get)
        )

        # We assume that we start going from left to right
        start_diversion_direction = (
            "normal"
            if start_node.connected_nodes[0].connected_on_head == start_node
            else "reverse"
        )

        self.__set_node_orientation_and_diversion(
            start_node.connected_nodes[0], "Left", start_diversion_direction
        )

    def __group_edges_per_node(self, edges: list[Edge]) -> dict[Node, list[Edge]]:
        """For each node list the edges it is part of"""
        visited_nodes = {}
        for edge in edges:
            for node in [edge.node_a, edge.node_b]:
                uuid = node.uuid
                if visited_nodes.get(uuid):
                    visited_nodes.get(uuid).append(edge)
                else:
                    visited_nodes[uuid] = [edge]
        return visited_nodes

    def __set_node_orientation_and_diversion(
        self, node: Node, orientation: str, divertsInDirection: str
    ):
        """ "Set each the orientaiton and diversion direction for each node based on the topology"""
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
            if not connected_node.__dict__.get("orientation"):
                if connected_node.turnout_side:
                    if connected_node.turnout_side.lower() == "left":
                        next_node_orientation = "Left"
                    else:
                        next_node_orientation = "Right"
                    self.__set_node_orientation_and_diversion(
                        connected_node,
                        next_node_orientation,
                        next_node_diverting_direction,
                    )
                next_node_orientation = None

                if connected_node.connected_on_head == node:
                    next_node_orientation = (
                        self.__get_node_orientation_based_on_neighbours(connected_node)
                    )

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
                        next_node_orientation = (
                            "Left" if orientation == "normal" else "Right"
                        )

                self.__set_node_orientation_and_diversion(
                    connected_node, next_node_orientation, next_node_diverting_direction
                )

    def __is_point(self, node: Node):
        return len(node.connected_nodes) == 3

    def __get_node_orientation_based_on_neighbours(self, node: Node):
        """Try to find the node orientation based on the connection to a neighbour.
        This works for the cases of being connected head-to-head, right-to-right or left-to-left.
        For other cases we cannot give a definitive answer.
        """
        head = node.connected_on_head
        head_connection = (
            None if not head else self.__get_connection_on_neighbour_node(node, head)
        )
        left = node.connected_on_left
        left_connection = (
            None if not left else self.__get_connection_on_neighbour_node(node, left)
        )
        right = node.connected_on_right
        right_connection = (
            None if not right else self.__get_connection_on_neighbour_node(node, right)
        )

        if head_connection == "Head":
            if left_connection == "Left" or "Right":
                return left_connection
            if right_connection == "Left" or "Right":
                return right_connection
        else:
            if right_connection == "Right":
                return (
                    "Right" if right.__dict__.get("orienation") == "Right" else "Left"
                )
            if left_connection == "Left":
                return "Left" if left.__dict__.get("orienation") == "Left" else "Right"
        return None

    def __get_connection_on_neighbour_node(self, node: Node, neighbour: Node):
        """Get the branch where this node is connected to the neighbour node"""
        if neighbour.connected_on_head == node:
            return "Head"
        if neighbour.connected_on_right == node:
            return "Right"
        if neighbour.connected_on_left == node:
            return "Left"
        return None

    def __map_connected_nodes_to_edge(self, edges: list[Edge]) -> dict[str, str]:
        """Create a dict pointing from two node uuids to the edge they connect.
        Both combinations of node_a and node_b a part of the dict and point to the same edge.
        """
        visited_edges = {}
        for edge in edges:
            if visited_edges.get((edge.node_a, edge.node_b)):
                visited_edges.get((edge.node_a, edge.node_b)).append(edge.uuid)
            else:
                visited_edges[(edge.node_a, edge.node_b)] = [edge.uuid]

            if visited_edges.get((edge.node_b, edge.node_a)):
                visited_edges.get((edge.node_b, edge.node_a)).append(edge.uuid)
            else:
                visited_edges[(edge.node_b, edge.node_a)] = [edge.uuid]
        return visited_edges
