import re
import uuid

class Filter:
    """
    Provides boolean expression evaluation for workflow filtering.
    """

    def __init__(self, expression:str):
        """
        Initialize a filter.

        Inputs:
            expression (str): Filter expression to evaluate.
        """
        self.id = str(uuid.uuid4())
        self.expression = expression
        self.valid = Filter.validate(expression)

    def to_dict(self) -> dict:
        """
        Convert filter attributes into a dictionary.

        Outputs:
            dict: Filter attributes excluding private fields.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def copy(self) -> "Filter":
        """
        Create a copy of the filter.

        Outputs:
            Filter: New filter instance with the same expression.
        """
        return Filter(self.expression)

    def apply(self, input: dict) -> dict:
        """
        Apply the filter expression to input data.

        Inputs:
            input (dict): Data to evaluate against the filter expression.

        Outputs:
            dict: Input data if the filter passes, otherwise an empty dictionary.
        """
        tokens = Filter.tokenize(self.expression)

        if Filter.parse_or(tokens, 0, input)[0]:
            return input
        return {}

    @staticmethod
    def tokenize(expression: str) -> list:
        """
        Convert a filter expression into tokens.

        Inputs:
            expression (str): Filter expression to tokenize.

        Outputs:
            list: Tokens extracted from the expression.
        """
        return re.findall(
            r'"[^"]*"|\'[^\']*\'|<=|>=|!=|==|<|>|\(|\)|\d+\.\d+|\d+|\w+',
            expression
        )

    @staticmethod
    def parse_or(tokens: list, index: int, data: dict) -> tuple:
        """
        Parse OR expressions from filter tokens.

        Inputs:
            tokens (list): Tokenized filter expression.
            index (int): Current token index.
            data (dict): Data values used for evaluation.

        Outputs:
            tuple: Evaluation result and updated token index.
        """
        result, index = Filter.parse_and(tokens, index, data)

        while index < len(tokens) and tokens[index] == "or":
            index += 1
            right, index = Filter.parse_and(tokens, index, data)
            result = result or right

        return result, index

    @staticmethod
    def parse_and(tokens: list, index: int, data: dict) -> tuple:
        """
        Parse AND expressions from filter tokens.

        Inputs:
            tokens (list): Tokenized filter expression.
            index (int): Current token index.
            data (dict): Data values used for evaluation.

        Outputs:
            tuple: Evaluation result and updated token index.
        """
        result, index = Filter.parse_not(tokens, index, data)

        while index < len(tokens) and tokens[index] == "and":
            index += 1

            right, index = Filter.parse_not(tokens, index, data)
            result = result and right

        return result, index

    @staticmethod
    def parse_not(tokens: list, index: int, data: dict) -> tuple:
        """
        Parse NOT expressions from filter tokens.

        Inputs:
            tokens (list): Tokenized filter expression.
            index (int): Current token index.
            data (dict): Data values used for evaluation.

        Outputs:
            tuple: Evaluation result and updated token index.
        """
        if index < len(tokens) and tokens[index] == "not":
            result, index = Filter.parse_not(tokens, index + 1, data)
            return not result, index

        return Filter.parse_primary(tokens, index, data)

    @staticmethod
    def parse_primary(tokens: list, index: int, data: dict) -> tuple:
        """
        Parse grouped expressions or comparisons.

        Inputs:
            tokens (list): Tokenized filter expression.
            index (int): Current token index.
            data (dict): Data values used for evaluation.

        Outputs:
            tuple: Evaluation result and updated token index.
        """
        if index < len(tokens) and tokens[index] == "(":
            result, index = Filter.parse_or(tokens, index + 1, data)

            if index >= len(tokens) or tokens[index] != ")":
                raise ValueError("Expected )")

            return result, index + 1

        return Filter.compare(tokens, index, data)

    @staticmethod
    def compare(tokens: list, index: int, data: dict) -> tuple:
        """
        Compare a data value against a filter condition.

        Inputs:
            tokens (list): Tokenized filter expression.
            index (int): Current token index.
            data (dict): Data values used for comparison.

        Outputs:
            tuple: Comparison result and updated token index.
        """
        if index + 2 >= len(tokens):
            raise ValueError("Incomplete comparison")

        key = tokens[index]
        operator = tokens[index + 1]
        token = tokens[index + 2]

        index += 3

        if key not in data:
            return False, index

        left = data[key]
        right = Filter.resolve(token, data)

        match operator:
            case "==":
                return left == right, index

            case "!=":
                return left != right, index

            case "<":
                return left < right, index

            case ">":
                return left > right, index

            case "<=":
                return left <= right, index

            case ">=":
                return left >= right, index

            case "contains":
                return right in left, index

        raise ValueError(f"Unknown operator: {operator}")

    @staticmethod
    def resolve(token: str, data: dict) -> object:
        """
        Resolve a token into its corresponding value.

        Inputs:
            token (str): Token to resolve.
            data (dict): Data values used for variable lookup.

        Outputs:
            object: Resolved literal or data value.
        """
        value = Filter.literal(token)

        if value is not None:
            return value

        if token in data:
            return data[token]

        # when validating, unknown identifiers are assumed to be variables.
        if len(data) == 0:
            return 0

        raise ValueError(f"Unknown variable: {token}")

    @staticmethod
    def literal(token: str) -> object:
        """
        Convert a token into a literal value.

        Inputs:
            token (str): Token to convert.

        Outputs:
            object: Parsed literal value, or None if not a literal.
        """
        if token.startswith(("'", '"')):
            return token[1:-1]

        try:
            return int(token)
        except ValueError:
            pass

        try:
            return float(token)
        except ValueError:
            pass

        if token == "True":
            return True

        if token == "False":
            return False

        return None

    @staticmethod
    def validate(expression: str) -> bool:
        """
        Validate a filter expression.

        Inputs:
            expression (str): Filter expression to validate.

        Outputs:
            bool: Whether the expression is valid.
        """
        tokens = Filter.tokenize(expression)

        try:
            _, index = Filter.parse_or(tokens, 0, {})

            return index == len(tokens)

        except ValueError:
            return False