"""
ParserFactory — dynamically loads the institution-specific local data parser.
"""

import importlib

from ser_client_api.hl7v2.institution_config import InstitutionConfig


class ParserFactory:
    """Instantiates the local data parser declared in an InstitutionConfig."""

    def __init__(self, institution: InstitutionConfig):
        self._institution = institution

    def create(self):
        module_path = self._institution.local_data_parser
        module = importlib.import_module(module_path)
        if not hasattr(module, "get_parser"):
            raise AttributeError(
                f"Module '{module_path}' must expose a get_parser() function"
            )
        return module.get_parser()
