import json
from yaramo.model import Topology, Node, Edge, SignalDirection


class Exporter:
    def __init__(self, topology: Topology) -> None:
        self.topology = topology
        self.__ensure_nodes_orientations()
        self.__clean_topology()

    def __clean_topology(self):
    # remove false nodes and edges

        # find nodes that mark topology ends
        visited_nodes = self.__group_edges_per_node(self.topology.edges.values())
        visited_nodes_length = {
            node: len(items) for node, items in visited_nodes.items()
        }

        visited_edges = self.__map_connected_nodes_to_edge(self.topology.edges.values())
        
        get_edge_from_nodes = lambda a, b: self.topology.edges.get(visited_edges.get(f"{a}.{b}")[0])

        # Use one of the ends as start for a graph traversal
        start_node = self.topology.nodes.get(
            min(visited_nodes_length, key=visited_nodes_length.get)
        )

        edges: dict[str, Edge] = {}
        deleted_points: dict[str, Node] = {}


        def merge_binary_connected_nodes(previous_node: Node, node: Node, current_edge: Edge | None, edges: dict[str, Edge], deleted_points: dict[str, Node]):
            edge = get_edge_from_nodes(previous_node, node)

            if edge.__dict__.get('visited'):
                return
            edge.__dict__['visited'] = True
            next_nodes = node.connected_nodes

            # We need to merge this node
            if len(next_nodes) == 2:
                next_node = next_nodes[0] if next_nodes[0] != previous_node else next_nodes[1]
                next_edge = get_edge_from_nodes(node, next_node)

                deleted_points[node.uuid] = node

                # We are already in process of merging an edge
                if current_edge is None:
                    current_edge = edge
                    
                # Assign signals of merged edge to current edge and vice versa
                for signal in sorted(next_edge.signals, key=lambda x: x.distance_edge):
                    signal.edge = edge
                    current_edge.signals.append(signal)
                
                merge_binary_connected_nodes(node, next_node, current_edge, edges, deleted_points)

            else:
                if current_edge:
                    # Save current_edge in case of an ending
                    edges[current_edge.uuid] = current_edge

                    # swap the end node of the merged edge with node
                    current_edge_start_node = current_edge.node_a if current_edge.node_b.uuid in deleted_points else current_edge.node_b
                    current_edge_end_node =  current_edge.node_b if current_edge.node_b.uuid in deleted_points else current_edge.node_a
                    if current_edge.node_a == current_edge_end_node:
                        current_edge.node_a = node
                    else:
                        current_edge.node_b = node        

                    # Connect node with the merged edge's start node
                    currently_connected_node = edge.node_a if edge.node_a != node else edge.node_b
                    if node.connected_on_head == currently_connected_node:
                        node.connected_on_head = current_edge_start_node
                    elif node.connected_on_left == currently_connected_node:
                        node.connected_on_left = current_edge_start_node
                    elif node.connected_on_right == currently_connected_node:
                        node.connected_on_right = current_edge_start_node

                    # Connect current edge's start node with node
                    if current_edge_start_node.connected_on_head == current_edge_end_node:
                        current_edge_start_node.connected_on_head = node
                    elif current_edge_start_node.connected_on_left == current_edge_end_node:
                        current_edge_start_node.connected_on_left = node
                    elif current_edge_start_node.connected_on_right == current_edge_end_node:
                        current_edge_start_node.connected_on_right = node

                else:
                    edges[edge.uuid] = edge

                # Go on with a fresh edge
                for next_node in next_nodes:
                    if next_node != previous_node:
                        merge_binary_connected_nodes(node, next_node, None, edges, deleted_points)

        merge_binary_connected_nodes(start_node, start_node.connected_nodes[0], None, edges, deleted_points)

        # Remove merged points from the topology nodes
        for deleted_point_id in deleted_points.keys():
            self.topology.nodes.pop(deleted_point_id)

        # Keep the merged edges as topology edges
        self.topology.edges = edges

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

        points = {}
        visited_edges = self.__map_connected_nodes_to_edge(self.topology.edges.values())

        get_edges_from_nodes = lambda a, b: visited_edges.get(f"{a}.{b}")
        for node in self.topology.nodes.values():
            if not self.__is_point(node):
                continue

            edges_right = get_edges_from_nodes(node.uuid, node.connected_on_right)
            edges_left = get_edges_from_nodes(node.uuid, node.connected_on_left)

            # We found two points being connected by two edges
            if edges_right == edges_left:
                # We already connected them once
                other_nodes_right_edge = None
                if node.connected_on_left.__dict__.get('right_edge'):
                    # Assign edges to match previous assignment
                    other_nodes_right_edge = node.connected_on_left.__dict__.get('right_edge')
                    other_nodes_left_edge = edges_right[0] if edges_right[0] != other_nodes_right_edge else edges_right[1]

                    diverting = other_nodes_right_edge if node.__dict__.get("orientation") == "Left" else other_nodes_left_edge
                    through = other_nodes_right_edge if node.__dict__.get("orientation") == "Right" else other_nodes_left_edge
                # We see them the first time
                else:
                    # Choose randomly
                    diverting = edges_left[0]
                    through = edges_left[1]

                    node.__dict__["right_edge"] = diverting if node.__dict__.get("orientation") == "Right" else through
            else:
                # There are different edges and the are onl singular
                diverting = (
                    get_edges_from_nodes(node.uuid, node.connected_on_left)[0]
                    if node.__dict__.get("orientation") == "Left"
                    else get_edges_from_nodes(node.uuid, node.connected_on_right)[0]
                )
                through = (
                    get_edges_from_nodes(node.uuid, node.connected_on_right)[0]
                    if node.__dict__.get("orientation") == "Left"
                    else get_edges_from_nodes(node.uuid, node.connected_on_left)[0]
                )

            point = {
                "toe": get_edges_from_nodes(node.uuid, node.connected_on_head.uuid)[0]
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

    def __map_connected_nodes_to_edge(self, edges: list[Edge]) -> dict[str, str]:
        visited_edges = {}
        for edge in edges:
            if visited_edges.get(f"{edge.node_a.uuid}.{edge.node_b.uuid}"):
                visited_edges.get(f"{edge.node_a.uuid}.{edge.node_b.uuid}").append(edge.uuid)
            else:
                visited_edges[f"{edge.node_a.uuid}.{edge.node_b.uuid}"] = [edge.uuid]

            if visited_edges.get(f"{edge.node_b.uuid}.{edge.node_a.uuid}"):
                visited_edges.get(f"{edge.node_b.uuid}.{edge.node_a.uuid}").append(edge.uuid)
            else:
                visited_edges[f"{edge.node_b.uuid}.{edge.node_a.uuid}"] = [edge.uuid]
        return visited_edges
