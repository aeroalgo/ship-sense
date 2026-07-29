"""OPC UA plugin package.

B3: OpcUaConnector + security helpers + browse + subscription.
"""

from collector.plugins.opcua.browse import browse_diff, browse_nodes
from collector.plugins.opcua.connector import OpcUaConnector
from collector.plugins.opcua.security import (
    build_client_security,
    ensure_trust_store,
)
from collector.plugins.opcua.subscription import SubscriptionManager

__all__ = [
    "OpcUaConnector",
    "SubscriptionManager",
    "browse_nodes",
    "browse_diff",
    "build_client_security",
    "ensure_trust_store",
]
