class Display:
    def __init__(self):
        self.data = set()

    def render(self) -> str:
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
        if isinstance(value, dict):
            return tuple(sorted((key, Display.to_hashable(val)) for key, val in value.items()))
        if isinstance(value, (list, tuple)):
            return tuple(Display.to_hashable(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return frozenset(Display.to_hashable(item) for item in value)
        return value

    @staticmethod
    def from_hashable(value):
        if isinstance(value, tuple):
            return {key: Display.from_hashable(val) for key, val in value}
        if isinstance(value, frozenset):
            return {Display.from_hashable(item) for item in value}
        return value

    def add(self, data:dict):
        self.data.add(Display.to_hashable(data))