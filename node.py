from uuid import uuid4
from filter import Filter
from target import Target
from module import Module
from display import Display
from history import History

class Node:
    """
    Represents a node in a workflow graph.
    """
    def __init__(self, type: str, x: int = 0, y: int = 0):
        """
        Initialize a workflow node.

        Args:
            type (str): Node type identifier.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        self.id = str(uuid4())
        self.type = type
        self.x = x
        self.y = y
        self._in = []
        self._out = []

    def to_dict(self) -> dict:
        """
        Convert node attributes into a dictionary.

        Returns:
            dict: Node attributes and rendered HTML excluding private fields.
        """
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        data["html"] = self.render()
        return data

    def get_next(self) -> list:
        """
        Get nodes connected by outgoing edges.

        Returns:
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

        Args:
            target (Target): Target object represented by this node.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="TARGET",
            x=x,
            y=y
        )
        self._target = target

    def render(self) -> str:
        """
        Render the target node HTML.

        Returns:
            str: HTML representation of the node.
        """
        return f"""
            <div class="node-title">Target</div>
            <div class="node-value">{self._target.target}</div>
        """

    def get_ips(self) -> list:
        """
        Get target IP addresses.

        Returns:
            list: List of target IP addresses.
        """
        ip_list = self._target.target
        if not isinstance(ip_list, list):
            ip_list = [ip_list]
        return ip_list

class DisplayNode(Node):
    """
    Workflow node for display.
    """
    def __init__(self, display:Display, x:int = 0, y:int = 0):
        """
        Initialize a filter workflow node.

        Args:
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="DISPLAY",
            x=x,
            y=y
        )
        self._display = display

    def render(self) -> str:
        """
        Render the display node HTML.

        Returns:
            str: HTML representation of the node.
        """
        return f"""
            <div class="node-title">Display</div>
        """

    def render_config(self) -> str:
        """
        Render the display HTML.

        Returns:
            str: HTML representation of the display.
        """
        return self._display.render()


    def run(self, input: dict):
        """
        Update display node.

        Args:
            input (dict): Data used to update display.
        """
        self._display.add(input)

class FilterNode(Node):
    """
    Workflow node for filter.
    """
    def __init__(self, filter: Filter, x: int = 0, y: int = 0):
        """
        Initialize a filter workflow node.

        Args:
            filter (Filter): Filter object represented by this node.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="FILTER",
            x=x,
            y=y
        )
        self._filter = filter.copy()

    def render(self) -> str:
        """
        Render the filter node HTML.

        Returns:
            str: HTML representation of the node.
        """
        return f"""
            <div class="node-title">Filter</div>
            <div class="node-value">{self._filter.expression}</div>
        """

    def render_config(self) -> str:
        """
        Render the filter configuration HTML.

        Returns:
            str: HTML representation of the filter configuration.
        """
        return f"""
        <div class="config-group">
            <label for="filter-expression">Expression</label>

            <textarea
                id="filter-expression"
                name="expression"
                class="config-textarea"
            >{self._filter.expression}</textarea>
        </div>
        """

    def update_config(self, data: dict):
        """
        Update filter configuration values.

        Args:
            data (dict): Updated filter configuration data.
        """
        self._filter.expression = data["expression"]
        self._filter.valid = Filter.validate(self._filter.expression)

    def run(self, input: dict) -> dict:
        """
        Apply the filter to input data.

        Args:
            input (dict): Data to evaluate against the filter.

        Returns:
            dict: Filtered input data if filter is valid and data matches, otherwise an empty dictionary.
        """
        if History.verbose:
            History.write(root_id=input['root_id'], source_id=self.id, message=f"Filter\n    Input: {input}\n    Expression: {self._filter.expression}")
        if self._filter.valid:
            output = self._filter.apply(input)
            if History.verbose:
                if output != input:
                    History.write(root_id=input['root_id'], source_id=self.id, message=f"Rejected")
                else:
                    History.write(root_id=input['root_id'], source_id=self.id, message=f"Match")
            return output
        if History.verbose:
            History.write(root_id=input['root_id'], source_id=self.id, message=f"Invalid expression")
        return {}

class ModuleNode(Node):
    """
    Workflow node for module.
    """
    def __init__(self, module: Module, x: int = 0, y: int = 0):
        """
        Initialize a module workflow node.

        Args:
            module (Module): Module object represented by this node.
            x (int): X-coordinate position on the canvas.
            y (int): Y-coordinate position on the canvas.
        """
        super().__init__(
            type="MODULE",
            x=x,
            y=y
        )
        self._module = module.copy()

    def render(self) -> str:
        """
        Render the module node HTML.

        Returns:
            str: HTML representation of the node.
        """
        inputs = "".join(
            f'<div class="node-input"><span>{input.name}: </span><span>{input.value}</span></div>'
            for input in self._module._inputs
            if "CONFIG" in input.input_type
        )

        return f"""
            <div class="node-title">Module</div>
            <div class="node-value">{self._module.name}</div>
            <div class="node-inputs">
                {inputs}
            </div>
        """

    def render_config(self) -> str:
        """
        Render the module configuration HTML.

        Returns:
            str: HTML representation of the module configuration.
        """
        fields = ""

        for input in self._module._inputs:
            if "CONFIG" not in input.input_type:
                continue

            if "FILE" in input.input_type:
                field = f"""
                <div class="config-group">
                    <label for="{input.name}">{input.name}</label>

                    <input
                        id="{input.name}"
                        name="{input.name}"
                        type="file"
                        class="config-input"
                    >
                </div>
                """
            else:
                field = f"""
                <div class="config-group">
                    <label for="{input.name}">{input.name}</label>

                    <input
                        id="{input.name}"
                        name="{input.name}"
                        type="text"
                        class="config-input"
                        value="{input.value}"
                    >
                </div>
                """

            fields += field

        return fields

    def update_config(self, data: dict):
        """
        Update module configuration values.

        Args:
            data (dict): Updated module input values.
        """
        self._module.update_inputs(data)

    def run(self, input: dict) -> dict:
        """
        Execute the module using input data.

        Args:
            input (dict): Data used to update module inputs.

        Returns:
            dict: Module execution results.
        """
        input['source_id'] = self.id
        self._module.update_inputs(input)
        if History.verbose:
            History.write(root_id=input['root_id'], source_id=self.id, message=f"Starting module: {self._module.name}\n    Input: { {input.name: input.value for input in self._module._inputs} }")
        result = self._module.run(root_id=input['root_id'], source_id=self.id)
        result['root_id'] = input['root_id']
        if History.verbose:
            History.write(root_id=input['root_id'], source_id=self.id, message=f"Module complete\n    Output: {result}")
        return result

class Edge:
    """
    Represents a connection between two workflow nodes.
    """
    def __init__(self, source: Node, destination: Node):
        """
        Initialize a workflow edge.

        Args:
            source (Node): Source node of the connection.
            destination (Node): Destination node of the connection.
        """
        self.id = str(uuid4())
        self.source = source
        self.destination = destination

    def to_dict(self) -> dict:
        """
        Convert edge data into a dictionary.

        Returns:
            dict: Edge identifier and connected node identifiers.
        """
        return {
            "id": self.id,
            "source": self.source.id,
            "destination": self.destination.id
        }