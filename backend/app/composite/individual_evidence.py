"""LEAF: an evidence item that cannot contain children. Operations act on this object only."""
from typing import Any, Dict, List

from .errors import InvalidHierarchyOperation
from .evidence import Evidence


class IndividualEvidence(Evidence):
    role = "LEAF"
    analysis_steps: List[str] = ["Hash verification", "Metadata extraction", "Analysis complete"]
    findings: Dict[str, int] = {"network": 0, "suspicious": 0}

    def _no_children(self):
        return InvalidHierarchyOperation(f"'{self.name}' is an individual evidence item (Leaf) and cannot contain children.")

    def get_children(self) -> List[Evidence]:
        return []

    def add(self, child: Evidence) -> None:
        raise self._no_children()

    def remove(self, child: Evidence) -> None:
        raise self._no_children()

    def validate_add(self, child: Evidence) -> None:
        raise self._no_children()

    def get_status(self) -> str:
        return self.status

    def analyze(self, actor: str = "Investigator") -> Dict[str, Any]:
        self.emit_custody("Analysis started", actor, details="analyze() invoked on a Leaf")
        steps = list(self.analysis_steps)
        self.status = "ANALYZED"
        self.emit_custody("Analysis completed", actor, details=" > ".join(steps))
        return self._result("COMPLETED", steps, dict(self.findings), [])

    def verify(self, actor: str = "Investigator") -> None:
        if self.status in ("PENDING", "FLAGGED"):
            self.status = "VERIFIED"
            self.emit_custody("SHA-256 verified", actor, integrity="VERIFIED", details="Stored hash matches recomputed hash (simulated)")

    def summary(self) -> Dict[str, int]:
        analyzed = self.status == "ANALYZED"
        f = self.findings if analyzed else {"network": 0, "suspicious": 0}
        return {"items": 1, "analyzed": int(analyzed), "verified": int(analyzed or self.status == "VERIFIED"),
                "flagged": int(self.status == "FLAGGED"), "network": f["network"], "suspicious": f["suspicious"]}

    def display(self) -> Dict[str, Any]:
        return self._base_display()

    def on_created(self, actor: str) -> None:
        self.emit_custody("Evidence collected", actor, details=f"Acquired from {self.source_device or 'source device'}", at=self.collected_at)
        self.emit_custody("SHA-256 generated", "FORENSICVAULT", details=self.sha256[:16] + "...")

    def on_moved(self, actor: str, old_parent: str, new_parent: str) -> None:
        self.emit_custody("Moved within evidence hierarchy", actor, details=f"{old_parent} -> {new_parent}")
