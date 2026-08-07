import uuid
from queue import Queue

class Target:
    """
    Represents a workflow target.
    """

    def __init__(self, ip: str):
        """
        Initialize a target.

        Args:
            ip (str): Target IP address.
        """
        self.id = str(uuid.uuid4())
        self.tgt_ip = ip
        self.name = ip
        self._history = Queue()

    def to_dict(self) -> dict:
        """
        Convert target attributes into a dictionary.

        Returns:
            dict: Target attributes excluding private fields.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}