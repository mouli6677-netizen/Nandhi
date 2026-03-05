# capabilities/registry.py

class CapabilityRegistry:
    """
    Registry for managing available capabilities/tools in the Nandhi engine.
    Previously this file incorrectly contained PDFLoader code — that belongs in ingestion/pdf_loader.py.
    """

    def __init__(self):
        self._capabilities = {}

    def register(self, name: str, handler):
        """Register a capability by name."""
        self._capabilities[name] = handler

    def get(self, name: str):
        """Retrieve a registered capability by name."""
        return self._capabilities.get(name)

    def list_capabilities(self):
        """Return all registered capability names."""
        return list(self._capabilities.keys())

    def has(self, name: str) -> bool:
        """Check if a capability is registered."""
        return name in self._capabilities
