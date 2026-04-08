"""
Auragen local data parser — stub, not yet implemented.
"""


class AuragenParser:
    def validate(self, data):
        raise NotImplementedError("Auragen schema validation is not yet implemented")

    def parse(self, data):
        raise NotImplementedError("Auragen parser is not yet implemented")


def get_parser() -> AuragenParser:
    return AuragenParser()
