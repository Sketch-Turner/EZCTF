class Display:
    """
    Represents display data.
    """

    def __init__(self):
        """
        Initialize the display.
        """
        self.data = set()

    def render(self) -> str:
        """
        Render the display HTML.

        Returns:
            str: HTML representation of the display.
        """
        data = [Display.from_hashable(item) for item in self.data]

        fields = set()
        for item in data:
            fields.update(item.keys())

        fields.remove("root_id")
        fields.remove("source_id")

        html = '<div class="config-group"><table><thead><tr>'

        for field in fields:
            html += f"<th>{field}</th>"

        html += "</tr></thead><tbody>"

        for item in data:
            html += "<tr>"

            for field in fields:
                html += f"<td>{item.get(field, '')}</td>"

            html += "</tr>"

        html += "</tbody></table></div>"

        return html

    @staticmethod
    def to_hashable(value):
        """
        Convert a value into a hashable representation.

        Args:
            value: Value to convert.

        Returns:
            Hashable representation of the value.
        """
        if isinstance(value, dict):
            return tuple(sorted((key, Display.to_hashable(val)) for key, val in value.items()))
        if isinstance(value, (list, tuple)):
            return tuple(Display.to_hashable(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return frozenset(Display.to_hashable(item) for item in value)
        return value

    @staticmethod
    def from_hashable(value):
        """
        Revert hashable to original.

        Args:
            value: Value to convert.

        Returns:
            Original representation of the value.
        """
        if isinstance(value, tuple):
            return {key: Display.from_hashable(val) for key, val in value}
        if isinstance(value, frozenset):
            return {Display.from_hashable(item) for item in value}
        return value

    def add(self, data:dict):
        """
        Update display data.

        Args:
            input (dict): Data used to update display.
        """
        self.data.add(Display.to_hashable(data))