from .connectors.elempleo import ElempleoConnector
from .connectors.computrabajo import ComputrabajoConnector

_CONNECTOR_TYPES = {
    ElempleoConnector.source: ElempleoConnector,
    ComputrabajoConnector.source: ComputrabajoConnector,
}


def register_connector(connector_class):
    """Register a connector implementing the shared public-source interface."""
    _CONNECTOR_TYPES[connector_class.source] = connector_class


def configured_connectors():
    return [connector_type() for connector_type in _CONNECTOR_TYPES.values()]
