import importlib.util
import yaml
import os
import uuid

class Module:
    """
    Represents a loadable workflow module.
    """

    def __init__(self, config_file: str):
        """
        Initialize a module from a configuration file.

        Inputs:
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

        self.inputs = data.get("inputs", {}) # input values
        self.inputs['source_id'] = None
        self.inputs['root_id'] = None
        self.config = [k for k, v in self.inputs.items() if v is not None] # config key names
        self.outputs = data.get("outputs", []) # output values

        self.src = data.get("src")
        self._module = self.load_source(self.src)

    def to_dict(self) -> dict:
        """
        Convert module attributes into a dictionary.

        Outputs:
            dict: Module attributes excluding private fields.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def load_source(self, path: str) -> object:
        """
        Load a Python module from a source file.

        Inputs:
            path (str): Path to the Python source file.

        Outputs:
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

        Inputs:
            data (dict): New input values keyed by input name.
        """
        for k in self.inputs.keys():
            self.inputs[k] = data.get(k, self.inputs[k])

    def copy(self) -> "Module":
        """
        Create a copy of the module.

        Outputs:
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

        new.inputs = self.inputs.copy()
        new.config = self.config.copy()
        new.outputs = self.outputs.copy()

        new.src = self.src
        new._module = self._module

        return new

    def run(self) -> dict:
        """
        Execute the module with its configured inputs.

        Outputs:
            dict: Module output values matching configured outputs.
        """
        result = self._module.run(self.inputs)

        return {
            key: result[key]
            for key in self.outputs
            if key in result
        }