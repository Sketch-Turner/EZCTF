from queue import Queue
from time import time

class History:
    """
    Thread-safe history queue for log messages.
    """

    _queue = Queue()
    verbose = True

    class Log:
        """
        Represents a history log entry.

        Attributes:
            timestamp (float): Unix timestamp when the log was created.
            root_id (str): Target associated with the log entry.
            source_id (str): Source associated with the log entry.
            message (str): Log message.
        """

        def __init__(self, root_id: str, source_id: str, message: str):
            """
            Initialize a history log entry.

            Args:
                root_id (str): Target associated with the log entry.
                source_id (str): Source associated with the log entry.
                message (str): Log message.
            """
            self.timestamp = time()
            self.root_id = root_id
            self.source_id = source_id
            self.message = message

    @staticmethod
    def write(root_id: str, source_id: str, message: str):
        """
        Write a log entry to the history queue.

        Args:
            root_id (str): Target associated with the log entry.
            source_id (str): Source associated with the log entry.
            message (str): Log message.
        """
        print(f"LOG: {(time(), root_id, source_id, message)}")
        History._queue.put(History.Log(root_id, source_id, message))

    @staticmethod
    def read() -> "History.Log":
        """
        Read the next log entry from the history queue.

        Returns:
            History.Log: Next log entry.
        """
        return History._queue.get()