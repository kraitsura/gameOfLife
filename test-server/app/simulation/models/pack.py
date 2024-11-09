from typing import List, Optional, Set
from uuid import UUID, uuid4
from app.simulation.core.interfaces import GameObject
from app.simulation.models import Entity
from app.simulation.core.context import SimulationContext

class Pack(GameObject):
    def __init__(self, members: List[Entity]):
        self.id: UUID = uuid4()
        self.members: Set[Entity] = set(members)

    def update(self, context: 'SimulationContext', dt: float) -> None:
        for member in self.members:
            member.update(context, dt)

    def serialize(self) -> dict:
        return {
            "id": str(self.id),
            "members": [str(member.id) for member in self.members]
        }

    @classmethod
    def deserialize(cls, data: dict, context: SimulationContext) -> 'Pack':
        return cls(members=[context.get_by_id(Entity, id) for id in data["members"]])
