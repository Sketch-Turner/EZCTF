from uuid import uuid4
from filter import Filter
from target import Target
from module import Module

class Node:
    """
    Represents a node in a workflow graph.
    """
    def __init__(self, type: str, data: dict, x: int = 0, y: int = 0):
        """
        Initialize a workflow node.

        Inputs:
            type (str): Node type identifier.
            data (dict): Node-specific data.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        self.id = str(uuid4())
        self.type = type
        self.x = x
        self.y = y
        self.data = data
        self._in = []
        self._out = []

    def to_dict(self) -> dict:
        """
        Convert node attributes into a dictionary.

        Outputs:
            dict: Node attributes and rendered HTML excluding private fields.
        """
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        data["html"] = self.render()
        return data

    def get_next(self) -> list:
        """
        Get nodes connected by outgoing edges.

        Outputs:
            list: Destination nodes connected to this node.
        """
        next = []
        for edge in self._out:
            next.append(edge.destination)
        return next

    def render(self):
        raise NotImplementedError

    def render_config(self):
        raise NotImplementedError

    def update_config(self, data):
        raise NotImplementedError

    def run(self, input):
        raise NotImplementedError

class TargetNode(Node):
    """
    Workflow node for target data.
    """
    def __init__(self, target: Target, x: int = 0, y: int = 0):
        """
        Initialize a target workflow node.

        Inputs:
            target (Target): Target object represented by this node.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="TARGET",
            data=target.to_dict(),
            x=x,
            y=y
        )

    def render(self) -> str:
        """
        Render the target node HTML.

        Outputs:
            str: HTML representation of the node.
        """
        return f"""
            <div class="node-title">Target</div>
            <div class="node-value">{self.data["tgt_ip"]}</div>
        """

    def get_ips(self) -> list:
        """
        Get target IP addresses.

        Outputs:
            list: List of target IP addresses.
        """
        ip_list = self.data.get("tgt_ip", [])
        if not isinstance(ip_list, list):
            ip_list = [ip_list]
        return ip_list

class FilterNode(Node):
    """
    Workflow node for filter.
    """
    def __init__(self, filter: Filter, x: int = 0, y: int = 0):
        """
        Initialize a filter workflow node.

        Inputs:
            filter (Filter): Filter object represented by this node.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="FILTER",
            data=filter.to_dict(),
            x=x,
            y=y
        )
        self._filter = filter.copy()

    def render(self) -> str:
        """
        Render the filter node HTML.

        Outputs:
            str: HTML representation of the node.
        """
        return f"""
            <div class="node-title">Filter</div>
            <div class="node-value">{self.data["expression"]}</div>
        """

    def render_config(self) -> str:
        """
        Render the filter configuration HTML.

        Outputs:
            str: HTML representation of the filter configuration.
        """
        return f"""
        <div class="config-group">
            <label for="filter-expression">Expression</label>

            <textarea
                id="filter-expression"
                name="expression"
                class="config-textarea"
            >{self.data["expression"]}</textarea>
        </div>
        """

    def update_config(self, data: dict):
        """
        Update filter configuration values.

        Inputs:
            data (dict): Updated filter configuration data.
        """
        self.data["expression"] = data["expression"]
        self._filter.expression = self.data["expression"]
        self.data["valid"] = Filter.validate(data["expression"])
        self._filter.valid = self.data["valid"]

    def run(self, input: dict) -> dict:
        """
        Apply the filter to input data.

        Inputs:
            input (dict): Data to evaluate against the filter.

        Outputs:
            dict: Filtered input data if filter is valid and data matches, otherwise an empty dictionary.
        """
        if self._filter.valid:
            return self._filter.apply(input)
        return {}

class ModuleNode(Node):
    """
    Workflow node for module.
    """
    def __init__(self, module: Module, x: int = 0, y: int = 0):
        """
        Initialize a module workflow node.

        Inputs:
            module (Module): Module object represented by this node.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="MODULE",
            data=module.to_dict(),
            x=x,
            y=y
        )
        self._module = module.copy()

    def render(self) -> str:
        """
        Render the module node HTML.

        Outputs:
            str: HTML representation of the node.
        """
        inputs = "".join(
            f'<div class="node-input"><span>{k}: </span><span>{v}</span></div>'
            for k, v in self.data["inputs"].items() if k in self.data["config"]
        )

        return f"""
            <div class="node-title">Module</div>
            <div class="node-value">{self.data["name"]}</div>
            <div class="node-inputs">
                {inputs}
            </div>
        """

    def render_config(self) -> str:
        """
        Render the module configuration HTML.

        Outputs:
            str: HTML representation of the module configuration.
        """
        fields = "".join(
            f"""
            <div class="config-group">
                <label for="{key}">{key}</label>

                <input
                    id="{key}"
                    name="{key}"
                    type="text"
                    class="config-input"
                    value="{self.data["inputs"].get(key, "")}"
                >
            </div>
            """
            for key in self.data["config"]
        )

        return fields

    def update_config(self, data: dict):
        """
        Update module configuration values.

        Inputs:
            data (dict): Updated module input values.
        """
        self._module.update_inputs(data)
        self.data = self._module.to_dict()


    def run(self, input: dict) -> dict:
        """
        Execute the module using input data.

        Inputs:
            input (dict): Data used to update module inputs.

        Outputs:
            dict: Module execution results.
        """
        self._module.update_inputs(input)
        return self._module.run()

class Edge:
    """
    Represents a connection between two workflow nodes.
    """
    def __init__(self, source: Node, destination: Node):
        """
        Initialize a workflow edge.

        Inputs:
            source (Node): Source node of the connection.
            destination (Node): Destination node of the connection.
        """
        self.id = str(uuid4())
        self.source = source
        self.destination = destination

    def to_dict(self) -> dict:
        """
        Convert edge data into a dictionary.

        Outputs:
            dict: Edge identifier and connected node identifiers.
        """
        return {
            "id": self.id,
            "source": self.source.id,
            "destination": self.destination.id
        }