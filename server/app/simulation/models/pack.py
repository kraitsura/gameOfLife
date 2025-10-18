from typing import List, Set, TYPE_CHECKING
from uuid import uuid4
from app.simulation.core.interfaces import GameObject
from app.simulation.models import Entity

if TYPE_CHECKING:
    from app.simulation.core.context import SimulationContext

class Pack(GameObject):
    def __init__(self, members: List[Entity]):
        self.id = str(uuid4())
        self.members: Set[Entity] = set(members)

    def update(self, context: 'SimulationContext', dt: float) -> None:
        for member in self.members:
            member.update(context, dt)

    def serialize(self) -> dict:
        """Serialize pack to camelCase format for frontend compatibility"""
        return {
            "id": str(self.id),
            "memberIds": [str(member.id) for member in self.members]
        }
