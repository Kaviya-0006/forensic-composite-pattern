"""COMPONENT of the Composite pattern: the interface shared by individual evidence (Leaf) and evidence groups (Composite)."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional


def now() -> datetime:
    return datetime.now()


class Evidence(ABC):
    role = "ABSTRACT"
    is_case_root = False

    def __init__(self, id: str, name: str, type: str, case_id: str, status: str = "PENDING", description: str = "",
                 sha256: str = "", file_size: str = "", source_device: str = "", collected_by: str = "",
                 collected_at: Optional[datetime] = None):
        self.id, self.name, self.type, self.case_id = id, name, type, case_id
        self.status, self.description = status, description
        self.sha256, self.file_size, self.source_device = sha256, file_size, source_device
        self.collected_by, self.collected_at = collected_by, collected_at
        self.parent: Optional["Evidence"] = None          # parent reference, maintained by the Composite
        self._custody: List[Dict[str, Any]] = []
        self._new_custody: List[Dict[str, Any]] = []

    # ---- operations every Evidence object supports (implemented by Leaf and Composite) ----
    @abstractmethod
    def analyze(self, actor: str = "Investigator") -> Dict[str, Any]: ...
    @abstractmethod
    def display(self) -> Dict[str, Any]: ...
    @abstractmethod
    def get_children(self) -> List["Evidence"]: ...
    @abstractmethod
    def add(self, child: "Evidence") -> None: ...
    @abstractmethod
    def remove(self, child: "Evidence") -> None: ...
    @abstractmethod
    def validate_add(self, child: "Evidence") -> None: ...
    @abstractmethod
    def verify(self, actor: str = "Investigator") -> None: ...
    @abstractmethod
    def get_status(self) -> str: ...
    @abstractmethod
    def summary(self) -> Dict[str, int]: ...

    # ---- shared behaviour ----
    @property
    def class_name(self) -> str:
        return type(self).__name__

    def is_composite(self) -> bool:
        return False

    def get_child(self, index: int) -> Optional["Evidence"]:
        kids = self.get_children()
        return kids[index] if 0 <= index < len(kids) else None

    def descendant_count(self) -> int:
        return 0

    def group_count(self) -> int:
        return 0

    def walk(self) -> Iterator["Evidence"]:
        yield self
        for child in self.get_children():
            yield from child.walk()

    def find(self, evidence_id: str) -> Optional["Evidence"]:
        return next((n for n in self.walk() if n.id == evidence_id), None)

    def path(self) -> List["Evidence"]:
        return (self.parent.path() if self.parent else []) + [self]

    def root(self) -> "Evidence":
        return self.parent.root() if self.parent else self

    def dissolve(self) -> List["Evidence"]:
        """Detach this object from its parent. Composites override this to keep their children."""
        from .errors import InvalidHierarchyOperation
        if self.parent is None:
            raise InvalidHierarchyOperation("The investigation case root cannot be removed.")
        self.parent.remove(self)
        return []

    # ---- chain of custody ----
    def custody(self) -> List[Dict[str, Any]]:
        return sorted(self._custody, key=lambda e: e["occurred_at"])

    def record_custody(self, event: Dict[str, Any]) -> None:
        self._custody.append(event)

    def emit_custody(self, action: str, actor: str, integrity: str = "INTACT", details: str = "", at: Optional[datetime] = None):
        event = {"evidence_id": self.id, "evidence_name": self.name, "action": action, "actor": actor,
                 "integrity": integrity, "details": details, "occurred_at": at or now()}
        self._custody.append(event)
        self._new_custody.append(event)
        return event

    def pop_new_custody(self) -> List[Dict[str, Any]]:
        events, self._new_custody = self._new_custody, []
        return events

    def on_created(self, actor: str) -> None: ...
    def on_moved(self, actor: str, old_parent: str, new_parent: str) -> None: ...

    # ---- serialisation ----
    def _base_display(self) -> Dict[str, Any]:
        return {"id": self.id, "case_id": self.case_id, "parent_id": self.parent.id if self.parent else None,
                "parent_name": self.parent.name if self.parent else None, "name": self.name, "type": self.type,
                "kind": "group" if self.is_composite() else "leaf", "role": self.role, "class_name": self.class_name,
                "status": self.get_status(), "description": self.description, "hash": self.sha256,
                "file_size": self.file_size, "source_device": self.source_device, "collected_by": self.collected_by,
                "collected_at": self.collected_at, "descendant_count": self.descendant_count(), "summary": self.summary()}

    def to_tree(self) -> Dict[str, Any]:
        node = self.display()
        node["children"] = [c.to_tree() for c in self.get_children()]   # recursion through the common interface
        return node

    def _result(self, status: str, steps: List[str], findings: Dict[str, int], children: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"evidence_id": self.id, "name": self.name, "type": self.type, "class_name": self.class_name,
                "role": self.role, "status": status, "steps": steps, "findings": findings, "children": children}
