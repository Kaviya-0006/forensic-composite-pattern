from datetime import datetime
from typing import Optional


def log(repo, actor: str, action: str, message: str, case_id: Optional[str] = None, entity_id: Optional[str] = None):
    repo.add_activity({"case_id": case_id, "actor": actor, "action": action, "entity_id": entity_id, "message": message, "created_at": datetime.now()})


def list_activity(repo, limit: int = 50, case_id: Optional[str] = None):
    return repo.list_activity(limit, case_id)
