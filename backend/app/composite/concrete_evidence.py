"""Concrete Leaf classes (evidence types) and concrete Composite classes (group types)."""
from typing import Dict, Type

from .evidence_group import EvidenceGroup
from .individual_evidence import IndividualEvidence


def _leaf(name, type_name, steps, network=0, suspicious=0):
    return type(name, (IndividualEvidence,), {"type_name": type_name, "analysis_steps": steps, "findings": {"network": network, "suspicious": suspicious}})


DiskImage = _leaf("DiskImage", "Disk Image", ["Hash verification", "Metadata extraction", "File-system scan", "Analysis complete"], 1, 2)
BrowserHistory = _leaf("BrowserHistory", "Browser History", ["URL metadata", "Timestamp extraction", "Suspicious-domain simulation", "Analysis complete"], 4, 1)
SystemLog = _leaf("SystemLog", "System Log", ["Log parsing", "Event correlation", "Analysis complete"], 2, 1)
MobileDeviceImage = _leaf("MobileDeviceImage", "Device Image", ["Hash verification", "Partition mapping", "App inventory", "Analysis complete"], 1, 0)
MobileMessage = _leaf("MobileMessage", "Mobile Message", ["Message extraction", "Contact resolution", "Link analysis", "Analysis complete"], 0, 2)
CallRecord = _leaf("CallRecord", "Call Record", ["Call log parsing", "Contact frequency", "Analysis complete"], 0, 0)
NetworkPCAP = _leaf("NetworkPCAP", "Network PCAP", ["Packet metadata", "Protocol summary", "Connection summary", "Analysis complete"], 3, 0)
FirewallLog = _leaf("FirewallLog", "Firewall Log", ["Rule hit parsing", "Blocked-connection summary", "Analysis complete"], 1, 0)
DNSLog = _leaf("DNSLog", "DNS Log", ["Query extraction", "Domain reputation simulation", "Analysis complete"], 0, 0)
OtherEvidence = _leaf("OtherEvidence", "Other", ["Hash verification", "Metadata extraction", "Analysis complete"])
LEAF_CLASSES: Dict[str, Type[IndividualEvidence]] = {c.type_name: c for c in (DiskImage, BrowserHistory, SystemLog, MobileDeviceImage, MobileMessage, CallRecord, NetworkPCAP, FirewallLog, DNSLog, OtherEvidence)}


class InvestigationCase(EvidenceGroup):
    group_type = "Investigation Case"
    is_case_root = True


class ComputerEvidenceGroup(EvidenceGroup):
    group_type = "Computer Evidence"
    category = "Computer"


class MobileEvidenceGroup(EvidenceGroup):
    group_type = "Mobile Evidence"
    category = "Mobile"


class NetworkEvidenceGroup(EvidenceGroup):
    group_type = "Network Evidence"
    category = "Network"


class CustomEvidenceGroup(EvidenceGroup):
    group_type = "Custom Group"


GROUP_CLASSES: Dict[str, Type[EvidenceGroup]] = {c.group_type: c for c in (InvestigationCase, ComputerEvidenceGroup, MobileEvidenceGroup, NetworkEvidenceGroup)}
GROUP_TYPES = ["Computer Evidence", "Mobile Evidence", "Network Evidence", "Forensic Collection", "Custom Group"]
