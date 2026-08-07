from node import *
from target import Target
from history import History
from queue import Empty

class Workflow:
    def __init__(self):
        """
        Initialize an empty workflow.
        """
        self.nodes = []
        self.edges = []
        self.targets = [] # target nodes
        self.history = [] # global history logs

    def add_node(self, type: str, source: object, x: int = 0, y: int = 0) -> Node:
        """
        Add a node to the workflow.

        Args:
            type (str): Type of node to create. Supported values are TARGET, FILTER, and MODULE.
            source (object): Source object used to initialize the node.
            x (int): X-coordinate position of the node.
            y (int): Y-coordinate position of the node.

        Returns:
            Node: Newly created workflow node.

        Raises:
            ValueError: If the provided node type is unsupported.
        """
        match type.upper():
            case "TARGET":
                node = TargetNode(source, x, y)
                self.targets.append(node)

            case "FILTER":
                node = FilterNode(source, x, y)

            case "MODULE":
                node = ModuleNode(source, x, y)

            case _:
                raise ValueError(f"Unknown node type: {type}")

        self.nodes.append(node)

        return node

    def remove_node(self, node_id: str):
        """
        Remove a node and its connected edges from the workflow.

        Args:
            node_id (str): ID of the node to remove.
        """
        self.nodes = [
            node for node in self.nodes
            if node.id != node_id
        ]

        self.targets = [
            node for node in self.nodes
            if node.type == "TARGET"
        ]

        # remove connected edges
        self.edges = [
            edge for edge in self.edges
            if edge.source.id != node_id
            and edge.destination.id != node_id
        ]

    def get_node(self, node_id: str) -> Node:
        """
        Retrieve a node by its ID.

        Args:
            node_id (str): ID of the node to retrieve.

        Returns:
            Node: Node with the matching ID.

        Raises:
            ValueError: If no node with the given ID exists.
        """
        for node in self.nodes:
            if node.id == node_id:
                return node

        raise ValueError(f"Node not found: {node_id}")

    def add_edge(self, source_id: str, destination_id: str) -> Edge:
        """
        Add an edge between two workflow nodes.

        Args:
            source_id (str): ID of the source node.
            destination_id (str): ID of the destination node.

        Returns:
            Edge: Newly created edge connecting the nodes.
        """
        source = self.get_node(source_id)
        destination = self.get_node(destination_id)

        edge = Edge(
            source,
            destination
        )

        self.edges.append(edge)
        source._out.append(edge)
        destination._in.append(edge)

        return edge

    def remove_edge(self, edge_id: str):
        """
        Remove an edge from the workflow.

        Args:
            edge_id (str): ID of the edge to remove.
        """
        edge = next(
            edge for edge in self.edges
            if edge.id == edge_id
        )

        edge.source._out.remove(edge)
        edge.destination._in.remove(edge)

        self.edges.remove(edge)

    def get_nodes(self) -> list[dict]:
        """
        Get all workflow nodes as dictionaries.

        Returns:
            list[dict]: List of serialized workflow nodes.
        """
        return [
            node.to_dict()
            for node in self.nodes
        ]

    def get_edges(self) -> list[dict]:
        """
        Get all workflow edges as dictionaries.

        Returns:
            list[dict]: List of serialized workflow edges.
        """
        return [
            edge.to_dict()
            for edge in self.edges
        ]

    def to_dict(self) -> dict:
        """
        Convert the workflow to a dictionary.

        Returns:
            dict: Serialized workflow containing nodes and edges.
        """
        return {
            "nodes": self.get_nodes(),
            "edges": self.get_edges()
        }

    def get_root_id(self, ip: str, targets:list[Target]) -> str | None:
        """
        Find the workflow target node ID for an IP address.

        Args:
            ip (str): Target IP address.
            targets (list[Target]): List of target objects.

        Returns:
            str | None: Matching target node ID, or None if no match is found.
        """
        for t in targets:
            tgt = t.tgt_ip
            if isinstance(tgt, str):
                if ip == tgt:
                    return t.id

        return None

    def run(self, targets:list[Target]):
        """
        Execute the workflow starting from each target node.

        Args:
            targets (list[Target]): List of target objects.
        """
        for t in self.targets:
            ip_list = t.get_ips()

            for ip in ip_list:
                root_id = self.get_root_id(ip, targets)
                History.write(root_id=root_id, source_id=root_id, message="Workflow started")
                for node in t.get_next():
                    self.dfs(node, {'tgt_ip':ip, 'root_id':root_id})
                History.write(root_id=root_id, source_id=root_id, message="Workflow complete")

    def dfs(self, node: Node, input: dict):
        """
        Recursively execute workflow nodes using depth-first traversal.

        Args:
            node (Node): Current workflow node to execute.
            input (dict): Input data passed into the node.
        """
        input['source_id'] = node.id
        output = node.run(input)
        if len(output) == 0:
            return

        next = node.get_next()
        if len(next) == 0:
            return

        for n in next:
            self.dfs(n, output)

    def update_targets(self, target_pool:list):
        """
        Updates any TARGET node with multiple targets to match `target_pool`. 

        Args:
            target_pool (list): List of all targets.
        """
        for node in self.targets:
            if isinstance(node.data["tgt_ip"], list):
                node.data["tgt_ip"] = target_pool
                node.data["name"] = target_pool

    def sync_history(self, targets:list[Target]):
        """
        Syncs target history.
        """
        while True:
            log = History.read()
            self.history.append(log)
            target = None
            for t in targets:
                if t.id == log.root_id:
                    target = t
                    break
            if target:
                target._history.put(log)

    def get_target_history(self, target_id: str, targets:list[Target]) -> list:
        """
        Retrieve and remove all pending history entries for a Target.

        Args:
            node_id: ID of the Target whose history should be retrieved.

        Returns:
            List of history log entries for the Target.
        """
        logs = []
        target = None
        for t in targets:
            if t.id == target_id:
                target = t
                break
        if target:
            while True:
                try:
                    logs.append(target._history.get_nowait().__dict__)
                except Empty:
                    break

        return logs