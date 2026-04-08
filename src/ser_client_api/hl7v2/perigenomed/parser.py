"""
Perigenomed local data parser — stub, not yet implemented.
"""


class PerigenomedParser:
    def validate(self, data):
        raise NotImplementedError("Perigenomed schema validation is not yet implemented")

    def parse(self, data):
        raise NotImplementedError("Perigenomed parser is not yet implemented")


def get_parser() -> PerigenomedParser:
    return PerigenomedParser()
