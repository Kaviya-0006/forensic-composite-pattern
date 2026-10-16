"""COMPOSITE: stores child Evidence objects and performs operations by delegating to them recursively."""
from typing import Any, Dict, List

from .errors import CircularHierarchyError, DuplicateChildError, InvalidHierarchyOperation
from .evidence import Evidence

ZERO = {"items": 0, "analyzed": 0, "verified": 0, "flagged": 0, "network": 0, "suspicious": 0}


class EvidenceGroup(Evidence):
    role = "COMPOSITE"
    group_type = "Custom Group"
    category = "General"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._children: List[Evidence] = []

    def is_composite(self) -> bool:
        return True

    def validate_add(self, child: Evidence) -> None:
        if child.is_case_root:
            raise InvalidHierarchyOperation("An investigation case cannot be placed inside an evidence group.")
        node = self
        while node is not None:                      # walk up: is `child` this group or one of its ancestors?
            if node is child:
                raise CircularHierarchyError("A group cannot be placed inside itself or one of its own descendants.")
            node = node.parent
        if child.parent is self or child in self._children:
            raise DuplicateChildError(f"'{child.name}' is already a child of '{self.name}'.")

    def add(self, child: Evidence) -> None:
        self.validate_add(child)
        if child.parent is not None:
            raise InvalidHierarchyOperation(f"'{child.name}' already has a parent; remove it from there first.")
        child.parent = self
        self._children.append(child)

    def remove(self, child: Evidence) -> None:
        if child not in self._children:
            raise InvalidHierarchyOperation(f"'{child.name}' is not a child of '{self.name}'.")
        self._children.remove(child)
        child.parent = None

    def get_children(self) -> List[Evidence]:
        return list(self._children)

    def descendant_count(self) -> int:
        return sum(1 + c.descendant_count() for c in self._children)

    def group_count(self) -> int:
        return 1 + sum(c.group_count() for c in self._children)

    def dissolve(self) -> List[Evidence]:
        parent = self.parent
        if parent is None:
            raise InvalidHierarchyOperation("The investigation case root cannot be removed.")
        moved = self.get_children()
        for child in moved:                          # promote children to the grandparent
            self.remove(child)
            parent.add(child)
        parent.remove(self)
        return moved

    def analyze(self, actor: str = "Investigator") -> Dict[str, Any]:
        results = [child.analyze(actor) for child in self._children]     # delegate; nested groups recurse
        steps = [f"{self.class_name}.analyze() received", f"Delegated to {len(results)} child evidence object(s)", "Aggregated child results"]
        s = self.summary()
        return self._result("COMPLETED", steps, {"network": s["network"], "suspicious": s["suspicious"]}, results)

    def verify(self, actor: str = "Investigator") -> None:
        for child in self._children:
            child.verify(actor)

    def custody(self) -> List[Dict[str, Any]]:
        events = list(self._custody)
        for child in self._children:
            events.extend(child.custody())
        return sorted(events, key=lambda e: e["occurred_at"])

    def summary(self) -> Dict[str, int]:
        total = dict(ZERO)
        for child in self._children:
            for key, value in child.summary().items():
                total[key] += value
        return total

    def get_status(self) -> str:
        s = self.summary()
        if s["items"] == 0:
            return "PENDING"
        if s["flagged"]:
            return "FLAGGED"
        if s["analyzed"] == s["items"]:
            return "ANALYZED"
        return "VERIFIED" if s["verified"] == s["items"] else "PENDING"

    def display(self) -> Dict[str, Any]:
        d = self._base_display()
        d.update({"children_count": len(self._children), "group_type": self.group_type, "category": self.category,
                  "analysis": "READY" if self.summary()["items"] else "EMPTY"})
        return d
