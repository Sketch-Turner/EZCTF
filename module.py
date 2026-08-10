import importlib.util
import yaml
import os
import uuid

class ModuleInput:
    """
    Represents an input accepted by a module.

    Attributes:
        name (str): Name of the input.
        value (object): Current value of the input.
        input_type (str): Type of the input.
        description (str): Description of the input.
    """

    def __init__(self, name: str, value, input_type: str, description: str):
        """
        Initialize a module input.

        Args:
            name: Name of the input.
            value: Current value of the input.
            input_type: Type of the input.
            description: Description of the input.
        """
        self.name = name
        self.value = value
        self.input_type = input_type
        self.description = description

class ModuleOutput:
    """
    Represents an output produced by a module.

    Attributes:
        name (str): Name of the output.
        description (str): Description of the output.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize a module output.

        Args:
            name: Name of the output.
            description: Description of the output.
        """
        self.name = name
        self.description = description

class Module:
    """
    Represents a loadable workflow module.
    """

    def __init__(self, config_file: str):
        """
        Initialize a module from a configuration file.

        Args:
            config_file (str): Path to the module YAML configuration file.
        """
        self.id = str(uuid.uuid4())
        self.config_file = config_file

        data = {}
        with open(config_file) as f:
            data = yaml.safe_load(f)

        self.name = data.get("name")
        self.author = data.get("author")
        self.version = data.get("version")
        self.platform = data.get("platform")
        self.description = data.get("description")

        self._inputs = [
            ModuleInput(
                name=name,
                value=info.get("value"),
                input_type=info.get("input"),
                description=info.get("description")
            )
            for name, info in data.get("inputs", {}).items()
        ]

        self._outputs = [
            ModuleOutput(
                name=name,
                description=info.get("description")
            )
            for name, info in data.get("outputs", {}).items()
        ]

        self.src = data.get("src")
        self._module = self.load_source(self.src)

    def to_dict(self) -> dict:
        """
        Convert module attributes into a dictionary.

        Returns:
            dict: Module attributes excluding private fields.
        """
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        data["inputs"] = [dict(input.__dict__) for input in self._inputs]

        data["outputs"] = [dict(output.__dict__) for output in self._outputs]

        return data

    def load_source(self, path: str) -> object:
        """
        Load a Python module from a source file.

        Args:
            path (str): Path to the Python source file.

        Returns:
            object: Loaded Python module.
        """
        name = os.path.splitext(os.path.basename(path))[0]

        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        return module

    def update_inputs(self, data: dict):
        """
        Update module input values.

        Args:
            data (dict): New input values keyed by input name.
        """
        for input in self._inputs:
            input.value = data.get(input.name, input.value)

    def copy(self) -> "Module":
        """
        Create a copy of the module.

        Returns:
            Module: New module instance with copied configuration data.
        """
        new = type(self).__new__(type(self))

        new.id = str(uuid.uuid4())
        new.config_file = self.config_file

        new.name = self.name
        new.author = self.author
        new.version = self.version
        new.platform = self.platform
        new.description = self.description

        new._inputs = self._inputs.copy()
        new._outputs = self._outputs.copy()

        new.src = self.src
        new._module = self._module

        return new

    def run(self, source_id, root_id) -> dict:
        """
        Execute the module with its configured inputs.

        Returns:
            dict: Module output values matching configured outputs.
        """
        config = {input.name: input.value for input in self._inputs}
        config["source_id"] = source_id
        config["root_id"] = root_id

        result = self._module.run(config)

        return {output.name: result.get(output.name) for output in self._outputs}
